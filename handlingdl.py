from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import os
import json
import time

SESSION_FILE = "session.json"
LOGIN_URL = "https://hiring.idenhq.com/"
DASHBOARD_URL = "https://hiring.idenhq.com/instructions"

def save_session_data(context, page):
    """Get state from Playwright and manually add sessionStorage."""
    playwright_state = context.storage_state()
    session_storage = page.evaluate("() => Object.assign({}, window.sessionStorage)")
    
    full_session_data = {
        "playwright_state": playwright_state,
        "session_storage": session_storage
    }

    with open(SESSION_FILE, "w") as f:
        json.dump(full_session_data, f, indent=2)
    print("Session data saved successfully.")

def load_session_data(p):
    """Load data from file and return both playwright state and session storage."""
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
    
    page.wait_for_load_state('networkidle')
    save_session_data(context, page)
    return browser, context

def wait_for_table_stability(page, timeout=30000):
    """Wait for the table to be stable and ready for interaction"""
    try:
        # Wait for table to exist
        page.wait_for_selector("table tbody", timeout=timeout)
        
        # Wait for at least some rows to be present
        page.wait_for_selector("table tbody tr", timeout=timeout)
        
        # Wait for network to be idle (important for dynamic loading)
        page.wait_for_load_state('networkidle', timeout=timeout)
        
        return True
    except PlaywrightTimeoutError:
        print("⚠️ Timeout waiting for table to stabilize")
        return False

def enhanced_infinite_scroll(page, max_items_expected=5000):
    """Enhanced infinite scroll with multiple strategies"""
    print("\nStarting enhanced infinite scroll...")
    
    # Finding the scrollable container more precisely
    scroll_containers = [
        "div.infinite-table",
        "div[class*='table']",
        "div[class*='scroll']", 
        ".table-container",
        "main",
        "body"
    ]
    
    scroll_container = None
    for selector in scroll_containers:
        try:
            if page.locator(selector).count() > 0:
                scroll_container = selector
                print(f"Found scroll container: {selector}")
                break
        except:
            continue
    
    if not scroll_container:
        scroll_container = "body"  # Fallback
    
    last_row_count = 0
    consecutive_no_change = 0
    scroll_attempts = 0
    max_scroll_attempts = 200  # Prevent infinite loops
    
    while scroll_attempts < max_scroll_attempts:
        scroll_attempts += 1
        
        # Get current row count
        try:
            rows = page.locator("table tbody tr")
            current_row_count = rows.count()
        except:
            print("Could not count table rows")
            break
            
        print(f"  -> Scroll attempt {scroll_attempts}: {current_row_count} rows visible")
        
        # Check if we've loaded enough data
        if current_row_count >= max_items_expected:
            print(f"Reached expected item count: {current_row_count}")
            break
        
        # If no new rows loaded
        if current_row_count == last_row_count:
            consecutive_no_change += 1
            print(f"  -> No new rows loaded (attempt {consecutive_no_change})")
            
            # Try different scroll strategies when stuck
            if consecutive_no_change == 3:
                print("  -> Trying aggressive scroll strategy...")
                # Strategy: Scroll to absolute bottom
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)
                
            elif consecutive_no_change == 6:
                print("  -> Trying container-specific scroll...")
                # Strategy: Scroll within the container
                page.evaluate(f"""
                    const container = document.querySelector('{scroll_container}');
                    if (container) {{
                        container.scrollTop = container.scrollHeight;
                    }}
                """)
                page.wait_for_timeout(2000)
                
            elif consecutive_no_change == 9:
                print("  -> Trying keyboard-based scroll...")
                # Strategy: Use keyboard navigation
                page.keyboard.press("End")
                page.wait_for_timeout(1500)
                
            elif consecutive_no_change >= 12:
                print("🏁 No new content after multiple strategies. Assuming end reached.")
                break
        else:
            consecutive_no_change = 0  # Reset counter
            
        last_row_count = current_row_count
        
        # Multiple scroll strategies in sequence
        try:
            # Strategy 1: Mouse wheel in container
            page.locator(scroll_container).hover()
            for _ in range(5):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(200)
            
            # Strategy 2: JavaScript scroll
            page.evaluate(f"""
                const container = document.querySelector('{scroll_container}');
                if (container) {{
                    container.scrollBy(0, 2000);
                }} else {{
                    window.scrollBy(0, 2000);
                }}
            """)
            
            # Strategy 3: Page Down key
            page.keyboard.press("PageDown")
            
        except Exception as e:
            print(f"Scroll error: {e}")
        
        # Wait for potential new content to load
        try:
            # Wait for either new rows to appear OR a reasonable timeout
            page.wait_for_function(
                f"() => document.querySelectorAll('table tbody tr').length > {current_row_count}",
                timeout=5000
            )
        except PlaywrightTimeoutError:
            # Timeout is expected when no new content loads
            pass
        
        # Additional wait for network requests
        try:
            page.wait_for_load_state('networkidle', timeout=3000)
        except PlaywrightTimeoutError:
            pass
    
    final_count = page.locator("table tbody tr").count()
    print(f"\nFinal result: {final_count} rows loaded after {scroll_attempts} scroll attempts")
    return final_count

