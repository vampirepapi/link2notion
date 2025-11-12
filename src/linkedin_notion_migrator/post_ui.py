"""Terminal UI for interacting with migrated posts."""

from __future__ import annotations

import logging
from typing import Iterable, List

from .export import PostExporter
from .models import SavedPost


logger = logging.getLogger(__name__)


class PostMigrationUI:
    """Provide a simple CLI UI for viewing and managing posts."""

    def __init__(self, posts: Iterable[SavedPost], migrator: "LinkedInNotionMigrator"):
        from .migrator import LinkedInNotionMigrator  # Local import to avoid circular dependency

        if not isinstance(migrator, LinkedInNotionMigrator):
            raise TypeError("migrator must be an instance of LinkedInNotionMigrator")

        self.posts: List[SavedPost] = list(posts)
        self.migrator = migrator

    def run(self) -> None:
        """Run the interactive UI."""
        if not self.posts:
            logger.info("No posts available to display in UI.")
            return

        while True:
            self._display_menu()
            try:
                choice = input("Select an option (1-4): ").strip().lower()
            except EOFError:  # pragma: no cover - non-interactive environments
                logger.info("No user input available; exiting UI.")
                return

            if choice in {"1", "view"}:
                self._display_posts()
            elif choice in {"2", "export"}:
                self._export_posts()
            elif choice in {"3", "sync"}:
                self._sync_with_notion()
            elif choice in {"4", "q", "quit", "exit"}:
                print("Exiting post management UI.")
                return
            else:
                print("Invalid choice. Please try again.")

    def _display_menu(self) -> None:
        """Display the main menu."""
        print("\nPost Migration UI Options")
        print("=" * 28)
        print("1. View all posts")
        print("2. Export posts as Markdown")
        print("3. Sync posts with Notion")
        print("4. Exit")
        print("")

    def _display_posts(self) -> None:
        """Display a summary of all posts."""
        print("\nSaved Posts")
        print("=" * 80)
        print(f"Total: {len(self.posts)} posts")
        print("=" * 80)
        for idx, post in enumerate(self.posts, 1):
            preview = (post.content or "")[:120].replace("\n", " ")
            if len(post.content or "") > 120:
                preview += "..."
            print(f"\n{idx:03d}. {preview}")
            if post.author:
                print(f"     Author: {post.author}")
            if post.url:
                print(f"     URL: {post.url}")
            if post.posted_at:
                print(f"     Posted: {post.posted_at.isoformat()}")
            if post.saved_at:
                print(f"     Saved: {post.saved_at.isoformat()}")
            print("     " + "-" * 76)

    def _export_posts(self) -> None:
        """Export posts to markdown files."""
        exporter = PostExporter()
        try:
            export_path = exporter.export_posts_to_single_markdown(self.posts)
        except Exception as exc:  # pragma: no cover - unexpected filesystem issues
            logger.error("Failed to export posts: %s", exc)
            print(f"Failed to export posts: {exc}")
            return
        print(f"Exported {len(self.posts)} posts to {export_path}")

    def _sync_with_notion(self) -> None:
        """Re-sync posts with Notion."""
        try:
            created, skipped = self.migrator.sync_posts_with_notion(self.posts)
        except Exception as exc:  # pragma: no cover - network/API failures
            logger.error("Failed to sync posts with Notion: %s", exc)
            print(f"Failed to sync posts with Notion: {exc}")
            return
        print(f"Sync complete. Created: {created}, Skipped: {skipped}")
