"""Streamlit UI for LinkedIn to Notion migration tool."""

import logging
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List

import streamlit as st

from .config import Config
from .export import PostExporter
from .migrator import LinkedInNotionMigrator
from .models import SavedPost
from .notion_client import NotionClient


logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging for the app."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_config() -> Config:
    """Load configuration from environment variables."""
    try:
        config = Config.from_env()
        return config
    except ValueError as e:
        st.error(f"Configuration error: {str(e)}")
        st.stop()


def fetch_posts_from_notion(config: Config) -> List[SavedPost]:
    """Fetch all posts from the Notion database."""
    notion_client = NotionClient(
        api_key=config.notion_api_key,
        database_id=config.notion_database_id,
        properties=config.notion_properties,
    )
    
    posts = notion_client.fetch_all_posts()
    return posts


def main():
    """Main Streamlit app."""
    setup_logging()
    
    st.set_page_config(
        page_title="LinkedIn to Notion Migration",
        page_icon="📚",
        layout="wide",
    )
    
    st.title("📚 LinkedIn to Notion Migration Tool")
    st.markdown("Manage your migrated LinkedIn posts")
    
    config = get_config()
    
    tabs = st.tabs(["📋 View Posts", "📤 Export", "🔄 Sync with Notion"])
    
    with tabs[0]:
        view_posts_tab(config)
    
    with tabs[1]:
        export_posts_tab(config)
    
    with tabs[2]:
        sync_posts_tab(config)


def view_posts_tab(config: Config):
    """Display the View Posts tab."""
    st.header("View All Posts")
    
    if st.button("Load Posts from Notion", type="primary"):
        with st.spinner("Fetching posts from Notion..."):
            try:
                posts = fetch_posts_from_notion(config)
                st.session_state["posts"] = posts
                st.success(f"Loaded {len(posts)} posts from Notion")
            except Exception as e:
                st.error(f"Error fetching posts: {str(e)}")
                logger.exception("Error fetching posts from Notion")
    
    if "posts" in st.session_state and st.session_state["posts"]:
        posts = st.session_state["posts"]
        st.info(f"Total Posts: {len(posts)}")
        
        search_query = st.text_input("Search posts", "")
        
        filtered_posts = posts
        if search_query:
            filtered_posts = [
                p for p in posts
                if search_query.lower() in (p.content or "").lower()
                or search_query.lower() in (p.author or "").lower()
            ]
            st.info(f"Found {len(filtered_posts)} matching posts")
        
        for idx, post in enumerate(filtered_posts, 1):
            with st.expander(f"Post {idx}: {(post.content or 'Untitled')[:80]}..."):
                st.markdown(f"**Author:** {post.author or 'Unknown'}")
                
                if post.posted_at:
                    st.markdown(f"**Posted:** {post.posted_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if post.saved_at:
                    st.markdown(f"**Saved:** {post.saved_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if post.url:
                    st.markdown(f"**URL:** [{post.url}]({post.url})")
                
                st.markdown("---")
                st.markdown(post.content or "No content")


def export_posts_tab(config: Config):
    """Display the Export Posts tab."""
    st.header("Export Posts as Markdown")
    
    if "posts" not in st.session_state or not st.session_state["posts"]:
        st.warning("No posts loaded. Please go to 'View Posts' tab and load posts first.")
        return
    
    posts = st.session_state["posts"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export as Single File", type="primary"):
            with st.spinner("Generating markdown..."):
                try:
                    exporter = PostExporter()
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = Path(f"linkedin_posts_{timestamp}.md")
                    
                    result_path = exporter.export_posts_to_single_markdown(posts, output_file)
                    
                    with open(result_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    st.success(f"✅ Exported {len(posts)} posts")
                    st.download_button(
                        label="Download Markdown File",
                        data=content,
                        file_name=output_file.name,
                        mime="text/markdown",
                    )
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
                    logger.exception("Error exporting posts")
    
    with col2:
        if st.button("Export as Multiple Files (ZIP)", type="primary"):
            with st.spinner("Generating markdown files..."):
                try:
                    import zipfile
                    from io import BytesIO
                    
                    exporter = PostExporter()
                    export_folder = exporter.export_posts_to_markdown(posts)
                    
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for md_file in export_folder.glob("*.md"):
                            zip_file.write(md_file, md_file.name)
                    
                    zip_buffer.seek(0)
                    
                    st.success(f"✅ Exported {len(posts)} posts")
                    st.download_button(
                        label="Download ZIP Archive",
                        data=zip_buffer.getvalue(),
                        file_name=f"linkedin_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                    )
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
                    logger.exception("Error exporting posts as ZIP")


def sync_posts_tab(config: Config):
    """Display the Sync with Notion tab."""
    st.header("Sync Posts with Notion")
    
    st.markdown("""
    This will re-run the migration process:
    - Scrape your LinkedIn saved posts
    - Create new pages in Notion for any posts not already migrated
    - Skip posts that already exist in Notion
    """)
    
    if st.button("Run Migration / Sync", type="primary"):
        with st.spinner("Running migration..."):
            try:
                migrator = LinkedInNotionMigrator(config)
                created, skipped = migrator.migrate()
                
                st.success(f"✅ Migration complete!")
                st.info(f"Created: {created} new pages")
                st.info(f"Skipped: {skipped} existing pages")
                
                if "posts" in st.session_state:
                    del st.session_state["posts"]
                st.info("Please reload posts from the 'View Posts' tab to see the latest data.")
                
            except Exception as e:
                st.error(f"Migration failed: {str(e)}")
                logger.exception("Error during migration")


if __name__ == "__main__":
    main()
