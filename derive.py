#!/usr/bin/env python3
"""
derive.py — Derivation Engine v1.0 for the Field Playbooks Kit.

Computes a composed rail cell (audience × industry) from the authored YAML profiles,
the currency-signal map, and the benchmark corpus. Called at session start by the kit
and at harness build time by the bundler script.

Public API:
    derive(audience, industry, config) -> DeriveResult
    log_correction(audience, industry, original_signals, corrected_signals, analyst_note) -> None
    DeriveConfig, DeriveResult, SignalEntry
"""

from __future__ import annotations

try:
    import yaml
except ImportError as _yaml_missing:
    # PyYAML is a third-party package and Python does not ship it. Say what is missing and how to get it, in a
    # sentence a person can act on, instead of a bare traceback. Run as a program this exits non-zero; imported
    # as a library it raises ModuleNotFoundError (an ImportError) with name="yaml" and the same sentence. The name
    # matters: harness_bundle._exit_on_missing_dependency routes on exc.name == "yaml", so a bare ImportError
    # would slip past the bundler's handler and surface as a traceback.
    _YAML_HELP = ("derive.py needs the PyYAML package, which is not installed for this Python. "
                  "Install it with: python3 -m pip install pyyaml")
    if __name__ == "__main__":
        raise SystemExit(_YAML_HELP)
    raise ModuleNotFoundError(_YAML_HELP, name="yaml") from _yaml_missing
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

# ── Constants ─────────────────────────────────────────────────────────────────

_ROOT = Path(__file__).parent

# Ordered from lowest to highest altitude. Hardcoded — do not read from MANIFEST.
ALTITUDE_ORDER = [
    "event", "session", "cohort", "population", "path", "arc", "portfolio"
]

VALID_AUDIENCES = [
    "engineering", "product-mgmt", "ux-design", "support",
    "data", "customer-experience", "marketing", "acct-mgmt", "exec",
]

NON_EXEC_AUDIENCES = [
    "engineering", "product-mgmt", "ux-design", "support",
    "data", "customer-experience", "marketing", "acct-mgmt",
]

VALID_INDUSTRIES = ["retail", "fintech", "saas", "travel", "gaming"]

TEMPO_MAP = {"fast": 3, "slow": 6}
L1_CODES: frozenset = frozenset({"TRS", "RSK"})
# Canonical 4-step ASR session-review protocol. Referenced by DeriveResult.asr_protocol.
# derive.py is a static engine and does not call these tools directly; the harness agent
# layer executes the protocol when DeriveResult.asr_protocol == "required".
ASR_PROTOCOL_STEPS: list = [
    "get_session_events",
    "session_open",
    "session_screenshot | session_get_a11y_tree | session_diff",
    "session_close",
]

# Wave 6 Part B: signal keys that receive a ranking boost when session_mode == "tactical".
# These are the five new KNW arc signals added in Wave 6 Part A — the hypothesis-driven
# signals that only surface when the analyst enters with a named, falsifiable question.
# The boost lifts them above the sort's pattern-signal penalty (dimension 4: not requires_segment),
# making them reachable within the tempo window when a hypothesis is active.
TACTICAL_SIGNAL_KEYS: frozenset = frozenset({
    "funnel_median_time_hypothesis",
    "campaign_sourced_session",
    "conversion_drop_significant",
    "error_with_journey_break",
    "escalation_to_eng",
})

# Wave 6 Part C: per-audience preferred signal keys.
# Applied in both exploratory and tactical mode. Signals in this set receive persona_preferred=1
# in _rank_and_truncate(), lifting them above non-preferred signals in the same sort tier.
# persona_preferred sits above tactical_boost so that audience identity is the primary
# differentiator and hypothesis type is the secondary.
# Audiences with no entry (support) get frozenset().
# Wave 8: CX and AM now have static preferred keys based on their gold signal families.
# These are overridden at runtime by ROLE_BOUNDARY_PREFERRED_KEYS when a role.boundary
# fact is present in DeriveConfig.role_boundary.
PERSONA_PREFERRED_KEYS: dict = {
    "product-mgmt": frozenset({
        "escalation_to_eng",
        "error_with_journey_break",
    }),
    "ux-design": frozenset({
        "funnel_median_time_hypothesis",
        "error_with_journey_break",
    }),
    "data": frozenset({
        "conversion_drop_significant",
    }),
    "marketing": frozenset({
        "campaign_sourced_session",
    }),
    "engineering": frozenset({
        "error_rate_spike_no_behavior_change",
        "exception_recurrence",
    }),
    # Wave 8: trust-recovery arc — post-incident return behavior (one account, one journey).
    "customer-experience": frozenset({
        "post_incident_depth_drop",
        "cautious_return_dead_click",
        "session_recurrence_on_error",
        "reload_surge_post_error",
    }),
    # Wave 8: portfolio health arc — longitudinal account-level engagement signals.
    "acct-mgmt": frozenset({
        "session_depth_decline",
        "feature_abandonment_trend",
    }),
}

