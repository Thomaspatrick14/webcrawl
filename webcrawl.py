import time
import random
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "1234567890:abcdefghijklmnopqrstuvwxyz"  # Replace with your bot token
TELEGRAM_CHAT_ID = "1234567890"  # Replace with your chat ID

# URL of the page to monitor
URL = "abc.xyz"  # Add the URL of the page you want to monitor

# Set up Selenium WebDriver with visible browser
chrome_options = Options()
# Remove headless mode - browser will be visible
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--window-size=1920,1080")
# Add a user agent to avoid detection
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

# Configure service
service = Service('/usr/bin/chromedriver')  # Replace with the path to your ChromeDriver

# Function to send a Telegram message
def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
        }
        response = requests.post(url, json=payload, timeout=30)  # Add timeout
        if response.status_code == 200:
            print("Telegram message sent successfully!")
        else:
            print(f"Failed to send Telegram message. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending Telegram message: {str(e)}")

# Function to create a new driver instance
def create_driver():
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(120)  # Set page load timeout
        driver.set_script_timeout(120)  # Set script timeout
        return driver
    except Exception as e:
        print(f"Error creating driver: {str(e)}")
        return None

# Function to check for 502 error
def is_502_error(driver):
    try:
        # Check if response status is 502
        response_status = driver.execute_script("return window.performance.getEntries()[0].responseStatus")
        if response_status == 502:
            print("502 Bad Gateway Error detected.")
            return True
            
        # Also check page content for typical 502 error messages
        page_source = driver.page_source.lower()
        if "502 bad gateway" in page_source or "bad gateway" in page_source:
            print("502 Bad Gateway Error detected in page content.")
            return True
            
        return False
    except Exception as e:
        print(f"Error checking for 502: {str(e)}")
        return False

# Function to check if the page is fully loaded
def is_page_fully_loaded(driver):
    try:
        # Check if residence blocks are present
        residence_blocks = driver.find_elements("css selector", "div.residence_block")
        if not residence_blocks:
            print("No residence blocks found on page")
            return False
        
        # Check if at least one property has a proper name and price
        for block in residence_blocks[:3]:  # Check at least first 3 blocks
            try:
                name = block.find_element("css selector", "div.leftSide h5.residence_name").text.strip()
                price = block.find_element("css selector", "div.rightSide h4.price_text").text.strip()
                if name and price and len(name) > 1 and len(price) > 1:
                    return True
            except:
                continue
                
        print("Residence blocks found but couldn't extract valid name and price")
        return False
    except Exception as e:
        print(f"Error checking if page is fully loaded: {str(e)}")
        return False

# JSON file to store properties
PROPERTIES_FILE = "properties.json"

# Function to read properties from JSON file
def read_properties_from_file():
    try:
        with open(PROPERTIES_FILE, "r") as file:
            properties = json.load(file)
            return set(tuple(prop) for prop in properties)
    except FileNotFoundError:
        return set()
    except Exception as e:
        print(f"Error reading properties from file: {str(e)}")
        return set()

# Function to write properties to JSON file
def write_properties_to_file(properties):
    try:
        with open(PROPERTIES_FILE, "w") as file:
            json.dump(list(properties), file)
    except Exception as e:
        print(f"Error writing properties to file: {str(e)}")

# Function to scrape properties
def scrape_properties(driver):
    try:
        driver.get(URL)
        # Wait for content to load
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Check for 502 error
        if is_502_error(driver):
            print("502 Bad Gateway Error. Retrying...")
            return []
        
        # Wait for actual content to be visible and properly loaded
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            if is_page_fully_loaded(driver):
                break
            print(f"Page not fully loaded yet. Waiting... (attempt {retry_count+1}/{max_retries})")
            time.sleep(3)
            retry_count += 1
            
        if retry_count >= max_retries:
            print("Failed to fully load page content after multiple attempts")
            return []
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        properties = []
        property_blocks = soup.find_all('div', class_='residence_block')
        
        if not property_blocks:
            print("Warning: No property blocks found. Page might not have loaded correctly.")
            return []
            
        for property_block in property_blocks:
            try:
                # Extract property name
                name_tag = property_block.find('div', class_='leftSide')
                if not name_tag:
                    continue
                    
                name_element = name_tag.find('h5', class_='residence_name')
                if not name_element:
                    continue
                    
                property_name = name_element.text.strip()
                if not property_name or len(property_name) <= 1:
                    continue
                
                # Extract property price
                price_tag = property_block.find('div', class_='rightSide')
                if not price_tag:
                    continue
                    
                price_element = price_tag.find('h4', class_='price_text')
                if not price_element:
                    continue
                    
                property_price = price_element.text.strip()
                if not property_price or len(property_price) <= 1:
                    continue
                
                # Only add if both name and price are valid
                if property_name and property_price:
                    # print(f"Found property: {property_name} - {property_price}")
                    properties.append((property_name, property_price))
            except Exception as e:
                print(f"Error parsing property block: {str(e)}")
                continue
        
        print(f"Successfully scraped {len(properties)} properties")
        return properties
    except TimeoutException:
        print("Page load timed out. Restarting driver...")
        return []
    except Exception as e:
        print(f"Error scraping properties: {str(e)}")
        return []

