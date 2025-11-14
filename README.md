# LinkedIn Saved Posts to Notion Migration Tool

A Python tool that migrates all your saved LinkedIn posts to a Notion database as individual pages.

## Features

- Authenticates with LinkedIn using your credentials
- Extracts all saved posts from your LinkedIn account
- Creates organized Notion pages for each post with metadata
- Includes post content, author, URL, and date
- Comprehensive logging and error handling
- **Post Management UI** - View, export, and sync posts after migration
- **Export as Markdown** - Download all posts as markdown files
- **Sync with Notion** - Re-run migration to sync new posts
- **Streamlit Web UI** - Modern web interface for managing posts

## Prerequisites

- Python 3.8 or higher
- A LinkedIn account with saved posts
- A Notion integration token and database ID

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your credentials:
```
# LinkedIn Credentials
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-linkedin-password

# Notion Configuration
NOTION_API_KEY=your-notion-integration-token
NOTION_DATABASE_ID=your-notion-database-id
```

### Setting up Notion

1. Create a new Notion integration at https://www.notion.so/my-integrations
2. Copy the integration token (starts with `secret_`)
3. Create a new database in Notion with the following properties:
   - **Title** (title) - Post title/preview
   - **Content** (rich_text) - Post content
   - **Author** (rich_text) - Post author name
   - **Post URL** (url) - Original LinkedIn post URL
   - **Date Posted** (date) - When the post was created
   - **Saved Date** (date) - When you saved the post
4. Share the database with your integration
5. Copy the database ID from the database URL: 
   `https://notion.so/[workspace]/[database-id]?v=...`

## Usage

Run the migration script:
```bash
python -m src.linkedin_notion_migrator.main
```

Or use the example script:
```bash
python examples/migrate.py
```

### Command-line Options

```bash
python -m src.linkedin_notion_migrator.main [OPTIONS]

Options:
  --env-file PATH       Path to environment file (.env)
  --verbose             Enable verbose logging
  --headless            Run browser in headless mode (overrides config)
  --no-headless         Run browser with UI (overrides config)
  --no-ui               Skip the post management CLI UI after migration
  --streamlit           Launch the Streamlit web UI instead of the CLI flow
```

The tool will:
1. Log into LinkedIn using your credentials
2. Navigate to your saved posts
3. Extract all post data
4. Create a Notion page for each post
5. Display the post management UI for additional actions

### Post Management UI

After migration completes, an interactive UI will be displayed with these options:

1. **View all posts** - Browse the scraped posts with author, URL, and date information
2. **Export posts as Markdown** - Generate markdown files for all posts
3. **Sync posts with Notion** - Re-sync posts with your Notion database
4. **Exit** - Close the UI

See [POST_MANAGEMENT_GUIDE.md](POST_MANAGEMENT_GUIDE.md) for a full walkthrough.

### Streamlit Web UI

For a modern web interface, launch the Streamlit UI:

```bash
python -m src.linkedin_notion_migrator.main --streamlit
```

The web UI provides 5 main tabs:

#### 1. ⚙️ Settings
- Configure LinkedIn and Notion credentials directly in the GUI
- Load configuration from environment variables or enter manually
- No need to set up a `.env` file if using the GUI
- View current configuration status

#### 2. 🔍 Scrape LinkedIn
- Scrape your LinkedIn saved posts with a single click
- Choose between headless or visible browser mode
- View scraping progress and results
- Posts are stored in memory for viewing and exporting

#### 3. 📋 View Posts
- Browse all your scraped posts or posts from Notion
- Search posts by content or author
- View post details including author, dates, URLs, and content
- Load posts from either LinkedIn scrape or Notion database

#### 4. 📤 Export to Markdown
- Export posts to markdown without requiring Notion
- **Single File Export**: Download all posts in one markdown file
- **Multiple Files Export**: Download each post as a separate file in a ZIP archive
- Perfect for backup or importing to other platforms

#### 5. 🔄 Sync with Notion
- Connect and sync posts to your Notion database
- Scrapes LinkedIn and creates Notion pages
- Skips existing posts (based on URN)
- View created vs skipped post metrics

**Key Benefits:**
- Configure credentials directly in the GUI (no `.env` file required)
- Export to markdown without Notion (scrape LinkedIn → export markdown)
- Connect to Notion only when you're ready to sync
- All features accessible through an intuitive web interface

## Logging

Logs are displayed in the console with timestamps and log levels.

## Security Notes

- Never commit your `.env` file to version control
- Use environment variables for sensitive credentials
- The tool uses Playwright in headless mode by default
- Session data is not persisted after the script completes

## Troubleshooting

**LinkedIn login fails:**
- Verify your credentials in `.env`
- LinkedIn may require CAPTCHA or 2FA - if so, set `HEADLESS=false` in the script to solve manually

**Notion API errors:**
- Ensure your integration token is correct
- Verify the database is shared with your integration
- Check that database properties match the expected schema

**No posts found:**
- Verify you have saved posts at https://www.linkedin.com/my-items/saved-posts/
- Check the browser console logs for scraping errors

**Windows: NotImplementedError with Playwright (Streamlit):**
- This is automatically handled by the tool
- If you encounter this error, the tool will automatically switch to the Windows-compatible event loop
- No manual configuration is required

## License

MIT