def scrape_table_data_fast(page):
    """Fast bulk table data extraction using JavaScript evaluation"""
    print("\nFast bulk table data extraction...")
    
    try:
        table_data = page.evaluate("""
            () => {
                const table = document.querySelector('table');
                if (!table) return { headers: [], rows: [] };
                
                // Get headers
                const headerCells = Array.from(table.querySelectorAll('thead th'));
                const headers = headerCells.map(th => th.textContent.trim());
                
                // Get all row data in bulk
                const bodyRows = Array.from(table.querySelectorAll('tbody tr'));
                const rows = bodyRows.map(row => {
                    const cells = Array.from(row.querySelectorAll('td'));
                    return cells.map(cell => cell.textContent.trim());
                });
                
                return { headers, rows };
            }
        """)
        
        headers = table_data['headers']
        rows_data = table_data['rows']
        
        print(f"Table Headers: {headers}")
        print(f"Extracted {len(rows_data)} rows in bulk")
        
        # Convert to list of dictionaries
        all_products_data = []
        for row_data in rows_data:
            if len(row_data) == len(headers):
                product_dict = dict(zip(headers, row_data))
                all_products_data.append(product_dict)
            else:
                print(f"Skipping row with {len(row_data)} cells (expected {len(headers)})")
        
        print(f"✅ Successfully processed {len(all_products_data)} products")
        return all_products_data
        
    except Exception as e:
        print(f"Fast extraction failed: {e}")
        return []

def scrape_table_data_traditional(page):
    """Traditional row-by-row scraping as fallback"""
    print("\nTraditional table scraping (slower but more reliable)...")
    
    try:
        headers = [header.text_content().strip() for header in page.locator("table thead th").all()]
        print(f"Table Headers: {headers}")
    except Exception as e:
        print(f"Could not get headers: {e}")
        return []
    
    all_products_data = []
    try:
        all_rows = page.locator("table tbody tr").all()
        total_rows = len(all_rows)
        print(f"Processing {total_rows} rows...")
        
        # Process in smaller batches with progress updates
        batch_size = 100
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            print(f"  -> Processing rows {batch_start+1}-{batch_end} of {total_rows}")
            
            for i in range(batch_start, batch_end):
                try:
                    row = all_rows[i]
                    cells = row.locator("td").all()
                    row_data = [cell.text_content().strip() for cell in cells]
                    
                    if len(row_data) == len(headers):
                        product_dict = dict(zip(headers, row_data))
                        all_products_data.append(product_dict)
                        
                except Exception as e:
                    print(f"Error processing row {i}: {e}")
                    continue
                    
        print(f"✅ Successfully scraped {len(all_products_data)} products")
        
    except Exception as e:
        print(f"Error during table scraping: {e}")
    
    return all_products_data

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
        
        if session_storage_data:
            print("Injecting sessionStorage data...")
            page.add_init_script(f"""
                const data = {json.dumps(session_storage_data)};
                for (const [key, value] of Object.entries(data)) {{
                    window.sessionStorage.setItem(key, value);
                }}
            """)

        print("Navigating to dashboard...")
        page.goto(DASHBOARD_URL)
        page.wait_for_selector("text=Instructions")

        print("\n🧭 Following breadcrumb navigation...")
        page.get_by_text("Dashboard", exact=True).click()
        page.get_by_text("Inventory", exact=True).click()
        page.get_by_text("Products", exact=True).click()
        page.get_by_text("Full Catalog", exact=True).click()
        
        # Wait for table to be ready
        if not wait_for_table_stability(page):
            print("Table failed to load properly")
            browser.close()
            return

        print("\nProduct table loaded. Starting data extraction...")
        
        # Enhanced infinite scroll + table scraping
        try:
            print("\nEnhanced table scraping with pagination handling...")
            final_row_count = enhanced_infinite_scroll(page, max_items_expected=4887)
            
            # Try fast bulk extraction first
            scraped_data = scrape_table_data_fast(page)
            
            # If fast method fails or returns too little data, try traditional method
            if len(scraped_data) < final_row_count * 0.8:  # If we got less than 80% of expected
                print("🔄 Fast method didn't get enough data, trying traditional method...")
                scraped_data = scrape_table_data_traditional(page)
            
            print(f"Table scraping result: {len(scraped_data)} items")
            
            # Export scraped data
            if scraped_data:
                output_file = "products.json"
                with open(output_file, "w") as f:
                    json.dump(scraped_data, f, indent=4)
                print(f"✅ Data saved to {output_file}")
                print(f"Successfully extracted {len(scraped_data)} products using table scraping!")
            else:
                print("No data was successfully extracted")
                
        except Exception as e:
            print(f"Table scraping failed: {e}")

        browser.close()

if __name__ == "__main__":
    main()