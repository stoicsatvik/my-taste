from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .config import default_db_path
from .core.engine import TasteEngine


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="my-taste", description="Local-first personal preference engine")
    parser.add_argument("--db", default=str(default_db_path()), help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)

    choice = sub.add_parser("observe-choice", help="Learn preferred > rejected")
    choice.add_argument("--preferred", required=True)
    choice.add_argument("--rejected", required=True)
    choice.add_argument("--domain", default="writing")
    choice.add_argument("--context", default="")

    edit = sub.add_parser("observe-edit", help="Learn edited > original")
    edit.add_argument("--original", required=True)
    edit.add_argument("--edited", required=True)
    edit.add_argument("--domain", default="writing")
    edit.add_argument("--context", default="")

    rank = sub.add_parser("rank", help="Rank candidate strings")
    rank.add_argument("candidates", nargs="+")
    rank.add_argument("--domain", default="writing")

    profile = sub.add_parser("profile", help="Show learned taste profile")
    profile.add_argument("--domain", default="writing")
    profile.add_argument("--limit", type=int, default=20)

    explain = sub.add_parser("explain", help="Explain one candidate")
    explain.add_argument("text")
    explain.add_argument("--domain", default="writing")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    engine = TasteEngine(args.db)

    if args.command == "observe-choice":
        _print(engine.observe_choice(args.preferred, args.rejected, domain=args.domain, context=args.context))
    elif args.command == "observe-edit":
        _print(engine.observe_edit(args.original, args.edited, domain=args.domain, context=args.context))
    elif args.command == "rank":
        _print([asdict(item) for item in engine.rank_text(args.candidates, domain=args.domain)])
    elif args.command == "profile":
        _print(engine.profile(domain=args.domain, limit=args.limit))
    elif args.command == "explain":
        _print(engine.explain_text(args.text, domain=args.domain))


if __name__ == "__main__":
    main()
