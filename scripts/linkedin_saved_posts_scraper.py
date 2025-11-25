"""
LinkedIn Saved Posts Scraper
============================
This script opens LinkedIn, navigates to your saved posts,
extracts post content and author names, and creates markdown files.

Requirements:
- playwright (pip install playwright)
- Run: playwright install chromium

Usage:
- Run the script and log in manually when the browser opens
- The script will wait for you to complete login, then scrape posts
"""

import os
import re
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Please install playwright: pip install playwright")
    print("Then run: playwright install chromium")
    exit(1)


def sanitize_filename(text: str, max_length: int = 50) -> str:
    """Create a safe filename from text."""
    # Remove special characters and limit length
    safe = re.sub(r'[^\w\s-]', '', text)
    safe = re.sub(r'[-\s]+', '-', safe).strip('-')
    return safe[:max_length] if safe else 'untitled'


def extract_posts(page) -> list[dict]:
    """Extract saved posts from the LinkedIn page."""
    posts = []
    
    # Wait for posts to load
    print("Waiting for posts to load...")
    time.sleep(3)
    
    # Scroll to load more posts
    print("Scrolling to load all posts...")
    last_height = 0
    scroll_attempts = 0
    max_scrolls = 20
    
    while scroll_attempts < max_scrolls:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_attempts += 1
        print(f"  Scrolled {scroll_attempts} times...")
    
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


def create_markdown_files(posts: list[dict], output_dir: str = "linkedin_saved_posts"):
    """Create markdown files for each post in the requested format."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    now = datetime.now()
    import_time = now.strftime("%B %d, %Y %I:%M %p (GMT+5:30)")
    
    for post in posts:
        # Create title from first line of body
        title = post['body'].split('\n')[0] if post['body'] else "LinkedIn Post"
        title = title[:100]  # Limit title length
        
        # Create individual markdown file
        filename = f"{post['index']:03d}-{sanitize_filename(post['author'])}.md"
        filepath = output_path / filename
        
        # Format timestamp for Post Created At
        post_created = post['timestamp'] if post['timestamp'] else "Unknown"
        
        # Build the markdown in the exact requested format
        md_content = f"""# {title}

App Imported Time: {import_time}
Author: {post['author_url']}
Post Created At: {post_created}
Post Link: {post['url']}

<aside>
<img src="{post['author_image']}" alt="{post['author_image']}" width="40px" /> [**{post['author']}**]({post['author_url']}) 

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
        filename = f"{post['index']:03d}-{sanitize_filename(post['author'])}.md"
        preview = post['body'][:80].replace('\n', ' ') + "..." if len(post['body']) > 80 else post['body'].replace('\n', ' ')
        index_content += f"- [{post['author']}]({filename}): {preview}\n"
    
    index_path = output_path / "README.md"
    index_path.write_text(index_content, encoding='utf-8')
    print(f"\nCreated index: {index_path}")
    
    return output_path


def main():
    print("=" * 60)
    print("LinkedIn Saved Posts Scraper")
    print("=" * 60)
    print()
    print("This script will:")
    print("1. Open LinkedIn in a browser")
    print("2. Wait for you to log in (if needed)")
    print("3. Navigate to your saved posts")
    print("4. Extract all posts and create markdown files")
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
        
        # Navigate to LinkedIn saved posts
        saved_posts_url = "https://www.linkedin.com/my-items/saved-posts/"
        print(f"Navigating to: {saved_posts_url}")
        page.goto(saved_posts_url, wait_until="networkidle")
        
        # Check if we need to log in
        if "login" in page.url or "signin" in page.url:
            print()
            print("=" * 60)
            print("LOGIN REQUIRED")
            print("=" * 60)
            print("Please log in to LinkedIn in the browser window.")
            print("The script will continue automatically after login.")
            print()
            
            # Wait for user to log in (wait for URL to change)
            try:
                page.wait_for_url("**/my-items/saved-posts/**", timeout=300000)  # 5 min timeout
                print("Login successful! Continuing...")
            except PlaywrightTimeout:
                print("Login timeout. Please run the script again.")
                browser.close()
                return
        
        # Wait for page to fully load
        print("Waiting for saved posts page to load...")
        time.sleep(5)
        
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
            
            # Create markdown files
            output_dir = create_markdown_files(posts)
            print()
            print("=" * 60)
            print(f"SUCCESS! Created {len(posts)} markdown files in: {output_dir}")
            print("=" * 60)
        
        # Keep browser open briefly so user can see results
        print("\nClosing browser in 5 seconds...")
        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    main()
