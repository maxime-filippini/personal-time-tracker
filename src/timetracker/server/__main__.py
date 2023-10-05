import argparse
from unittest import defaultTestLoader

import uvicorn


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", action="store", default="8000")
    parser.add_argument("--reload", action="store_true", default=False)
    args = parser.parse_args()
    uvicorn.run(
        app="timetracker.server.main:app", port=int(args.port), reload=args.reload
    )
    return 0


raise SystemExit(main())
