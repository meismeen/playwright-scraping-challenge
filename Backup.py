from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import os
import json

SESSION_FILE = "session.json"
LOGIN_URL = "https://hiring.idenhq.com/"
DASHBOARD_URL = "https://hiring.idenhq.com/instructions"

def save_session_data(context, page):
    """ Get state from Playwright and manually add sessionStorage."""
    
    # Get the standard state (cookies, localStorage) from Playwright
    playwright_state = context.storage_state()

    # Manually get the sessionStorage and add it to our custom structure
    session_storage = page.evaluate("() => Object.assign({}, window.sessionStorage)")
    
    # Combine both into a single dictionary
    full_session_data = {
        "playwright_state": playwright_state,
        "session_storage": session_storage
    }

    with open(SESSION_FILE, "w") as f:
        json.dump(full_session_data, f, indent=2)
    print("Session data saved successfully.")

def load_session_data(p):
    """ Load data from file and return both playwright state and session storage."""
    if not os.path.exists(SESSION_FILE):
        return None, None, None

    print("Using saved session...")
    with open(SESSION_FILE, "r") as f:
        full_session_data = json.load(f)

    playwright_state = full_session_data.get("playwright_state")
    session_storage = full_session_data.get("session_storage")

    browser = p.chromium.launch(headless=False)
    context = browser.new_context(storage_state=playwright_state)
    
    return browser, context, session_storage

def manual_login(p):
    """Do manual login and save session"""
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(LOGIN_URL)

    print("Login manually in the opened browser window...")
    page.wait_for_url("**/instructions", timeout=120000)
    print("Redirected to dashboard.")
    
    print("Waiting for network to be idle to ensure session is stable...")
    page.wait_for_load_state('networkidle')
    print("Network is idle. Session should be fully established.")

    save_session_data(context, page) 
    return browser, context

def main():
    with sync_playwright() as p:
        browser, context, session_storage_data = load_session_data(p)

        if not context:
            print("No saved session found.")
            browser, context = manual_login(p)
            print("\n✅ Session created successfully! Please run the script again to use it.")
            browser.close()
            return

        page = context.new_page()
        
        # Set up the interception before we navigate.
        def handle_route(route):
            response = route.fetch()
            body = response.text()
            # Modify the script to expose the C0 function globally
            body += "\n;window.C0 = C0;"
            route.fulfill(response=response, body=body)

        # Intercept the specific JS file to modify it on the fly
        page.route("**/*index-D*.js", handle_route)

        if session_storage_data:
            # ... (session injection block remains the same) ...
            print("Injecting sessionStorage data into the new page...")
            page.add_init_script(f"""
                const data = {json.dumps(session_storage_data)};
                for (const [key, value] of Object.entries(data)) {{
                    window.sessionStorage.setItem(key, value);
                }}
            """)

        print("Attempting to go directly to dashboard...")
        page.goto(DASHBOARD_URL)
        page.wait_for_selector("text=Instructions")
        print("Landed on dashboard.")

        print("\n🧭 Starting breadcrumb navigation...")
        page.get_by_text("Dashboard", exact=True).click()
        page.get_by_text("Inventory", exact=True).click()
        page.get_by_text("Products", exact=True).click()
        page.get_by_text("Full Catalog", exact=True).click()
        page.wait_for_load_state('networkidle')
        print("Product table page loaded successfully.")

        print("\nExecuting the exposed internal data generator function...")

        TOTAL_ITEMS = 4887

        # Now we call window.C0, which we created via our interception
        all_products_data = page.evaluate(f"() => window.C0(0, {TOTAL_ITEMS})")
        
        if not all_products_data or len(all_products_data) < TOTAL_ITEMS:
             raise ValueError("Failed to retrieve data from the generator function.")

        print(f"Extracted {len(all_products_data)} products instantly!")

        # Export to json 
        output_file = "products.json"
        print(f"Saving data to {output_file}...")
        with open(output_file, "w") as f:
            json.dump(all_products_data, f, indent=4)
        print("Challenge complete!")

        browser.close()

if __name__ == "__main__":
    main() 