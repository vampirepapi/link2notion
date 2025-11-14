"""LinkedIn scraper using Playwright to extract saved posts."""

import asyncio
import logging
import platform
import time
from datetime import datetime
from typing import Dict, List, Optional

# Fix Windows asyncio issue before any Playwright imports
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from playwright.sync_api import TimeoutError as PlaywrightTimeout, sync_playwright

from .models import SavedPost


logger = logging.getLogger(__name__)


class LinkedInScraperError(Exception):
    """Base error for LinkedIn scraper."""


class LinkedInAuthenticationError(LinkedInScraperError):
    """Raised when authentication with LinkedIn fails."""


class LinkedInScraper:
    """Scraper for LinkedIn saved posts using Playwright."""

    SAVED_POSTS_URL = "https://www.linkedin.com/my-items/saved-posts/"
    LOGIN_URL = "https://www.linkedin.com/login"

    def __init__(self, email: str, password: str, headless: bool = True):
        self.email = email
        self.password = password
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self):
        """Start the Playwright browser."""
        logger.debug("Starting Playwright browser")
        # Fix Windows asyncio issue with Playwright
        if platform.system() == "Windows":
            # Set the event loop policy to WindowsSelectorEventLoopPolicy
            # This MUST be done before Playwright creates any event loops
            policy = asyncio.WindowsSelectorEventLoopPolicy()
            asyncio.set_event_loop_policy(policy)
            logger.debug("Set Windows event loop policy to SelectorEventLoopPolicy")

            # Clear any existing event loop to force Playwright to create a new one
            # using the SelectorEventLoopPolicy we just set
            try:
                loop = asyncio.get_event_loop()
                loop_type = type(loop).__name__
                logger.debug(f"Current event loop type: {loop_type}")
                
                # Close and remove any existing ProactorEventLoop
                if not loop.is_running() and not loop.is_closed():
                    try:
                        loop.close()
                        logger.debug("Closed existing event loop")
                    except Exception as e:
                        logger.debug(f"Failed to close event loop: {e}")
                
                # Set event loop to None to force Playwright to create a new one
                asyncio.set_event_loop(None)
                logger.debug("Cleared event loop to force Playwright to create new SelectorEventLoop")
            except RuntimeError:
                logger.debug("No existing event loop found")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        logger.debug("Browser started")

    def close(self):
        """Close Playwright resources."""
        logger.debug("Closing Playwright resources")
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self) -> None:
        """Authenticate the user on LinkedIn."""
        logger.info("Logging into LinkedIn")
        try:
            self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
            self.page.fill('input[name="session_key"]', self.email)
            self.page.fill('input[name="session_password"]', self.password)
            self.page.click('button[type="submit"]')
            self.page.wait_for_load_state("networkidle", timeout=45000)
        except PlaywrightTimeout as exc:  # pragma: no cover - network timing issues
            raise LinkedInAuthenticationError("LinkedIn login timed out") from exc
        except Exception as exc:  # pragma: no cover - unexpected errors
            raise LinkedInAuthenticationError("Unexpected error during LinkedIn login") from exc

        if "checkpoint" in self.page.url:
            logger.warning("LinkedIn presented a security checkpoint")
            if self.headless:
                raise LinkedInAuthenticationError(
                    "LinkedIn requested additional verification. Run with --no-headless to complete manually."
                )
            logger.info("Pausing to allow manual completion of checkpoint challenge")
            time.sleep(30)

        if "login" in self.page.url:
            raise LinkedInAuthenticationError("LinkedIn login failed. Check credentials or complete challenges.")

        logger.info("Successfully authenticated with LinkedIn")

    def navigate_to_saved_posts(self) -> None:
        """Navigate to the saved posts page."""
        logger.info("Navigating to LinkedIn saved posts page")
        try:
            self.page.goto(self.SAVED_POSTS_URL, wait_until="domcontentloaded")
            self.page.wait_for_load_state("networkidle", timeout=45000)
        except PlaywrightTimeout as exc:  # pragma: no cover - network timing issues
            raise LinkedInScraperError("Timed out while loading saved posts page") from exc
        except Exception as exc:  # pragma: no cover - unexpected errors
            raise LinkedInScraperError("Unexpected error while loading saved posts page") from exc

        if "my-items/saved-posts" not in self.page.url:
            raise LinkedInScraperError("Failed to reach LinkedIn saved posts page")

        logger.info("Saved posts page loaded")

    def scroll_to_load_all_posts(self, max_idle_rounds: int = 3, max_scrolls: int = 60) -> None:
        """Scroll the page until no more new content loads."""
        logger.info("Scrolling through saved posts to load all content")
        idle_rounds = 0
        previous_height = 0

        for scroll_count in range(1, max_scrolls + 1):
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)
            current_height = self.page.evaluate("document.body.scrollHeight")

            if current_height == previous_height:
                idle_rounds += 1
                logger.debug("Scroll %s: no new content (idle round %s)", scroll_count, idle_rounds)
                if idle_rounds >= max_idle_rounds:
                    logger.info("No additional content detected after %s scrolls", scroll_count)
                    break
            else:
                idle_rounds = 0
                previous_height = current_height
                logger.debug("Scroll %s: content height increased to %s", scroll_count, current_height)
        else:
            logger.info("Reached maximum number of scrolls (%s)", max_scrolls)

    def extract_saved_posts(self) -> List[SavedPost]:
        """Extract saved posts after navigating to the saved posts page."""
        self.scroll_to_load_all_posts()
        raw_posts = self._collect_post_dicts()
        posts: List[SavedPost] = []
        seen_urns = set()

        for raw in raw_posts:
            urn = raw.get("urn") or ""
            if not urn or urn in seen_urns:
                continue
            seen_urns.add(urn)
            post = self._convert_raw_post(raw)
            posts.append(post)

        logger.info("Extracted %s saved posts", len(posts))
        return posts

    def _collect_post_dicts(self) -> List[Dict[str, Optional[str]]]:
        """Collect raw post dictionaries from the browser context."""
        script = """
        () => {
            const results = [];
            const seen = new Set();

            const addContainers = (selector, set) => {
                document.querySelectorAll(selector).forEach(element => set.add(element));
            };

            const containers = new Set();
            [
                'article',
                'div.feed-shared-update-v2',
                'div.feed-shared-update-v3',
                'li[data-urn]',
                'div[data-urn]'
            ].forEach(selector => addContainers(selector, containers));

            const getText = (element, selectors) => {
                for (const selector of selectors) {
                    const target = element.querySelector(selector);
                    if (target) {
                        const text = target.innerText || target.textContent;
                        if (text && text.trim()) {
                            return text.trim();
                        }
                    }
                }
                return '';
            };

            const getUrl = (element) => {
                const selectors = [
                    'a[data-control-name="view_post"]',
                    'a[data-control-name="update_details"]',
                    'a.feed-shared-update-v2__see-more',
                    'a.feed-shared-post-meta__permalink',
                    'a[href*="/feed/update/"]',
                    'a[href*="/posts/"]',
                    'a.app-aware-link'
                ];

                for (const selector of selectors) {
                    const anchor = element.querySelector(selector);
                    if (anchor && anchor.href) {
                        return anchor.href.split('?')[0];
                    }
                }
                return null;
            };

            containers.forEach(element => {
                const urn = element.getAttribute('data-urn') || element.getAttribute('data-id') || (element.dataset && (element.dataset.entityUrn || element.dataset.urn));
                if (!urn || seen.has(urn)) {
                    return;
                }
                seen.add(urn);

                const content = getText(element, [
                    '.feed-shared-update-v2__commentary',
                    '.feed-shared-update-v3__commentary',
                    '.feed-shared-update-v2__description',
                    '.feed-shared-text',
                    '.feed-shared-inline-show-more-text',
                    '.break-words',
                    '[data-test-id="main-feed-text"]',
                    'p'
                ]);

                const author = getText(element, [
                    '.feed-shared-actor__name',
                    '.feed-shared-actor__title',
                    '.update-components-actor__name',
                    '.update-components-actor__title',
                    'span.feed-shared-actor__name',
                    'a[href*="/in/"] span'
                ]);

                const dateText = getText(element, [
                    'span.feed-shared-actor__sub-description',
                    'span.update-components-actor__sub-description',
                    'time'
                ]);

                const savedText = getText(element, [
                    'span[data-test-saved-timestamp]',
                    '.saved-item-action__meta',
                    '.artdeco-entity-lockup__caption'
                ]);

                const timeElement = element.querySelector('time');
                const isoDate = timeElement ? (timeElement.getAttribute('datetime') || timeElement.dateTime || timeElement.getAttribute('aria-label')) : null;

                const url = getUrl(element);

                results.push({
                    urn,
                    content,
                    author,
                    url,
                    isoDate,
                    dateText,
                    savedText
                });
            });

            return results;
        }
        """
        return self.page.evaluate(script)

    def _convert_raw_post(self, data: Dict[str, Optional[str]]) -> SavedPost:
        """Convert raw JavaScript dictionaries to SavedPost dataclass."""
        urn = data.get("urn") or self._generate_fallback_urn(data)
        content = (data.get("content") or "").strip()
        author = (data.get("author") or "").strip() or None
        url = (data.get("url") or None)
        iso_date = (data.get("isoDate") or "").strip()
        posted_at = self._parse_datetime(iso_date)
        raw_date_text = (data.get("dateText") or "").strip() or None
        saved_text = (data.get("savedText") or "").strip() or None

        if not content:
            content = "LinkedIn saved post"

        return SavedPost(
            urn=urn,
            content=content,
            author=author,
            url=url,
            posted_at=posted_at,
            saved_at=None,
            raw_date_text=raw_date_text,
            raw_saved_text=saved_text,
        )

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parse ISO formatted datetime strings."""
        if not value:
            return None
        candidate = value.strip()
        try:
            return datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _generate_fallback_urn(data: Dict[str, Optional[str]]) -> str:
        """Generate a fallback URN when none is available."""
        content = data.get("content") or ""
        author = data.get("author") or ""
        url = data.get("url") or ""
        key = "-".join(filter(None, [content[:20], author[:20], url[:20]])) or str(time.time())
        return f"generated:{hash(key)}"

    def scrape_saved_posts(self) -> List[SavedPost]:
        """Full workflow for scraping saved posts."""
        self.login()
        self.navigate_to_saved_posts()
        return self.extract_saved_posts()
