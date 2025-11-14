import os
import requests
from playwright.sync_api import sync_playwright
import time

# --- Configuration ---
# These will be loaded from GitHub Secrets for security
GLOBARDIARY_USERNAME = os.getenv("GLOBARDIARY_USERNAME")
GLOBARDIARY_PASSWORD = os.getenv("GLOBARDIARY_PASSWORD")
FACT_API_URL = "https://uselessfacts.jsph.pl/api/v2/facts/random"

def get_interesting_fact():
    """Fetches a random fact from the API."""
    print("Fetching a new interesting fact...")
    try:
        response = requests.get(FACT_API_URL)
        response.raise_for_status()  # Raises an exception for bad status codes
        fact_data = response.json()
        # The API returns 'text' for the fact itself
        return fact_data.get('text', "Could not retrieve a fact at this time.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching fact: {e}")
        return None

def post_to_globardiary(fact_text):
    """Automates the login and posting process on globardiary.com."""
    if not fact_text:
        print("No fact to post. Exiting.")
        return

    print("Starting browser to post to Globardiary...")
    # Use 'with' for proper resource management
    with sync_playwright() as p:
        # Launch browser in headless mode (no UI)
        # Set headless=False for debugging to see the browser actions
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. Go to the login page
            print("Navigating to login page...")
            page.goto("https://www.globardiary.com/login")
            page.wait_for_load_state('networkidle')

            # 2. Fill in login details and submit
            print("Logging in...")
            # NOTE: You MUST find the correct selectors for the username, password fields, and login button.
            # Right-click on the element on the webpage and select "Inspect" to find its name, id, or class.
            page.locator('input[name="username"]').fill(GLOBARDIARY_USERNAME)
            page.locator('input[name="password"]').fill(GLOBARDIARY_PASSWORD)
            page.locator('button[type="submit"]').click()

            # 3. Wait for login to complete and navigate to new post page
            print("Waiting for login to complete...")
            # Wait for a URL that indicates a successful login, e.g., the dashboard
            page.wait_for_url("**/dashboard", timeout=15000)
            
            # Look for a "New Post" or "Write" button and click it
            print("Navigating to new post page...")
            # This selector is a guess. You will need to inspect the page to find the correct one.
            # It might be a link with text 'New Post' or an icon.
            page.locator('a[href="/post/new"]').click()
            page.wait_for_load_state('networkidle')

            # 4. Fill in the post title and content
            print("Filling in post content...")
            # Again, these selectors are examples. You must verify them.
            title = f"Did You Know? - {time.strftime('%Y-%m-%d %H:%M')}"
            page.locator('input[name="title"]').fill(title)
            
            # For the content, it might be a textarea or a contenteditable div
            content_area = page.locator('#content') # Example selector
            content_area.fill(fact_text)

            # 5. Publish the post
            print("Publishing the post...")
            page.locator('button:has-text("Publish")').click()
            
            # Wait for a success message or redirect
            page.wait_for_url("**/post/**", timeout=10000)
            print("Post published successfully!")

        except Exception as e:
            print(f"An error occurred during the posting process: {e}")
            # Take a screenshot for debugging
            page.screenshot(path="error_screenshot.png")
        finally:
            browser.close()

def main():
    """Main function to orchestrate the workflow."""
    fact = get_interesting_fact()
    if fact:
        post_to_globardiary(fact)

if __name__ == "__main__":
    main()
