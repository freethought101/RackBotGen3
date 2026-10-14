"""Entry point: `python -m rackbot.main [--sim] [--config config.yaml]`."""

from __future__ import annotations

import argparse
import asyncio
import logging

import uvicorn

from .config import Config
from .system import System
from .web.app import create_app


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RackBotGen3 Pi application")
    p.add_argument("--sim", action="store_true", help="simulated robot, rack and camera (laptop development)")
    p.add_argument("--config", default=None, help="config.yaml path (default: the one next to the package)")
    p.add_argument("--speed", type=float, default=None, help="sim speed-up factor, e.g. 4 = 4x faster")
    p.add_argument("--db", default=None, help="SQLite path (default from config)")
    p.add_argument("--port", type=int, default=None)
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


async def run(args: argparse.Namespace) -> None:
    overrides = {"sim": {"time_scale": 1.0 / args.speed}} if args.speed else None
    cfg = Config.load(args.config, overrides)
    system = System(cfg, sim=args.sim, db_path=args.db)
    app = create_app(system)
    server = uvicorn.Server(uvicorn.Config(app, host=cfg.web.host, port=args.port or cfg.web.port, log_level="warning"))
    logging.getLogger("rackbot").info("dashboard on http://localhost:%s", args.port or cfg.web.port)
    await server.serve()


def main(argv=None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname).1s %(name)s: %(message)s", datefmt="%H:%M:%S")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
