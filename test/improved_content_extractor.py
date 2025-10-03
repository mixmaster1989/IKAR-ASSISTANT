#!/usr/bin/env python3
"""
🔍 УЛУЧШЕННАЯ СИСТЕМА ИЗВЛЕЧЕНИЯ КОНТЕНТА
Множественные методы парсинга с фильтрацией релевантности
"""

import asyncio
import aiohttp
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import trafilatura
from newspaper import Article
from bs4 import BeautifulSoup
import readability
import justext
import nltk
from nltk.tokenize import sent_tokenize
import hashlib

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ОТКЛЮЧАЕМ DEBUG ЛОГИ ОТ СТОРОННИХ БИБЛИОТЕК
try:
    from internet_intelligence_logger import disable_third_party_debug_logs
    disable_third_party_debug_logs()
except ImportError:
    # Fallback если функция недоступна
    third_party_loggers = ['htmldate', 'trafilatura', 'newspaper', 'readability', 'justext',
                          'bs4', 'urllib3', 'aiohttp', 'asyncio', 'charset_normalizer',
                          'requests', 'feedparser', 'nltk', 'lxml', 'html5lib']
    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

@dataclass
class ExtractedContent:
    """Извлеченный контент с метаданными"""
    text: str
    title: str
    author: Optional[str]
    publish_date: Optional[str]
    language: str
    word_count: int
    relevance_score: float
    extraction_method: str
    url: str
    metadata: Dict[str, Any]

