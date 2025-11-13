"""Streamlit UI for LinkedIn to Notion migration tool."""

import logging
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Optional

import streamlit as st

if __package__:
    from .config import Config
    from .export import PostExporter
    from .linkedin_scraper import LinkedInScraper
    from .migrator import LinkedInNotionMigrator
    from .models import SavedPost
    from .notion_client import NotionClient
else:
    import sys

    current_dir = Path(__file__).resolve().parent
    parent_dir = current_dir.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

    from linkedin_notion_migrator.config import Config
    from linkedin_notion_migrator.export import PostExporter
    from linkedin_notion_migrator.linkedin_scraper import LinkedInScraper
    from linkedin_notion_migrator.migrator import LinkedInNotionMigrator
    from linkedin_notion_migrator.models import SavedPost
    from linkedin_notion_migrator.notion_client import NotionClient


logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging for the app."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_config_from_session() -> Optional[Config]:
    """Get configuration from session state or environment variables."""
    if "config" in st.session_state:
        return st.session_state["config"]
    
    try:
        config = Config.from_env()
        st.session_state["config"] = config
        return config
    except ValueError:
        return None


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
    
    config = get_config_from_session()
    
    tabs = st.tabs(["⚙️ Settings", "🔍 Scrape LinkedIn", "📋 View Posts", "📤 Export", "🔄 Sync with Notion"])
    
    with tabs[0]:
        settings_tab()
    
    with tabs[1]:
        scrape_linkedin_tab()
    
    with tabs[2]:
        view_posts_tab(config)
    
    with tabs[3]:
        export_posts_tab()
    
    with tabs[4]:
        sync_posts_tab(config)


def settings_tab():
    """Display the Settings tab for configuring credentials."""
    st.header("⚙️ Configuration Settings")
    
    st.markdown("""
    Configure your credentials here. You can either:
    - Load settings from environment variables
    - Manually enter credentials in the form below
    """)
    
    if st.button("Load from Environment Variables"):
        try:
            config = Config.from_env()
            st.session_state["config"] = config
            st.success("✅ Configuration loaded from environment variables")
        except ValueError as e:
            st.error(f"Failed to load from environment: {str(e)}")
    
    st.markdown("---")
    st.subheader("Manual Configuration")
    
    with st.form("config_form"):
        st.markdown("### LinkedIn Credentials")
        
        current_email = ""
        current_headless = True
        if "config" in st.session_state:
            current_email = st.session_state["config"].linkedin_email
            current_headless = st.session_state["config"].headless
        
        linkedin_email = st.text_input("LinkedIn Email", value=current_email)
        linkedin_password = st.text_input("LinkedIn Password", type="password", value="")
        headless = st.checkbox("Run browser in headless mode", value=current_headless)
        
        st.markdown("### Notion Configuration (Optional)")
        st.markdown("Get your API key from [Notion Integrations](https://www.notion.so/my-integrations)")
        notion_api_key = st.text_input("Notion API Key", type="password", value="")
        notion_database_id = st.text_input("Notion Database ID", value="")
        
        submit_button = st.form_submit_button("Save Configuration")
        
        if submit_button:
            if not linkedin_email or not linkedin_password:
                st.error("LinkedIn email and password are required")
            elif not notion_api_key or not notion_database_id:
                st.warning("Notion credentials are not required for scraping and exporting, but are needed for syncing to Notion")
                config = Config(
                    linkedin_email=linkedin_email,
                    linkedin_password=linkedin_password,
                    notion_api_key=notion_api_key or "dummy",
                    notion_database_id=notion_database_id or "dummy",
                    headless=headless,
                )
                st.session_state["config"] = config
                st.success("✅ LinkedIn configuration saved")
            else:
                config = Config(
                    linkedin_email=linkedin_email,
                    linkedin_password=linkedin_password,
                    notion_api_key=notion_api_key,
                    notion_database_id=notion_database_id,
                    headless=headless,
                )
                st.session_state["config"] = config
                st.success("✅ Configuration saved successfully")
    
    if "config" in st.session_state:
        st.markdown("---")
        st.subheader("Current Configuration Status")
        config = st.session_state["config"]
        st.write(f"✅ LinkedIn Email: {config.linkedin_email}")
        st.write(f"✅ Browser Mode: {'Headless' if config.headless else 'Visible'}")
        if config.notion_api_key and config.notion_api_key != "dummy":
            st.write(f"✅ Notion API Key: {'*' * 20}")
            st.write(f"✅ Notion Database ID: {config.notion_database_id[:20]}...")
        else:
            st.write("⚠️ Notion not configured (required for syncing)")


