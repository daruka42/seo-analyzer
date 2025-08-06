import asyncio
import aiohttp
import time
import logging
import hashlib
from typing import List, Dict, Optional, Set, Callable, Any
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse, urlunparse
from playwright.async_api import async_playwright, Browser, BrowserContext
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
import spacy
from collections import Counter
import re
import json
import os
from pathlib import Path
from core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CrawlConfig:
    """Comprehensive crawl configuration"""
    max_urls: int = 1000
    max_depth: int = 3
    delay: float = 1.0
    timeout: int = 30
    max_concurrent: int = 10
    user_agent: str = "SEO-Analyzer-Bot/1.0"
    respect_robots: bool = True
    render_javascript: bool = True
    follow_redirects: bool = True
    screenshot_enabled: bool = False
    mobile_analysis: bool = True
    analyze_images: bool = True
    analyze_links: bool = True
    analyze_performance: bool = True
    analyze_accessibility: bool = True
    analyze_security: bool = False
    exclude_patterns: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=list)
    custom_headers: Dict[str, str] = field(default_factory=dict)

class ContentAnalyzer:
    """Advanced content analysis using NLP"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def analyze_content(self, content: str, url: str) -> Dict[str, Any]:
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
            'internal_links_count': self.count_internal_links(soup, url),
            'external_links_count': self.count_external_links(soup, url),
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
    
    def analyze_keyword_density(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Analyze keyword density"""
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)
        
        if total_words == 0:
            return {}
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
            'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 
            'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 
            'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 
            'will', 'just', 'should', 'now', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
            'have', 'has', 'had', 'do', 'does', 'did', 'get', 'got', 'make', 'made', 'go', 'went', 
            'come', 'came', 'see', 'saw', 'know', 'knew', 'take', 'took', 'think', 'thought'
        }
        
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
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
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
    
    def analyze_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
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
    
    def analyze_images(self, soup: BeautifulSoup) -> Dict[str, Any]:
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
    
    def analyze_page(self, url: str, content: str, headers: Dict[str, str], status_code: int) -> List[Dict[str, Any]]:
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
    
    def analyze_title(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
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
                'impact_score': 95,
                'element_selector': 'title',
                'current_value': None,
                'suggested_value': 'Add a descriptive title tag'
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
                    'impact_score': 95,
                    'element_selector': 'title',
                    'current_value': '',
                    'suggested_value': 'Add descriptive title content'
                })
            elif len(title_text) < 30:
                issues.append({
                    'type': 'short_title',
                    'severity': 'medium',
                    'category': 'content',
                    'description': f'Title tag is too short ({len(title_text)} characters)',
                    'recommendation': 'Expand title to 30-60 characters for better SEO',
                    'impact_score': 60,
                    'element_selector': 'title',
                    'current_value': title_text,
                    'suggested_value': 'Expand to 30-60 characters'
                })
            elif len(title_text) > 60:
                issues.append({
                    'type': 'long_title',
                    'severity': 'medium',
                    'category': 'content',
                    'description': f'Title tag is too long ({len(title_text)} characters)',
                    'recommendation': 'Shorten title to under 60 characters to prevent truncation',
                    'impact_score': 50,
                    'element_selector': 'title',
                    'current_value': title_text,
                    'suggested_value': 'Shorten to under 60 characters'
                })
        
        return issues
    
    def analyze_meta_description(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
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
                'impact_score': 80,
                'element_selector': 'meta[name="description"]',
                'current_value': None,
                'suggested_value': 'Add meta description tag'
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
                    'impact_score': 80,
                    'element_selector': 'meta[name="description"]',
                    'current_value': '',
                    'suggested_value': 'Add descriptive content'
                })
            elif len(desc_content) < 120:
                issues.append({
                    'type': 'short_meta_description',
                    'severity': 'low',
                    'category': 'content',
                    'description': f'Meta description is short ({len(desc_content)} characters)',
                    'recommendation': 'Expand meta description to 120-160 characters',
                    'impact_score': 30,
                    'element_selector': 'meta[name="description"]',
                    'current_value': desc_content,
                    'suggested_value': 'Expand to 120-160 characters'
                })
            elif len(desc_content) > 160:
                issues.append({
                    'type': 'long_meta_description',
                    'severity': 'medium',
                    'category': 'content',
                    'description': f'Meta description is too long ({len(desc_content)} characters)',
                    'recommendation': 'Shorten meta description to under 160 characters',
                    'impact_score': 40,
                    'element_selector': 'meta[name="description"]',
                    'current_value': desc_content,
                    'suggested_value': 'Shorten to under 160 characters'
                })
        
        return issues
    
    def analyze_heading_structure(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
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
                'impact_score': 85,
                'element_selector': 'h1',
                'current_value': None,
                'suggested_value': 'Add H1 tag'
            })
        elif len(h1_tags) > 1:
            issues.append({
                'type': 'multiple_h1',
                'severity': 'medium',
                'category': 'technical',
                'description': f'Page has {len(h1_tags)} H1 tags',
                'recommendation': 'Use only one H1 tag per page',
                'impact_score': 50,
                'element_selector': 'h1',
                'current_value': f'{len(h1_tags)} H1 tags found',
                'suggested_value': 'Use only one H1 tag'
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
                    'impact_score': 25,
                    'element_selector': f'h{heading_levels[i+1]}',
                    'current_value': f'H{heading_levels[i]} to H{heading_levels[i+1]}',
                    'suggested_value': 'Use sequential heading levels'
                })
                break
        
        return issues
    
    def analyze_canonical(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
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
                'impact_score': 60,
                'element_selector': 'link[rel="canonical"]',
                'current_value': None,
                'suggested_value': f'<link rel="canonical" href="{url}">'
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
                    'impact_score': 30,
                    'element_selector': 'link[rel="canonical"]',
                    'current_value': canonical_url,
                    'suggested_value': 'Verify canonical URL is correct'
                })
        
        return issues
    
    def analyze_robots_meta(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
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
                    'impact_score': 100,
                    'element_selector': 'meta[name="robots"]',
                    'current_value': content,
                    'suggested_value': 'Remove noindex directive'
                })
            if 'nofollow' in content:
                issues.append({
                    'type': 'nofollow_found',
                    'severity': 'medium',
                    'category': 'technical',
                    'description': 'Page has nofollow directive',
                    'recommendation': 'Remove nofollow if you want links to be followed',
                    'impact_score': 40,
                    'element_selector': 'meta[name="robots"]',
                    'current_value': content,
                    'suggested_value': 'Remove nofollow directive'
                })
        
        return issues
    
    def analyze_https(self, url: str) -> List[Dict[str, Any]]:
        """Analyze HTTPS usage"""
        issues = []
        if not url.startswith('https://'):
            issues.append({
                'type': 'not_https',
                'severity': 'high',
                'category': 'security',
                'description': 'Page is not served over HTTPS',
                'recommendation': 'Implement SSL certificate and redirect HTTP to HTTPS',
                'impact_score': 90,
                'element_selector': None,
                'current_value': 'HTTP',
                'suggested_value': 'HTTPS'
            })
        
        return issues
    
    def analyze_schema(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
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
                'impact_score': 35,
                'element_selector': None,
                'current_value': 'No schema markup',
                'suggested_value': 'Add JSON-LD or microdata'
            })
        
        return issues
    
    def analyze_performance_indicators(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
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
                'impact_score': 45,
                'element_selector': 'img',
                'current_value': f'{unoptimized_images} unoptimized images',
                'suggested_value': 'Add width/height and srcset attributes'
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
                'impact_score': 40,
                'element_selector': None,
                'current_value': f'{len(all_elements)} DOM elements',
                'suggested_value': 'Reduce to under 1500 elements'
            })
        
        return issues
    
    def analyze_accessibility(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
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
                'impact_score': 50,
                'element_selector': 'img',
                'current_value': f'{missing_alt} images without alt text',
                'suggested_value': 'Add alt attributes to all images'
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
                'impact_score': 45,
                'element_selector': 'input',
                'current_value': f'{inputs_without_labels} inputs without labels',
                'suggested_value': 'Add label elements for all inputs'
            })
        
        return issues
    
    def analyze_open_graph(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
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
                'impact_score': 20,
                'element_selector': 'meta[property="og:title"]',
                'current_value': None,
                'suggested_value': 'Add og:title meta tag'
            })
        
        if not og_description:
            issues.append({
                'type': 'missing_og_description',
                'severity': 'low',
                'category': 'social',
                'description': 'Missing Open Graph description',
                'recommendation': 'Add og:description meta tag for better social media sharing',
                'impact_score': 20,
                'element_selector': 'meta[property="og:description"]',
                'current_value': None,
                'suggested_value': 'Add og:description meta tag'
            })
        
        if not og_image:
            issues.append({
                'type': 'missing_og_image',
                'severity': 'low',
                'category': 'social',
                'description': 'Missing Open Graph image',
                'recommendation': 'Add og:image meta tag for better social media sharing',
                'impact_score': 15,
                'element_selector': 'meta[property="og:image"]',
                'current_value': None,
                'suggested_value': 'Add og:image meta tag'
            })
        
        return issues