# Wave 8: Role-boundary preferred keys — dynamic override layer on top of PERSONA_PREFERRED_KEYS.
# When DeriveConfig.role_boundary is set (from the 7B role-boundary gate answer stored in
# org_memory), this dict overrides the static per-audience preferred keys. Audience-agnostic
# by design: a CX analyst who owns expansion + renewal gets AM-shaped signal preference, and
# an AM analyst with a churn/enablement remit gets CX-shaped preference.
ROLE_BOUNDARY_PREFERRED_KEYS: dict = {
    "churn-enablement": frozenset({
        "post_incident_depth_drop",
        "cautious_return_dead_click",
        "session_recurrence_on_error",
        "reload_surge_post_error",
    }),
    "expansion-renewal": frozenset({
        "session_depth_decline",
        "feature_abandonment_trend",
    }),
}

# Wave 6 Part D: signal keys lifted when the analyst's hypothesis maps to a named object family.
# hypothesis_match sits above persona_preferred so that the shape of the question overrides
# the audience's static preference when a specific object is named.
# When hypothesis_object == "none", hypothesis_match = 0 for all signals → C's persona_preferred governs.
HYPOTHESIS_OBJECT_KEYS: dict = {
    "funnel_step": frozenset({"funnel_median_time_hypothesis", "error_with_journey_break"}),
    "campaign":    frozenset({"campaign_sourced_session"}),
    "error":       frozenset({"error_with_journey_break", "escalation_to_eng", "error_rate_spike_no_behavior_change"}),
    "conversion":  frozenset({"conversion_drop_significant"}),
    "none":        frozenset(),
}


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class DeriveConfig:
    logging: bool = False
    default_audiences_by_role: Dict[str, List[str]] = None
    persona_currency_boost: bool = True   # set False in derive-config.yaml to revert to pre-boost ranking
    logging_enabled: bool = False         # co-creation decision logging; default off (CSE/SE zero-route proof)
    logging_tier: str = "off"            # "off" | "internal" | "customer"; "internal" wired via Step 4b internal branch in build-harness.md
    session_mode: str = "exploratory"    # "exploratory" | "tactical" — set by harness pre-derive prompt (Wave 6 Part B)
    hypothesis_text: str = ""            # free text from analyst; empty when session_mode == "exploratory"
    role_boundary: str = ""             # from org_memory role.boundary gate (Wave 8); "" = use static PERSONA_PREFERRED_KEYS

    def __post_init__(self):
        if self.default_audiences_by_role is None:
            self.default_audiences_by_role = {}

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "DeriveConfig":
        """Load from derive-config.yaml at workspace root.
        Returns defaults (logging=False, default_audiences_by_role={}) if the file
        is absent or unreadable. The default_audiences_by_role key is optional in the
        YAML — any config file without it defaults to an empty dict.
        """
        path = config_path or (_ROOT / "derive-config.yaml")
        if not path.exists():
            return cls(logging=False, default_audiences_by_role={})
        raw = yaml.safe_load(path.read_text()) or {}
        raw_mapping = raw.get("default_audiences_by_role") or {}
        # Normalise: ensure every value is a list of strings
        audiences_by_role: Dict[str, List[str]] = {
            str(role): [str(a) for a in (audiences or [])]
            for role, audiences in raw_mapping.items()
        }
        return cls(
            logging=bool(raw.get("logging", False)),
            default_audiences_by_role=audiences_by_role,
            persona_currency_boost=bool(raw.get("persona_currency_boost", True)),
            logging_enabled=bool(raw.get("logging_enabled", False)),
            logging_tier=str(raw.get("logging_tier", "off")),
        )


@dataclass
class DecisionLog:
    """One co-creation decision log entry. Written to co-creation-registry.yaml
    when DeriveConfig.logging_enabled is True and logging_tier != "off".
    Only the workshop-operator build path (build-harness.md gate) sets logging_tier: customer.
    CSE/SE self-service harnesses always have logging_tier: off.
    """
    date: str
    audience: str
    industry: str
    asr_protocol: str
    signals: list    # list[str] signal keys
    analyst_note: str = ""
    logging_tier: str = "off"


@dataclass
class SignalEntry:
    signal: str                       # signal key from currency-signals.yaml
    currency: str                     # MANIFEST currency code or "substrate"
    signal_class: str                 # "exchange" or "substrate"
    requires_segment: bool            # True when pattern: true in currency-signals.yaml
    benchmark_deviation: Optional[float]  # industry_rate/all_rate; None if not in corpus
    intent: Optional[str]             # parent intent label from currency-signals.yaml


