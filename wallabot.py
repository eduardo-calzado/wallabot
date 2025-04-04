#!/usr/bin/python
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from selenium.common.exceptions import NoSuchElementException
import pickle
import os
import config as cfg
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import email_template

# Set up logging based on DEBUG flag in config
DEBUG = getattr(cfg, 'DEBUG', False)
log_level = logging.DEBUG if DEBUG else logging.INFO
ENABLE_FILE_LOGGING = getattr(cfg, 'ENABLE_FILE_LOGGING', True)

# Create formatters
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Set root logger to DEBUG to capture all messages
logger.handlers = []  # Clear any existing handlers

# Create console handler (respects the DEBUG setting)
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Create file handler only if enabled
if ENABLE_FILE_LOGGING:
    # Create file handler (always logs at DEBUG level for complete traces)
    file_handler = logging.FileHandler("wallabot.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    if DEBUG:
        logger.debug("File logging enabled, writing detailed logs to wallabot.log")

def log_debug(message):
    """Log debug messages only when DEBUG is True"""
    if DEBUG:
        logger.debug(message)

def send_mail(offers):
    """Build message with current offers and send them via email.
    
    Args:
        offers: List of offer dictionaries containing product information
    """
    if not offers:
        logger.info("No offers to send.")
        return
        
    # Setup mail server
    try:
        # Select the appropriate mail server based on the email domain
        if '@gmail.com' in cfg.username:
            server = smtplib.SMTP("smtp.gmail.com", port=587)
            server.starttls()
            logger.info("Using Gmail SMTP server")
        else:
            server = smtplib.SMTP("smtp.sapo.pt", port=587)
            server.starttls()
            logger.info("Using Sapo SMTP server")
        
        server.set_debuglevel(DEBUG)

        try:
            server.login(cfg.username, cfg.password)
            logger.info("Email login successful")
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {e}")
            logger.error("\nFor Gmail accounts, you need to:")
            logger.error("1. Enable 2-factor authentication: https://myaccount.google.com/security")
            logger.error("2. Create an app password: https://myaccount.google.com/apppasswords")
            logger.error("3. Use that app password in config.py instead of your regular password")
            server.quit()
            return

        # Setup message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Wallapop Offers Alert"
        message["From"] = cfg.username
        message["To"] = cfg.receiver

        # Generate email content using the template module
        text = email_template.generate_text_body(offers)
        html = email_template.generate_html_body(offers)

        # Convert both parts to MIMEText objects and add them to the MIMEMultipart message
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)

        # Send Mail
        try:
            server.sendmail(
                cfg.username, cfg.receiver, message.as_string()
            )
            logger.info("Email sent successfully.")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Exception: {e}")
        finally:
            server.quit()
            
    except Exception as e:
        logger.error(f"Error setting up email: {e}")

