from __future__ import annotations

from dataclasses import dataclass
from math import fsum
from pathlib import Path
from tempfile import TemporaryDirectory

from .benchmark import Pair, evaluate
from .core.engine import TasteEngine


@dataclass(frozen=True)
class TasteBenchCase:
    domain: str
    train: tuple[Pair, ...]
    sealed: tuple[Pair, ...]


def _pairs(context: str, preferred: tuple[str, ...], rejected: tuple[str, ...]) -> tuple[Pair, ...]:
    if len(preferred) != len(rejected):
        raise ValueError("preferred/rejected fixture lengths must match")
    return tuple(Pair(a, b, context) for a, b in zip(preferred, rejected))


def deterministic_context_cases() -> tuple[TasteBenchCase, ...]:
    """Synthetic train/sealed families. Sealed wording is withheld from training evidence."""
    return (
        TasteBenchCase(
            domain="writing",
            train=(
                Pair("Sales rose 12% after retries fell.", "We leverage seamless strategic capabilities.", "status update"),
                Pair("Latency fell from 420ms to 260ms.", "Our innovative ecosystem unlocks transformative value.", "status update"),
                Pair("We gather to honour years of patient service and shared achievement.", "Service improved 8%.", "ceremonial speech"),
                Pair("Tonight we celebrate the people who carried this work forward.", "Output rose 6%.", "ceremonial speech"),
            ),
            sealed=(
                *_pairs("status update",
                    ("Errors fell 19% after validation moved earlier.", "Build time dropped from 11 minutes to 8 minutes.", "Cache misses fell 14% after the index change.", "The migration completed with zero failed records."),
                    ("We enable holistic synergistic outcomes.", "Our strategy unlocks integrated excellence.", "The platform empowers transformative capabilities.", "We leverage a seamless innovation ecosystem.")),
                *_pairs("ceremonial speech",
                    ("Today we recognise the craft, patience, and care behind this milestone.", "This evening belongs to everyone who kept the work moving through difficult weeks.", "We honour the quiet discipline that turned an idea into a shared achievement.", "Let this milestone recognise the people whose steady effort made it possible."),
                    ("Throughput rose 9%.", "Attendance increased 7%.", "Output reached 1,240 units.", "Completion time fell 5%.")),
            ),
        ),
        TasteBenchCase(
            domain="writing",
            train=(
                Pair("Deploy finished in 7 minutes with zero rollback.", "We drive next-generation integrated excellence.", "incident note"),
                Pair("Three requests failed after the cache expired.", "Our platform empowers dynamic transformation.", "incident note"),
                Pair("A measured opening can establish context before the central claim.", "Open with the result.", "essay introduction"),
                Pair("The first paragraph should orient the reader before compressing the argument.", "Lead with one metric.", "essay introduction"),
            ),
            sealed=(
                *_pairs("incident note",
                    ("Queue depth returned to normal at 14:32.", "The worker recovered after the second restart at 09:18.", "Five writes timed out before the connection pool was reset.", "Error rate returned below 1% after the rollback."),
                    ("We unlock resilient operational synergy.", "Our solution accelerates strategic transformation.", "We deliver adaptive next-generation excellence.", "The ecosystem enables seamless operational value.")),
                *_pairs("essay introduction",
                    ("Begin by locating the problem in its historical setting before stating the thesis.", "Establish the institutional context before narrowing to the central argument.", "Orient the reader to the competing explanations before presenting the claim.", "Introduce the underlying tension before compressing it into the thesis."),
                    ("State the thesis immediately.", "Lead with one statistic.", "Open with the conclusion.", "Start with the final recommendation.")),
            ),
        ),
        TasteBenchCase(
            domain="writing",
            train=(
                Pair("Use the smallest reproducible example and include the observed exception.", "The system is broken and weird.", "bug report"),
                Pair("Expected 201; received 409 after the second identical request.", "It fails sometimes.", "bug report"),
                Pair("Could you send the revised figures by Thursday afternoon?", "Send this ASAP.", "client request"),
                Pair("Please confirm whether the revised scope still fits the quoted budget.", "Need confirmation now.", "client request"),
            ),
            sealed=(
                *_pairs("bug report",
                    ("Reproduction: submit the same token twice; expected idempotent success, observed 409.", "On version 2.4.1 the parser raises ValueError for an empty optional field.", "Expected the retry counter to stop at three; observed five requests.", "The failure occurs only when the fixture contains a quoted comma."),
                    ("The API acts strange.", "Parsing is kind of broken.", "Retries seem wrong.", "CSV support does not work.")),
                *_pairs("client request",
                    ("Please share the approved copy before Friday so the build can remain on schedule.", "Could you confirm the final attendee count by 3 PM tomorrow?", "Please review the attached scope and flag any changes before we estimate delivery.", "Could you send the missing dimensions when convenient today?"),
                    ("Need the copy immediately.", "Send attendee count ASAP.", "Approve scope now.", "Send dimensions.")),
            ),
        ),
        TasteBenchCase(
            domain="writing",
            train=(
                Pair("Decision: retain the current cache. Reason: the measured hit-rate gain does not offset invalidation complexity.", "We talked about caching and decided stuff.", "decision record"),
                Pair("Decision: postpone migration until rollback coverage reaches the agreed threshold.", "Migration is delayed for now.", "decision record"),
                Pair("First verify the input checksum, then rerun the importer with dry-run enabled.", "Try importing it again.", "procedure"),
                Pair("Record the current version before changing configuration, then validate one fixture.", "Change the config and test it.", "procedure"),
            ),
            sealed=(
                *_pairs("decision record",
                    ("Decision: keep polling at 60 seconds. Reason: lower intervals add cost without improving the alert SLA.", "Decision: reject the new dependency until its license review is complete.", "Decision: preserve the existing schema because the proposed field is derivable.", "Decision: keep the feature disabled until the sealed benchmark passes."),
                    ("Polling stays the same.", "We are not adding the dependency yet.", "Schema will not change.", "Feature remains off.")),
                *_pairs("procedure",
                    ("Export the current settings, apply the change to one fixture, then compare the generated diff.", "Check the source hash before unpacking the archive, then run validation.", "Create the branch from the frozen commit, apply one change, then execute targeted tests.", "Capture the failing seed first, then rerun it with logging enabled."),
                    ("Change settings and see what happens.", "Unpack it and test.", "Make a branch and modify things.", "Rerun with logs.")),
            ),
        ),
    )


