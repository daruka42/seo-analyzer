import asyncio
import aiohttp
import time
import logging
import hashlib
from typing import List, Dict, Optional, Set
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse, urlunparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from dataclasses import dataclass
import spacy
from collections import Counter
import re
from core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CrawlConfig:
    max_urls: int = 1000
    max_depth: int = 3
    delay: float = 1.0
    user_agent: str = "SEO-Analyzer-Bot/1.0"
    respect_robots: bool = True
    render_javascript: bool = True
    timeout: int = 30
    exclude_patterns: List[str] = None
    follow_redirects: bool = True

class ContentAnalyzer:
    """Advanced content analysis using NLP"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def analyze_content(self, content: str, url: str) -> Dict:
        """Perform comprehensive content analysis"""
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
        
        text = soup.get_text()
        clean_text = ' '.join(text.split())
        
        analysis = {
            'word_count': len(clean_text.split()),
            'character_count': len(clean_text),
            'paragraph_count': len(soup.find_all('p')),
            'readability_score': self.calculate_readability(clean_text),
            'keyword_density': self.analyze_keyword_density(clean_text),
            'entities': self.extract_entities(clean_text) if self.nlp else [],
            'headings_structure': self.analyze_headings(soup),
            'internal_links': self.count_internal_links(soup, url),
            'external_links': self.count_external_links(soup, url),
            'images': self.analyze_images(soup),
            'content_hash': self.generate_content_hash(clean_text)
        }
        
        return analysis
    
    def calculate_readability(self, text: str) -> float:
        """Calculate Flesch Reading Ease score"""
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        
        if sentences == 0 or words == 0:
            return 0
        
        syllables = sum([self.count_syllables(word) for word in text.split()])
        
        if syllables == 0:
            return 0
        
        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        return round(max(0, min(100, score)), 2)
    
    def count_syllables(self, word: str) -> int:
        """Estimate syllable count"""
        word = word.lower().strip('.,!?;:"')
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not previous_was_vowel:
                    syllable_count += 1
                previous_was_vowel = True
            else:
                previous_was_vowel = False
        
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def analyze_keyword_density(self, text: str) -> Dict:
        """Analyze keyword density"""
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)
        
        if total_words == 0:
            return {}
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'get', 'got', 'make', 'made', 'go', 'went', 'come', 'came', 'see', 'saw', 'know', 'knew', 'take', 'took', 'think', 'thought'}
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        word_freq = Counter(filtered_words)
        
        # Get top 20 keywords
        top_keywords = word_freq.most_common(20)
        return {
            keyword: {
                'count': count,
                'density': round((count / total_words) * 100, 2)
            }
            for keyword, count in top_keywords if count > 1
        }
    
    def extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities using spaCy"""
        if not self.nlp:
            return []
        
        # Limit text length for performance
        doc = self.nlp(text[:100000])
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'description': spacy.explain(ent.label_) or ent.label_
            })
        
        return entities
    
    def analyze_headings(self, soup: BeautifulSoup) -> Dict:
        """Analyze heading structure"""
        headings = {}
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            headings[f'h{i}'] = [tag.get_text().strip() for tag in h_tags]
        
        return headings
    
    def count_internal_links(self, soup: BeautifulSoup, base_url: str) -> int:
        """Count internal links"""
        domain = urlparse(base_url).netloc
        links = soup.find_all('a', href=True)
        internal_count = 0
        
        for link in links:
            href = link['href']
            if href.startswith('/') or domain in href:
                internal_count += 1
        
        return internal_count
    
    def count_external_links(self, soup: BeautifulSoup, base_url: str) -> int:
        """Count external links"""
        domain = urlparse(base_url).netloc
        links = soup.find_all('a', href=True)
        external_count = 0
        
        for link in links:
            href = link['href']
            if href.startswith('http') and domain not in href:
                external_count += 1
        
        return external_count
    
    def analyze_images(self, soup: BeautifulSoup) -> Dict:
        """Analyze images on the page"""
        images = soup.find_all('img')
        total_images = len(images)
        missing_alt = sum(1 for img in images if not img.get('alt'))
        missing_src = sum(1 for img in images if not img.get('src'))
        
        return {
            'total_images': total_images,
            'missing_alt_text': missing_alt,
            'missing_src': missing_src,
            'alt_text_coverage': round(((total_images - missing_alt) / total_images * 100), 2) if total_images > 0 else 100
        }
    
    def generate_content_hash(self, content: str) -> str:
        """Generate hash for duplicate content detection"""
        return hashlib.sha256(content.encode()).hexdigest()