def get_seller_info(driver, product_url):
    """Get seller info, location, and shipping details from product detail page
    
    Args:
        driver: Selenium WebDriver instance
        product_url: URL of the product detail page
        
    Returns:
        Dictionary containing seller information and product details
    """
    # Initialize result dictionary with default values for product page data
    result = {
        "name": "Sin nombre",
        "sales": "0",
        "number_of_rates": "0",
        "rate": "0",
        "location": "Ubicación desconocida",
        "shipping": "No",
        "image_url": "",  # Fallback if not found on search page
        "filtered": False,
        "last_update": "Desconocido",  # New: Last update time
        "views": "0",                  # New: View count
        "favorites": "0"               # New: Favorites count
    }
    
    try:
        logger.info(f"Visiting product page: {product_url}")
        driver.get(product_url)
        sleep(3)  # Increase wait time for page to load
        
        # Debug page title
        log_debug(f"Product page title: {driver.title}")
        
        # Extract last update time
        try:
            last_update_element = driver.find_element(By.CSS_SELECTOR, 'span[class*="ItemDetailStats__description"]')
            if last_update_element:
                result["last_update"] = last_update_element.text.strip()
                log_debug(f"Found last update: {result['last_update']}")
        except Exception:
            log_debug("Last update time not found")
            
        # Extract views count
        try:
            views_element = driver.find_element(By.CSS_SELECTOR, 'span[aria-label="Views"]')
            if views_element:
                result["views"] = views_element.text.strip()
                log_debug(f"Found views: {result['views']}")
        except Exception:
            log_debug("Views count not found")
            
        # Extract favorites count
        try:
            favorites_element = driver.find_element(By.CSS_SELECTOR, 'span[aria-label="Favorites"]')
            if favorites_element:
                result["favorites"] = favorites_element.text.strip()
                log_debug(f"Found favorites: {result['favorites']}")
        except Exception:
            log_debug("Favorites count not found")
            
        # Extract product image - handled in separate try/except
        # Only as fallback, we now primarily get images from the search page
        try:
            # Try a few common selectors for product images
            selectors = ['img.ImageSlider__image', 'div.detail-gallery img', 'img.detail-image']
            for selector in selectors:
                try:
                    image_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if image_element:
                        result["image_url"] = image_element.get_attribute('src')
                        log_debug(f"Found product image: {result['image_url']}")
                        break
                except Exception:
                    continue
                    
            if not result["image_url"] and DEBUG:
                logger.debug("No product image found with any selector")
        except Exception:
            log_debug("Error while trying to find product image")
        
        # Check if shipping is available
        has_shipping = False
        try:
            shipping_element = driver.find_element(By.CSS_SELECTOR, 'section[class*="item-detail_ItemDetail"] wallapop-badge[badge-type="shippingAvailable"]')
            if shipping_element:
                result["shipping"] = "Sí"
                has_shipping = True
                log_debug("Found shipping badge")
            else:
                result["shipping"] = "No"
                log_debug("Shipping not available (no badge)")
        except Exception:
            log_debug("Shipping not available (no element)")
            result["shipping"] = "No"
        
        # If shipping is required but this item doesn't have it, return early
        if getattr(cfg, 'SHIPPING_REQUIRED', False) and not has_shipping:
            logger.info(f"Skipping item without shipping: {driver.title}")
            result["filtered"] = True
            return result
            
        # Continue with other data extraction if not skipping
        
        # Extract sales count - handled in separate try/except
        try:
            sales_element = driver.find_element(By.CSS_SELECTOR, 'span[data-testid="sellsCounter"]')
            result["sales"] = sales_element.text.strip()
            log_debug(f"Found sales info: {result['sales']}")
            
            # Check if we should skip items with low sales counts
            min_sales = getattr(cfg, 'SKIP_WITH_LESS_THAN_SALES_NUMBER', 0)
            if min_sales > 0:
                try:
                    # Extract numeric part from sales text and handle various formats
                    sales_text = result["sales"].split()[0]  # Get first part before any space
                    # Remove parentheses if they exist
                    sales_text = sales_text.replace("(", "").replace(")", "")
                    # Remove thousands separators
                    sales_text = sales_text.replace(".", "").replace(",", "")
                    sales_count = int(sales_text)
                    
                    if sales_count < min_sales:
                        logger.info(f"Skipping item with too few sales ({sales_count} < {min_sales}): {driver.title}")
                        result["filtered"] = True
                        return result
                except (ValueError, TypeError, IndexError):
                    # If we can't parse the sales count, assume it's lower than minimum
                    logger.info(f"Skipping item with unparseable sales count: {result['sales']}")
                    result["filtered"] = True
                    return result
        except Exception:
            log_debug("Sales number not found")
        
        # Extract reviews link - handled in separate try/except
        try:
            reviews_link = driver.find_element(By.CSS_SELECTOR, 'a[href="#item-detail-reviews"]')
            result["number_of_rates"] = reviews_link.text.strip()
            log_debug(f"Found rating link: {result['number_of_rates']}")
        except Exception:
            log_debug("Rating link not found")
        
        # Extract reviews counter - handled in separate try/except
        try:
            reviews_counter = driver.find_element(By.CSS_SELECTOR, '[data-testid="reviewsCounter"]')
            counter_text = reviews_counter.text.strip()
            result["number_of_rates"] = counter_text if counter_text else "0"
            log_debug(f"Found reviews counter: {result['number_of_rates']}")
            
            # Try to find the rate in the span before the reviews counter
            try:
                # Find the parent of the reviews counter
                parent = reviews_counter.find_element(By.XPATH, '..')
                # Find all spans in the parent
                spans = parent.find_elements(By.TAG_NAME, 'span')
                # Find the position of the reviews_counter in the spans
                for i, span in enumerate(spans):
                    if span == reviews_counter:
                        # Check if there's a span before this one
                        if i > 0:
                            rate_span = spans[i-1]
                            result["rate"] = rate_span.text.strip()
                            log_debug(f"Found seller rate from span before reviews counter: {result['rate']}")
                            break
            except Exception as e:
                log_debug(f"Couldn't get rate from span before reviews counter: {e}")
            
            # Check if we should skip items with low rating counts
            min_ratings = getattr(cfg, 'SKIP_WITH_LESS_THAN_RATING_COUNTER', 0)
            if min_ratings > 0:
                try:
                    # Convert to int for comparison, handling various formats: (290), 290, etc.
                    cleaned_rating = result["number_of_rates"]
                    # Remove parentheses if they exist
                    cleaned_rating = cleaned_rating.replace("(", "").replace(")", "")
                    # Remove dots and commas (thousands separators)
                    cleaned_rating = cleaned_rating.replace(".", "").replace(",", "")
                    # Convert to integer
                    rating_count = int(cleaned_rating)
                    
                    if rating_count < min_ratings:
                        logger.info(f"Skipping item with too few ratings ({rating_count} < {min_ratings}): {driver.title}")
                        result["filtered"] = True
                        return result
                except (ValueError, TypeError):
                    # If we can't parse the rating count, assume it's lower than minimum
                    logger.info(f"Skipping item with unparseable rating count: {result['number_of_rates']}")
                    result["filtered"] = True
                    return result
                    
        except Exception:
            log_debug("Reviews counter not found")
            
        
        # Extract seller name - handled in separate try/except
        try:
            seller_name_element = driver.find_element(By.CSS_SELECTOR, 'h3[class*="item-detail-header"]')
            result["name"] = seller_name_element.text.strip()
            log_debug(f"Found seller name: {result['name']}")
        except Exception as e:
            log_debug("Seller name not found")
            
        # Extract location - handled in separate try/except
        try:
            # Multiple ways to find location
            location_found = False
            
            # Primary method: Find div with class containing "item-detail-location" and extract text from anchor element
            try:
                location_div = driver.find_element(By.CSS_SELECTOR, 'div[class*="item-detail-location"]')
                location_link = location_div.find_element(By.TAG_NAME, 'a')
                if location_link and location_link.text.strip():
                    result["location"] = location_link.text.strip()
                    location_found = True
                    log_debug(f"Found location from div-link: {result['location']}")
            except Exception:
                pass
            
            # First fallback: walla-icon with location icon
            if not location_found:
                try:
                    location_element = driver.find_element(By.CSS_SELECTOR, 'walla-icon[icon="location"] span')
                    if location_element and location_element.text.strip():
                        result["location"] = location_element.text.strip()
                        location_found = True
                        log_debug(f"Found location with icon selector: {result['location']}")
                except Exception:
                    pass
                
            # Second fallback: location section by class
            if not location_found:
                try:
                    location_element = driver.find_element(By.CSS_SELECTOR, '.ItemDetail__location')
                    if location_element and location_element.text.strip():
                        result["location"] = location_element.text.strip()
                        location_found = True
                        log_debug(f"Found location with class selector: {result['location']}")
                except Exception:
                    pass
                    
            if not location_found and DEBUG:
                logger.debug("Location not found with any selector")
        except Exception as e:
            log_debug(f"Error while finding location: {e}")
            log_debug("Using default location")
            
        # Take a screenshot for debugging only if configured
        if DEBUG:
            try:
                screenshot_filename = f"product_page_{product_url.split('/')[-1][:10]}.png"
                driver.save_screenshot(screenshot_filename)
                logger.debug(f"Saved product page screenshot to {screenshot_filename}")
            except Exception:
                log_debug("Failed to save screenshot, continuing anyway")
            
    except Exception as e:
        logger.error(f"Error getting seller info, using defaults: {e}")
    finally:
        # Always navigate back, even if errors occurred
        try:
            driver.back()
            sleep(2)
        except Exception:
            log_debug("Error navigating back, continuing anyway")
        
        # Always return result, with default values for any missing data
        return result