class ImprovedContentExtractor:
    """Улучшенная система извлечения контента"""
    
    def __init__(self):
        self.session = None
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        # Настройки фильтрации
        self.min_word_count = 50
        self.max_word_count = 10000
        self.min_relevance_score = 0.3
        
        # Список доменов с известными проблемами парсинга
        self.problematic_domains = {
            'wikipedia.org': 'wikipedia',
            'youtube.com': 'video',
            'facebook.com': 'social',
            'twitter.com': 'social',
            'instagram.com': 'social',
            'linkedin.com': 'social'
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение HTTP сессии"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15),
                headers={'User-Agent': self.user_agent}
            )
        return self.session
    
    def _get_domain_type(self, url: str) -> str:
        """Определение типа домена для выбора метода парсинга"""
        domain = urlparse(url).netloc.lower()
        
        for problematic_domain, domain_type in self.problematic_domains.items():
            if problematic_domain in domain:
                return domain_type
        
        # Определяем по ключевым словам в домене
        if any(word in domain for word in ['news', 'rbc', 'ria', 'tass', 'interfax']):
            return 'news'
        elif any(word in domain for word in ['blog', 'medium', 'substack']):
            return 'blog'
        elif any(word in domain for word in ['forum', 'reddit', 'stackoverflow']):
            return 'forum'
        else:
            return 'general'
    
    async def extract_with_trafilatura(self, html: str, url: str) -> Optional[ExtractedContent]:
        """Извлечение контента с помощью Trafilatura"""
        try:
            # Пробуем разные настройки Trafilatura
            configs = [
                {'include_formatting': True, 'include_links': False},
                {'include_formatting': False, 'include_links': False},
                {'include_formatting': True, 'include_links': True}
            ]
            
            for config in configs:
                extracted = trafilatura.extract(html, **config)
                if extracted and len(extracted.strip()) > 100:
                    # Получаем метаданные
                    metadata = trafilatura.extract_metadata(html)
                    
                    return ExtractedContent(
                        text=extracted.strip(),
                        title=metadata.title if metadata else '',
                        author=metadata.author if metadata else None,
                        publish_date=metadata.date if metadata else None,
                        language=metadata.language if metadata else 'ru',
                        word_count=len(extracted.split()),
                        relevance_score=0.0,  # Будет рассчитано позже
                        extraction_method='trafilatura',
                        url=url,
                        metadata={'config': config}
                    )
            
            return None
        except Exception as e:
            logger.debug(f"Trafilatura failed for {url}: {e}")
            return None
    
    async def extract_with_newspaper(self, html: str, url: str) -> Optional[ExtractedContent]:
        """Извлечение контента с помощью Newspaper3k"""
        try:
            article = Article(url)
            article.download(input_html=html)
            article.parse()
            
            if article.text and len(article.text.strip()) > 100:
                return ExtractedContent(
                    text=article.text.strip(),
                    title=article.title or '',
                    author=article.authors[0] if article.authors else None,
                    publish_date=article.publish_date.isoformat() if article.publish_date else None,
                    language=article.language or 'ru',
                    word_count=len(article.text.split()),
                    relevance_score=0.0,
                    extraction_method='newspaper',
                    url=url,
                    metadata={'authors': article.authors, 'top_image': article.top_image}
                )
            
            return None
        except Exception as e:
            logger.debug(f"Newspaper failed for {url}: {e}")
            return None
    
    async def extract_with_readability(self, html: str, url: str) -> Optional[ExtractedContent]:
        """Извлечение контента с помощью Readability"""
        try:
            doc = readability.Document(html)
            if doc.title() and doc.summary():
                return ExtractedContent(
                    text=doc.summary(),
                    title=doc.title(),
                    author=None,
                    publish_date=None,
                    language='ru',
                    word_count=len(doc.summary().split()),
                    relevance_score=0.0,
                    extraction_method='readability',
                    url=url,
                    metadata={'short_title': doc.short_title()}
                )
            
            return None
        except Exception as e:
            logger.debug(f"Readability failed for {url}: {e}")
            return None
    
    async def extract_with_justext(self, html: str, url: str) -> Optional[ExtractedContent]:
        """Извлечение контента с помощью Justext"""
        try:
            paragraphs = justext.justext(html, justext.get_stoplist("Russian"))
            
            # Собираем текст из хороших параграфов
            good_texts = []
            for paragraph in paragraphs:
                if not paragraph.is_boilerplate and paragraph.text.strip():
                    good_texts.append(paragraph.text.strip())
            
            if good_texts:
                full_text = '\n\n'.join(good_texts)
                if len(full_text) > 100:
                    return ExtractedContent(
                        text=full_text,
                        title='',
                        author=None,
                        publish_date=None,
                        language='ru',
                        word_count=len(full_text.split()),
                        relevance_score=0.0,
                        extraction_method='justext',
                        url=url,
                        metadata={'paragraphs_count': len(good_texts)}
                    )
            
            return None
        except Exception as e:
            logger.debug(f"Justext failed for {url}: {e}")
            return None
    
    async def extract_with_bs4(self, html: str, url: str) -> Optional[ExtractedContent]:
        """Извлечение контента с помощью BeautifulSoup (fallback)"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Удаляем ненужные элементы
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
                element.decompose()
            
            # Ищем основной контент
            content_selectors = [
                'article',
                '[role="main"]',
                '.content',
                '.post-content',
                '.article-content',
                '.entry-content',
                '#content',
                '.main-content'
            ]
            
            content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content and len(content.get_text().strip()) > 100:
                    break
            
            if not content:
                # Берем body если ничего не найдено
                content = soup.find('body')
            
            if content:
                text = content.get_text(separator='\n', strip=True)
                # Очищаем текст
                text = re.sub(r'\n\s*\n', '\n\n', text)
                text = re.sub(r'\s+', ' ', text)
                
                if len(text) > 100:
                    return ExtractedContent(
                        text=text,
                        title=soup.find('title').get_text() if soup.find('title') else '',
                        author=None,
                        publish_date=None,
                        language='ru',
                        word_count=len(text.split()),
                        relevance_score=0.0,
                        extraction_method='beautifulsoup',
                        url=url,
                        metadata={'used_selector': selector if content else 'body'}
                    )
            
            return None
        except Exception as e:
            logger.debug(f"BeautifulSoup failed for {url}: {e}")
            return None
    
    def calculate_relevance_score(self, content: ExtractedContent, query: str) -> float:
        """Расчет релевантности контента к запросу"""
        query_words = set(query.lower().split())
        content_words = set(content.text.lower().split())
        
        # Количество совпадающих слов
        matching_words = len(query_words.intersection(content_words))
        
        # Длина контента (предпочитаем среднюю длину)
        length_score = 1.0
        if content.word_count < 100:
            length_score = 0.3
        elif content.word_count > 5000:
            length_score = 0.7
        
        # Качество извлечения (предпочитаем trafilatura и newspaper)
        method_scores = {
            'trafilatura': 1.0,
            'newspaper': 0.9,
            'readability': 0.8,
            'justext': 0.7,
            'beautifulsoup': 0.5
        }
        method_score = method_scores.get(content.extraction_method, 0.5)
        
        # Наличие заголовка
        title_score = 1.0 if content.title else 0.8
        
        # Общий скор
        relevance = (
            (matching_words / max(len(query_words), 1)) * 0.4 +
            length_score * 0.2 +
            method_score * 0.2 +
            title_score * 0.1 +
            (1.0 if content.author else 0.8) * 0.1
        )
        
        return min(relevance, 1.0)
    
    def filter_content(self, content: ExtractedContent, query: str) -> bool:
        """Фильтрация контента по качеству"""
        # Проверяем минимальную длину
        if content.word_count < self.min_word_count:
            return False
        
        # Проверяем максимальную длину
        if content.word_count > self.max_word_count:
            return False
        
        # Проверяем релевантность
        relevance = self.calculate_relevance_score(content, query)
        if relevance < self.min_relevance_score:
            return False
        
        # Проверяем на спам/рекламу
        spam_indicators = [
            'купить сейчас', 'акция', 'скидка', 'бесплатно',
            'зарегистрируйтесь', 'подпишитесь', 'реклама'
        ]
        
        text_lower = content.text.lower()
        spam_count = sum(1 for indicator in spam_indicators if indicator in text_lower)
        if spam_count > 3:
            return False
        
        return True
    
    async def extract_content(self, url: str, query: str) -> Optional[ExtractedContent]:
        """Основной метод извлечения контента"""
        try:
            session = await self._get_session()
            
            async with session.get(url, timeout=15) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                
                html = await response.text()
                domain_type = self._get_domain_type(url)
                
                # Выбираем методы парсинга в зависимости от типа домена
                extraction_methods = []
                
                if domain_type == 'news':
                    extraction_methods = [
                        self.extract_with_newspaper,
                        self.extract_with_trafilatura,
                        self.extract_with_readability
                    ]
                elif domain_type == 'blog':
                    extraction_methods = [
                        self.extract_with_trafilatura,
                        self.extract_with_newspaper,
                        self.extract_with_justext
                    ]
                elif domain_type == 'wikipedia':
                    extraction_methods = [
                        self.extract_with_trafilatura,
                        self.extract_with_bs4
                    ]
                else:
                    extraction_methods = [
                        self.extract_with_trafilatura,
                        self.extract_with_newspaper,
                        self.extract_with_readability,
                        self.extract_with_justext,
                        self.extract_with_bs4
                    ]
                
                # Пробуем все методы
                extracted_contents = []
                for method in extraction_methods:
                    try:
                        content = await method(html, url)
                        if content:
                            extracted_contents.append(content)
                    except Exception as e:
                        logger.debug(f"Method {method.__name__} failed: {e}")
                
                if not extracted_contents:
                    logger.warning(f"No content extracted from {url}")
                    return None
                
                # Выбираем лучший результат
                best_content = None
                best_score = 0.0
                
                for content in extracted_contents:
                    relevance = self.calculate_relevance_score(content, query)
                    content.relevance_score = relevance
                    
                    if relevance > best_score and self.filter_content(content, query):
                        best_score = relevance
                        best_content = content
                
                if best_content:
                    logger.info(f"✅ Extracted {best_content.word_count} words from {url} (relevance: {best_score:.2f})")
                    return best_content
                else:
                    logger.warning(f"No suitable content found for {url}")
                    return None
                
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    async def close(self):
        """Закрытие сессии"""
        if self.session and not self.session.closed:
            await self.session.close()

# Глобальный экземпляр
extractor = None

async def get_extractor() -> ImprovedContentExtractor:
    """Получение глобального экземпляра экстрактора"""
    global extractor
    if extractor is None:
        extractor = ImprovedContentExtractor()
    return extractor

async def main():
    """Тестирование экстрактора"""
    extractor = await get_extractor()
    
    test_urls = [
        "https://www.rbc.ru/technology_and_media/15/07/2025/65b123a29a794767a69a45a3",
        "https://ria.ru/20250715/novosti-1951234567.html",
        "https://www.interfax.ru/russia/123456"
    ]
    
    query = "новости за сегодня"
    
    for url in test_urls:
        print(f"\n🔍 Testing: {url}")
        content = await extractor.extract_content(url, query)
        
        if content:
            print(f"✅ Extracted: {content.word_count} words")
            print(f"📝 Method: {content.extraction_method}")
            print(f"🎯 Relevance: {content.relevance_score:.2f}")
            print(f"📄 Preview: {content.text[:200]}...")
        else:
            print("❌ Failed to extract content")
    
    await extractor.close()

if __name__ == "__main__":
    asyncio.run(main()) 