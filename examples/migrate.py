"""Example script to run the LinkedIn to Notion migration."""

# Fix Windows asyncio issue before any other imports
import asyncio
import platform
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.linkedin_notion_migrator.config import Config
from src.linkedin_notion_migrator.migrator import LinkedInNotionMigrator
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    config = Config.from_env()
    migrator = LinkedInNotionMigrator(config)
    created, skipped = migrator.migrate()
    print(f"\nMigration complete!")
    print(f"Created: {created} pages")
    print(f"Skipped: {skipped} pages")