# Function to monitor the website
def monitor_website():
    driver = create_driver()
    if not driver:
        send_telegram_message("Failed to initialize browser. Please check your configuration.")
        return
    
    try:
        # Initial scrape
        retry_count = 0
        previous_properties = read_properties_from_file()
        
        while not previous_properties and retry_count < 5:  # Increased retries
            properties = scrape_properties(driver)
            if properties and len(properties) > 0:  # Make sure we have valid properties
                previous_properties = set(properties)
                write_properties_to_file(previous_properties)
                break
            retry_count += 1
            print(f"Retrying initial scrape (attempt {retry_count}/5)...")
            # Restart driver
            driver.quit()
            driver = create_driver()
            time.sleep(5)
        
        if not previous_properties or len(previous_properties) == 0:
            error_msg = "Failed to scrape initial properties after multiple attempts."
            print(error_msg)
            send_telegram_message(error_msg)
            return
        
        # Send the initial number of properties and its names and prices to Telegram
        message = f"Crawling started\nInitial number of properties: {len(previous_properties)}\n\n"
        for name, price in previous_properties:
            message += f"Name: {name}\nPrice: {price}\n\n"
        send_telegram_message(message)
        
        consecutive_failures = 0
        
        while True:
            try:
                print("Checking for new properties...")
                current_properties = set(scrape_properties(driver))
                
                # Check for 502 error again explicitly
                if is_502_error(driver):
                    print("502 Bad Gateway Error detected during monitoring. Retrying...")
                    time.sleep(10)  # Wait before retry
                    continue
                
                # Reset failure counter on success
                if current_properties and len(current_properties) > 0:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    print(f"Failed to get properties ({consecutive_failures}/5).")
                    
                    if consecutive_failures >= 5:
                        print("Too many consecutive failures. Restarting driver...")
                        send_telegram_message("Restarting monitoring due to consecutive failures.")
                        driver.quit()
                        driver = create_driver()
                        consecutive_failures = 0
                        continue
                    
                    time.sleep(30)  # Wait longer on failure
                    continue
                
                if len(current_properties) > len(previous_properties):
                    new_properties = current_properties - previous_properties
                    print(f"Found {len(new_properties)} new properties!")
                    message = ""
                    for name, price in new_properties:
                        message += f"New Property Available!\nName: {name}\nPrice: {price}\n\n"
                    send_telegram_message(message)
                    previous_properties = current_properties
                    write_properties_to_file(previous_properties)
                    
                elif len(current_properties) < len(previous_properties):
                    removed_properties = previous_properties - current_properties
                    message = f"{len(new_properties)} properties were removed.\n"
                    for name, price in removed_properties:
                        message += f"Name: {name}\nPrice: {price}\n\n"
                    send_telegram_message(message)
                    previous_properties = current_properties
                    write_properties_to_file(previous_properties)
                else:
                    print("No changes in properties found.")
                
                # Randomize wait time to avoid detection
                wait_time = random.randint(10, 20)
                print(f"Waiting for {wait_time} seconds before the next check...")
                time.sleep(wait_time)
                
            except Exception as e:
                error_message = f"Error during monitoring: {str(e)}"
                print(error_message)
                send_telegram_message(error_message)
                
                # Restart the driver on error
                try:
                    driver.quit()
                except:
                    pass
                    
                time.sleep(15)
                driver = create_driver()
                if not driver:
                    send_telegram_message("Failed to restart browser after error. Stopping monitoring.")
                    return
    
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
        send_telegram_message("Monitoring stopped by user.")
    finally:
        try:
            driver.quit()
        except:
            pass

# Run the monitor
if __name__ == "__main__":
    try:
        send_telegram_message("Property monitoring script starting up...")
        monitor_website()
    except Exception as e:
        error_message = f"Critical error occurred: {str(e)}"
        print(error_message)
        send_telegram_message(error_message)