class TechnicalSEOAnalyzer:
    """Comprehensive technical SEO analysis"""
    
    def analyze_page(self, url: str, content: str, headers: Dict, status_code: int) -> List[Dict]:
        """Perform comprehensive technical SEO analysis"""
        issues = []
        soup = BeautifulSoup(content, 'html.parser')
        
        # Title tag analysis
        issues.extend(self.analyze_title(soup))
        
        # Meta description analysis
        issues.extend(self.analyze_meta_description(soup))
        
        # Heading structure
        issues.extend(self.analyze_heading_structure(soup))
        
        # Canonical tag analysis
        issues.extend(self.analyze_canonical(soup, url))
        
        # Robot meta tags
        issues.extend(self.analyze_robots_meta(soup))
        
        # HTTPS analysis
        issues.extend(self.analyze_https(url))
        
        # Schema markup
        issues.extend(self.analyze_schema(soup))
        
        # Performance indicators
        issues.extend(self.analyze_performance_indicators(soup))
        
        # Accessibility
        issues.extend(self.analyze_accessibility(soup))
        
        # Open Graph tags
        issues.extend(self.analyze_open_graph(soup))
        
        return issues
    
    def analyze_title(self, soup: BeautifulSoup) -> List[Dict]:
        """Analyze title tag"""
        issues = []
        title = soup.find('title')
        
        if not title:
            issues.append({
                'type': 'missing_title',
                'severity': 'critical',
                'category': 'technical',
                'description': 'Page is missing a title tag',
                'recommendation': 'Add a descriptive title tag between 30-60 characters',
                'impact_score': 95
            })
        else:
            title_text = title.get_text().strip()
            if len(title_text) == 0:
                issues.append({
                    'type': 'empty_title',
                    'severity': 'critical',
                    'category': 'technical',
                    'description': 'Title tag is empty',
                    'recommendation': 'Add descriptive content to the title tag',
                    'impact_score': 95
                })
            elif len(title_text) < 30:
                issues.append({
                    'type': 'short_title',
                    'severity': 'medium',
                    'category': 'content',
                    'description': f'Title tag is too short ({len(title_text)} characters)',
                    'recommendation': 'Expand title to 30-60 characters for better SEO',
                    'impact_score': 60
                })
            elif len(title_text) > 60:
                issues.append({
                    'type': 'long_title',
                    'severity': 'medium',
                    'category': 'content',
                    'description': f'Title tag is too long ({len(title_text)} characters)',
                    'recommendation': 'Shorten title to under 60 characters to prevent truncation',
                    'impact_score': 50
                })
        
        return issues
    
    def analyze_meta_description(self, soup: BeautifulSoup) -> List[Dict]:
        """Analyze meta description"""
        issues = []
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        
        if not meta_desc:
            issues.append({
                'type': 'missing_meta_description',
                'severity': 'high',
                'category': 'content',
                'description': 'Page is missing a meta description',
                'recommendation': 'Add a compelling meta description between 120-160 characters',
                'impact_score': 80
            })
        else:
            desc_content = meta_desc.get('content', '').strip()
            if len(desc_content) == 0:
                issues.append({
                    'type': 'empty_meta_description',
                    'severity': 'high',
                    'category': 'content',
                    'description': 'Meta description is empty',
                    'recommendation': 'Add descriptive content to the meta description',
                    'impact_score': 80
                })
            elif len(desc_content) < 120:
                issues.append({
                    'type': 'short_meta_description',
                    'severity': 'low',
                    'category': 'content',
                    'description': f'Meta description is short ({len(desc_content)} characters)',
                    'recommendation': 'Expand meta description to 120-160 characters',
                    'impact_score': 30
                })
            elif len(desc_content) > 160:
                issues.append({
                    'type': 'long_meta_description',
                    'severity': 'medium',
                    'category': 'content',
                    'description': f'Meta description is too long ({len(desc_content)} characters)',
                    'recommendation': 'Shorten meta description to under 160 characters',
                    'impact_score': 40
                })
        
        return issues
    
    def analyze_heading_structure(self, soup: BeautifulSoup) -> List[Dict]:
        """Analyze heading structure"""
        issues = []
        h1_tags = soup.find_all('h1')
        
        if len(h1_tags) == 0:
            issues.append({
                'type': 'missing_h1',
                'severity': 'high',
                'category': 'technical',
                'description': 'Page is missing an H1 tag',
                'recommendation': 'Add one H1 tag that describes the main topic of the page',
                'impact_score': 85
            })
        elif len(h1_tags) > 1:
            issues.append({
                'type': 'multiple_h1',
                'severity': 'medium',
                'category': 'technical',
                'description': f'Page has {len(h1_tags)} H1 tags',
                'recommendation': 'Use only one H1 tag per page',
                'impact_score': 50
            })
        
        # Check heading hierarchy
        headings = []
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            for tag in h_tags:
                headings.append((i, tag.get_text().strip()))
        
        # Check for skipped heading levels
        heading_levels = [h[0] for h in headings]
        for i in range(len(heading_levels) - 1):
            if heading_levels[i+1] - heading_levels[i] > 1:
                issues.append({
                    'type': 'skipped_heading_level',
                    'severity': 'low',
                    'category': 'accessibility',
                    'description': f'Heading structure skips from H{heading_levels[i]} to H{heading_levels[i+1]}',
                    'recommendation': 'Use sequential heading levels for better accessibility',
                    'impact_score': 25
                })
                break
        
        return issues
    
    def analyze_canonical(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Analyze canonical tag"""
        issues = []
        canonical = soup.find('link', rel='canonical')
        
        if not canonical:
            issues.append({
                'type': 'missing_canonical',
                'severity': 'medium',
                'category': 'technical',
                'description': 'Page is missing a canonical tag',
                'recommendation': 'Add a canonical tag to prevent duplicate content issues',
                'impact_score': 60
            })
        else:
            canonical_url = canonical.get('href')
            if canonical_url != url and canonical_url != url.rstrip('/'):
                issues.append({
                    'type': 'non_self_canonical',
                    'severity': 'low',
                    'category': 'technical',
                    'description': 'Canonical tag points to a different URL',
                    'recommendation': 'Verify if this canonical reference is intentional',
                    'impact_score': 30
                })
        
        return issues
    
    def analyze_robots_meta(self, soup: BeautifulSoup) -> List[Dict]:
        """Analyze robots meta tag"""
        issues = []
        robots_meta = soup.find('meta', attrs={'name': 'robots'})
        
        if robots_meta:
            content = robots_meta.get('content', '').lower()
            if 'noindex' in content:
                issues.append({
                    'type': 'noindex_found',
                    'severity': 'critical',
                    'category': 'technical',
                    'description': 'Page has noindex directive',
                    'recommendation': 'Remove noindex if you want this page to be indexed',
                    'impact_score': 100
                })
            if 'nofollow' in content:
                issues.append({
                    'type': 'nofollow_found',
                    'severity': 'medium',
                    'category': 'technical',
                    'description': 'Page has nofollow directive',
                    'recommendation': 'Remove nofollow if you want links to be followed',
                    'impact_score': 40
                })
        
        return issues
    
    def analyze_https(self, url: str) -> List[Dict]:
        """Analyze HTTPS usage"""
        issues = []
        if not url.startswith('https://'):
            issues.append({
                'type': 'not_https',
                'severity': 'high',
                'category': 'technical',
                'description': 'Page is not served over HTTPS',
                'recommendation': 'Implement SSL certificate and redirect HTTP to HTTPS',
                'impact_score': 90
            })
        
        return issues
    
    def analyze_schema(self, soup: BeautifulSoup) -> List[Dict]:
        """Analyze schema markup"""
        issues = []
        
        # Check for JSON-LD
        json_ld = soup.find_all('script', type='application/ld+json')
        
        # Check for microdata
        microdata = soup.find_all(attrs={'itemtype': True})
        
        if not json_ld and not microdata:
            issues.append({
                'type': 'missing_schema',
                'severity': 'low',
                'category': 'technical',
                'description': 'Page has no structured data markup',
                'recommendation': 'Add relevant schema markup to help search engines understand your content',
                'impact_score': 35
            })
        
        return issues
    
    def analyze_performance_indicators(self, soup: BeautifulSoup) -> List[Dict]:
        """Analyze performance indicators"""
        issues = []
        
        # Check for large images without optimization
        images = soup.find_all('img')
        unoptimized_images = 0
        
        for img in images:
            # Check if image has width/height attributes or responsive attributes
            if not img.get('width') and not img.get('height') and 'srcset' not in img.attrs:
                unoptimized_images += 1
        
        if unoptimized_images > 0:
            issues.append({
                'type': 'unoptimized_images',
                'severity': 'medium',
                'category': 'performance',
                'description': f'{unoptimized_images} images may not be optimized',
                'recommendation': 'Add width/height attributes and consider responsive images',
                'impact_score': 45
            })
        
        # Check for excessive DOM size
        all_elements = soup.find_all()
        if len(all_elements) > 1500:
            issues.append({
                'type': 'large_dom',
                'severity': 'medium',
                'category': 'performance',
                'description': f'Large DOM size ({len(all_elements)} elements)',
                'recommendation': 'Reduce DOM complexity for better performance',
                'impact_score': 40
            })
        
        return issues
    
    def analyze_accessibility(self, soup: BeautifulSoup) -> List[Dict]:
        """Analyze accessibility issues"""
        issues = []
        
        # Check for images without alt text
        images = soup.find_all('img')
        missing_alt = sum(1 for img in images if not img.get('alt'))
        
        if missing_alt > 0:
            issues.append({
                'type': 'missing_alt_text',
                'severity': 'medium',
                'category': 'accessibility',
                'description': f'{missing_alt} images are missing alt text',
                'recommendation': 'Add descriptive alt text to all images',
                'impact_score': 50
            })
        
        # Check for form inputs without labels
        inputs = soup.find_all('input', type=['text', 'email', 'password', 'tel', 'search'])
        inputs_without_labels = 0
        
        for input_tag in inputs:
            input_id = input_tag.get('id')
            if not input_id or not soup.find('label', attrs={'for': input_id}):
                inputs_without_labels += 1
        
        if inputs_without_labels > 0:
            issues.append({
                'type': 'inputs_without_labels',
                'severity': 'medium',
                'category': 'accessibility',
                'description': f'{inputs_without_labels} form inputs lack proper labels',
                'recommendation': 'Associate all form inputs with descriptive labels',
                'impact_score': 45
            })
        
        return issues
    
    def analyze_open_graph(self, soup: BeautifulSoup) -> List[Dict]:
        """Analyze Open Graph tags"""
        issues = []
        
        og_title = soup.find('meta', property='og:title')
        og_description = soup.find('meta', property='og:description')
        og_image = soup.find('meta', property='og:image')
        
        if not og_title:
            issues.append({
                'type': 'missing_og_title',
                'severity': 'low',
                'category': 'social',
                'description': 'Missing Open Graph title',
                'recommendation': 'Add og:title meta tag for better social media sharing',
                'impact_score': 20
            })
        
        if not og_description:
            issues.append({
                'type': 'missing_og_description',
                'severity': 'low',
                'category': 'social',
                'description': 'Missing Open Graph description',
                'recommendation': 'Add og:description meta tag for better social media sharing',
                'impact_score': 20
            })
        
        if not og_image:
            issues.append({
                'type': 'missing_og_image',
                'severity': 'low',
                'category': 'social',
                'description': 'Missing Open Graph image',
                'recommendation': 'Add og:image meta tag for better social media sharing',
                'impact_score': 15
            })
        
        return issues

class AsyncWebCrawler:
    """Enhanced asynchronous web crawler with comprehensive SEO analysis"""
    
    def __init__(self, config: CrawlConfig):
        self.config = config
        self.visited_urls: Set[str] = set()
        self.robots_cache = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(settings.CRAWLER_MAX_WORKERS)
        self.content_analyzer = ContentAnalyzer()
        self.technical_analyzer = TechnicalSEOAnalyzer()
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': None
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={'User-Agent': self.config.user_agent},
            connector=connector
        )
        self.stats['start_time'] = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        if not self.config.respect_robots:
            return True
        
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if domain not in self.robots_cache:
            try:
                rp = RobotFileParser()
                rp.set_url(f"{domain}/robots.txt")
                rp.read()
                self.robots_cache[domain] = rp
            except Exception as e:
                logger.warning(f"Could not read robots.txt for {domain}: {e}")
                return True
        
        return self.robots_cache[domain].can_fetch(self.config.user_agent, url)
    
    async def render_with_javascript(self, url: str) -> Optional[str]:
        """Render page with JavaScript using Playwright"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_user_agent(self.config.user_agent)
                await page.goto(url, wait_until='networkidle', timeout=30000)
                content = await page.content()
                await browser.close()
                return content
        except Exception as e:
            logger.error(f"JavaScript rendering failed for {url}: {e}")
            return None
    
    def extract_links(self, content: str, base_url: str) -> List[str]:
        """Extract links from page content"""
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip unwanted links
            if any(pattern in href for pattern in ['mailto:', 'tel:', 'javascript:', '#']):
                continue
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                full_url = urljoin(base_url, href)
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(base_url, href)
            
            # Only include same domain links
            if urlparse(full_url).netloc == base_domain:
                # Clean URL
                clean_url = full_url.split('#')[0]  # Remove fragments
                if clean_url not in links:
                    links.append(clean_url)
        
        return links
    
    def should_exclude_url(self, url: str) -> bool:
        """Check if URL should be excluded based on patterns"""
        if not self.config.exclude_patterns:
            return False
        
        for pattern in self.config.exclude_patterns:
            if pattern in url:
                return True
        
        return False
    
    async def analyze_page(self, url: str, content: str, status_code: int,
                          headers: dict, load_time: float, depth: int) -> dict:
        """Perform comprehensive page analysis"""
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract basic SEO elements
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_desc.get('content', '') if meta_desc else ""
        
        h1_elements = soup.find_all('h1')
        h1_text = h1_elements[0].get_text().strip() if h1_elements else ""
        
        # Perform content analysis
        content_analysis = self.content_analyzer.analyze_content(content, url)
        
        # Perform technical SEO analysis
        technical_issues = self.technical_analyzer.analyze_page(url, content, headers, status_code)
        
        # Extract links for further crawling
        links = self.extract_links(content, url)
        
        return {
            'url': url,
            'status_code': status_code,
            'title': title_text,
            'meta_description': meta_desc_text,
            'h1': h1_text,
            'word_count': content_analysis['word_count'],
            'load_time': load_time,
            'depth': depth,
            'content_hash': content_analysis['content_hash'],
            'technical_issues': technical_issues,
            'content_analysis': content_analysis,
            'headers': headers,
            'links': links
        }
    
    async def fetch_page(self, url: str, depth: int) -> Optional[dict]:
        """Fetch and analyze a single page"""
        async with self.semaphore:
            if (url in self.visited_urls or 
                not self.can_fetch(url) or 
                self.should_exclude_url(url)):
                return None
            
            self.visited_urls.add(url)
            self.stats['total_processed'] += 1
            
            try:
                start_time = time.time()
                
                # Fetch with aiohttp
                async with self.session.get(url, allow_redirects=self.config.follow_redirects) as response:
                    basic_html = await response.text()
                    status_code = response.status
                    headers = dict(response.headers)
                
                # Render with JavaScript if needed
                if self.config.render_javascript:
                    rendered_html = await self.render_with_javascript(url)
                    content = rendered_html or basic_html
                else:
                    content = basic_html
                
                load_time = time.time() - start_time
                
                # Analyze the page
                page_data = await self.analyze_page(url, content, status_code, headers, load_time, depth)
                
                # Respect crawl delay
                await asyncio.sleep(self.config.delay)
                
                self.stats['successful'] += 1
                logger.info(f"Successfully crawled: {url} (depth: {depth})")
                
                return page_data
                
            except Exception as e:
                self.stats['failed'] += 1
                logger.error(f"Failed to fetch {url}: {e}")
                return None
    
    async def crawl_website(self, start_url: str, callback=None) -> List[dict]:
        """Main crawling method with progress callback"""
        urls_to_crawl = [(start_url, 0)]  # (url, depth)
        crawled_pages = []
        
        while urls_to_crawl and len(crawled_pages) < self.config.max_urls:
            # Process URLs in batches
            batch_size = min(self.config.max_urls // 10, len(urls_to_crawl))
            current_batch = urls_to_crawl[:batch_size]
            urls_to_crawl = urls_to_crawl[batch_size:]
            
            # Create tasks for concurrent processing
            tasks = []
            for url, depth in current_batch:
                if depth <= self.config.max_depth:
                    task = asyncio.create_task(self.fetch_page(url, depth))
                    tasks.append(task)
            
            # Wait for all tasks in batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, dict):
                    crawled_pages.append(result)
                    
                    # Add new URLs to crawl queue
                    if result['depth'] < self.config.max_depth:
                        for link in result.get('links', []):
                            if link not in self.visited_urls:
                                urls_to_crawl.append((link, result['depth'] + 1))
                    
                    # Call progress callback if provided
                    if callback:
                        await callback(len(crawled_pages), self.stats)
            
            logger.info(f"Crawled {len(crawled_pages)} pages so far...")
        
        # Final stats
        total_time = time.time() - self.stats['start_time']
        logger.info(f"Crawl completed: {len(crawled_pages)} pages in {total_time:.2f} seconds")
        
        return crawled_pages
