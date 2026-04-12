"""ODIA Desktop backend entry point.

This module provides the entry point for the PyInstaller-bundled backend.
It starts the uvicorn server with the ODIA FastAPI application.
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    """Start the ODIA backend server for the desktop application."""
    parser = argparse.ArgumentParser(description="ODIA Desktop Backend")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=18741,
        help="Port to listen on (default: 18741)",
    )
    args = parser.parse_args()

    import uvicorn

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()
