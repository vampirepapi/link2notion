"""Entry point for the LinkedIn to Notion migration tool."""

import argparse
import logging
import sys

from .config import Config
from .migrator import LinkedInNotionMigrator


def configure_logging(verbose: bool):
    """Configure logging settings."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Migrate LinkedIn saved posts to Notion.")

    parser.add_argument(
        "--env-file",
        dest="env_file",
        default=None,
        help="Path to environment file (.env).",
    )

    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Enable verbose logging.",
    )

    parser.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        help="Run browser in headless mode (overrides config).",
    )

    parser.add_argument(
        "--no-headless",
        dest="no_headless",
        action="store_true",
        help="Run browser with UI (overrides config).",
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    # Configure logging
    configure_logging(args.verbose)

    # Load configuration
    config = Config.from_env(args.env_file)

    # Override headless if specified
    if args.headless:
        config.headless = True
    if args.no_headless:
        config.headless = False

    # Run migration
    migrator = LinkedInNotionMigrator(config)
    migrator.migrate()


if __name__ == "__main__":
    main()