class AsyncWebCrawler:
    """Production-ready asynchronous web crawler with comprehensive SEO analysis"""
    
    def __init__(self, config: CrawlConfig):
        self.config = config
        self.visited_urls: Set[str] = set()
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.browser: Optional[Browser] = None
        self.browser_context: Optional[BrowserContext] = None
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self.content_analyzer = ContentAnalyzer()
        self.technical_analyzer = TechnicalSEOAnalyzer()
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': None,
            'errors': []
        }
    
    async def __aenter__(self):
        """Enhanced async context manager entry"""
        # Setup HTTP session
        connector = aiohttp.TCPConnector(
            limit=100, 
            limit_per_host=self.config.max_concurrent,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        headers = {
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        headers.update(self.config.custom_headers)
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=headers,
            connector=connector
        )
        
        # Setup Playwright browser if JavaScript rendering is enabled
        if self.config.render_javascript:
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--disable-gpu',
                        '--window-size=1920x1080'
                    ]
                )
                self.browser_context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=self.config.user_agent
                )
                logger.info("Playwright browser initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Playwright: {e}")
                self.config.render_javascript = False
        
        self.stats['start_time'] = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Enhanced async context manager exit"""
        if self.session:
            await self.session.close()
        
        if self.browser_context:
            await self.browser_context.close()
        
        if self.browser:
            await self.browser.close()
        
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
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
    
    def should_exclude_url(self, url: str) -> bool:
        """Check if URL should be excluded based on patterns"""
        # Check exclude patterns
        if self.config.exclude_patterns:
            for pattern in self.config.exclude_patterns:
                if pattern in url:
                    return True
        
        # Check include patterns (if specified, URL must match at least one)
        if self.config.include_patterns:
            for pattern in self.config.include_patterns:
                if pattern in url:
                    return False
            return True  # URL doesn't match any include pattern
        
        return False
    
    async def render_with_javascript(self, url: str) -> Optional[Dict[str, Any]]:
        """Enhanced JavaScript rendering with mobile analysis"""
        if not self.browser_context:
            return None
        
        try:
            page = await self.browser_context.new_page()
            
            # Set up page monitoring
            performance_metrics = {}
            
            # Navigate to page
            response = await page.goto(
                url, 
                wait_until='networkidle', 
                timeout=30000
            )
            
            # Wait for additional JavaScript execution
            await page.wait_for_timeout(2000)
            
            # Get rendered content
            content = await page.content()
            
            # Get performance metrics
            try:
                metrics = await page.evaluate("""
                    () => {
                        const navigation = performance.getEntriesByType('navigation')[0];
                        const paint = performance.getEntriesByType('paint');
                        return {
                            loadTime: navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0,
                            domContentLoaded: navigation ? navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart : 0,
                            firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
                            firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                            domElements: document.querySelectorAll('*').length,
                            images: document.querySelectorAll('img').length,
                            scripts: document.querySelectorAll('script').length,
                            stylesheets: document.querySelectorAll('link[rel="stylesheet"]').length
                        };
                    }
                """)
                performance_metrics.update(metrics)
            except Exception as e:
                logger.warning(f"Could not get performance metrics for {url}: {e}")
            
            # Mobile analysis if enabled
            mobile_content = None
            mobile_metrics = {}
            if self.config.mobile_analysis:
                try:
                    await page.set_viewport_size({'width': 375, 'height': 667})
                    await page.wait_for_timeout(1000)
                    mobile_content = await page.content()
                    
                    # Mobile-specific metrics
                    mobile_metrics = await page.evaluate("""
                        () => {
                            const viewport = document.querySelector('meta[name="viewport"]');
                            return {
                                hasViewportMeta: !!viewport,
                                viewportContent: viewport ? viewport.content : null,
                                isMobileFriendly: window.innerWidth <= 768,
                                touchElements: document.querySelectorAll('button, a, input[type="button"], input[type="submit"]').length
                            };
                        }
                    """)
                except Exception as e:
                    logger.warning(f"Mobile analysis failed for {url}: {e}")
            
            # Take screenshot if enabled
            screenshot_path = None
            if self.config.screenshot_enabled:
                try:
                    # Ensure screenshots directory exists
                    screenshots_dir = Path("screenshots")
                    screenshots_dir.mkdir(exist_ok=True)
                    
                    screenshot_path = screenshots_dir / f"{hashlib.md5(url.encode()).hexdigest()}.png"
                    await page.screenshot(path=str(screenshot_path), full_page=True)
                    screenshot_path = str(screenshot_path)
                except Exception as e:
                    logger.warning(f"Screenshot failed for {url}: {e}")
            
            await page.close()
            
            return {
                'content': content,
                'mobile_content': mobile_content,
                'performance_metrics': performance_metrics,
                'mobile_metrics': mobile_metrics,
                'screenshot_path': screenshot_path,
                'status_code': response.status if response else None
            }
            
        except Exception as e:
            logger.error(f"JavaScript rendering failed for {url}: {e}")
            return None
    
    def extract_links_detailed(self, content: str, base_url: str) -> tuple:
        """Extract and categorize internal and external links"""
        soup = BeautifulSoup(content, 'html.parser')
        base_domain = urlparse(base_url).netloc
        
        internal_links = []
        external_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text().strip()
            
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
            
            link_data = {
                'url': full_url,
                'anchor_text': link_text,
                'rel': link.get('rel', []),
                'title': link.get('title', ''),
                'target': link.get('target', ''),
                'is_navigation': bool(link.find_parent(['nav', 'header', 'footer']))
            }
            
            # Categorize as internal or external
            if urlparse(full_url).netloc == base_domain:
                internal_links.append(link_data)
            else:
                external_links.append(link_data)
        
        return internal_links, external_links
    
    def extract_schema_markup(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract and parse schema markup"""
        schema_data = []
        
        # JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                schema_data.append({
                    'type': 'json-ld',
                    'data': data
                })
            except json.JSONDecodeError:
                continue
        
        # Microdata
        microdata_items = soup.find_all(attrs={'itemtype': True})
        for item in microdata_items:
            schema_data.append({
                'type': 'microdata',
                'itemtype': item.get('itemtype'),
                'properties': self.extract_microdata_properties(item)
            })
        
        return schema_data
    
    def extract_microdata_properties(self, element) -> Dict[str, str]:
        """Extract microdata properties from an element"""
        properties = {}
        
        for prop_element in element.find_all(attrs={'itemprop': True}):
            prop_name = prop_element.get('itemprop')
            
            if prop_element.get('content'):
                prop_value = prop_element.get('content')
            elif prop_element.get('href'):
                prop_value = prop_element.get('href')
            else:
                prop_value = prop_element.get_text().strip()
            
            properties[prop_name] = prop_value
        
        return properties
    
    def analyze_social_tags(self, soup: BeautifulSoup) -> Dict[str, Dict[str, str]]:
        """Analyze social media meta tags"""
        social_tags = {
            'open_graph': {},
            'twitter': {},
            'facebook': {}
        }
        
        # Open Graph tags
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            prop = tag.get('property', '').replace('og:', '')
            content = tag.get('content', '')
            social_tags['open_graph'][prop] = content
        
        # Twitter tags
        twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
        for tag in twitter_tags:
            name = tag.get('name', '').replace('twitter:', '')
            content = tag.get('content', '')
            social_tags['twitter'][name] = content
        
        return social_tags
    
    def analyze_mobile_specific(self, mobile_soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze mobile-specific elements"""
        viewport_meta = mobile_soup.find('meta', attrs={'name': 'viewport'})
        
        return {
            'viewport_configured': bool(viewport_meta),
            'viewport_content': viewport_meta.get('content') if viewport_meta else None,
            'mobile_friendly_nav': len(mobile_soup.find_all('nav')) > 0,
            'touch_friendly_buttons': len(mobile_soup.find_all('button')) + len(mobile_soup.find_all('a', class_=re.compile('btn|button'))),
            'responsive_images': len(mobile_soup.find_all('img', srcset=True)),
            'mobile_specific_css': len(mobile_soup.find_all('link', media=re.compile('screen and.*max-width|mobile')))
        }
    
    async def analyze_page_comprehensive(self, url: str, content: str, status_code: int,
                                       headers: Dict[str, str], load_time: float, depth: int,
                                       js_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Comprehensive page analysis with enhanced features"""
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Basic SEO elements extraction
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_desc.get('content', '') if meta_desc else ""
        
        h1_elements = soup.find_all('h1')
        h1_text = h1_elements[0].get_text().strip() if h1_elements else ""
        
        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        canonical_url = canonical.get('href') if canonical else None
        
        # Language attribute
        html_tag = soup.find('html')
        lang_attribute = html_tag.get('lang') if html_tag else None
        
        # Robots meta
        robots_meta = soup.find('meta', attrs={'name': 'robots'})
        robots_content = robots_meta.get('content') if robots_meta else None
        
        # Enhanced content analysis
        content_analysis = self.content_analyzer.analyze_content(content, url)
        
        # Technical SEO analysis
        technical_issues = self.technical_analyzer.analyze_page(url, content, headers, status_code)
        
        # Extract all links for crawling and analysis
        internal_links, external_links = self.extract_links_detailed(content, url)
        
        # Schema markup analysis
        schema_data = self.extract_schema_markup(soup)
        
        # Social media tags analysis
        social_tags = self.analyze_social_tags(soup)
        
        # Performance analysis
        performance_data = {
            'load_time': load_time,
            'page_size': len(content.encode('utf-8')),
            'js_metrics': js_data.get('performance_metrics', {}) if js_data else {}
        }
        
        # Mobile analysis if available
        mobile_analysis = {}
        if js_data and js_data.get('mobile_content'):
            mobile_soup = BeautifulSoup(js_data['mobile_content'], 'html.parser')
            mobile_analysis = self.analyze_mobile_specific(mobile_soup)
            if js_data.get('mobile_metrics'):
                mobile_analysis.update(js_data['mobile_metrics'])
        
        return {
            'url': url,
            'status_code': status_code,
            'title': title_text,
            'meta_description': meta_desc_text,
            'h1': h1_text,
            'canonical_url': canonical_url,
            'lang_attribute': lang_attribute,
            'robots_meta': robots_content,
            'word_count': content_analysis['word_count'],
            'character_count': content_analysis['character_count'],
            'paragraph_count': content_analysis['paragraph_count'],
            'readability_score': content_analysis['readability_score'],
            'load_time': load_time,
            'page_size': len(content.encode('utf-8')),
            'depth': depth,
            'content_hash': content_analysis['content_hash'],
            'technical_issues': technical_issues,
            'content_analysis': content_analysis,
            'schema_markup': schema_data,
            'social_tags': social_tags,
            'performance': performance_data,
            'mobile_analysis': mobile_analysis,
            'internal_links': internal_links,
            'external_links': external_links,
            'internal_links_count': len(internal_links),
            'external_links_count': len(external_links),
            'total_images': content_analysis['images']['total_images'],
            'images_missing_alt': content_analysis['images']['missing_alt_text'],
            'headers': dict(headers),
            'screenshot_path': js_data.get('screenshot_path') if js_data else None,
            'crawled_at': time.time()
        }
    
    async def fetch_page(self, url: str, depth: int) -> Optional[Dict[str, Any]]:
        """Enhanced page fetching with comprehensive analysis"""
        async with self.semaphore:
            if (url in self.visited_urls or 
                not self.can_fetch(url) or 
                self.should_exclude_url(url)):
                return None
            
            self.visited_urls.add(url)
            self.stats['total_processed'] += 1
            
            try:
                start_time = time.time()
                
                # Fetch with aiohttp first
                async with self.session.get(url, allow_redirects=self.config.follow_redirects) as response:
                    basic_html = await response.text()
                    status_code = response.status
                    headers = dict(response.headers)
                
                # Enhanced JavaScript rendering
                js_data = None
                if self.config.render_javascript:
                    js_data = await self.render_with_javascript(url)
                    content = js_data['content'] if js_data else basic_html
                else:
                    content = basic_html
                
                load_time = time.time() - start_time
                
                # Comprehensive page analysis
                page_data = await self.analyze_page_comprehensive(
                    url, content, status_code, headers, load_time, depth, js_data
                )
                
                # Respect crawl delay
                await asyncio.sleep(self.config.delay)
                
                self.stats['successful'] += 1
                logger.info(f"✓ Crawled: {url} (depth: {depth}, {load_time:.2f}s, {len(page_data['technical_issues'])} issues)")
                
                return page_data
                
            except Exception as e:
                self.stats['failed'] += 1
                error_msg = f"Failed to fetch {url}: {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
                return None
    
    async def crawl_website(self, start_url: str, progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Enhanced main crawling method with better progress tracking"""
        urls_to_crawl = [(start_url, 0)]
        crawled_pages = []
        
        logger.info(f"Starting crawl of {start_url}")
        logger.info(f"Config: max_urls={self.config.max_urls}, max_depth={self.config.max_depth}, max_concurrent={self.config.max_concurrent}")
        
        while urls_to_crawl and len(crawled_pages) < self.config.max_urls:
            # Process URLs in batches for better performance
            batch_size = min(self.config.max_concurrent, len(urls_to_crawl))
            current_batch = urls_to_crawl[:batch_size]
            urls_to_crawl = urls_to_crawl[batch_size:]
            
            # Create tasks for concurrent processing
            tasks = []
            for url, depth in current_batch:
                if depth <= self.config.max_depth:
                    task = asyncio.create_task(self.fetch_page(url, depth))
                    tasks.append(task)
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, dict):
                    crawled_pages.append(result)
                    
                    # Add new URLs to crawl queue
                    if result['depth'] < self.config.max_depth:
                        for link_data in result.get('internal_links', []):
                            link_url = link_data['url']
                            if (link_url not in self.visited_urls and 
                                len(crawled_pages) < self.config.max_urls and
                                not self.should_exclude_url(link_url)):
                                urls_to_crawl.append((link_url, result['depth'] + 1))
                    
                    # Progress callback
                    if progress_callback:
                        await progress_callback({
                            'pages_crawled': len(crawled_pages),
                            'total_processed': self.stats['total_processed'],
                            'successful': self.stats['successful'],
                            'failed': self.stats['failed'],
                            'current_url': result['url'],
                            'queue_size': len(urls_to_crawl),
                            'avg_load_time': sum(p['load_time'] for p in crawled_pages) / len(crawled_pages),
                            'total_issues': sum(len(p['technical_issues']) for p in crawled_pages)
                        })
                
                elif isinstance(result, Exception):
                    self.stats['errors'].append(str(result))
            
            logger.info(f"Batch completed. Total crawled: {len(crawled_pages)}, Queue: {len(urls_to_crawl)}")
        
        # Final statistics
        total_time = time.time() - self.stats['start_time']
        avg_load_time = sum(p['load_time'] for p in crawled_pages) / len(crawled_pages) if crawled_pages else 0
        total_issues = sum(len(p['technical_issues']) for p in crawled_pages)
        
        logger.info(f"Crawl completed:")
        logger.info(f"  - Pages crawled: {len(crawled_pages)}")
        logger.info(f"  - Total time: {total_time:.2f}s")
        logger.info(f"  - Average load time: {avg_load_time:.2f}s")
        logger.info(f"  - Total issues found: {total_issues}")
        logger.info(f"  - Success rate: {(self.stats['successful'] / self.stats['total_processed'] * 100):.1f}%")
        
        return crawled_pages

# Convenience function for easy usage
async def crawl_website(start_url: str, config: Optional[CrawlConfig] = None, 
                       progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
    """Convenience function to crawl a website"""
    if config is None:
        config = CrawlConfig()
    
    async with AsyncWebCrawler(config) as crawler:
        return await crawler.crawl_website(start_url, progress_callback)