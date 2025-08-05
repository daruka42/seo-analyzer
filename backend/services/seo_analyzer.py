from typing import List, Dict
from bs4 import BeautifulSoup
import re

class MultiLanguageTechnicalSEOAnalyzer:
    """Technical SEO analysis with Hungarian language considerations"""
    
    def analyze_page(self, url: str, content: str, headers: Dict, status_code: int, language: str = 'hu') -> List[Dict]:
        """Perform comprehensive technical SEO analysis with language awareness"""
        issues = []
        soup = BeautifulSoup(content, 'html.parser')
        
        # Title tag analysis
        issues.extend(self.analyze_title(soup, language))
        
        # Meta description analysis
        issues.extend(self.analyze_meta_description(soup, language))
        
        # Heading structure
        issues.extend(self.analyze_heading_structure(soup))
        
        # Language-specific meta tags
        issues.extend(self.analyze_language_meta_tags(soup, language))
        
        # Hungarian-specific SEO checks
        if language == 'hu':
            issues.extend(self.analyze_hungarian_seo(soup, content))
        
        # Standard technical checks
        issues.extend(self.analyze_canonical(soup, url))
        issues.extend(self.analyze_robots_meta(soup))
        issues.extend(self.analyze_https(url))
        issues.extend(self.analyze_schema(soup))
        issues.extend(self.analyze_performance_indicators(soup))
        issues.extend(self.analyze_accessibility(soup))
        issues.extend(self.analyze_open_graph(soup, language))
        
        return issues

    def analyze_title(self, soup: BeautifulSoup, language: str) -> List[Dict]:
        """Analyze title tag with language-specific recommendations"""
        issues = []
        title = soup.find('title')
        
        if not title:
            issues.append({
                'type': 'missing_title',
                'severity': 'critical',
                'category': 'technical',
                'description': 'Az oldal nem tartalmaz title tag-et' if language == 'hu' else 'Page is missing a title tag',
                'recommendation': 'Adjon hozzá egy leíró title tag-et 30-60 karakter között' if language == 'hu' else 'Add a descriptive title tag between 30-60 characters',
                'impact_score': 95
            })
        else:
            title_text = title.get_text().strip()
            
            if len(title_text) == 0:
                issues.append({
                    'type': 'empty_title',
                    'severity': 'critical',
                    'category': 'technical',
                    'description': 'A title tag üres' if language == 'hu' else 'Title tag is empty',
                    'recommendation': 'Adjon tartalmat a title tag-hez' if language == 'hu' else 'Add descriptive content to the title tag',
                    'impact_score': 95
                })
            elif len(title_text) < 30:
                issues.append({
                    'type': 'short_title',
                    'severity': 'medium',
                    'category': 'content',
                    'description': f'A title tag túl rövid ({len(title_text)} karakter)' if language == 'hu' else f'Title tag is too short ({len(title_text)} characters)',
                    'recommendation': 'Bővítse a title-t 30-60 karakterre a jobb SEO érdekében' if language == 'hu' else 'Expand title to 30-60 characters for better SEO',
                    'impact_score': 60
                })
            elif len(title_text) > 60:
                issues.append({
                    'type': 'long_title',
                    'severity': 'medium',
                    'category': 'content',
                    'description': f'A title tag túl hosszú ({len(title_text)} karakter)' if language == 'hu' else f'Title tag is too long ({len(title_text)} characters)',
                    'recommendation': 'Rövidítse a title-t 60 karakter alá a csonkítás elkerülése érdekében' if language == 'hu' else 'Shorten title to under 60 characters to prevent truncation',
                    'impact_score': 50
                })
        
        return issues

    def analyze_meta_description(self, soup: BeautifulSoup, language: str) -> List[Dict]:
        """Analyze meta description with language-specific recommendations"""
        issues = []
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        
        if not meta_desc:
            issues.append({
                'type': 'missing_meta_description',
                'severity': 'high',
                'category': 'content',
                'description': 'Az oldal nem tartalmaz meta description-t' if language == 'hu' else 'Page is missing a meta description',
                'recommendation': 'Adjon hozzá egy vonzó meta description-t 120-160 karakter között' if language == 'hu' else 'Add a compelling meta description between 120-160 characters',
                'impact_score': 80
            })
        else:
            desc_content = meta_desc.get('content', '').strip()
            
            if len(desc_content) == 0:
                issues.append({
                    'type': 'empty_meta_description',
                    'severity': 'high',
                    'category': 'content',
                    'description': 'A meta description üres' if language == 'hu' else 'Meta description is empty',
                    'recommendation': 'Adjon leíró tartalmat a meta description-höz' if language == 'hu' else 'Add descriptive content to the meta description',
                    'impact_score': 80
                })
            elif len(desc_content) < 120:
                issues.append({
                    'type': 'short_meta_description',
                    'severity': 'low',
                    'category': 'content',
                    'description': f'A meta description rövid ({len(desc_content)} karakter)' if language == 'hu' else f'Meta description is short ({len(desc_content)} characters)',
                    'recommendation': 'Bővítse a meta description-t 120-160 karakterre' if language == 'hu' else 'Expand meta description to 120-160 characters',
                    'impact_score': 30
                })
            elif len(desc_content) > 160:
                issues.append({
                    'type': 'long_meta_description',
                    'severity': 'medium',
                    'category': 'content',
                    'description': f'A meta description túl hosszú ({len(desc_content)} karakter)' if language == 'hu' else f'Meta description is too long ({len(desc_content)} characters)',
                    'recommendation': 'Rövidítse a meta description-t 160 karakter alá' if language == 'hu' else 'Shorten meta description to under 160 characters',
                    'impact_score': 40
                })
        
        return issues

    def analyze_language_meta_tags(self, soup: BeautifulSoup, detected_language: str) -> List[Dict]:
        """Analyze language-related meta tags"""
        issues = []
        
        # Check html lang attribute
        html_tag = soup.find('html')
        if html_tag:
            lang_attr = html_tag.get('lang')
            if not lang_attr:
                issues.append({
                    'type': 'missing_html_lang',
                    'severity': 'medium',
                    'category': 'accessibility',
                    'description': 'Hiányzik a lang attribútum a html tag-ből' if detected_language == 'hu' else 'Missing lang attribute in html tag',
                    'recommendation': f'Adja hozzá a lang="{detected_language}" attribútumot a html tag-hez' if detected_language == 'hu' else f'Add lang="{detected_language}" attribute to html tag',
                    'impact_score': 45
                })
            elif lang_attr != detected_language:
                issues.append({
                    'type': 'incorrect_html_lang',
                    'severity': 'medium',
                    'category': 'accessibility',
                    'description': f'A html lang attribútum ({lang_attr}) nem egyezik az észlelt nyelvvel ({detected_language})' if detected_language == 'hu' else f'HTML lang attribute ({lang_attr}) does not match detected language ({detected_language})',
                    'recommendation': f'Változtassa a lang attribútumot "{detected_language}"-re' if detected_language == 'hu' else f'Change lang attribute to "{detected_language}"',
                    'impact_score': 40
                })
        
        # Check for hreflang tags (important for Hungarian sites targeting multiple regions)
        hreflang_tags = soup.find_all('link', rel='alternate', hreflang=True)
        if detected_language == 'hu' and not hreflang_tags:
            issues.append({
                'type': 'missing_hreflang',
                'severity': 'low',
                'category': 'technical',
                'description': 'Hiányoznak a hreflang tag-ek' if detected_language == 'hu' else 'Missing hreflang tags',
                'recommendation': 'Fontolja meg hreflang tag-ek hozzáadását a nemzetközi SEO javítása érdekében' if detected_language == 'hu' else 'Consider adding hreflang tags for international SEO',
                'impact_score': 25
            })
        
        return issues

    def analyze_hungarian_seo(self, soup: BeautifulSoup, content: str) -> List[Dict]:
        """Hungarian-specific SEO analysis"""
        issues = []
        
        # Check for Hungarian character encoding
        charset_meta = soup.find('meta', charset=True) or soup.find('meta', {'http-equiv': 'Content-Type'})
        if charset_meta:
            charset = charset_meta.get('charset', '').lower()
            content_type = charset_meta.get('content', '').lower()
            
            if charset and 'utf-8' not in charset:
                issues.append({
                    'type': 'non_utf8_charset',
                    'severity': 'high',
                    'category': 'technical',
                    'description': 'A karakterkódolás nem UTF-8, ami problémákat okozhat a magyar karakterekkel',
                    'recommendation': 'Változtassa a karakterkódolást UTF-8-ra a magyar karakterek helyes megjelenítéséhez',
                    'impact_score': 75
                })
            elif content_type and 'utf-8' not in content_type:
                issues.append({
                    'type': 'non_utf8_content_type',
                    'severity': 'high',
                    'category': 'technical',
                    'description': 'A Content-Type nem tartalmazza az UTF-8 kódolást',
                    'recommendation': 'Adja hozzá a charset=utf-8 paramétert a Content-Type header-hez',
                    'impact_score': 75
                })
        
        # Check for Hungarian local business schema
        text_content = soup.get_text().lower()
        if any(keyword in text_content for keyword in ['budapest', 'debrecen', 'szeged', 'miskolc', 'pécs', 'győr']):
            local_business_schema = soup.find('script', type='application/ld+json')
            if local_business_schema:
                schema_content = local_business_schema.get_text()
                if 'LocalBusiness' not in schema_content and 'Organization' not in schema_content:
                    issues.append({
                        'type': 'missing_local_business_schema',
                        'severity': 'low',
                        'category': 'technical',
                        'description': 'Helyi üzlet séma markup hiányzik magyar helységnév említése ellenére',
                        'recommendation': 'Adjon hozzá LocalBusiness vagy Organization schema markup-ot a helyi SEO javítása érdekében',
                        'impact_score': 35
                    })
        
        # Check for Hungarian currency and contact info patterns
        if re.search(r'\b\d+\s*Ft\b|\bforint\b', text_content):
            # Hungarian currency detected - recommend currency schema
            if 'PriceSpecification' not in content and 'Product' not in content:
                issues.append({
                    'type': 'missing_price_schema_hu',
                    'severity': 'low',
                    'category': 'technical',
                    'description': 'Árinfó észlelve séma markup nélkül',
                    'recommendation': 'Adjon hozzá PriceSpecification vagy Product schema markup-ot az árakhoz',
                    'impact_score': 30
                })
        
        return issues

    def analyze_heading_structure(self, soup: BeautifulSoup) -> List[Dict]:
        """Analyze heading structure (language-independent but with Hungarian messages)"""
        issues = []
        h1_tags = soup.find_all('h1')
        
        if len(h1_tags) == 0:
            issues.append({
                'type': 'missing_h1',
                'severity': 'high',
                'category': 'technical',
                'description': 'Az oldal nem tartalmaz H1 tag-et',
                'recommendation': 'Adjon hozzá egy H1 tag-et, amely leírja az oldal fő témáját',
                'impact_score': 85
            })
        elif len(h1_tags) > 1:
            issues.append({
                'type': 'multiple_h1',
                'severity': 'medium',
                'category': 'technical',
                'description': f'Az oldal {len(h1_tags)} H1 tag-et tartalmaz',
                'recommendation': 'Használjon csak egy H1 tag-et oldalanként',
                'impact_score': 50
            })
        
        return issues

    # ... (continue with other analyze methods with Hungarian language support)
    
    def analyze_canonical(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Analyze canonical tag"""
        issues = []
        canonical = soup.find('link', rel='canonical')
        
        if not canonical:
            issues.append({
                'type': 'missing_canonical',
                'severity': 'medium',
                'category': 'technical',
                'description': 'Az oldal nem tartalmaz canonical tag-et',
                'recommendation': 'Adjon hozzá canonical tag-et a duplikált tartalom problémák elkerülése érdekében',
                'impact_score': 60
            })
        else:
            canonical_url = canonical.get('href')
            if canonical_url != url and canonical_url != url.rstrip('/'):
                issues.append({
                    'type': 'non_self_canonical',
                    'severity': 'low',
                    'category': 'technical',
                    'description': 'A canonical tag másik URL-re mutat',
                    'recommendation': 'Ellenőrizze, hogy a canonical hivatkozás szándékos-e',
                    'impact_score': 30
                })
        
        return issues

    def analyze_open_graph(self, soup: BeautifulSoup, language: str) -> List[Dict]:
        """Analyze Open Graph tags with language consideration"""
        issues = []
        
        og_title = soup.find('meta', property='og:title')
        og_description = soup.find('meta', property='og:description')
        og_image = soup.find('meta', property='og:image')
        og_locale = soup.find('meta', property='og:locale')
        
        if not og_title:
            issues.append({
                'type': 'missing_og_title',
                'severity': 'low',
                'category': 'social',
                'description': 'Hiányzik az Open Graph title' if language == 'hu' else 'Missing Open Graph title',
                'recommendation': 'Adjon hozzá og:title meta tag-et a jobb közösségi média megosztáshoz' if language == 'hu' else 'Add og:title meta tag for better social media sharing',
                'impact_score': 20
            })
        
        if not og_description:
            issues.append({
                'type': 'missing_og_description',
                'severity': 'low',
                'category': 'social',
                'description': 'Hiányzik az Open Graph description' if language == 'hu' else 'Missing Open Graph description',
                'recommendation': 'Adjon hozzá og:description meta tag-et a jobb közösségi média megosztáshoz' if language == 'hu' else 'Add og:description meta tag for better social media sharing',
                'impact_score': 20
            })
        
        if not og_image:
            issues.append({
                'type': 'missing_og_image',
                'severity': 'low',
                'category': 'social',
                'description': 'Hiányzik az Open Graph image' if language == 'hu' else 'Missing Open Graph image',
                'recommendation': 'Adjon hozzá og:image meta tag-et a jobb közösségi média megosztáshoz' if language == 'hu' else 'Add og:image meta tag for better social media sharing',
                'impact_score': 15
            })
        
        # Check for appropriate locale
        if language == 'hu' and not og_locale:
            issues.append({
                'type': 'missing_og_locale',
                'severity': 'low',
                'category': 'social',
                'description': 'Hiányzik az og:locale meta tag',
                'recommendation': 'Adjon hozzá og:locale meta tag-et "hu_HU" értékkel',
                'impact_score': 15
            })
        elif og_locale:
            locale_content = og_locale.get('content', '')
            if language == 'hu' and not locale_content.startswith('hu'):
                issues.append({
                    'type': 'incorrect_og_locale',
                    'severity': 'low',
                    'category': 'social',
                    'description': f'Az og:locale ({locale_content}) nem megfelelő a magyar tartalomhoz',
                    'recommendation': 'Változtassa az og:locale értékét "hu_HU"-ra',
                    'impact_score': 15
                })
        
        return issues

    # Add other standard methods here (analyze_robots_meta, analyze_https, etc.)
    # They can remain largely the same but with Hungarian error messages