@dataclass
class DeriveResult:
    status: str                       # always "ok" — field exists for serializer guard
    audience: str
    industry: str
    signals: list                     # list[SignalEntry], truncated to tempo count
    currency_mix: list                # list[str] — ranked currency codes driving derivation
    tempo: int                        # 3 (fast) or 6 (slow)
    entry_altitude: str               # characteristic altitude for this audience
    exec_rollup: bool                 # True only when audience == "exec"
    pattern_signals_excluded: int     # count excluded by legibility rule
    missing_benchmark_count: int      # signals with no benchmark corpus entry
    asr_protocol: str = "none"        # "none" | "optional" | "required" — max ASR tier across all persona jobs
    asr_protocol_steps: list = field(default_factory=list)   # ordered 4-step sequence; populated iff asr_protocol != "none"
    asr_required_job_ids: list = field(default_factory=list) # job IDs with asr=="required"; empty when none
    session_mode: str = "exploratory" # "exploratory" | "tactical" — echoed from DeriveConfig (Wave 6 Part B)
    hypothesis_text: str = ""         # echoed from DeriveConfig; empty when exploratory
    hypothesis_object: str = "none"   # classified object family (Wave 6 Part D): funnel_step | campaign | error | conversion | none
    role_boundary: str = ""           # echoed from DeriveConfig (Wave 8); "" = static PERSONA_PREFERRED_KEYS governed
    segment: Optional[str] = None     # industry segment applied (gaming: "igaming"); None = default profile


# ── File Loaders ──────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    """Load a YAML file. Raises FileNotFoundError with parse detail on YAML error."""
    try:
        return yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        raise FileNotFoundError(f"YAML parse error in {path}: {e}") from e


def _load_persona(audience: str) -> dict:
    path = _ROOT / ".claude" / "rails" / f"persona-{audience}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Persona profile not found: {path}")
    return _load_yaml(path)


def _load_industry(industry: str) -> dict:
    path = _ROOT / ".claude" / "rails" / f"industry-{industry}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Industry profile not found: {path}")
    return _load_yaml(path)


def _load_currency_signals() -> dict:
    path = _ROOT / "_workshop" / "field-model" / "currency-signals.yaml"
    if not path.exists():
        raise FileNotFoundError(f"currency-signals.yaml not found: {path}")
    return _load_yaml(path)


def _load_benchmark_corpus() -> dict:
    path = _ROOT / "_workshop" / "field-model" / "benchmark-corpus.yaml"
    if not path.exists():
        raise FileNotFoundError(f"benchmark-corpus.yaml not found: {path}")
    return _load_yaml(path)


# ── Hypothesis Classifier ─────────────────────────────────────────────────────

def _classify_hypothesis(text: str) -> str:
    """Classify analyst hypothesis text into a closed object-family enum.

    Returns: 'funnel_step' | 'campaign' | 'error' | 'conversion' | 'none'

    Rules: keyword / phrase matching only. No LLM call. Ambiguous text (multiple
    families match) → 'none'. Empty text or explicit negation → 'none'.

    Marketing prompt must never require UTM, urchin, or query-parameter vocabulary —
    analysts name campaigns in plain language; this classifier translates.
    """
    if not text:
        return "none"
    t = text.strip().lower()
    if t in ("no", "none", "n/a", "nope", ""):
        return "none"

    matches: set = set()

    if any(kw in t for kw in ("campaign", "email blast", "facebook", "tiktok", "instagram",
                               "google ads", " ads", "launch ", "promotion", "promo ")):
        matches.add("campaign")

    if any(kw in t for kw in ("step", "funnel", "checkout", "median time",
                               "takes too long", "onboarding", "time to complete")):
        matches.add("funnel_step")

    if any(kw in t for kw in ("conversion", "real vs noise", "significant drop",
                               "drop real", "is the drop")):
        matches.add("conversion")

    if any(kw in t for kw in ("error", "bug", "exception", "broken", "spike")):
        matches.add("error")

    return next(iter(matches)) if len(matches) == 1 else "none"


# ── R1 Steps ──────────────────────────────────────────────────────────────────

_SEGMENTS = {"gaming": ("f2p", "igaming")}


def _apply_segment(industry_profile: dict, industry: str, segment: Optional[str]) -> dict:
    """Return the industry profile with a segment's currency ranking applied.

    The override replaces industry_profile["end_user_currencies"] once, here, so every
    downstream step sees one consistent profile. None and the default segment return the
    profile untouched. Fails loudly on a segment the industry does not define.
    """
    if segment is None:
        return industry_profile
    legal = _SEGMENTS.get(industry)
    if legal is None:
        raise ValueError(f"Industry {industry!r} has no segments; got segment={segment!r}")
    if segment not in legal:
        raise ValueError(f"Unknown segment {segment!r} for {industry!r}. Valid: {legal}")
    if segment == "f2p":
        return industry_profile
    override = (industry_profile.get("segments") or {}).get(segment, {}).get("end_user_currencies")
    if not override:
        raise ValueError(f"Industry profile {industry!r} has no segments.{segment}.end_user_currencies")
    return {**industry_profile, "end_user_currencies": override}


def _currency_mix(industry_profile: dict) -> list:
    """Step 1: Resolve ranked currency mix from industry profile.

    Handles two schema shapes:
    - Flat list (fintech, gaming, saas): ranked = ["ACQ", "KNW", ...]
    - Cohort-conditional dict (retail, travel):
        ranked = {"cohorts": {...}, "population_default": [...]}
        -> use population_default; one composed cell per audience x industry pair.
    """
    ranked = industry_profile.get("end_user_currencies", {}).get("ranked", [])
    if isinstance(ranked, dict) and "cohorts" in ranked:
        return ranked.get("population_default", [])
    if isinstance(ranked, list):
        return ranked
    return []


