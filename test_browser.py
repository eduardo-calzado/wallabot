#!/usr/bin/python
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import config as cfg

def test_browser():
    """Test the browser functionality"""
    print("Testing browser functionality...")
    print(f"Using URL: {cfg.OFFERS_URL}")
    
    driver = None
    try:
        # Setup Chrome options
        print("Setting up Chrome options...")
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # Run in visible mode for debugging
        print("Running in visible mode")
        
        # Setup driver
        print("Initializing Chrome driver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Navigate to the URL
        print(f"Navigating to URL: {cfg.OFFERS_URL}")
        driver.get(cfg.OFFERS_URL)
        print(f"Page title: {driver.title}")
        
        # Take a screenshot
        print("Taking screenshot...")
        driver.save_screenshot("test_screenshot.png")
        print("Screenshot saved to test_screenshot.png")
        
        # Wait for the cookie dialog
        print("Waiting for cookie dialog...")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
            )
            print("Cookie dialog found")
            
            accept_button = driver.find_element("id", "onetrust-accept-btn-handler")
            print("Clicking accept button...")
            accept_button.click()
            print("Cookies accepted")
        except Exception as e:
            print(f"Cookie dialog not found or error: {e}")
        
        # Wait for content to load
        print("Waiting for page to load fully...")
        sleep(5)
        
        # Find item cards with different selectors
        print("Trying to find item cards with different selectors...")
        
        selectors = [
            '.ItemCardList__item',
            'a[data-testid="itemCard"]',
            '.ItemCard',
            '.Card',
            'div[class*="Card"]'
        ]
        
        for selector in selectors:
            print(f"Trying selector: {selector}")
            cards = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"Found {len(cards)} elements with selector '{selector}'")
            
            if cards:
                print(f"First element HTML:")
                print(cards[0].get_attribute('outerHTML')[:200] + "...")
                break
        
        # Save page source for inspection
        print("Saving page source...")
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Page source saved to page_source.html")
        
        # Wait for user to inspect the browser
        print("Test complete. Browser will close in 30 seconds...")
        sleep(30)
        
    except Exception as e:
        print(f"Error in browser test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()
            print("Browser closed")

if __name__ == "__main__":
    test_browser() 