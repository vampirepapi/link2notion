"""
LinkedIn Saved Posts Scraper
============================
This script opens LinkedIn, navigates to your saved posts,
extracts post content and author names, and creates markdown files.

Requirements:
- playwright (pip install playwright)
- python-dotenv (pip install python-dotenv)
- Run: playwright install chromium

Usage:
- Create a .env file with LINKEDIN_EMAIL and LINKEDIN_PASSWORD
- Run the script
"""

import os
import re
import time
import webbrowser  # Added for opening HTML page
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Please install python-dotenv: pip install python-dotenv")
    exit(1)

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Please install playwright: pip install playwright")
    print("Then run: playwright install chromium")
    exit(1)


def login_to_linkedin(page) -> bool:
    """Attempt to log in using credentials from .env file."""
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not email or not password:
        print("No credentials found in .env file.")
        print("Please create a .env file with LINKEDIN_EMAIL and LINKEDIN_PASSWORD")
        return False
    
    print(f"Logging in as: {email}")
    
    try:
        # Fill in email
        email_input = page.wait_for_selector('input[name="session_key"], input#username', timeout=10000)
        if email_input:
            email_input.fill(email)
        
        # Fill in password
        password_input = page.wait_for_selector('input[name="session_password"], input#password', timeout=5000)
        if password_input:
            password_input.fill(password)
        
        # Click sign in button
        sign_in_button = page.query_selector('button[type="submit"], button[data-litms-control-urn="login-submit"]')
        if sign_in_button:
            sign_in_button.click()
        
        # Wait for navigation
        time.sleep(5)
        
        # Check if login was successful (no longer on login page)
        if "login" not in page.url and "signin" not in page.url and "checkpoint" not in page.url:
            print("Login successful!")
            return True
        else:
            print("Login may have failed or requires additional verification.")
            return False
            
    except Exception as e:
        print(f"Error during login: {e}")
        return False


def sanitize_filename(text: str, max_length: int = 80) -> str:
    """Create a safe filename from text."""
    safe = re.sub(r'[^\w\s-]', '', text)
    safe = re.sub(r'[-\s]+', '-', safe).strip('-')
    return safe[:max_length] if safe else 'untitled'


def extract_posts(page) -> list[dict]:
    """Extract saved posts from the LinkedIn page."""
    posts = []
    
    # Wait for posts to load
    print("Waiting for posts to load...")
    time.sleep(3)
    
    print("Scrolling to load all posts...")
    last_post_count = 0
    no_new_posts_count = 0
    scroll_count = 0
    max_scrolls = 200  # Increased from 100 to 200
    max_no_new_posts = 3  # Increased from 5 to 10 to handle slow loading
    
    while scroll_count < max_scrolls and no_new_posts_count < max_no_new_posts:
        # Scroll down
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2.5)  # Increased wait time from 2 to 2.5 seconds
        
        # Check current post count
        current_count = page.evaluate("""
            () => document.querySelectorAll('div[data-chameleon-result-urn]').length
        """)
        
        scroll_count += 1
        
        if current_count > last_post_count:
            print(f"  Scrolled {scroll_count} times... Found {current_count} posts")
            last_post_count = current_count
            no_new_posts_count = 0  # Reset counter when new posts found
        else:
            no_new_posts_count += 1
            print(f"  Scrolled {scroll_count} times... No new posts (attempt {no_new_posts_count}/{max_no_new_posts})")
        
        if scroll_count % 5 == 0:
            print("  Pausing for content to load...")
            time.sleep(4)  # Increased pause time to 4 seconds
    
    print(f"Finished scrolling. Total scrolls: {scroll_count}")
    
    # The saved posts page uses a different structure than the feed
    post_selectors = [
        "div[data-chameleon-result-urn]",
        "div[data-view-name='search-entity-result-content-a-template']",
        "li.reusable-search__result-container",
        ".entity-result",
    ]
    
    post_elements = []
    for selector in post_selectors:
        elements = page.query_selector_all(selector)
        if elements:
            post_elements = elements
            print(f"Found {len(elements)} posts using selector: {selector}")
            break
    
    for i, post_el in enumerate(post_elements):
        try:
            author = "Unknown Author"
            author_selectors = [
                "span[dir='ltr'] span[aria-hidden='true']",
                ".entity-result__title-text a span[aria-hidden='true']",
                "a[href*='/in/'] span[aria-hidden='true']",
            ]
            
            for sel in author_selectors:
                author_el = post_el.query_selector(sel)
                if author_el:
                    author = author_el.inner_text().strip()
                    if author:
                        break
            
            author_url = ""
            author_link_el = post_el.query_selector("a[href*='/in/']")
            if author_link_el:
                href = author_link_el.get_attribute("href")
                if href:
                    author_url = href if href.startswith("http") else f"https://www.linkedin.com{href}"
            
            author_image = ""
            img_selectors = [
                "img.presence-entity__image",
                "img.EntityPhoto-circle-4",
                ".entity-result__universal-image img",
                "img[class*='presence']",
                ".presence-entity img",
            ]
            for sel in img_selectors:
                img_el = post_el.query_selector(sel)
                if img_el:
                    src = img_el.get_attribute("src")
                    if src and "data:" not in src:
                        author_image = src
                        break
            
            body = ""
            content_selectors = [
                "p.entity-result__content-summary",
                ".entity-result__content-summary",
                ".entity-result__summary",
            ]
            
            for sel in content_selectors:
                content_el = post_el.query_selector(sel)
                if content_el:
                    body = content_el.inner_text().strip()
                    body = re.sub(r'…see more\s*$', '', body).strip()
                    body = re.sub(r'\.\.\.see more\s*$', '', body).strip()
                    if len(body) > 10:
                        break
            
            post_url = ""
            link_el = post_el.query_selector("a[href*='/feed/update/']")
            if link_el:
                href = link_el.get_attribute("href")
                if href:
                    post_url = href if href.startswith("http") else f"https://www.linkedin.com{href}"
            
            timestamp = ""
            time_el = post_el.query_selector("p.t-black--light.t-12, .t-12.t-black--light")
            if time_el:
                timestamp = time_el.inner_text().strip()
                timestamp = re.sub(r'[•·].*$', '', timestamp).strip()
                timestamp = timestamp.split('\n')[0].strip()
            
            if body or author != "Unknown Author":
                posts.append({
                    "author": author,
                    "author_url": author_url,
                    "author_image": author_image,
                    "body": body,
                    "url": post_url,
                    "timestamp": timestamp,
                    "index": i + 1
                })
                print(f"  Extracted post {i + 1}: {author[:30]}...")
                
        except Exception as e:
            print(f"  Error extracting post {i + 1}: {e}")
            continue
    
    return posts


