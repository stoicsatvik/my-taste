from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .config import default_db_path
from .connect import run_chatgpt_connection
from .core.engine import TasteEngine


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def _json_object(value: str) -> dict[str, object]:
    path = Path(value)
    raw = path.read_text(encoding="utf-8") if path.exists() else value
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("expected a JSON object or path to a JSON object")
    return parsed


def _json_list(value: str) -> list[object]:
    path = Path(value)
    raw = path.read_text(encoding="utf-8") if path.exists() else value
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise argparse.ArgumentTypeError("expected a JSON array or path to a JSON array")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="my-taste", description="Local-first personal preference engine")
    parser.add_argument("--db", default=str(default_db_path()), help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)

    connect = sub.add_parser(
        "connect",
        help="Start My Taste and expose a temporary HTTPS MCP URL for ChatGPT testing",
    )
    connect.add_argument("--port", type=int, default=8000)
    connect.add_argument(
        "--no-download-cloudflared",
        action="store_true",
        help="Require cloudflared to already be installed",
    )

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

    artifact = sub.add_parser("observe-artifact", help="Save a structured liked/disliked artifact fingerprint")
    artifact.add_argument("--domain", required=True)
    artifact.add_argument("--modality", required=True)
    artifact.add_argument("--features-json", required=True, type=_json_object)
    artifact.add_argument("--context-json", default={}, type=_json_object)
    artifact.add_argument("--preference", choices=["positive", "negative"], default="positive")
    artifact.add_argument("--strength", type=float, default=1.0)
    artifact.add_argument("--source-reference", default="")
    artifact.add_argument("--note", default="")

    retrieve = sub.add_parser("retrieve", help="Retrieve contextual taste evidence")
    retrieve.add_argument("--domain", required=True)
    retrieve.add_argument("--modality", default="")
    retrieve.add_argument("--context-json", default={}, type=_json_object)
    retrieve.add_argument("--limit", type=int, default=8)

    brief = sub.add_parser("brief", help="Build a context-specific prefer/avoid taste brief")
    brief.add_argument("--domain", required=True)
    brief.add_argument("--modality", default="")
    brief.add_argument("--context-json", default={}, type=_json_object)
    brief.add_argument("--limit", type=int, default=12)

    profile_rank = sub.add_parser("rank-profiles", help="Rank structured candidate fingerprints")
    profile_rank.add_argument("--domain", required=True)
    profile_rank.add_argument("--modality", default="")
    profile_rank.add_argument("--context-json", default={}, type=_json_object)
    profile_rank.add_argument("--candidates-json", required=True, type=_json_list)

    rank = sub.add_parser("rank", help="Rank candidate strings")
    rank.add_argument("candidates", nargs="+")
    rank.add_argument("--domain", default="writing")

    profile = sub.add_parser("profile", help="Show learned lexical taste profile")
    profile.add_argument("--domain", default="writing")
    profile.add_argument("--limit", type=int, default=20)

    explain = sub.add_parser("explain", help="Explain one text candidate")
    explain.add_argument("text")
    explain.add_argument("--domain", default="writing")

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "connect":
        run_chatgpt_connection(
            db_path=args.db,
            port=args.port,
            allow_cloudflared_download=not args.no_download_cloudflared,
        )
        return

    engine = TasteEngine(args.db)

    if args.command == "observe-choice":
        _print(engine.observe_choice(args.preferred, args.rejected, domain=args.domain, context=args.context))
    elif args.command == "observe-edit":
        _print(engine.observe_edit(args.original, args.edited, domain=args.domain, context=args.context))
    elif args.command == "observe-artifact":
        _print(
            engine.observe_artifact(
                domain=args.domain,
                modality=args.modality,
                features=args.features_json,
                context={str(k): str(v) for k, v in args.context_json.items()},
                preference=args.preference,
                strength=args.strength,
                source="cli",
                source_reference=args.source_reference,
                note=args.note,
            )
        )
    elif args.command == "retrieve":
        _print(
            engine.retrieve_taste(
                domain=args.domain,
                modality=args.modality,
                context={str(k): str(v) for k, v in args.context_json.items()},
                limit=args.limit,
            )
        )
    elif args.command == "brief":
        _print(
            engine.taste_brief(
                domain=args.domain,
                modality=args.modality,
                context={str(k): str(v) for k, v in args.context_json.items()},
                limit=args.limit,
            )
        )
    elif args.command == "rank-profiles":
        candidates = [item for item in args.candidates_json if isinstance(item, dict)]
        _print(
            engine.rank_profiles(
                candidates,
                domain=args.domain,
                modality=args.modality,
                context={str(k): str(v) for k, v in args.context_json.items()},
            )
        )
    elif args.command == "rank":
        _print([asdict(item) for item in engine.rank_text(args.candidates, domain=args.domain)])
    elif args.command == "profile":
        _print(engine.profile(domain=args.domain, limit=args.limit))
    elif args.command == "explain":
        _print(engine.explain_text(args.text, domain=args.domain))


if __name__ == "__main__":
    main()