def _exchange_candidates(currency_mix: list, currency_signals: dict) -> list:
    """Step 2: Collect exchange signal candidates for each currency in the mix.

    Traverses exchange_signals[currency_code].intents[*].signals[*].
    Deduplicates on signal key — first appearance wins (preserves currency attribution).
    """
    exchange_signals = currency_signals.get("exchange_signals", {})
    candidates = []
    seen: set = set()

    for currency_code in currency_mix:
        currency_data = exchange_signals.get(currency_code, {})
        for intent in currency_data.get("intents", []):
            intent_label = intent.get("label", "")
            for sig in intent.get("signals", []):
                signal_key = sig.get("signal", "")
                if not signal_key or signal_key in seen:
                    continue
                seen.add(signal_key)
                candidates.append(SignalEntry(
                    signal=signal_key,
                    currency=currency_code,
                    signal_class="exchange",
                    requires_segment=bool(sig.get("pattern", False)),
                    benchmark_deviation=None,   # enriched in Step 6
                    intent=intent_label,
                ))
    return candidates


def _l1_exchange_candidates(job_currencies: set, currency_signals: dict) -> list:
    """Step 2b: Collect exchange signal candidates for L1 currencies in job_currencies.

    Industry profiles never list L1 codes (TRS, RSK), so _exchange_candidates() never
    collects them. This step injects those signals for personas whose jobs carry L1 currencies.
    All authored L1 signals carry pattern=True — they require arc altitude to pass legibility.
    Cross-L2/L1 deduplication is handled downstream by _union_candidates().

    Added: Wave 3 destack (wave3-destack-engine-20260912).
    """
    exchange_signals = currency_signals.get("exchange_signals", {})
    candidates = []
    seen: set = set()

    l1_in_jobs = job_currencies & L1_CODES
    for currency_code in sorted(l1_in_jobs):
        currency_data = exchange_signals.get(currency_code, {})
        for intent in currency_data.get("intents", []):
            intent_label = intent.get("label", "")
            for sig in intent.get("signals", []):
                signal_key = sig.get("signal", "")
                if not signal_key or signal_key in seen:
                    continue
                seen.add(signal_key)
                candidates.append(SignalEntry(
                    signal=signal_key,
                    currency=currency_code,
                    signal_class="exchange",
                    requires_segment=bool(sig.get("pattern", False)),
                    benchmark_deviation=None,
                    intent=intent_label,
                ))
    return candidates


def _substrate_candidates(currency_signals: dict) -> list:
    """Step 3: Collect substrate signal candidates (lcp, network_error, availability).

    Reads substrate_signals list. Only the three R1-specified signals are included.
    """
    substrate_signals = currency_signals.get("substrate_signals", [])
    candidates = []
    target_signals = {"lcp", "network_error", "availability"}

    for sig in substrate_signals:
        signal_key = sig.get("signal", "")
        if signal_key not in target_signals:
            continue
        candidates.append(SignalEntry(
            signal=signal_key,
            currency="substrate",
            signal_class="substrate",
            requires_segment=False,
            benchmark_deviation=None,
            intent=None,
        ))
    return candidates


def _union_candidates(exchange: list, substrate: list) -> list:
    """Step 4: Union of exchange and substrate candidates.

    On signal-key collision, keep the exchange-class entry — it carries the more
    specific currency attribution. Substrate entry is deduplicated away.
    """
    result = []
    seen: set = set()
    for entry in exchange:
        if entry.signal not in seen:
            seen.add(entry.signal)
            result.append(entry)
    for entry in substrate:
        if entry.signal not in seen:
            seen.add(entry.signal)
            result.append(entry)
    return result


def _persona_job_currencies(persona_profile: dict) -> set:
    """Option C helper: Extract the set of currency_code values from all persona jobs.

    Returns an empty set if no jobs or no currency_code fields are present.
    Called once per derive() invocation; result passed to _narrow_by_persona_currencies.
    """
    currencies: set = set()
    for job in persona_profile.get("jobs", []):
        code = job.get("currency_code")
        if code:
            currencies.add(code)
    return currencies


def _derive_asr_protocol(persona_profile: dict) -> str:
    """Return the highest-priority ASR tier across all persona jobs.

    Priority: required > optional > none.
    Blank or missing asr fields are treated as "none" (per W4-01 normalization).
    Callers use this to populate DeriveResult.asr_protocol, which gates whether
    the harness agent layer invokes the ASR_PROTOCOL_STEPS sequence.
    """
    tier_rank = {"required": 2, "optional": 1, "none": 0}
    best = 0
    for job in persona_profile.get("jobs", []):
        tier = str(job.get("asr", "none")).strip().lower() or "none"
        best = max(best, tier_rank.get(tier, 0))
    return {2: "required", 1: "optional", 0: "none"}[best]


def _collect_asr_required_ids(persona_profile: dict) -> list:
    """Return job IDs where asr == 'required'."""
    return [
        job.get("id", "")
        for job in persona_profile.get("jobs", [])
        if (str(job.get("asr", "none")).strip().lower() or "none") == "required"
    ]


