"""Export functionality for saved posts."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import SavedPost


logger = logging.getLogger(__name__)


class PostExporter:
    """Handles exporting posts to various formats."""

    @staticmethod
    def post_to_markdown(post: SavedPost, heading_level: int = 1, include_divider: bool = True) -> str:
        """Convert a SavedPost to markdown format."""
        heading_level = max(1, heading_level)
        heading_prefix = "#" * heading_level
        lines = []

        lines.append(f"{heading_prefix} {post.content[:100] if post.content else 'LinkedIn Post'}")
        lines.append("")

        if post.author:
            lines.append(f"**Author:** {post.author}")

        if post.posted_at:
            lines.append(f"**Posted:** {post.posted_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if post.saved_at:
            lines.append(f"**Saved:** {post.saved_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if post.url:
            lines.append(f"**URL:** [{post.url}]({post.url})")

        if post.urn:
            lines.append(f"**URN:** `{post.urn}`")

        lines.append("")

        if post.content:
            lines.append(post.content)

        if include_divider:
            lines.append("")
            lines.append("---")

        return "\n".join(lines)

    @staticmethod
    def export_posts_to_markdown(posts: List[SavedPost], output_dir: Optional[Path] = None) -> Path:
        """Export multiple posts to markdown files in a directory."""
        if output_dir is None:
            output_dir = Path.cwd() / "exported_posts"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_folder = output_dir / f"export_{timestamp}"
        export_folder.mkdir(parents=True, exist_ok=True)
        
        for idx, post in enumerate(posts, 1):
            safe_author = (post.author or "unknown").replace("/", "_").replace("\\", "_")[:50]
            filename = f"{idx:03d}_{safe_author}.md"
            filepath = export_folder / filename

            markdown_content = PostExporter.post_to_markdown(post, heading_level=1, include_divider=False)
            filepath.write_text(markdown_content, encoding="utf-8")
            logger.debug(f"Exported post to {filepath}")
        
        logger.info(f"Exported {len(posts)} posts to {export_folder}")
        return export_folder

    @staticmethod
    def export_posts_to_single_markdown(posts: List[SavedPost], output_file: Optional[Path] = None) -> Path:
        """Export all posts to a single markdown file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path.cwd() / f"linkedin_posts_{timestamp}.md"
        
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        lines = []
        lines.append("# LinkedIn Saved Posts Export")
        lines.append("")
        lines.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Total Posts:** {len(posts)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        for idx, post in enumerate(posts, 1):
            lines.append(f"## Post {idx}")
            lines.append("")
            lines.append(PostExporter.post_to_markdown(post, heading_level=3, include_divider=False))
            lines.append("")
            lines.append("---")
            lines.append("")
        
        output_file.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Exported {len(posts)} posts to {output_file}")
        return output_file
