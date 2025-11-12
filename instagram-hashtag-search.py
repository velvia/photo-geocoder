#!/usr/bin/env python3
"""
Instagram Hashtag Search Script

This script uses Playwright to automate searching Instagram for specific hashtags
and finding the most recent posting date for each hashtag/user combination.

Usage:
    python instagram-hashtag-search.py --hashtag rebelscapes --users user1 user2 user3
    python instagram-hashtag-search.py --hashtag rebelscapes --users-file users.txt
    python instagram-hashtag-search.py --hashtag rebelscapes --users user1 --browser safari

Requirements:
    - Playwright installed (poetry install)
    - Browser drivers installed (playwright install safari chromium)
    - You may need to be logged into Instagram for better results
"""

import asyncio
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, Page, TimeoutError


class InstagramHashtagSearcher:
    def __init__(self, browser_type: str = "chromium", headless: bool = False):
        """
        Initialize the Instagram Hashtag Searcher.

        Args:
            browser_type: Browser to use ('chromium', 'webkit' for Safari, or 'firefox')
            headless: Whether to run browser in headless mode
        """
        self.browser_type = browser_type
        self.headless = headless
        self.results: Dict[str, Dict] = {}

    async def search_hashtag_for_user(
        self,
        page: Page,
        hashtag_base: str,
        username: str
    ) -> Optional[Dict]:
        """
        Search for a specific hashtag and find the most recent post date.

        Args:
            page: Playwright page object
            hashtag_base: Base hashtag without the username (e.g., 'rebelscapes')
            username: Username to append to hashtag (e.g., 'johndoe')

        Returns:
            Dictionary with results or None if not found
        """
        hashtag = f"{hashtag_base}_{username}"
        search_url = f"https://www.instagram.com/explore/tags/{hashtag}/"

        print(f"\n🔍 Searching for #{hashtag}...")

        try:
            # Navigate to the hashtag page
            await page.goto(search_url, wait_until="networkidle", timeout=30000)

            # Wait a bit for content to load
            await page.wait_for_timeout(3000)

            # Check if hashtag exists (look for "No posts yet" or similar)
            page_content = await page.content()

            if "No posts yet" in page_content:
                print(f"  ⚠️  No posts found for #{hashtag}")
                return {
                    "username": username,
                    "hashtag": f"#{hashtag}",
                    "post_count": 0,
                    "most_recent_date": None,
                    "status": "no_posts"
                }

            # Try to find the first post in the grid (check for actual posts, not just count)
            try:
                # Instagram shows posts in various ways - try multiple selectors
                first_post_selectors = [
                    'article a[href*="/p/"]',  # Posts in article
                    'main a[href*="/p/"]',     # Posts in main section
                    'a[href*="/p/"] img',      # Links with images
                    'div._aagw a',             # Instagram grid container (may change)
                ]

                first_post = None
                for selector in first_post_selectors:
                    try:
                        first_post = await page.wait_for_selector(selector, timeout=5000)
                        if first_post:
                            print(f"  📸 Found posts using selector: {selector[:30]}...")
                            break
                    except TimeoutError:
                        continue

                if not first_post:
                    print(f"  ⚠️  Could not find clickable posts for #{hashtag}")
                    print(f"  💡 Tip: The page may have loaded but posts aren't clickable. Try increasing wait time.")
                    return {
                        "username": username,
                        "hashtag": f"#{hashtag}",
                        "post_count": "unknown",
                        "most_recent_date": None,
                        "status": "posts_not_accessible"
                    }

                # Click on the first post
                print(f"  🖱️  Clicking on first post...")
                await first_post.click()
                await page.wait_for_timeout(3000)

                # Try to find the date/time information
                # Instagram shows dates in multiple ways
                date_selectors = [
                    'time[datetime]',  # Standard time tag with datetime
                    'time',  # Time tag without datetime
                    'article time',  # Time within article
                    'a time',  # Time within link
                ]

                post_date = None

                # First try standard time selectors
                for selector in date_selectors:
                    try:
                        time_elements = await page.query_selector_all(selector)
                        for time_element in time_elements:
                            # Try datetime attribute first
                            datetime_attr = await time_element.get_attribute('datetime')
                            if datetime_attr:
                                post_date = datetime_attr
                                print(f"  📅 Found datetime attribute: {post_date}")
                                break

                            # Try text content
                            text = await time_element.text_content()
                            if text and text.strip():
                                post_date = text.strip()
                                print(f"  📅 Found time text: {post_date}")
                                break

                        if post_date:
                            break
                    except Exception as e:
                        continue

                # If no time element found, look for date-like text patterns
                # Instagram shows dates like "May 21", "24w", etc.
                if not post_date:
                    print(f"  🔍 No <time> element found, searching for date text...")
                    try:
                        # Look for links or spans that might contain dates
                        # Common patterns: "May 21", "24w", "2d", etc.
                        all_text_elements = await page.query_selector_all('article a, article span')

                        date_patterns = [
                            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}',  # "May 21"
                            r'\d{1,2}[wdhm]',  # "24w", "5d", "3h", "45m"
                            r'\d{4}-\d{2}-\d{2}',  # "2025-05-21"
                        ]

                        for element in all_text_elements:
                            text = await element.text_content()
                            if text:
                                text = text.strip()
                                for pattern in date_patterns:
                                    if re.search(pattern, text):
                                        post_date = text
                                        print(f"  📅 Found date pattern: {post_date}")
                                        break
                            if post_date:
                                break
                    except Exception as e:
                        print(f"  ⚠️  Error searching for date text: {e}")

                if post_date:
                    # Try to parse the date
                    try:
                        if 'T' in str(post_date):  # ISO format
                            parsed_date = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                            formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            formatted_date = str(post_date)
                    except:
                        formatted_date = str(post_date)

                    print(f"  ✅ Most recent post: {formatted_date}")
                    return {
                        "username": username,
                        "hashtag": f"#{hashtag}",
                        "post_count": "found",
                        "most_recent_date": formatted_date,
                        "status": "success"
                    }
                else:
                    print(f"  ⚠️  Could not find date for #{hashtag}")
                    print(f"  💡 The post opened but date element wasn't found.")
                    return {
                        "username": username,
                        "hashtag": f"#{hashtag}",
                        "post_count": "found",
                        "most_recent_date": None,
                        "status": "date_not_found"
                    }

            except Exception as e:
                print(f"  ❌ Error processing #{hashtag}: {str(e)}")
                return {
                    "username": username,
                    "hashtag": f"#{hashtag}",
                    "post_count": "error",
                    "most_recent_date": None,
                    "status": f"error: {str(e)}"
                }

        except TimeoutError:
            print(f"  ❌ Timeout loading #{hashtag}")
            return {
                "username": username,
                "hashtag": f"#{hashtag}",
                "post_count": "timeout",
                "most_recent_date": None,
                "status": "timeout"
            }
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return {
                "username": username,
                "hashtag": f"#{hashtag}",
                "post_count": "error",
                "most_recent_date": None,
                "status": f"error: {str(e)}"
            }

    async def run(
        self,
        hashtag_base: str,
        usernames: List[str],
        wait_between_searches: int = 3,
        login_wait: int = 30
    ) -> Dict[str, Dict]:
        """
        Run the hashtag search for multiple users.

        Args:
            hashtag_base: Base hashtag without username (e.g., 'rebelscapes')
            usernames: List of usernames to search
            wait_between_searches: Seconds to wait between searches
            login_wait: Seconds to wait for user to log in (0 to skip)

        Returns:
            Dictionary of results keyed by username
        """
        print(f"\n🚀 Starting Instagram Hashtag Search")
        print(f"   Base hashtag: {hashtag_base}")
        print(f"   Users to search: {len(usernames)}")
        print(f"   Browser: {self.browser_type}")
        print(f"=" * 60)

        async with async_playwright() as p:
            # Launch browser
            if self.browser_type == "webkit":
                browser = await p.webkit.launch(headless=self.headless)
            elif self.browser_type == "firefox":
                browser = await p.firefox.launch(headless=self.headless)
            else:
                browser = await p.chromium.launch(headless=self.headless)

            # Create a new page
            page = await browser.new_page()

            # Set a reasonable viewport size
            await page.set_viewport_size({"width": 1280, "height": 800})

            # Optional: Load Instagram once to use any existing login session
            print("\n📱 Loading Instagram...")
            await page.goto("https://www.instagram.com/", wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # Check if logged in
            page_content = await page.content()
            if "Log in" in page_content or "Sign up" in page_content:
                if login_wait > 0:
                    print("\n" + "=" * 60)
                    print("⚠️  NOT LOGGED INTO INSTAGRAM")
                    print("=" * 60)
                    print(f"   Please log in to Instagram in the browser window.")
                    print(f"   You have {login_wait} seconds to complete login.")
                    print(f"   (Use --login-wait to adjust this time)")
                    print("=" * 60)

                    # Wait for login with countdown
                    for remaining in range(login_wait, 0, -5):
                        if remaining > 5:
                            print(f"   ⏳ {remaining} seconds remaining...")
                            await page.wait_for_timeout(5000)
                        else:
                            print(f"   ⏳ {remaining} seconds remaining...")
                            await page.wait_for_timeout(remaining * 1000)
                            break

                    # Check again if logged in
                    page_content = await page.content()
                    if "Log in" in page_content or "Sign up" in page_content:
                        print("\n⚠️  Still not logged in. Results may be limited.")
                        print("   Consider using --login-wait with more time next time.\n")
                    else:
                        print("\n✅ Successfully logged in!\n")
                else:
                    print("⚠️  Not logged into Instagram. Some features may be limited.")
            else:
                print("✅ Already logged into Instagram")

            # Search for each user's hashtag
            for i, username in enumerate(usernames, 1):
                print(f"\n[{i}/{len(usernames)}] Processing user: {username}")
                result = await self.search_hashtag_for_user(page, hashtag_base, username)
                if result:
                    self.results[username] = result

                # Wait between searches to avoid rate limiting
                if i < len(usernames):
                    print(f"   ⏳ Waiting {wait_between_searches} seconds before next search...")
                    await page.wait_for_timeout(wait_between_searches * 1000)

            # Close browser
            await browser.close()

        return self.results

    def save_results(self, output_file: str):
        """Save results to a JSON file."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")

    def print_summary(self):
        """Print a summary of the results."""
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)

        for username, data in self.results.items():
            status_emoji = {
                "success": "✅",
                "no_posts": "📭",
                "posts_not_accessible": "🔒",
                "date_not_found": "⚠️",
                "timeout": "⏱️",
            }.get(data.get("status", "").split(":")[0], "❌")

            print(f"\n{status_emoji} {username}")
            print(f"   Hashtag: {data.get('hashtag', 'N/A')}")
            print(f"   Posts: {data.get('post_count', 'N/A')}")
            print(f"   Most Recent: {data.get('most_recent_date', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")


def load_usernames_from_file(file_path: str) -> List[str]:
    """Load usernames from a text file (one per line)."""
    with open(file_path, 'r') as f:
        usernames = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return usernames


async def main():
    parser = argparse.ArgumentParser(
        description='Search Instagram hashtags and find most recent posts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for multiple users
  %(prog)s --hashtag rebelscapes --users alice bob charlie

  # Use a file with usernames
  %(prog)s --hashtag rebelscapes --users-file users.txt

  # Use Safari instead of Chrome
  %(prog)s --hashtag rebelscapes --users alice --browser webkit

  # Give yourself 60 seconds to log in
  %(prog)s --hashtag rebelscapes --users alice --login-wait 60

  # Run in headless mode (no visible browser)
  %(prog)s --hashtag rebelscapes --users alice --headless
        """
    )

    parser.add_argument(
        '--hashtag', '-t',
        required=True,
        help='Base hashtag to search (without # or username), e.g., "rebelscapes"'
    )

    parser.add_argument(
        '--users', '-u',
        nargs='+',
        help='List of usernames to search'
    )

    parser.add_argument(
        '--users-file', '-f',
        help='File containing usernames (one per line)'
    )

    parser.add_argument(
        '--browser', '-b',
        choices=['chromium', 'webkit', 'firefox'],
        default='chromium',
        help='Browser to use (webkit = Safari) [default: chromium]'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (no visible window)'
    )

    parser.add_argument(
        '--output', '-o',
        default='instagram_results.json',
        help='Output file for results [default: instagram_results.json]'
    )

    parser.add_argument(
        '--wait',
        type=int,
        default=3,
        help='Seconds to wait between searches [default: 3]'
    )

    parser.add_argument(
        '--login-wait',
        type=int,
        default=30,
        help='Seconds to wait for Instagram login (0 to skip) [default: 30]'
    )

    args = parser.parse_args()

    # Get usernames from command line or file
    usernames = []
    if args.users:
        usernames.extend(args.users)
    if args.users_file:
        usernames.extend(load_usernames_from_file(args.users_file))

    if not usernames:
        print("❌ Error: No usernames provided. Use --users or --users-file")
        sys.exit(1)

    # Remove duplicates while preserving order
    usernames = list(dict.fromkeys(usernames))

    # Create searcher and run
    searcher = InstagramHashtagSearcher(
        browser_type=args.browser,
        headless=args.headless
    )

    try:
        await searcher.run(
            hashtag_base=args.hashtag,
            usernames=usernames,
            wait_between_searches=args.wait,
            login_wait=args.login_wait
        )

        # Print summary
        searcher.print_summary()

        # Save results
        searcher.save_results(args.output)

        print("\n✨ Done!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        if searcher.results:
            searcher.print_summary()
            searcher.save_results(args.output)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())


