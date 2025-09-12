"""
Legal Renderer - Selenium-based web scraping for legal sites
"""

import time
import logging
import tempfile
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

from .config import SELENIUM_CONFIG, CHROME_OPTIONS, LEGAL_SITES
from .exceptions import SeleniumError, WebsiteBlockedError, SearchError

logger = logging.getLogger(__name__)

class LegalRenderer:
    """Selenium-based renderer for legal websites"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        
    def _setup_driver(self):
        """Setup Chrome driver with stealth options"""
        try:
            options = Options()
            
            if self.headless:
                options.add_argument("--headless=new")
            
            # Add stealth options
            for option in CHROME_OPTIONS:
                options.add_argument(option)
            
            # Set window size
            window_size = SELENIUM_CONFIG["window_size"]
            options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
            
            # Use temporary profile
            options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
            options.add_argument(f"--profile-directory={uuid.uuid4()}")
            
            # Disable automation flags
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Create driver - Selenium Manager will auto-download ChromeDriver
            self.driver = webdriver.Chrome(options=options)
            
            # Set timeouts
            self.driver.set_page_load_timeout(SELENIUM_CONFIG["page_load_timeout"])
            self.driver.implicitly_wait(SELENIUM_CONFIG["implicit_wait"])
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise SeleniumError(f"Driver setup failed: {e}")
    
    def render_page(self, url, wait_for_element=None, scroll=True):
        """
        Render a page and return HTML content
        
        Args:
            url: URL to render
            wait_for_element: CSS selector to wait for (optional)
            scroll: Whether to scroll to load dynamic content
            
        Returns:
            str: HTML content of the page
        """
        if not self.driver:
            self._setup_driver()
        
        try:
            logger.info(f"Loading page: {url}")
            self.driver.get(url)
            
            # Wait for specific element if provided
            if wait_for_element:
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                    )
                    logger.info(f"Found element: {wait_for_element}")
                except TimeoutException:
                    logger.warning(f"Timeout waiting for element: {wait_for_element}")
            
            # Wait for body to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll to load dynamic content
            if scroll:
                self._scroll_page()
            
            # Get final HTML
            html = self.driver.page_source
            logger.info(f"Successfully rendered page: {url} (HTML length: {len(html)})")
            
            return html
            
        except TimeoutException:
            logger.error(f"Timeout loading page: {url}")
            raise WebsiteBlockedError(f"Page load timeout: {url}")
        except WebDriverException as e:
            logger.error(f"WebDriver error for {url}: {e}")
            raise SeleniumError(f"WebDriver error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error rendering {url}: {e}")
            raise SeleniumError(f"Rendering failed: {e}")
    
    def _scroll_page(self):
        """Scroll page to load dynamic content"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(SELENIUM_CONFIG["max_scrolls"]):
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content to load
                time.sleep(SELENIUM_CONFIG["scroll_pause_time"])
                
                # Check if page height changed
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    logger.info(f"Scrolling complete after {i+1} scrolls")
                    break
                
                last_height = new_height
                
        except Exception as e:
            logger.warning(f"Error during scrolling: {e}")
    
    def search_pair(self, query):
        """
        Search PAIR website for Hansard content
        
        Args:
            query: Search query
            
        Returns:
            str: HTML content of search results
        """
        try:
            url = LEGAL_SITES["pair_search"]
            html = self.render_page(url, wait_for_element="input[type='search'], input[name='q']")
            
            # Find search input
            search_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[name='q']")
            search_input.clear()
            search_input.send_keys(query)
            search_input.submit()
            
            # Wait for results
            time.sleep(3)
            
            # Get results HTML
            results_html = self.driver.page_source
            logger.info(f"PAIR search completed for query: {query}")
            
            return results_html
            
        except Exception as e:
            logger.error(f"PAIR search failed for query '{query}': {e}")
            raise SearchError(f"PAIR search failed: {e}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome driver closed")
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def test_selenium():
    """Test basic Selenium functionality"""
    try:
        with LegalRenderer(headless=True) as renderer:
            # Test with a simple website first
            html = renderer.render_page("https://httpbin.org/html")
            return len(html) > 0
    except Exception as e:
        logger.error(f"Selenium test failed: {e}")
        return False

def test_pair_search():
    """Test PAIR search accessibility"""
    try:
        with LegalRenderer(headless=True) as renderer:
            html = renderer.render_page(LEGAL_SITES["pair_search"])
            # Check if we got blocked or if page loaded
            return "search" in html.lower() and len(html) > 1000
    except WebsiteBlockedError:
        logger.warning("PAIR search is blocked")
        return False
    except Exception as e:
        logger.error(f"PAIR search test failed: {e}")
        return False