# LinkedIn Saved Posts Scraper

A Python tool to export your LinkedIn saved posts to markdown files.

## Setup

1. **Install dependencies:**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

2. **Install Playwright browsers:**
   \`\`\`bash
   playwright install chromium
   \`\`\`

## Usage

Run the script:
\`\`\`bash
python linkedin_saved_posts_scraper.py
\`\`\`

### What happens:
1. A browser window opens and navigates to LinkedIn
2. If not logged in, you'll need to log in manually
3. The script waits for you to complete login
4. It scrolls through your saved posts to load them all
5. Extracts author names and post content
6. Creates a folder `linkedin_saved_posts/` with:
   - Individual `.md` files for each post
   - A `README.md` index file

## Output Structure

\`\`\`
linkedin_saved_posts/
├── README.md              # Index of all posts
├── 001-John-Doe.md        # Individual post files
├── 002-Jane-Smith.md
└── ...
\`\`\`

## Notes

- LinkedIn requires authentication, so the browser opens visibly
- The script handles various LinkedIn page layouts
- Posts are numbered in the order they appear
- If no posts are found, try scrolling manually in the browser

## Troubleshooting

- **Login issues:** Make sure you complete the login process in the browser
- **No posts found:** LinkedIn may have changed their page structure
- **Timeout errors:** Increase wait times in the script
