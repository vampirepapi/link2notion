# Post Management Guide

This guide explains how to use the post management features added to the LinkedIn to Notion migration tool.

## Features Overview

After running the migration, you now have three ways to manage your posts:

1. **Terminal UI** - Interactive command-line interface (automatically shown after migration)
2. **Streamlit Web UI** - Modern web-based interface
3. **Export Functionality** - Export posts as markdown files

## Terminal UI (CLI)

The terminal UI is automatically displayed after the migration completes. It provides these options:

### 1. View All Posts
Browse through all scraped posts with:
- Post content preview
- Author information
- Post URL
- Posted and saved dates

### 2. Export Posts as Markdown
Generates a single markdown file containing all posts with:
- Structured headings for each post
- Metadata (author, dates, URLs)
- Full post content
- Automatic timestamping of export files

The file is saved in your current directory as `linkedin_posts_YYYYMMDD_HHMMSS.md`

### 3. Sync Posts with Notion
Re-syncs all posts with your Notion database:
- Creates pages for new posts
- Skips existing posts (duplicate detection by URN)
- Shows summary of created/skipped posts

### 4. Exit
Close the post management UI

## Streamlit Web UI

Launch the web UI with:
```bash
python -m src.linkedin_notion_migrator.main --streamlit
```

Or:
```bash
python examples/launch_ui.py
```

### Features:

#### 📋 View Posts Tab
- Load posts from your Notion database
- Search through posts by content or author
- View full post details in expandable cards

#### 📤 Export Tab
- **Export as Single File**: Download all posts as one markdown file
- **Export as ZIP Archive**: Get individual markdown files for each post in a ZIP archive
- Instant download via browser

#### 🔄 Sync with Notion Tab
- Run a new migration directly from the web interface
- See real-time progress and results
- Automatically refreshes post data after sync

## Export File Format

When you export posts as markdown, each post is formatted as:

```markdown
# [Post Content Preview]

**Author:** John Doe
**Posted:** 2024-01-15 10:30:00
**Saved:** 2024-01-20 15:45:00
**URL:** [https://linkedin.com/posts/...](https://linkedin.com/posts/...)
**URN:** `urn:li:activity:1234567890`

[Full post content here]

---
```

## Command Line Options

```bash
# Run migration with post management UI (default)
python -m src.linkedin_notion_migrator.main

# Launch Streamlit web UI instead
python -m src.linkedin_notion_migrator.main --streamlit

# Skip the CLI UI after migration
python -m src.linkedin_notion_migrator.main --no-ui

# Combine with other options
python -m src.linkedin_notion_migrator.main --verbose --no-headless
```

## Programmatic Usage

You can also use the export and UI functionality programmatically:

```python
from src.linkedin_notion_migrator import Config, LinkedInNotionMigrator, PostExporter
from src.linkedin_notion_migrator.post_ui import PostMigrationUI

# Run migration
config = Config.from_env()
migrator = LinkedInNotionMigrator(config)
created, skipped = migrator.migrate()

# Get posts
posts = migrator.get_last_scraped_posts()

# Export to markdown
exporter = PostExporter()
export_path = exporter.export_posts_to_single_markdown(posts)
print(f"Exported to {export_path}")

# Or use the UI
ui = PostMigrationUI(posts, migrator)
ui.run()
```

## Tips

1. **Regular Syncs**: Run the sync feature periodically to keep your Notion database up to date with new LinkedIn posts
2. **Backup**: Use the export feature to create markdown backups of your posts
3. **Search**: Use the Streamlit UI's search feature to quickly find specific posts
4. **Batch Processing**: The UI handles large numbers of posts efficiently with pagination and lazy loading

## Troubleshooting

**UI doesn't appear after migration:**
- Check if posts were successfully scraped
- Look for error messages in the console
- Try running with `--ui` flag explicitly

**Export fails:**
- Verify you have write permissions in the current directory
- Check disk space availability

**Streamlit UI won't launch:**
- Ensure streamlit is installed: `pip install streamlit`
- Check if the port is already in use
- Try specifying a different port: `streamlit run src/linkedin_notion_migrator/app.py --server.port 8502`

**Notion sync errors:**
- Verify your Notion API key is valid
- Check that the database is still shared with your integration
- Ensure the database schema hasn't changed
