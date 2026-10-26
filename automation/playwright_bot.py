"""Browser automation bot for Sora89 - runs in GitHub Actions (headless).

Uses Playwright to solve CF challenges and login/play demo.
Runs on GitHub runners, not on local device.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print(f"Playwright not installed: {e}")
        return

    username = os.getenv("SORA89_USERNAME")
    password = os.getenv("SORA89_PASSWORD")

    if not username or not password:
        print("Credentials not provided in secrets")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        try:
            print("Navigating to site...")
            page.goto("https://sora89juli.com/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(10)  # wait for CF challenge

            # Check if we're past CF
            content = page.content()
            if "Just a moment" in content or "cf-challenge" in content.lower():
                print("CF challenge detected, waiting longer...")
                time.sleep(15)
                content = page.content()

            # Try to find login/demo elements
            print(f"Page title: {page.title()}")
            print("Attempting to interact...")
            time.sleep(5)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
