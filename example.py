"""
Generate a user-scoped OAuth token using the local OAuth configuration.

Usage:
    python example.py --user-id alice_001
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from coze_oauth import OAuthConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Issue a Coze OAuth access token")
    parser.add_argument(
        "--user-id",
        dest="user_id",
        required=True,
        help="Business-side user identifier to bind with session_name",
    )
    parser.add_argument(
        "--dump-json",
        action="store_true",
        help="Dump the full token payload as formatted JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file to write the access token payload",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = OAuthConfig.from_env()
    payload = config.issue_access_token(session_name=args.user_id)

    if args.dump_json:
        print(json.dumps(payload, indent=2))
    else:
        print(payload.get("access_token"))

    if args.output:
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Token payload written to {args.output}")


if __name__ == "__main__":
    main()