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


def deterministic_context_cases() -> tuple[TasteBenchCase, ...]:
    """Synthetic cases with sealed wording withheld from training evidence."""
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
                Pair("Errors fell 19% after validation moved earlier.", "We enable holistic synergistic outcomes.", "status update"),
                Pair("Today we recognise the craft, patience, and care behind this milestone.", "Throughput rose 9%.", "ceremonial speech"),
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
                Pair("Queue depth returned to normal at 14:32.", "We unlock resilient operational synergy.", "incident note"),
                Pair("Begin by locating the problem in its historical setting before stating the thesis.", "State the thesis immediately.", "essay introduction"),
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
