"""Main migrator class that coordinates the migration process."""

# Fix Windows asyncio issue before any other imports
import asyncio
import platform
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging
from typing import List, Tuple

from .config import Config
from .linkedin_scraper import LinkedInScraper
from .models import SavedPost
from .notion_client import NotionClient


logger = logging.getLogger(__name__)


class LinkedInNotionMigrator:
    """Coordinates the migration of LinkedIn saved posts to Notion."""

    def __init__(self, config: Config):
        """Initialize the migrator with configuration."""
        self.config = config
        self._last_scraped_posts: List[SavedPost] = []
        self._last_created_count: int = 0
        self._last_skipped_count: int = 0

    def migrate(self) -> Tuple[int, int]:
        """Execute the migration process."""
        logger.info("=" * 80)
        logger.info("Starting LinkedIn to Notion migration")
        logger.info("=" * 80)

        logger.info("Step 1: Scraping LinkedIn saved posts...")
        posts = self._scrape_linkedin_posts()
        self._last_scraped_posts = posts

        if not posts:
            self._last_created_count = 0
            self._last_skipped_count = 0
            logger.warning("No posts found to migrate")
            return 0, 0

        logger.info(f"Step 2: Creating {len(posts)} Notion pages...")
        created, skipped = self._create_notion_pages(posts)

        self._last_created_count = created
        self._last_skipped_count = skipped

        logger.info("=" * 80)
        logger.info(f"Migration complete! Created: {created}, Skipped: {skipped}")
        logger.info("=" * 80)

        return created, skipped

    def _scrape_linkedin_posts(self) -> List[SavedPost]:
        """Scrape saved posts from LinkedIn."""
        with LinkedInScraper(
            email=self.config.linkedin_email,
            password=self.config.linkedin_password,
            headless=self.config.headless,
        ) as scraper:
            posts = scraper.scrape_saved_posts()

        logger.info(f"Successfully scraped {len(posts)} posts from LinkedIn")
        return posts

    def _create_notion_pages(self, posts: List[SavedPost]) -> Tuple[int, int]:
        """Create Notion pages for the scraped posts."""
        notion_client = NotionClient(
            api_key=self.config.notion_api_key,
            database_id=self.config.notion_database_id,
            properties=self.config.notion_properties,
        )

        created = 0
        skipped = 0

        for idx, post in enumerate(posts, 1):
            logger.info(f"Processing post {idx}/{len(posts)}: {post.to_summary()}")

            if notion_client.page_exists(post.urn):
                logger.info(f"Post already exists in Notion, skipping: {post.urn}")
                skipped += 1
                continue

            page_id = notion_client.create_page(post)
            if page_id:
                created += 1
            else:
                logger.error(f"Failed to create page for post: {post.to_summary()}")
                skipped += 1

        return created, skipped

    def sync_posts_with_notion(self, posts: List[SavedPost]) -> Tuple[int, int]:
        """Sync provided posts with Notion database."""
        logger.info(f"Syncing {len(posts)} posts with Notion")
        created, skipped = self._create_notion_pages(posts)
        self._last_created_count = created
        self._last_skipped_count = skipped
        return created, skipped

    def get_last_scraped_posts(self) -> List[SavedPost]:
        """Get the posts from the last migration run."""
        return list(self._last_scraped_posts)

    def get_last_created_count(self) -> int:
        """Get the number of pages created in the last run."""
        return self._last_created_count

    def get_last_skipped_count(self) -> int:
        """Get the number of skipped pages in the last run."""
        return self._last_skipped_count
