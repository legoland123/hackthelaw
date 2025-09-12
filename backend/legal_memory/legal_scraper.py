"""
Enhanced Legal Scraper - Extract structured data from legal websites
"""

import logging
import time
from typing import Dict, List
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .legal_renderer import LegalRenderer
from .exceptions import LegalMemoryError

logger = logging.getLogger(__name__)

class EnhancedLegalScraper:
    """Enhanced scraper that extracts structured legal data"""
    
    def __init__(self):
        self.renderer = None
    
    def search_hansard_with_extraction(self, keywords_list: List[str]) -> Dict:
        """
        Search Hansard and extract structured results
        
        Args:
            keywords_list: List of keywords to search
            
        Returns:
            Dict with extracted Hansard results
        """
        results = {}
        
        try:
            with LegalRenderer(headless=False) as renderer:
                self.renderer = renderer
                
                for keyword in keywords_list:
                    logger.info(f"Searching Hansard for: {keyword}")
                    
                    try:
                        # Perform PAIR search
                        html_content = self._search_pair_enhanced(keyword)
                        
                        # Extract structured data
                        extracted_data = self._extract_hansard_results(html_content, keyword)
                        
                        results[keyword] = {
                            'status': 'success',
                            'total_results': extracted_data['total_results'],
                            'results': extracted_data['results'],
                            'search_time': extracted_data['search_time'],
                            'raw_html_length': len(html_content)
                        }
                        
                        logger.info(f"Extracted {len(extracted_data['results'])} results for '{keyword}'")
                        
                    except Exception as e:
                        results[keyword] = {
                            'status': 'error',
                            'error': str(e)
                        }
                        logger.error(f"Search failed for '{keyword}': {e}")
        
        except Exception as e:
            logger.error(f"Hansard search failed: {e}")
            raise LegalMemoryError(f"Hansard search failed: {e}")
        
        return results
    
    def search_lawnet_with_extraction(self, keywords_list: List[str]) -> Dict:
        """
        Search LawNet and extract structured results
        
        Args:
            keywords_list: List of keywords to search
            
        Returns:
            Dict with extracted LawNet results
        """
        results = {}
        
        try:
            with LegalRenderer(headless=False) as renderer:
                self.renderer = renderer
                
                for keyword in keywords_list:
                    logger.info(f"Searching LawNet for: {keyword}")
                    
                    try:
                        # Perform LawNet search
                        html_content = self._search_lawnet_enhanced(keyword)
                        
                        # Extract structured data
                        extracted_data = self._extract_lawnet_results(html_content, keyword)
                        
                        results[keyword] = {
                            'status': 'success',
                            'total_results': extracted_data['total_results'],
                            'results': extracted_data['results'],
                            'search_time': extracted_data['search_time'],
                            'raw_html_length': len(html_content)
                        }
                        
                        logger.info(f"Extracted {len(extracted_data['results'])} results for '{keyword}'")
                        
                    except Exception as e:
                        results[keyword] = {
                            'status': 'error',
                            'error': str(e)
                        }
                        logger.error(f"Search failed for '{keyword}': {e}")
        
        except Exception as e:
            logger.error(f"LawNet search failed: {e}")
            raise LegalMemoryError(f"LawNet search failed: {e}")
        
        return results
    
    def _search_pair_enhanced(self, query: str) -> str:
        """Enhanced PAIR search with better error handling"""
        try:
            # Load PAIR search page
            self.renderer.render_page("https://search.pair.gov.sg/")
            
            # Wait for search elements
            wait = WebDriverWait(self.renderer.driver, 15)
            search_input = wait.until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            # Ensure Hansard is selected
            try:
                hansard_radio = self.renderer.driver.find_element(By.CSS_SELECTOR, 'input[value="hansard"]')
                if not hansard_radio.is_selected():
                    hansard_radio.click()
                    time.sleep(1)
            except Exception as e:
                logger.warning(f"Could not verify Hansard selection: {e}")
            
            # Enter search query
            search_input.clear()
            search_input.send_keys(query)
            
            # Click search button
            search_button = self.renderer.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Search"]')
            search_button.click()
            
            # Wait for results to load
            time.sleep(5)
            
            return self.renderer.driver.page_source
            
        except Exception as e:
            logger.error(f"PAIR search failed for '{query}': {e}")
            raise
    
    def _search_lawnet_enhanced(self, query: str) -> str:
        """Enhanced LawNet search with better error handling"""
        try:
            # Load LawNet Supreme Court page
            url = "https://www.lawnet.sg/lawnet/web/lawnet/free-resources?_freeresources_WAR_lawnet3baseportlet_action=supreme"
            self.renderer.render_page(url)
            
            # Try to use search function
            try:
                wait = WebDriverWait(self.renderer.driver, 10)
                search_input = wait.until(
                    EC.presence_of_element_located((By.ID, "_freeresources_WAR_lawnet3baseportlet_filterResult"))
                )
                
                search_input.clear()
                search_input.send_keys(query)
                search_input.send_keys("\n")  # Press Enter
                
                # Wait for results
                time.sleep(3)
                
            except Exception as search_error:
                logger.warning(f"LawNet search function failed: {search_error}")
            
            return self.renderer.driver.page_source
            
        except Exception as e:
            logger.error(f"LawNet search failed for '{query}': {e}")
            raise
    
    def _extract_hansard_results(self, html_content: str, query: str) -> Dict:
        """Extract structured data from PAIR search results"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        extracted_results = []
        search_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Look for result count
        total_results = 0
        result_count_element = soup.find('p', class_='chakra-text css-r4wv3p')
        if result_count_element:
            count_text = result_count_element.get_text()
            # Extract number from text like "About 1917 results (0.80 seconds)"
            import re
            match = re.search(r'About (\d+) results', count_text)
            if match:
                total_results = int(match.group(1))
        
        # Extract individual results
        result_links = soup.find_all('a', class_='chakra-link css-1y3y14i')
        
        for link in result_links:
            try:
                # Extract title
                title_element = link.find('p', class_='chakra-text css-3n3bc9')
                title = title_element.get_text(strip=True) if title_element else "No title"
                
                # Extract URL
                url = link.get('href', '')
                
                # Extract metadata (date, parliament info)
                metadata_element = link.find_next('p', class_='chakra-text css-js6d32')
                metadata = metadata_element.get_text(strip=True) if metadata_element else ""
                
                # Extract snippet/preview
                snippet_element = link.find_next('p', class_='chakra-text css-1ce87mw')
                snippet = snippet_element.get_text(strip=True) if snippet_element else ""
                
                extracted_results.append({
                    'title': title,
                    'url': url,
                    'metadata': metadata,
                    'snippet': snippet,
                    'source': 'Hansard'
                })
                
            except Exception as e:
                logger.warning(f"Error extracting result: {e}")
                continue
        
        return {
            'total_results': total_results,
            'results': extracted_results,
            'search_time': search_time,
            'query': query
        }
    
    def _extract_lawnet_results(self, html_content: str, query: str) -> Dict:
        """Extract structured data from LawNet search results"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        extracted_results = []
        search_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_results = 0
        
        # Look for judgment entries in LawNet
        # LawNet has different structure - look for judgment links
        judgment_links = soup.find_all('a', href=True)
        
        for link in judgment_links:
            try:
                href = link.get('href', '')
                
                # Filter for actual judgment links (contain judgment IDs or case references)
                if any(indicator in href.lower() for indicator in ['judgment', 'case', '.pdf']):
                    title = link.get_text(strip=True)
                    
                    if title and len(title) > 10:  # Filter out very short/empty titles
                        # Extract additional context from surrounding elements
                        parent = link.find_parent(['tr', 'div', 'li'])
                        context = ""
                        if parent:
                            context = parent.get_text(strip=True)[:200] + "..."
                        
                        extracted_results.append({
                            'title': title,
                            'url': href if href.startswith('http') else f"https://www.lawnet.sg{href}",
                            'metadata': "Supreme Court Judgment",
                            'snippet': context,
                            'source': 'LawNet'
                        })
                        
            except Exception as e:
                logger.warning(f"Error extracting LawNet result: {e}")
                continue
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_results = []
        for result in extracted_results:
            if result['title'] not in seen_titles:
                seen_titles.add(result['title'])
                unique_results.append(result)
        
        total_results = len(unique_results)
        
        return {
            'total_results': total_results,
            'results': unique_results[:20],  # Limit to top 20 results
            'search_time': search_time,
            'query': query
        }
    
    def close(self):
        """Clean up resources"""
        if self.renderer:
            self.renderer.close()
            self.renderer = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()