def _check_l2_only_prohibition(jobs: list, grammar_path: Path) -> None:
    """Raise ValueError if any job uses a currency code listed in l2_only_prohibition.

    Reads l2_only_prohibition from currency-grammar.yaml at derivation time and
    enforces that no persona job carries a code prohibited at the analyst layer.
    Called after the persona jobs list is loaded and before signals are ranked.

    This closes the Q-D packaging gate condition: the prohibition was previously
    documentation-only in currency-grammar.yaml; this function enforces it at runtime.
    Added: I-11, Wave 2 (wave2-trs-rsk-corpus-20260912).
    """
    grammar = yaml.safe_load(grammar_path.read_text()) or {}
    # l2_only_prohibition has a nested 'prohibited' dict; top-level keys include 'note'
    prohibited = set(grammar.get("l2_only_prohibition", {}).get("prohibited", {}).keys())
    if not prohibited:
        return
    for job in jobs:
        code = job.get("currency_code", "")
        if code in prohibited:
            raise ValueError(
                f"Job '{job.get('id', '?')}' uses currency_code {code!r} "
                f"which is in l2_only_prohibition. "
                f"L2-only codes cannot be assigned to analyst-layer jobs."
            )


def _narrow_by_persona_currencies(candidates: list, job_currencies: set) -> list:
    """Option C: Re-sort exchange candidates to prioritize persona job currencies.

    Signals whose currency attribute matches job_currencies are moved to the front
    of the exchange section. Substrate signals retain their relative position at the
    back. Within each group, original order is preserved. No signal is dropped.

    Effect: Two personas at the same industry and tempo but with different job
    currency sets produce different exchange signal orderings after this step.
    """
    if not job_currencies:
        return candidates
    priority = []
    remainder = []
    for entry in candidates:
        if entry.signal_class == "exchange" and entry.currency in job_currencies:
            priority.append(entry)
        else:
            remainder.append(entry)
    return priority + remainder


def _characteristic_altitude(persona_profile: dict) -> str:
    """Step 5 helper: Maximum entry_altitude across all jobs in the persona profile.

    Uses ALTITUDE_ORDER for comparison. Defaults to 'event' if no jobs or no
    recognizable altitude values.

    Maximum semantics: the characteristic altitude is the ceiling of what the
    persona can analyze, not the floor. A marketing persona with three arc-level
    jobs and one cohort job should reach arc altitude, unlocking pattern signals.
    MINIMUM semantics were incorrect — they discarded the highest-value jobs.
    """
    jobs = persona_profile.get("jobs", [])
    max_idx = -1

    for job in jobs:
        alt = job.get("entry_altitude", "")
        if alt in ALTITUDE_ORDER:
            idx = ALTITUDE_ORDER.index(alt)
            if idx > max_idx:
                max_idx = idx

    return ALTITUDE_ORDER[max_idx] if max_idx >= 0 else "event"


def _apply_legibility(candidates: list, characteristic_altitude: str) -> tuple:
    """Step 5: Filter candidates by legibility at the characteristic altitude.

    Legibility rule: a candidate is NOT legible if requires_segment == True
    AND characteristic_altitude is below 'arc' in ALTITUDE_ORDER.

    In plain terms: pattern signals (which require segment construction across sessions)
    are only meaningful at arc altitude or above. All current personas have characteristic
    altitude below arc, so all pattern signals are excluded from all current composed cells.

    Returns: (legible_candidates: list, excluded_count: int)
    """
    arc_idx = ALTITUDE_ORDER.index("arc")
    char_idx = ALTITUDE_ORDER.index(characteristic_altitude) if characteristic_altitude in ALTITUDE_ORDER else 0

    legible = []
    excluded_count = 0

    for entry in candidates:
        if entry.requires_segment and char_idx < arc_idx:
            excluded_count += 1
        else:
            legible.append(entry)

    return legible, excluded_count


def _lookup_benchmark_deviation(signal_key: str, industry: str, corpus: dict) -> Optional[float]:
    """Step 6 helper: Look up benchmark deviation for a signal at the given industry.

    Computes: industry_rate / all_rate from corpus slices.global.data.
    Signal key normalization: currency-signals uses singular (rage_click),
    corpus uses plural (rage_clicks) — try signal+'s' first, then signal directly.

    Returns float ratio or None if the signal has no corpus entry.
    """
    rails_to_corpus = {v: k for k, v in corpus.get("industry_to_rails_mapping", {}).items()}
    corpus_industry = rails_to_corpus.get(industry)
    if not corpus_industry:
        return None

    slices_data = corpus.get("slices", {}).get("global", {}).get("data", {})

    # Normalize singular signal key to plural corpus key
    corpus_key = signal_key + "s" if signal_key not in slices_data else signal_key
    if corpus_key not in slices_data:
        return None

    metric_data = slices_data[corpus_key]
    all_rate = metric_data.get("All")
    industry_rate = metric_data.get(corpus_industry)

    if all_rate is None or industry_rate is None or all_rate == 0:
        return None

    return round(float(industry_rate) / float(all_rate), 4)