def run_sealed_context_benchmark() -> dict[str, float]:
    baseline_accuracy: list[float] = []
    baseline_brier: list[float] = []
    context_accuracy: list[float] = []
    context_brier: list[float] = []

    with TemporaryDirectory() as directory:
        for index, case in enumerate(deterministic_context_cases()):
            engine = TasteEngine(Path(directory) / f"case-{index}.db")
            for pair in case.train:
                engine.observe_choice(pair.preferred, pair.rejected, domain=case.domain, context=pair.context)
            baseline = evaluate(engine, list(case.sealed), use_context=False)
            contextual = evaluate(engine, list(case.sealed), use_context=True)
            baseline_accuracy.append(baseline["accuracy"])
            baseline_brier.append(baseline["brier"])
            context_accuracy.append(contextual["accuracy"])
            context_brier.append(contextual["brier"])

    return {
        "v0_1_accuracy": fsum(baseline_accuracy) / len(baseline_accuracy),
        "v0_1_brier": fsum(baseline_brier) / len(baseline_brier),
        "v0_2_accuracy": fsum(context_accuracy) / len(context_accuracy),
        "v0_2_brier": fsum(context_brier) / len(context_brier),
        "sealed_pairs": float(sum(len(case.sealed) for case in deterministic_context_cases())),
    }


def run_domain_leakage_check() -> dict[str, float]:
    """Falsify accidental transfer of learned preference weights across domains."""
    preferred = "Latency fell from 420ms to 260ms."
    rejected = "We leverage seamless strategic capabilities."
    context = "status update"
    with TemporaryDirectory() as directory:
        engine = TasteEngine(Path(directory) / "leakage.db")
        control_before = engine.pairwise_probability(preferred, rejected, domain="design", context=context)
        for _ in range(4):
            engine.observe_choice(preferred, rejected, domain="writing", context=context)
        trained = engine.pairwise_probability(preferred, rejected, domain="writing", context=context)
        control_after = engine.pairwise_probability(preferred, rejected, domain="design", context=context)
    return {
        "trained_domain_probability": trained,
        "control_before": control_before,
        "control_after": control_after,
        "absolute_leakage": abs(control_after - control_before),
    }
