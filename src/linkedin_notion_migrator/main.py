"""Entry point for the LinkedIn to Notion migration tool."""

# Fix Windows asyncio issue before any other imports
import asyncio
import platform
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from .config import Config
from .migrator import LinkedInNotionMigrator
from .post_ui import PostMigrationUI


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

    parser.add_argument(
        "--no-ui",
        dest="disable_ui",
        action="store_true",
        help="Skip the post management UI after migration.",
    )

    parser.add_argument(
        "--streamlit",
        dest="launch_streamlit",
        action="store_true",
        help="Launch Streamlit web UI instead of running migration.",
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    # Configure logging
    configure_logging(args.verbose)

    # Launch Streamlit UI if requested
    if args.launch_streamlit:
        launch_streamlit_ui()
        return

    # Load configuration
    config = Config.from_env(args.env_file)

    # Override headless if specified
    if args.headless:
        config.headless = True
    if args.no_headless:
        config.headless = False

    # Run migration
    migrator = LinkedInNotionMigrator(config)
    created, skipped = migrator.migrate()
    logging.info("Migration summary - created %s, skipped %s", created, skipped)

    # Show post management UI after migration (unless disabled)
    if not args.disable_ui:
        posts = migrator.get_last_scraped_posts()

        if posts:
            ui = PostMigrationUI(posts, migrator)
            ui.run()
        else:
            logging.warning("No posts available to show in UI")
    else:
        logging.info("Post management UI disabled via --no-ui flag")


def launch_streamlit_ui():
    """Launch the Streamlit web UI."""
    app_path = Path(__file__).parent / "app.py"
    logging.info(f"Launching Streamlit UI from {app_path}")
    try:
        subprocess.run(["streamlit", "run", str(app_path)], check=True)
    except FileNotFoundError as exc:
        logging.error("Streamlit is not installed or not available in PATH.")
        raise exc


if __name__ == "__main__":
    main()