def _rank_and_truncate(
    candidates: list,
    industry: str,
    corpus: dict,
    tempo: int,
    job_currencies: Optional[set] = None,
    tactical_signal_keys: Optional[frozenset] = None,
    audience: str = "",
    hypothesis_object: str = "none",
    role_boundary: str = "",
) -> tuple:
    """Step 6: Enrich with benchmark deviation, rank by urgency, truncate to tempo.

    Ranking priority (descending):
    1. Exchange signals with L1 job currency (highest) — engineering RSK, etc.
    2. Hypothesis-match signals (Wave 6 Part D) — signals in the object family named
       by the analyst's hypothesis text. Overrides persona preference when a specific
       object is named. Zero for all signals when hypothesis_object == "none".
    3. Persona-preferred signals (Wave 6 Part C) — audience-specific keys that surface
       in both exploratory and tactical mode when no specific hypothesis is active.
    4. Tactical signals (Wave 6 Part B) — bounded boost for hypothesis-driven signals
       in tactical mode; secondary differentiator under hypothesis_match + persona_preferred.
    5. Exchange signals with benchmark entry
    6. Exchange signals without benchmark entry; within each group, in_job_currency first
    7. Substrate signals (lowest)
    Within each tier: persona-currency-matching signals rank above non-matching.
    Higher deviation first within matching groups.

    job_currencies: set of L2 currency codes from the persona's jobs.
    tactical_signal_keys: frozenset of signal keys boosted in tactical mode.
    audience: slug for PERSONA_PREFERRED_KEYS lookup; empty → no preferred keys.
    hypothesis_object: classified object family from _classify_hypothesis(); "none" → no lift.

    Substrate signals always receive in_job_currency=0 (is_exchange==0 gates them out).

    Returns: (truncated_signals: list[SignalEntry], missing_benchmark_count: int)
    """
    for entry in candidates:
        entry.benchmark_deviation = _lookup_benchmark_deviation(entry.signal, industry, corpus)

    _job_currencies: set = job_currencies or set()
    _tactical: frozenset = tactical_signal_keys or frozenset()
    # Wave 8: role_boundary overrides static PERSONA_PREFERRED_KEYS when set.
    _preferred: frozenset = (
        ROLE_BOUNDARY_PREFERRED_KEYS.get(role_boundary)
        if role_boundary
        else PERSONA_PREFERRED_KEYS.get(audience, frozenset())
    ) or frozenset()
    _hypothesis_keys: frozenset = HYPOTHESIS_OBJECT_KEYS.get(hypothesis_object, frozenset())

    def sort_key(e: SignalEntry):
        is_exchange = 1 if e.signal_class == "exchange" else 0
        is_l1_job_currency = (
            1 if (is_exchange and e.currency in L1_CODES and e.currency in _job_currencies)
            else 0
        )
        # Hypothesis-match: analyst named a specific object; its signal family surfaces first.
        hypothesis_match = 1 if (is_exchange and e.signal in _hypothesis_keys) else 0
        # Persona-preferred: audience-specific static lift (exploratory + tactical).
        persona_preferred = 1 if (is_exchange and e.signal in _preferred) else 0
        # Bounded boost: lifts hypothesis-driven signals above the pattern-signal penalty
        # when the analyst enters with a formed hypothesis (session_mode == "tactical").
        tactical_boost = 1 if (is_exchange and e.signal in _tactical) else 0
        has_benchmark = 1 if e.benchmark_deviation is not None else 0
        in_job_currency = (
            1 if (is_exchange and e.currency in _job_currencies) else 0
        )
        dev = e.benchmark_deviation if e.benchmark_deviation is not None else 0.0
        return (is_exchange, is_l1_job_currency, hypothesis_match, persona_preferred, tactical_boost, has_benchmark, in_job_currency, dev)

    ranked = sorted(candidates, key=sort_key, reverse=True)
    missing_count = sum(1 for e in ranked if e.benchmark_deviation is None)

    return ranked[:tempo], missing_count


# ── Exec Roll-Up ──────────────────────────────────────────────────────────────

def _exec_rollup(industry: str, config: DeriveConfig) -> DeriveResult:
    """Derive exec result by rolling up all 8 non-exec audiences at the given industry.

    Unions all signal lists, deduplicates on signal key (first appearance wins),
    re-ranks by benchmark deviation, truncates to 6 (exec is always slow).
    Sets entry_altitude='portfolio' and exec_rollup=True.
    """
    all_signals: list = []
    seen_signals: set = set()

    for aud in NON_EXEC_AUDIENCES:
        try:
            sub = derive(aud, industry, config)
        except (ValueError, FileNotFoundError):
            continue
        for entry in sub.signals:
            if entry.signal not in seen_signals:
                seen_signals.add(entry.signal)
                all_signals.append(entry)

    # Re-rank the union
    corpus = _load_benchmark_corpus()
    for entry in all_signals:
        if entry.benchmark_deviation is None:
            entry.benchmark_deviation = _lookup_benchmark_deviation(entry.signal, industry, corpus)

    def sort_key(e: SignalEntry):
        is_exchange = 1 if e.signal_class == "exchange" else 0
        has_benchmark = 1 if e.benchmark_deviation is not None else 0
        dev = e.benchmark_deviation if e.benchmark_deviation is not None else 0.0
        return (is_exchange, has_benchmark, dev)

    ranked = sorted(all_signals, key=sort_key, reverse=True)
    truncated = ranked[:6]
    missing = sum(1 for e in truncated if e.benchmark_deviation is None)

    return DeriveResult(
        status="ok",
        audience="exec",
        industry=industry,
        signals=truncated,
        currency_mix=[],  # not meaningful for exec roll-up
        tempo=6,
        entry_altitude="portfolio",
        exec_rollup=True,
        pattern_signals_excluded=0,
        missing_benchmark_count=missing,
    )


