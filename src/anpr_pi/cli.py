from __future__ import annotations

import argparse
import logging

from anpr_pi.config import load_config
from anpr_pi.pipeline import AnprPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Raspberry Pi ANPR recorder.")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML configuration file.")
    parser.add_argument("--log-level", default="INFO", help="Python log level.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    config = load_config(args.config)
    pipeline = AnprPipeline(config)
    pipeline.run_forever()


if __name__ == "__main__":
    main()