def scrape_linkedin_tab():
    """Display the Scrape LinkedIn tab."""
    st.header("🔍 Scrape LinkedIn Posts")
    
    st.markdown("""
    Scrape your saved posts from LinkedIn. This will:
    - Log into your LinkedIn account
    - Navigate to your saved posts page
    - Extract all saved posts
    - Store them in memory for viewing and exporting
    """)
    
    if "config" not in st.session_state:
        st.warning("⚠️ Please configure your credentials in the Settings tab first")
        return
    
    config = st.session_state["config"]
    
    if not config.linkedin_email or not config.linkedin_password:
        st.error("❌ LinkedIn credentials are not configured")
        return
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"Ready to scrape posts for: {config.linkedin_email}")
    with col2:
        headless_mode = st.checkbox("Headless mode", value=config.headless, key="scrape_headless")
    
    if st.button("Start Scraping", type="primary"):
        with st.spinner("Scraping LinkedIn... This may take a few minutes..."):
            try:
                with LinkedInScraper(
                    email=config.linkedin_email,
                    password=config.linkedin_password,
                    headless=headless_mode,
                ) as scraper:
                    posts = scraper.scrape_saved_posts()
                
                st.session_state["posts"] = posts
                st.session_state["posts_source"] = "linkedin"
                st.success(f"✅ Successfully scraped {len(posts)} posts from LinkedIn!")
                st.info("Go to the 'View Posts' or 'Export' tab to see and export your posts")
                
            except Exception as e:
                st.error(f"❌ Scraping failed: {str(e)}")
                logger.exception("Error during LinkedIn scraping")
                st.markdown("""
                **Troubleshooting:**
                - Check your LinkedIn credentials
                - Try running with headless mode disabled if you need to complete security challenges
                - Ensure you have a stable internet connection
                """)