# ── Logging ───────────────────────────────────────────────────────────────────

def _write_log(result: DeriveResult, config: DeriveConfig) -> None:
    """Append a derivation run entry to _workshop/derive-log.yaml when logging is enabled.

    Log is a file (not stdout) because harness build-time calls cannot capture stdout.
    The log grows without bound; it is a debugging aid, not a runtime dependency.
    """
    if not config.logging:
        return
    log_path = _ROOT / "_workshop" / "derive-log.yaml"
    entry = [{
        "run": {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "audience": result.audience,
            "industry": result.industry,
            "currency_mix": result.currency_mix,
            "entry_altitude": result.entry_altitude,
            "final_signals": [s.signal for s in result.signals],
            "pattern_excluded": result.pattern_signals_excluded,
            "missing_benchmark_signals": result.missing_benchmark_count,
            "exec_rollup": result.exec_rollup,
        }
    }]
    with open(log_path, "a") as f:
        f.write(yaml.dump(entry, default_flow_style=False))


def _write_decision_log(result: DeriveResult, config: DeriveConfig) -> None:
    """Append a DecisionLog entry to _workshop/co-creation-registry.yaml.

    Guard: no-op when logging_tier == "off" or logging_enabled is False.
    Only the workshop-operator gate in build-harness.md can produce a harness
    config with logging_tier: customer — CSE/SE self-service always yields "off".
    The logging_tier: internal tier is wired via Step 4b internal branch in build-harness.md.
    """
    if not config.logging_enabled or config.logging_tier == "off":
        return
    registry_path = _ROOT / "_workshop" / "co-creation-registry.yaml"
    existing = {}
    if registry_path.exists():
        existing = yaml.safe_load(registry_path.read_text()) or {}
    entries = existing.get("registry", [])
    entries.append({
        "date": datetime.now().date().isoformat(),
        "audience": result.audience,
        "industry": result.industry,
        "asr_protocol": result.asr_protocol,
        "signals": [s.signal for s in result.signals] if result.signals and hasattr(result.signals[0], "signal") else list(result.signals),
        "analyst_note": "",
        "logging_tier": config.logging_tier,
    })
    existing["registry"] = entries
    with open(registry_path, "w") as f:
        f.write(yaml.dump(existing, default_flow_style=False, sort_keys=False))


# ── Public API ────────────────────────────────────────────────────────────────

