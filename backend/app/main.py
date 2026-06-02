"""
main.py — PostureCoach entry point.

Usage
-----
    python main.py                    # live webcam session (OpenCV window)
    python main.py serve              # start FastAPI server  (default: 0.0.0.0:8000)
    python main.py serve --port 9000  # custom port
    python main.py report             # report from latest session CSV
    python main.py report <file.csv>  # report from a specific CSV
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import SESSION_DIR
os.makedirs(SESSION_DIR, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="posturecoach",
        description="PostureCoach — real-time posture monitoring.",
    )
    sub = parser.add_subparsers(dest="command")

    # ── session (default) ─────────────────────────────────────────────
    sub.add_parser("session", help="Live webcam session (OpenCV window)")

    # ── serve ─────────────────────────────────────────────────────────
    serve_p = sub.add_parser("serve", help="Start FastAPI / uvicorn server")
    serve_p.add_argument("--host",   default="0.0.0.0",  help="Bind host")
    serve_p.add_argument("--port",   default=8000, type=int, help="Bind port")
    serve_p.add_argument("--reload", action="store_true",   help="Hot-reload (dev)")

    # ── report ────────────────────────────────────────────────────────
    report_p = sub.add_parser("report", help="Generate session PNG report")
    report_p.add_argument("csv", nargs="?", default=None, help="Path to session CSV")

    args = parser.parse_args()

    if args.command is None or args.command == "session":
        from app.routes.posture import run_live_session
        run_live_session()

    elif args.command == "serve":
        import uvicorn
        uvicorn.run(
            "app.server:app",
            host   = args.host,
            port   = args.port,
            reload = args.reload,
        )

    elif args.command == "report":
        from app.routes.posture import run_report
        run_report(args.csv)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
