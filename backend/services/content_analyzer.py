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
from langdetect import detect, LangDetectError
from core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiLanguageContentAnalyzer:
    """Enhanced content analysis with Hungarian language support"""
    
    def __init__(self):
        # Load language models
        self.nlp_models = {}
        self.load_language_models()
        
        # Hungarian stop words
        self.hungarian_stop_words = {
            'a', 'az', 'egy', 'és', 'van', 'volt', 'lesz', 'be', 'ki', 'le', 'fel', 'el', 'meg', 'át', 'rá', 'ide', 'oda',
            'hogy', 'mint', 'vagy', 'de', 'ha', 'mert', 'mivel', 'amikor', 'ahol', 'aki', 'ami', 'amely', 'amelyet',
            'ezt', 'azt', 'itt', 'ott', 'akkor', 'most', 'már', 'még', 'csak', 'is', 'nem', 'igen', 'igen', 'talán',
            'lehet', 'kell', 'fog', 'tud', 'akar', 'szeret', 'lát', 'hall', 'mond', 'gondol', 'hisz', 'tudja', 'látja',
            'hallja', 'mondja', 'gondolja', 'hiszi', 'ellen', 'mellett', 'között', 'alatt', 'felett', 'előtt', 'után',
            'közben', 'során', 'nélkül', 'helyett', 'miatt', 'végett', 'számára', 'részére', 'által', 'felől', 'felé',
            'minden', 'semmi', 'valami', 'némely', 'több', 'kevés', 'sok', 'elég', 'túl', 'igen', 'nagyon', 'kissé',
            'egy', 'kettő', 'három', 'négy', 'öt', 'hat', 'hét', 'nyolc', 'kilenc', 'tíz', 'száz', 'ezer', 'millió',
            'első', 'második', 'harmadik', 'utolsó', 'nagy', 'kicsi', 'jó', 'rossz', 'új', 'régi', 'fiatal', 'öreg',
            'szép', 'csúnya', 'hosszú', 'rövid', 'magas', 'alacsony', 'vastag', 'vékony', 'nehéz', 'könnyű', 'gyors',
            'lassú', 'meleg', 'hideg', 'forró', 'jeges', 'világos', 'sötét', 'tiszta', 'piszkos', 'teljes', 'üres'
        }
        
        # English stop words (keep for fallback)
        self.english_stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up',
            'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'can', 'will', 'just', 'should', 'now', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'get', 'got', 'make', 'made', 'go', 'went', 'come', 'came',
            'see', 'saw', 'know', 'knew', 'take', 'took', 'think', 'thought'
        }

    def load_language_models(self):
        """Load spaCy models for different languages"""
        try:
            # Try to load Hungarian model (if available)
            self.nlp_models['hu'] = spacy.load("hu_core_news_sm")
            logger.info("Hungarian spaCy model loaded successfully")
        except OSError:
            logger.warning("Hungarian spaCy model not found. Install with: python -m spacy download hu_core_news_sm")
            
        try:
            # Load English model as fallback
            self.nlp_models['en'] = spacy.load("en_core_web_sm")
            logger.info("English spaCy model loaded successfully")
        except OSError:
            logger.warning("English spaCy model not found. Install with: python -m spacy download en_core_web_sm")

    def detect_language(self, text: str) -> str:
        """Detect the language of the text"""
        try:
            # Clean text for language detection
            clean_text = ' '.join(text.split()[:100])  # Use first 100 words
            detected_lang = detect(clean_text)
            logger.info(f"Detected language: {detected_lang}")
            return detected_lang
        except LangDetectError:
            logger.warning("Could not detect language, defaulting to Hungarian")
            return 'hu'

    def get_stop_words(self, language: str) -> Set[str]:
        """Get stop words for the detected language"""
        if language == 'hu':
            return self.hungarian_stop_words
        elif language == 'en':
            return self.english_stop_words
        else:
            # Default to Hungarian for unknown languages
            return self.hungarian_stop_words

    def analyze_content(self, content: str, url: str) -> Dict:
        """Perform comprehensive content analysis with language detection"""
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        text = soup.get_text()
        clean_text = ' '.join(text.split())
        
        # Detect language
        detected_language = self.detect_language(clean_text)
        
        analysis = {
            'detected_language': detected_language,
            'word_count': len(clean_text.split()),
            'character_count': len(clean_text),
            'paragraph_count': len(soup.find_all('p')),
            'readability_score': self.calculate_readability(clean_text, detected_language),
            'keyword_density': self.analyze_keyword_density(clean_text, detected_language),
            'entities': self.extract_entities(clean_text, detected_language),
            'headings_structure': self.analyze_headings(soup),
            'internal_links': self.count_internal_links(soup, url),
            'external_links': self.count_external_links(soup, url),
            'images': self.analyze_images(soup),
            'content_hash': self.generate_content_hash(clean_text),
            'language_specific_analysis': self.language_specific_analysis(clean_text, detected_language)
        }
        
        return analysis

    def calculate_readability(self, text: str, language: str) -> Dict:
        """Calculate readability score with language-specific adjustments"""
        if language == 'hu':
            return self.calculate_hungarian_readability(text)
        else:
            return self.calculate_flesch_readability(text)

    def calculate_hungarian_readability(self, text: str) -> Dict:
        """Calculate readability for Hungarian text using adapted metrics"""
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        
        if sentences == 0 or words == 0:
            return {'score': 0, 'level': 'unknown', 'method': 'hungarian_adapted'}
        
        # Hungarian-adapted syllable counting
        syllables = sum([self.count_hungarian_syllables(word) for word in text.split()])
        
        if syllables == 0:
            return {'score': 0, 'level': 'unknown', 'method': 'hungarian_adapted'}
        
        # Adapted Flesch formula for Hungarian
        # Hungarian has different syllable patterns than English
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        # Adjusted coefficients for Hungarian
        score = 200 - (1.1 * avg_sentence_length) - (60 * avg_syllables_per_word)
        score = max(0, min(100, score))
        
        # Hungarian readability levels
        if score >= 80:
            level = 'very_easy'
        elif score >= 65:
            level = 'easy'
        elif score >= 50:
            level = 'medium'
        elif score >= 35:
            level = 'difficult'
        else:
            level = 'very_difficult'
        
        return {
            'score': round(score, 2),
            'level': level,
            'method': 'hungarian_adapted',
            'avg_sentence_length': round(avg_sentence_length, 2),
            'avg_syllables_per_word': round(avg_syllables_per_word, 2)
        }

    def count_hungarian_syllables(self, word: str) -> int:
        """Count syllables in Hungarian words"""
        word = word.lower().strip('.,!?;:"')
        
        # Hungarian vowels (including long vowels and umlauts)
        hungarian_vowels = "aáeéiíoóöőuúüű"
        
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            if char in hungarian_vowels:
                if not previous_was_vowel:
                    syllable_count += 1
                previous_was_vowel = True
            else:
                previous_was_vowel = False
        
        # Hungarian-specific rules
        # Diphthongs and special cases
        if 'gy' in word or 'ny' in word or 'ty' in word or 'ly' in word:
            # These are single sounds in Hungarian
            pass
        
        return max(1, syllable_count)

    def calculate_flesch_readability(self, text: str) -> Dict:
        """Calculate standard Flesch Reading Ease score for non-Hungarian text"""
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        
        if sentences == 0 or words == 0:
            return {'score': 0, 'level': 'unknown', 'method': 'flesch'}
        
        syllables = sum([self.count_syllables(word) for word in text.split()])
        
        if syllables == 0:
            return {'score': 0, 'level': 'unknown', 'method': 'flesch'}
        
        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        score = max(0, min(100, score))
        
        if score >= 90:
            level = 'very_easy'
        elif score >= 80:
            level = 'easy'
        elif score >= 70:
            level = 'fairly_easy'
        elif score >= 60:
            level = 'standard'
        elif score >= 50:
            level = 'fairly_difficult'
        elif score >= 30:
            level = 'difficult'
        else:
            level = 'very_difficult'
        
        return {
            'score': round(score, 2),
            'level': level,
            'method': 'flesch'
        }

    def count_syllables(self, word: str) -> int:
        """Estimate syllable count for English words"""
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

    def analyze_keyword_density(self, text: str, language: str) -> Dict:
        """Analyze keyword density with language-specific stop words"""
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)
        
        if total_words == 0:
            return {}
        
        # Get appropriate stop words
        stop_words = self.get_stop_words(language)
        
        # Filter out stop words and short words
        filtered_words = [
            word for word in words 
            if word not in stop_words and len(word) > 2
        ]
        
        word_freq = Counter(filtered_words)
        
        # Get top 20 keywords
        top_keywords = word_freq.most_common(20)
        
        return {
            'language': language,
            'keywords': {
                keyword: {
                    'count': count,
                    'density': round((count / total_words) * 100, 2)
                }
                for keyword, count in top_keywords if count > 1
            },
            'total_unique_words': len(set(filtered_words)),
            'vocabulary_richness': round(len(set(filtered_words)) / len(filtered_words), 2) if filtered_words else 0
        }

    def extract_entities(self, text: str, language: str) -> List[Dict]:
        """Extract named entities using appropriate language model"""
        entities = []
        
        # Get appropriate NLP model
        if language in self.nlp_models:
            nlp = self.nlp_models[language]
        elif 'en' in self.nlp_models:
            nlp = self.nlp_models['en']
        else:
            return []
        
        try:
            # Limit text length for performance
            doc = nlp(text[:100000])
            
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'description': spacy.explain(ent.label_) or ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
        
        return entities

    def language_specific_analysis(self, text: str, language: str) -> Dict:
        """Perform language-specific analysis"""
        analysis = {
            'language': language,
            'confidence': 0.8  # Default confidence
        }
        
        if language == 'hu':
            analysis.update(self.hungarian_specific_analysis(text))
        elif language == 'en':
            analysis.update(self.english_specific_analysis(text))
        
        return analysis

    def hungarian_specific_analysis(self, text: str) -> Dict:
        """Hungarian-specific text analysis"""
        analysis = {}
        
        # Check for Hungarian character usage
        hungarian_chars = set('áéíóöőúüű')
        text_chars = set(text.lower())
        hungarian_char_ratio = len(text_chars.intersection(hungarian_chars)) / len(text_chars) if text_chars else 0
        
        analysis['hungarian_char_ratio'] = round(hungarian_char_ratio, 3)
        analysis['uses_hungarian_chars'] = hungarian_char_ratio > 0
        
        # Check for typical Hungarian words/patterns
        hungarian_patterns = [
            r'\b(hogy|amit|amely|amelyet|amikor|ahol)\b',  # Relative pronouns
            r'\b(van|volt|lesz|lenne|lehet)\b',  # Common verbs
            r'\b(egy|kettő|három|négy|öt)\b',  # Numbers
            r'\b(magyar|magyarország|budapest)\b',  # Geographic
        ]
        
        pattern_matches = 0
        for pattern in hungarian_patterns:
            matches = len(re.findall(pattern, text.lower()))
            pattern_matches += matches
        
        analysis['hungarian_pattern_score'] = pattern_matches / len(text.split()) if text.split() else 0
        
        # Hungarian word formation patterns
        # Check for typical Hungarian suffixes
        hungarian_suffixes = ['nak', 'nek', 'ban', 'ben', 'ból', 'ből', 'hoz', 'hez', 'höz', 'tól', 'től']
        suffix_count = 0
        words = text.split()
        
        for word in words:
            for suffix in hungarian_suffixes:
                if word.lower().endswith(suffix):
                    suffix_count += 1
                    break
        
        analysis['hungarian_suffix_ratio'] = suffix_count / len(words) if words else 0
        
        return analysis

    def english_specific_analysis(self, text: str) -> Dict:
        """English-specific text analysis"""
        analysis = {}
        
        # Basic English patterns
        english_patterns = [
            r'\b(the|and|that|have|for|not|with|you|this|but)\b',
            r'\b(ing|ed|er|est)\b',  # Common endings
        ]
        
        pattern_matches = 0
        for pattern in english_patterns:
            matches = len(re.findall(pattern, text.lower()))
            pattern_matches += matches
        
        analysis['english_pattern_score'] = pattern_matches / len(text.split()) if text.split() else 0
        
        return analysis

    def analyze_headings(self, soup: BeautifulSoup) -> Dict:
        """Analyze heading structure (language-independent)"""
        headings = {}
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            headings[f'h{i}'] = [tag.get_text().strip() for tag in h_tags]
        return headings

    def count_internal_links(self, soup: BeautifulSoup, base_url: str) -> int:
        """Count internal links (language-independent)"""
        domain = urlparse(base_url).netloc
        links = soup.find_all('a', href=True)
        internal_count = 0
        
        for link in links:
            href = link['href']
            if href.startswith('/') or domain in href:
                internal_count += 1
                
        return internal_count

    def count_external_links(self, soup: BeautifulSoup, base_url: str) -> int:
        """Count external links (language-independent)"""
        domain = urlparse(base_url).netloc
        links = soup.find_all('a', href=True)
        external_count = 0
        
        for link in links:
            href = link['href']
            if href.startswith('http') and domain not in href:
                external_count += 1
                
        return external_count

    def analyze_images(self, soup: BeautifulSoup) -> Dict:
        """Analyze images on the page (language-independent)"""
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