def derive(
    audience: str,
    industry: str,
    config: Optional[DeriveConfig] = None,
    segment: Optional[str] = None,
) -> DeriveResult:
    """Run Stage 1 static derivation for the given audience x industry pair.

    `segment` selects an industry segment profile. Only gaming has one: "igaming" replaces
    the industry's end_user_currencies with segments.igaming.end_user_currencies. None and
    "f2p" take the default path unchanged. A segment is not an industry: VALID_INDUSTRIES is
    not widened.

    Raises ValueError for unknown audience, unknown industry, or an unknown segment.
    Raises FileNotFoundError if required YAML sources are absent or unparseable.
    Does not raise for missing benchmark corpus entries — those become deviation=None.
    """
    if config is None:
        config = DeriveConfig()

    # MANIFEST validation — fail loudly on unknown inputs
    if audience not in VALID_AUDIENCES:
        raise ValueError(f"Unknown audience: {audience!r}. Valid: {VALID_AUDIENCES}")
    if industry not in VALID_INDUSTRIES:
        raise ValueError(f"Unknown industry: {industry!r}. Valid: {VALID_INDUSTRIES}")

    # Exec roll-up — no persona file lookup
    if audience == "exec":
        result = _exec_rollup(industry, config)
        _write_log(result, config)
        return result

    # Load all data sources
    persona_profile = _load_persona(audience)
    industry_profile = _load_industry(industry)
    industry_profile = _apply_segment(industry_profile, industry, segment)
    currency_signals = _load_currency_signals()
    corpus = _load_benchmark_corpus()

    # I-11: Enforce l2_only_prohibition — fail fast before any ranking
    _check_l2_only_prohibition(
        persona_profile.get("jobs", []),
        _ROOT / ".claude" / "rails" / "currency-grammar.yaml",
    )

    # ASR protocol tier — max across all persona jobs; set on DeriveResult for harness routing
    asr_protocol_tier = _derive_asr_protocol(persona_profile)
    asr_required_ids = _collect_asr_required_ids(persona_profile)

    # Step 1: Currency mix
    currency_mix = _currency_mix(industry_profile)

    # Collect persona job currencies before candidate steps (needed for Step 2b L1 injection)
    job_currencies = _persona_job_currencies(persona_profile)

    # Step 2: Exchange candidates (L2 currencies from industry profile)
    exchange = _exchange_candidates(currency_mix, currency_signals)

    # Step 2b: L1 supplement — inject TRS/RSK signals for personas with L1 job currencies
    l1_exchange = _l1_exchange_candidates(job_currencies, currency_signals)
    exchange = exchange + l1_exchange

    # Step 3: Substrate candidates
    substrate = _substrate_candidates(currency_signals)

    # Step 4: Union (cross-L2/L1 deduplication handled here)
    candidates = _union_candidates(exchange, substrate)

    # Step 5: Legibility evaluation
    char_altitude = _characteristic_altitude(persona_profile)
    legible, excluded_count = _apply_legibility(candidates, char_altitude)

    # Step 6: Benchmark deviation ranking + truncation
    raw_tempo = persona_profile.get("tempo", "fast")
    if isinstance(raw_tempo, int):
        tempo = raw_tempo if raw_tempo in (3, 6) else 3
    else:
        tempo = TEMPO_MAP.get(str(raw_tempo).lower(), 3)

    boost_currencies = job_currencies if config.persona_currency_boost else set()
    tactical_keys = TACTICAL_SIGNAL_KEYS if config.session_mode == "tactical" else None
    hypothesis_object = _classify_hypothesis(config.hypothesis_text)
    truncated, missing_count = _rank_and_truncate(
        legible, industry, corpus, tempo, boost_currencies, tactical_keys, audience, hypothesis_object,
        config.role_boundary
    )

    # Prepend L1 job currencies to currency_mix so output reflects analyst-job frame
    l1_in_jobs = sorted(job_currencies & L1_CODES)
    effective_currency_mix = l1_in_jobs + currency_mix

    result = DeriveResult(
        status="ok",
        audience=audience,
        industry=industry,
        signals=truncated,
        currency_mix=effective_currency_mix,
        tempo=tempo,
        entry_altitude=char_altitude,
        exec_rollup=False,
        pattern_signals_excluded=excluded_count,
        missing_benchmark_count=missing_count,
        asr_protocol=asr_protocol_tier,
        asr_protocol_steps=ASR_PROTOCOL_STEPS if asr_protocol_tier != "none" else [],
        asr_required_job_ids=asr_required_ids,
        session_mode=config.session_mode,
        hypothesis_text=config.hypothesis_text,
        hypothesis_object=hypothesis_object,
        role_boundary=config.role_boundary,
        # f2p is the default profile: record nothing, so its cell is byte-identical to an unset one
        segment=None if segment == "f2p" else segment,
    )

    _write_log(result, config)
    _write_decision_log(result, config)
    return result


def log_correction(
    audience: str,
    industry: str,
    original_signals: list,
    corrected_signals: list,
    analyst_note: str,
    log_path: Optional[Path] = None,
) -> None:
    """Append a correction entry to _workshop/derive-corrections.yaml.

    Creates the file if absent. NEVER modifies source profile files.
    Token cost: near-zero — one YAML dict append per call.
    See W-23 design: the correction log pattern avoids all risks of direct
    profile mutation (file-write gate, N-5 validation failure, YAML corruption).
    """
    corrections_path = log_path or (_ROOT / "_workshop" / "derive-corrections.yaml")

    if corrections_path.exists():
        existing = yaml.safe_load(corrections_path.read_text()) or {}
    else:
        existing = {}

    corrections = existing.get("corrections", [])
    corrections.append({
        "date": date.today().isoformat(),
        "audience": audience,
        "industry": industry,
        "original_signals": original_signals,
        "corrected_signals": corrected_signals,
        "analyst_note": analyst_note,
        "status": "pending_review",
    })

    header = (
        "# _workshop/derive-corrections.yaml\n"
        "# Derivation corrections — human review log.\n"
        "# Entries are APPEND-ONLY. Apply corrections manually to source profiles.\n"
        "# After applying: run tools/check_profile.py — N-5 compliance required.\n\n"
    )
    corrections_path.write_text(
        header + yaml.dump(
            {"corrections": corrections},
            default_flow_style=False,
            allow_unicode=True,
        )
    )


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) >= 3:
        aud, ind = sys.argv[1], sys.argv[2]
        cfg = DeriveConfig.load()
        r = derive(aud, ind, cfg)
        print(json.dumps({
            "status": r.status,
            "audience": r.audience,
            "industry": r.industry,
            "tempo": r.tempo,
            "entry_altitude": r.entry_altitude,
            "exec_rollup": r.exec_rollup,
            "signals": [s.signal for s in r.signals],
            "currency_mix": r.currency_mix,
            "asr_protocol": r.asr_protocol,
            "asr_protocol_steps": r.asr_protocol_steps,
            "asr_required_job_ids": r.asr_required_job_ids,
            "pattern_signals_excluded": r.pattern_signals_excluded,
            "missing_benchmark_count": r.missing_benchmark_count,
            "session_mode": r.session_mode,
            "hypothesis_text": r.hypothesis_text,
            "hypothesis_object": r.hypothesis_object,
            "role_boundary": r.role_boundary,
        }, indent=2))
    else:
        print("Usage: python3 derive.py <audience> <industry>")
        sys.exit(1)