def scrape_offers(driver):
    """Check all offers on the Wallapop search page
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of valid product items that pass all filtering criteria
    """
    try:
        logger.info("Processing Wallapop search page...")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
            )
            log_debug("Cookie dialog found")
            accept_terms_button = driver.find_element("id", "onetrust-accept-btn-handler")
            if accept_terms_button:
                log_debug("Clicking accept button...")
                accept_terms_button.click()
                log_debug("Cookies accepted")
        except Exception as e:
            log_debug(f"No cookie dialog or error accepting cookies: {e}")
            
        logger.info("Waiting for page to load...")
        sleep(5)
        
        # Take a screenshot for debugging
        if DEBUG:
            try:
                driver.save_screenshot("wallabot_screenshot.png")
                logger.debug("Screenshot saved to wallabot_screenshot.png")
            except Exception:
                log_debug("Failed to save screenshot, continuing anyway")

        # Wait for initial content to load
        log_debug("Loading page content...")
        try:
            sleep(3)
        except Exception as e:
            log_debug(f"Error while waiting for page: {e}")

        # Find all offer cards using the correct selector
        log_debug("Finding item cards...")
        cards = []
        try:
            cards = driver.find_elements(By.CSS_SELECTOR, '.ItemCardList__item')
            logger.info(f"Found {len(cards)} cards")
        except Exception as e:
            logger.error(f"Error finding cards: {e}")
        
        if not cards:
            logger.error("No cards found. Check your search URL.")
            if DEBUG:
                try:
                    with open("page_source.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    logger.debug("Page source saved to page_source.html")
                except Exception:
                    log_debug("Failed to save page source")
            return []
        
        # Extract data from cards WITHOUT visiting individual pages first
        new_cards = []
        logger.info("First pass: extracting basic info from cards...")
        
        # Get maximum items to check from config (default to 6 if not set)
        max_items = getattr(cfg, 'MAX_ITEMS_TO_CHECK', 6)
        
        # Limit cards to the maximum specified in config
        max_cards = min(max_items, len(cards))
        logger.info(f"Processing {max_cards} of {len(cards)} items (MAX_ITEMS_TO_CHECK={max_items})")
        
        for idx, card in enumerate(cards[:max_cards]):
            try:
                # Default values - seller info, location and shipping will be filled in second pass
                item_data = {
                    'titulo': "Unknown Title", 
                    'precio': "Unknown Price", 
                    'enlace': "#", 
                    'reservada': False,
                    'seller_name': "Desconocido",           # Only available on product page
                    'seller_number_of_rates': "0",          # Only available on product page
                    'seller_rate': "0",                     # Only available on product page
                    'seller_sales': "0",                    # Only available on product page
                    'location': "Desconocido",              # Only available on product page
                    'shipping': "No",                       # Only available on product page
                    'image_url': "",                        # Available on search page
                    'last_update': "Desconocido",           # New: Last update time
                    'views': "0",                           # New: View count
                    'favorites': "0"                        # New: Favorites count
                }
                
                # Extract basic card data with individual try/except for each field
                try:
                    item_data['precio'] = card.find_element(By.CLASS_NAME, 'ItemCard__price').text
                except Exception:
                    log_debug(f"Could not extract price for item {idx+1}")
                
                try:
                    item_data['titulo'] = card.find_element(By.CLASS_NAME, 'ItemCard__title').text
                except Exception:
                    log_debug(f"Could not extract title for item {idx+1}")
                
                try:
                    item_data['enlace'] = card.get_attribute('href')
                except Exception:
                    log_debug(f"Could not extract link for item {idx+1}")
                
                # Extract the thumbnail image directly from the card
                try:
                    img_element = card.find_element(By.TAG_NAME, 'img')
                    if img_element:
                        item_data['image_url'] = img_element.get_attribute('src')
                        log_debug(f"Found thumbnail image: {item_data['image_url']}")
                except Exception:
                    log_debug(f"Could not extract thumbnail for item {idx+1}")
                
                # Check if reserved
                try:
                    reservada_element = card.find_element(By.CLASS_NAME, 'ItemCard__badge')
                    if reservada_element:
                        item_data['reservada'] = True
                except Exception:
                    # Not reserved or couldn't find badge
                    pass
                
                # Skip reserved items in first pass if configured to do so
                if item_data['reservada'] and getattr(cfg, 'SKIP_RESERVED_ITEMS', False):
                    logger.info(f"Skipping reserved item in first pass: {item_data['titulo']}")
                    continue
                
                # Print basic info for debugging
                log_debug(f"Item {idx+1}: {item_data['titulo']} - {item_data['precio']}")
                new_cards.append(item_data)
                
            except Exception as e:
                logger.error(f"Error processing item {idx+1}: {e}")
                # Continue with next item instead of breaking
                continue
        
        logger.info(f"Collected data for {len(new_cards)} items")
        
        # Now visit all items' detail pages to get seller info
        logger.info(f"Second pass: visiting detail pages for {len(new_cards)} items to get seller info, location, and shipping details...")
        valid_items = []  # Create a list for items that pass all filters
        for idx, item in enumerate(new_cards):
            if item['enlace'] != "#":
                # Skip reserved items if configured to do so
                if item['reservada'] and getattr(cfg, 'SKIP_RESERVED_ITEMS', False):
                    logger.info(f"Skipping reserved item: {item['titulo']}")
                    continue
                    
                log_debug(f"Visiting product page for item {idx+1}: {item['titulo']}")
                seller_info = get_seller_info(driver, item['enlace'])
                
                # Check if the item was filtered in get_seller_info
                if seller_info.get('filtered', False):
                    logger.info(f"Item was filtered: {item['titulo']}")
                    continue
                
                # Update with data only available on product detail page
                item['seller_name'] = seller_info.get('name', "Desconocido")
                item['seller_number_of_rates'] = seller_info.get('number_of_rates', "0")
                item['seller_rate'] = seller_info.get('rate', "0")
                item['seller_sales'] = seller_info.get('sales', "0")
                item['location'] = seller_info.get('location', "Desconocido")
                item['shipping'] = seller_info.get('shipping', "No")
                
                # Add new statistics
                item['last_update'] = seller_info.get('last_update', "Desconocido")
                item['views'] = seller_info.get('views', "0")
                item['favorites'] = seller_info.get('favorites', "0")
                
                # Only update image URL if we didn't get it from the search page
                if not item['image_url'] and seller_info.get('image_url'):
                    item['image_url'] = seller_info.get('image_url', "")
                
                if DEBUG:
                    logger.debug(f"  Updated seller info for item {idx+1}")
                    logger.debug(f"  Seller: {item['seller_name']}")
                    logger.debug(f"  Location: {item['location']}")
                    logger.debug(f"  Shipping: {item['shipping']}")
                    logger.debug(f"  Seller rate: {item['seller_rate']}")
                    logger.debug(f"  Seller sales: {item['seller_sales']}")
                    logger.debug(f"  Seller number of rates: {item['seller_number_of_rates']}")
                    logger.debug(f"  Seller number of sales: {item['seller_sales']}")
                
                # Item passed all filters, add it to valid items
                valid_items.append(item)
        
        logger.info(f"Successfully processed {len(valid_items)} valid items out of {len(new_cards)} after filtering")
        
        # Print summary of what sources were used for data
        print("INFORMATION SUMMARY:")
        print("- Search page data: Product Title, Price, Link to Product, Reservation Status, Thumbnail Image")
        print("- Product page data: Seller Name, Seller Ratings, Seller Sales, Location, Shipping Availability, Fallback Images")
        
        return valid_items
        
    except Exception as e:
        logger.error(f"Error in scrape_offers: {e}")
        if DEBUG:
            import traceback
            traceback.print_exc()
        return []  # Return empty list instead of breaking

def setup_driver(headless=True):
    """Setup chrome driver to scrape
    
    Args:
        headless: Boolean indicating whether to run in headless mode
        
    Returns:
        Configured WebDriver instance
    """
    try:
        logger.info("Configuring Chrome...")
        chrome_options = webdriver.ChromeOptions()
        if headless:
            log_debug("Running in headless mode")
            chrome_options.add_argument('--headless=new')
        else:
            log_debug("Running in visible mode")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Try to create the driver with automatic version detection
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            log_debug("Using webdriver-manager to find compatible ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except ImportError:
            # Fall back to direct Chrome instantiation
            log_debug("webdriver-manager not available, using direct Chrome instantiation...")
            driver = webdriver.Chrome(options=chrome_options)
        
        logger.info(f"Opening URL: {cfg.OFFERS_URL}")
        driver.get(cfg.OFFERS_URL)
        log_debug(f"Page title: {driver.title}")
        return driver
    except Exception as e:
        logger.error(f"Error setting up ChromeDriver: {e}")
        if DEBUG:
            import traceback
            traceback.print_exc()
        raise

def check_history(current_offers):
    """Check local stored offers and only return the new ones
    
    Args:
        current_offers: List of current offers to check against history
        
    Returns:
        List of new offers not previously seen
    """
    new_offers = []
    
    try:
        if os.path.exists('offers.pickle') and os.path.getsize('offers.pickle') > 0:
            logger.info(f"Loading offer history...")
            try:
                with open('offers.pickle', 'rb') as f:
                    data = pickle.load(f)
                log_debug(f"Loaded {len(data)} previous offers")
                
                # Check for new offers
                for offer in current_offers:
                    if offer not in data:
                        logger.info(f"New offer: {offer['titulo']}")
                        data.append(offer)
                        new_offers.append(offer)
            except (pickle.UnpicklingError, EOFError, UnicodeDecodeError) as e:
                logger.error(f"Error loading pickle file: {e}")
                logger.info("Creating new history file due to corruption")
                # Create a backup of the corrupt file for debugging
                try:
                    if os.path.exists('offers.pickle'):
                        import shutil
                        shutil.copy2('offers.pickle', 'offers.pickle.corrupt')
                        logger.info("Backup of corrupt file saved as offers.pickle.corrupt")
                except Exception as backup_error:
                    logger.error(f"Failed to backup corrupt file: {backup_error}")
                
                # Use current offers as new data
                data = current_offers
                new_offers = current_offers
        else:
            logger.info("No history file found, creating new history")
            data = current_offers
            new_offers = current_offers
            
        # Save updated history
        log_debug(f"Saving {len(data)} offers to history")
        try:
            with open('offers.pickle', 'wb') as f:
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        except Exception as save_error:
            logger.error(f"Error saving history file: {save_error}")
            # Try with a new file if saving fails
            try:
                with open('offers_new.pickle', 'wb') as f:
                    pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
                logger.info("Saved to alternate file offers_new.pickle")
            except Exception:
                logger.error("Failed to save history to alternate file")
    except Exception as e:
        logger.error(f"Unexpected error in check_history: {e}")
        # Return current offers as new if we hit an unexpected error
        return current_offers
        
    return new_offers

def main(headless=True, debug_delay=0):
    """Main function to run the bot
    
    Args:
        headless: Boolean indicating whether to run in headless mode
        debug_delay: Seconds to keep browser open for debugging (when not headless)
    """
    driver = None
    logger.info("Starting Wallabot...")
    log_debug(f"Using search URL: {cfg.OFFERS_URL}")
    
    try:
        driver = setup_driver(headless)
        
        logger.info("Scraping offers...")
        offers = scrape_offers(driver)
        logger.info(f"Found {len(offers) if offers else 0} offers")

        if not offers:
            logger.info("No offers found")
            return
            
        logger.info("Checking for new offers...")
        new_offers = check_history(offers)
        logger.info(f"Found {len(new_offers)} new offers")

        if new_offers:
            logger.info("Sending email notification...")
            send_mail(new_offers)
        else:
            logger.info("No new offers to send")
            
        # Debug delay if requested
        if debug_delay > 0 and not headless:
            logger.info(f"Debug mode: Keeping browser open for {debug_delay} seconds...")
            sleep(debug_delay)
            
    except Exception as e:
        logger.error(f"Error running Wallabot: {e}")
        if DEBUG:
            import traceback
            traceback.print_exc()
    finally:
        if driver:
            logger.info("Closing driver...")
            try:
                driver.quit()
            except:
                logger.error("Error closing driver")
        logger.info("Done")
                     
if __name__=="__main__":
    import sys
    
    # Process command-line arguments
    headless = True
    debug_delay = 0
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == '--visible':
                headless = False
            elif arg == '--debug':
                headless = False
                debug_delay = 30
            elif arg.startswith('--delay='):
                try:
                    debug_delay = int(arg.split('=')[1])
                except:
                    logger.error(f"Invalid delay value in {arg}, using default")
    
    try:
        main(headless, debug_delay)
    except Exception as e:
        logger.error(f"Uncaught exception: {e}")
        if DEBUG:
            import traceback
            logger.error(traceback.format_exc())