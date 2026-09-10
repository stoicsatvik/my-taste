from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from my_taste.core.context_engine import ContextTasteEngine


def run() -> dict[str, float]:
    with TemporaryDirectory() as tmp:
        engine = ContextTasteEngine(Path(tmp) / "taste.db")

        short = "Price: 30000. Delivery: 3 days."
        long = (
            "We begin with the architecture, trade-offs, implementation details, "
            "testing strategy, deployment model, and reasoning behind each decision."
        )

        for _ in range(8):
            engine.observe_choice(short, long, context="sales landing page")
            engine.observe_choice(long, short, context="technical explanation")

        checks = [
            engine.rank_text([long, short], context="sales landing page")[0].text == short,
            engine.rank_text([short, long], context="technical explanation")[0].text == long,
        ]

        return {
            "context_pairwise_accuracy": sum(checks) / len(checks),
            "examples": float(len(checks)),
        }


if __name__ == "__main__":
    metrics = run()
    for name, value in metrics.items():
        print(f"{name}: {value:.3f}")