def create_markdown_files(posts: list[dict], output_dir: str = "saved_posts"):
    """Create markdown files for each post in the requested format."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    now = datetime.now()
    import_time = now.strftime("%B %d, %Y %I:%M %p (GMT+5:30)")
    
    for post in posts:
        first_line = post['body'].split('\n')[0] if post['body'] else "LinkedIn Post"
        
        title_slug = sanitize_filename(first_line)
        filename = f"{post['index']:03d}-{title_slug}.md"
        filepath = output_path / filename
        
        # Format timestamp for Post Created At
        post_created = post['timestamp'] if post['timestamp'] else "Unknown"
        
        md_content = f"""# {first_line}

App Imported Time: {import_time}
Author URL: {post['author_url']}
Post Created At: {post_created}
Post Link: {post['url']}

<aside>
<img src="{post['author_image']}" alt="{post['author']}" width="40px" /> **[{post['author']}]({post['author_url']})**

{post['body'] if post['body'] else "*No text content available*"}

</aside>
"""
        
        filepath.write_text(md_content, encoding='utf-8')
        print(f"Created: {filepath}")
    
    # Create index file
    index_content = f"""# LinkedIn Saved Posts

Exported on: {now.strftime("%Y-%m-%d %H:%M:%S")}

Total posts: {len(posts)}

## Posts

"""
    for post in posts:
        title_slug = sanitize_filename(post['body'].split('\n')[0] if post['body'] else "LinkedIn Post")
        filename = f"{post['index']:03d}-{title_slug}.md"
        preview = post['body'][:80].replace('\n', ' ') + "..." if len(post['body']) > 80 else post['body'].replace('\n', ' ')
        index_content += f"- [{post['author']}]({filename}): {preview}\n"
    
    index_path = output_path / "README.md"
    index_path.write_text(index_content, encoding='utf-8')
    print(f"\nCreated index: {index_path}")
    
    return output_path


def open_html_viewer(output_dir: str):
    """Open the HTML viewer in the default browser."""
    html_path = Path(output_dir) / "index.html"
    
    if html_path.exists():
        # Convert to file:// URL
        file_url = html_path.absolute().as_uri()
        print(f"\nOpening blog viewer: {file_url}")
        webbrowser.open(file_url)
    else:
        print(f"\nNote: HTML viewer not found at {html_path}")
        print("Copy index.html to your saved_posts folder to view posts as a blog.")


def main():
    print("=" * 60)
    print("LinkedIn Saved Posts Scraper")
    print("=" * 60)
    print()
    print("This script will:")
    print("1. Open LinkedIn in a browser")
    print("2. Log in automatically using .env credentials")
    print("3. Navigate to your saved posts")
    print("4. Extract all posts and create markdown files")
    print("5. Open the blog viewer in your browser")
    print()
    print("Starting browser...")
    print()
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode so user can log in
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        saved_posts_url = "https://www.linkedin.com/my-items/saved-posts/"
        print(f"Navigating to: {saved_posts_url}")
        page.goto(saved_posts_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        
        if "login" in page.url or "signin" in page.url:
            print()
            print("=" * 60)
            print("LOGIN REQUIRED")
            print("=" * 60)
            
            login_success = login_to_linkedin(page)
            
            if not login_success:
                print()
                print("Automatic login failed or not configured.")
                print("Please log in manually in the browser window.")
                print("The script will continue automatically after login.")
                print()
                
                try:
                    page.wait_for_url("**/my-items/saved-posts/**", timeout=300000)
                    print("Login successful! Continuing...")
                except PlaywrightTimeout:
                    print("Login timeout. Please run the script again.")
                    browser.close()
                    return
            else:
                print("Navigating to saved posts...")
                page.goto(saved_posts_url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(5)
        
        print("Waiting for saved posts page to load...")
        try:
            page.wait_for_selector("div[data-chameleon-result-urn], .entity-result, .reusable-search__result-container", timeout=30000)
            print("Posts container found!")
        except PlaywrightTimeout:
            print("Could not find posts container, will try to extract anyway...")
        
        time.sleep(3)
        
        # Extract posts
        print("\nExtracting saved posts...")
        posts = extract_posts(page)
        
        if not posts:
            print("\nNo posts found. This could be because:")
            print("- You have no saved posts")
            print("- LinkedIn's page structure has changed")
            print("- The page didn't load properly")
            print("\nTry scrolling manually in the browser and running again.")
        else:
            print(f"\nExtracted {len(posts)} posts!")
            
            output_dir = create_markdown_files(posts)
            print()
            print("=" * 60)
            print(f"SUCCESS! Created {len(posts)} markdown files in: {output_dir}")
            print("=" * 60)
            
            open_html_viewer(str(output_dir))
        
        print("\nClosing browser in 5 seconds...")
        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    main()
