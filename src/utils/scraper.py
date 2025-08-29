from firecrawl import FirecrawlApp
from typing import List, Dict, Any, Optional, Callable
import logging
import asyncio
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime

from ..core.config import settings

logger = logging.getLogger(__name__)

class FirecrawlScraper:
    def __init__(self):
        self.app = FirecrawlApp(api_key=settings.firecrawl_api_key)
        
    def scrape_single_url(self, url: str, formats: List[str] = None) -> Optional[Dict[str, Any]]:
        try:
            if not formats:
                formats = ["markdown", "html"]
                
            # Updated based on Firecrawl documentation
            document = self.app.scrape(
                url,
                formats=formats,
                wait_for=2000,
                timeout=30000
            )
            
            if not document:
                logger.error(f"Failed to scrape {url}: No data returned")
                return None
            
            # Assuming document is a Document object with direct properties
            markdown_content = getattr(document, 'markdown', '')
            html_content = getattr(document, 'html', '')
            metadata = getattr(document, 'metadata', {})
            
            parsed_url = urlparse(url)
            
            content = markdown_content or html_content or ''
            
            return {
                'content': content,
                'title': metadata.get('title', parsed_url.netloc),
                'url': url,
                'file_name': f"{parsed_url.netloc}_{int(time.time())}.md",
                'file_type': '.md',
                'mime_type': 'text/markdown',
                'file_size': len(content.encode('utf-8')),
                'metadata': {
                    'source': 'web_scraping',
                    'scraper': 'firecrawl',
                    'scraped_at': datetime.utcnow().isoformat(),
                    'original_url': url,
                    **metadata
                }
            }
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            return None
    
    async def crawl_website(
        self, 
        url: str, 
        max_pages: int = 10,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> List[Dict[str, Any]]:
        """Crawl a website and return structured data for each page"""
        try:
            if progress_callback:
                progress_callback(f"Starting crawl of {url}", 0.1)
            
            try:
                if progress_callback:
                    progress_callback(f"Crawling website {url}...", 0.3)
                
                # The crawl method now directly returns the crawled data
                crawl_data = self.app.crawl(
                    url,
                    limit=max_pages,
                    scrape_options={"formats": ["markdown"]},
                    poll_interval=2
                )
                
                if progress_callback:
                    progress_callback(f"Processing crawled data...", 0.7)
                
                if not crawl_data:
                    logger.error(f"No data returned for crawl of {url}")
                    return []
                
                # Process the data into our standardized format
                results = self._process_crawl_data(crawl_data, url)
                
                if progress_callback:
                    progress_callback(f"Crawl completed with {len(results)} pages", 1.0)
                    
                return results
                
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error crawling website {url}: {e}")
            return []
            
            for i, page_data in enumerate(data):
                try:
                    page_url = page_data.get('metadata', {}).get('sourceURL', '')
                    if not page_url:
                        continue
                    
                    content = page_data.get('markdown', '')
                    if not content.strip():
                        continue
                    
                    parsed_page_url = urlparse(page_url)
                    
                    result = {
                        'content': content,
                        'title': page_data.get('metadata', {}).get('title', parsed_page_url.path),
                        'url': page_url,
                        'file_name': f"{base_domain}_{i+1}_{int(time.time())}.md",
                        'file_type': '.md',
                        'mime_type': 'text/markdown',
                        'file_size': len(content.encode('utf-8')),
                        'metadata': {
                            'source': 'web_crawling',
                            'scraper': 'firecrawl',
                            'crawled_at': datetime.utcnow().isoformat(),
                            'original_url': page_url,
                            'base_url': url,
                            'page_index': i + 1,
                            **page_data.get('metadata', {})
                        }
                    }
                    
                    results.append(result)
                    pages_processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing page {i}: {e}")
                    continue
            
            if progress_callback:
                progress_callback(f"Crawl completed. Processed {pages_processed} pages", 1.0)
            
            logger.info(f"Successfully crawled {len(results)} pages from {url}")
            return results
    
    async def batch_scrape_urls(
        self, 
        urls: List[str],
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> List[Dict[str, Any]]:
        results = []
        total_urls = len(urls)
        
        for i, url in enumerate(urls):
            try:
                if progress_callback:
                    progress = (i / total_urls) * 0.9
                    progress_callback(f"Scraping {url}", progress)
                
                result = self.scrape_single_url(url)
                if result:
                    results.append(result)
                    
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in batch scraping URL {url}: {e}")
                continue
        
        if progress_callback:
            progress_callback(f"Batch scraping completed. {len(results)} URLs processed", 1.0)
        
        return results
    
    def validate_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False
    
    def extract_clean_markdown(self, html_content: str) -> str:
        try:
            document = self.app.scrape(
                "data:text/html;base64," + html_content,
                formats=['markdown']
            )
            
            # Get markdown property from the document object
            return getattr(document, 'markdown', '') or ""
            
        except Exception as e:
            logger.error(f"Error extracting markdown: {e}")
            return ""
            
    def _process_crawl_data(self, crawl_data, source_url: str) -> List[Dict[str, Any]]:
        """Helper method to process crawl data into standardized format"""
        results = []
        total_pages = len(crawl_data) if isinstance(crawl_data, list) else 0
        
        # Handle the case where crawl_data might be a list of documents
        if isinstance(crawl_data, list):
            for i, page in enumerate(crawl_data):
                try:
                    # Extract relevant data based on the structure
                    page_url = page.get('url') or page.get('metadata', {}).get('sourceURL', '')
                    page_markdown = page.get('markdown', '')
                    page_title = page.get('title') or page.get('metadata', {}).get('title', '')
                    
                    if not page_url or not page_markdown:
                        continue
                        
                    parsed_url = urlparse(page_url)
                    
                    result = {
                        'content': page_markdown,
                        'title': page_title or parsed_url.netloc,
                        'url': page_url,
                        'file_name': f"{parsed_url.netloc}_{int(time.time())}.md",
                        'file_type': '.md',
                        'mime_type': 'text/markdown',
                        'file_size': len(page_markdown.encode('utf-8')),
                        'metadata': {
                            'source': 'web_crawling',
                            'scraper': 'firecrawl',
                            'crawled_at': datetime.utcnow().isoformat(),
                            'original_url': page_url,
                            'page_index': i,
                            'total_pages': total_pages,
                            'parent_url': source_url
                        }
                    }
                    
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing page {i}: {e}")
                    continue
        
        logger.info(f"Successfully processed {len(results)} pages from {source_url}")
        return results

def get_scraper() -> FirecrawlScraper:
    return FirecrawlScraper()