def view_posts_tab(config: Optional[Config]):
    """Display the View Posts tab."""
    st.header("📋 View All Posts")
    
    notion_enabled = bool(config and config.notion_api_key and config.notion_api_key != "dummy")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh View", type="secondary"):
            if "posts" in st.session_state:
                st.success(f"Showing {len(st.session_state['posts'])} posts")
            else:
                st.warning("No posts loaded")
    
    with col2:
        if st.button("Load from Notion", disabled=not notion_enabled, type="primary"):
            with st.spinner("Fetching posts from Notion..."):
                try:
                    posts = fetch_posts_from_notion(config)
                    st.session_state["posts"] = posts
                    st.session_state["posts_source"] = "notion"
                    st.success(f"✅ Loaded {len(posts)} posts from Notion")
                except Exception as e:
                    st.error(f"Error fetching posts: {str(e)}")
                    logger.exception("Error fetching posts from Notion")
    
    st.markdown("---")
    
    if "posts" in st.session_state and st.session_state["posts"]:
        posts = st.session_state["posts"]
        source = st.session_state.get("posts_source", "unknown")
        st.info(f"📊 Total Posts: {len(posts)} | Source: {source}")
        
        search_query = st.text_input("🔍 Search posts by content or author", "")
        
        filtered_posts = posts
        if search_query:
            filtered_posts = [
                p for p in posts
                if search_query.lower() in (p.content or "").lower()
                or search_query.lower() in (p.author or "").lower()
            ]
            st.info(f"Found {len(filtered_posts)} matching posts")
        
        for idx, post in enumerate(filtered_posts, 1):
            title_preview = (post.content or "Untitled")[:80]
            with st.expander(f"Post {idx}: {title_preview}..."):
                st.markdown(f"**Author:** {post.author or 'Unknown'}")
                
                if post.posted_at:
                    st.markdown(f"**Posted:** {post.posted_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if post.saved_at:
                    st.markdown(f"**Saved:** {post.saved_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if post.url:
                    st.markdown(f"**URL:** [{post.url}]({post.url})")
                
                st.markdown("---")
                st.markdown(post.content or "No content")
    else:
        st.info("📭 No posts loaded yet. Scrape LinkedIn or load from Notion to see posts here.")


def export_posts_tab():
    """Display the Export Posts tab."""
    st.header("📤 Export Posts as Markdown")
    
    if "posts" not in st.session_state or not st.session_state["posts"]:
        st.warning("⚠️ No posts loaded. Please scrape LinkedIn or load from Notion first.")
        st.markdown("""
        **To get posts for export:**
        1. Go to the **Settings** tab and configure your credentials
        2. Go to the **Scrape LinkedIn** tab to scrape posts from LinkedIn
        3. Or go to **View Posts** tab and load posts from Notion (if configured)
        4. Return here to export
        """)
        return
    
    posts = st.session_state["posts"]
    source = st.session_state.get("posts_source", "unknown")
    st.info(f"📊 Ready to export {len(posts)} posts from {source}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Single File Export")
        st.markdown("Export all posts into one markdown file")
        if st.button("📄 Export as Single File", type="primary"):
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
                        label="⬇️ Download Markdown File",
                        data=content,
                        file_name=output_file.name,
                        mime="text/markdown",
                    )
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
                    logger.exception("Error exporting posts")
    
    with col2:
        st.subheader("Multiple Files Export")
        st.markdown("Export each post as a separate markdown file (ZIP)")
        if st.button("📁 Export as Multiple Files", type="primary"):
            with st.spinner("Generating markdown files..."):
                try:
                    import zipfile
                    
                    exporter = PostExporter()
                    export_folder = exporter.export_posts_to_markdown(posts)
                    
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for md_file in export_folder.glob("*.md"):
                            zip_file.write(md_file, md_file.name)
                    
                    zip_buffer.seek(0)
                    
                    st.success(f"✅ Exported {len(posts)} posts")
                    st.download_button(
                        label="⬇️ Download ZIP Archive",
                        data=zip_buffer.getvalue(),
                        file_name=f"linkedin_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                    )
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
                    logger.exception("Error exporting posts as ZIP")


def sync_posts_tab(config: Optional[Config]):
    """Display the Sync with Notion tab."""
    st.header("🔄 Sync Posts with Notion")
    
    if not config or not config.notion_api_key or config.notion_api_key == "dummy":
        st.error("❌ Notion is not configured. Please configure Notion credentials in the Settings tab first.")
        return
    
    st.markdown("""
    This will run the migration process:
    - Scrape your LinkedIn saved posts
    - Create new pages in Notion for any posts not already migrated
    - Skip posts that already exist in Notion (based on URN)
    """)
    
    st.info(f"🔗 Connected to Notion Database: {config.notion_database_id[:20]}...")
    
    if st.button("🚀 Run Migration / Sync", type="primary"):
        with st.spinner("Running migration... This may take several minutes..."):
            try:
                migrator = LinkedInNotionMigrator(config)
                created, skipped = migrator.migrate()
                
                st.success(f"✅ Migration complete!")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Created", created, delta=f"+{created}")
                with col2:
                    st.metric("Skipped", skipped, delta="Already exists")
                
                if "posts" in st.session_state:
                    del st.session_state["posts"]
                st.info("💡 Please reload posts from the 'View Posts' tab to see the latest data.")
                
            except Exception as e:
                st.error(f"Migration failed: {str(e)}")
                logger.exception("Error during migration")
                st.markdown("""
                **Troubleshooting:**
                - Check your LinkedIn and Notion credentials
                - Ensure your Notion database has the correct properties
                - Try running with headless mode disabled if you need to complete security challenges
                """)


if __name__ == "__main__":
    main()
