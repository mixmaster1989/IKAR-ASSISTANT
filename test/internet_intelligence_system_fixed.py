#!/usr/bin/env python3
"""
🌐 РЕВОЛЮЦИОННАЯ СИСТЕМА ИНТЕРНЕТ-ИНТЕЛЛЕКТА ДЛЯ IKAR (ИСПРАВЛЕННАЯ)
Автономный поиск, парсинг и обработка информации из интернета
"""

import asyncio
import aiohttp
import json
import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote_plus
from dataclasses import dataclass
import hashlib
import sqlite3
from pathlib import Path
import feedparser
from bs4 import BeautifulSoup
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Результат поиска"""
    title: str
    url: str
    snippet: str
    source: str
    relevance_score: float
    timestamp: datetime
    content: Optional[str] = None
    processed_content: Optional[str] = None

@dataclass
class ProcessedInformation:
    """Обработанная информация"""
    original_query: str
    search_results: List[SearchResult]
    ai_summary: str
    key_points: List[str]
    sources: List[str]
    confidence_score: float
    timestamp: datetime
    processing_time: float

class InternetIntelligenceSystem:
    """Революционная система интернет-интеллекта (исправленная)"""
    
    def __init__(self, openrouter_api_key: str = None):
        self.openrouter_api_key = openrouter_api_key or os.environ.get("OPENROUTER_API_KEY")
        self.session = None
        self.db_path = Path("data/internet_intelligence.db")
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
        
        # Конфигурация поисковых движков
        self.search_engines = {
            "google": {
                "enabled": True,
                "weight": 0.4,
                "max_results": 10
            },
            "bing": {
                "enabled": True,
                "weight": 0.3,
                "max_results": 8
            },
            "duckduckgo": {
                "enabled": True,
                "weight": 0.2,
                "max_results": 6
            },
            "news": {
                "enabled": True,
                "weight": 0.1,
                "max_results": 4
            }
        }
        
        # Источники новостей
        self.news_sources = [
            "https://rss.cnn.com/rss/edition.rss",
            "https://feeds.bbci.co.uk/news/rss.xml",
            "https://www.reuters.com/tools/rss",
            "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            "https://feeds.feedburner.com/TechCrunch/",
            "https://www.wired.com/feed/rss",
            "https://feeds.arstechnica.com/arstechnica/index",
            "https://www.theverge.com/rss/index.xml"
        ]
        
        # Кэш результатов
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
    
    def _init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для кэширования поисковых результатов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                query_hash TEXT PRIMARY KEY,
                query_text TEXT,
                results TEXT,
                timestamp REAL,
                expires_at REAL
            )
        ''')
        
        # Таблица для истории запросов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                results_count INTEGER,
                processing_time REAL,
                confidence_score REAL,
                timestamp REAL
            )
        ''')
        
        # Таблица для источников информации
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS information_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                domain TEXT,
                reliability_score REAL,
                last_accessed REAL,
                access_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение HTTP сессии"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
        return self.session
    
    async def _search_google(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Поиск через Google (используем публичные API)"""
        try:
            session = await self._get_session()
            
            # Используем Google Custom Search API или альтернативные методы
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
            
            async with session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    for result in soup.select('.g'):
                        try:
                            title_elem = result.select_one('h3')
                            link_elem = result.select_one('a')
                            snippet_elem = result.select_one('.VwiC3b')
                            
                            if title_elem and link_elem:
                                title = title_elem.get_text()
                                url = link_elem.get('href', '')
                                snippet = snippet_elem.get_text() if snippet_elem else ""
                                
                                # Очищаем URL
                                if url.startswith('/url?q='):
                                    url = url.split('/url?q=')[1].split('&')[0]
                                
                                results.append(SearchResult(
                                    title=title,
                                    url=url,
                                    snippet=snippet,
                                    source="google",
                                    relevance_score=0.8,
                                    timestamp=datetime.now()
                                ))
                        except Exception as e:
                            logger.warning(f"Ошибка парсинга Google результата: {e}")
                    
                    return results[:max_results]
                else:
                    logger.warning(f"Google поиск вернул статус {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Ошибка Google поиска: {e}")
            return []
    
    async def _search_bing(self, query: str, max_results: int = 8) -> List[SearchResult]:
        """Поиск через Bing"""
        try:
            session = await self._get_session()
            
            # Используем Bing Web Search API или альтернативные методы
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
            
            async with session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    for result in soup.select('.b_algo'):
                        try:
                            title_elem = result.select_one('h2 a')
                            snippet_elem = result.select_one('.b_caption p')
                            
                            if title_elem:
                                title = title_elem.get_text()
                                url = title_elem.get('href', '')
                                snippet = snippet_elem.get_text() if snippet_elem else ""
                                
                                results.append(SearchResult(
                                    title=title,
                                    url=url,
                                    snippet=snippet,
                                    source="bing",
                                    relevance_score=0.7,
                                    timestamp=datetime.now()
                                ))
                        except Exception as e:
                            logger.warning(f"Ошибка парсинга Bing результата: {e}")
                    
                    return results[:max_results]
                else:
                    logger.warning(f"Bing поиск вернул статус {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Ошибка Bing поиска: {e}")
            return []
    
    async def _search_duckduckgo(self, query: str, max_results: int = 6) -> List[SearchResult]:
        """Поиск через DuckDuckGo"""
        try:
            session = await self._get_session()
            
            # DuckDuckGo Instant Answer API
            search_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            
            async with session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    
                    # Добавляем Instant Answer если есть
                    if data.get('Abstract'):
                        results.append(SearchResult(
                            title=data.get('Heading', 'DuckDuckGo Answer'),
                            url=data.get('AbstractURL', ''),
                            snippet=data.get('Abstract', ''),
                            source="duckduckgo",
                            relevance_score=0.9,
                            timestamp=datetime.now()
                        ))
                    
                    # Добавляем Related Topics
                    for topic in data.get('RelatedTopics', [])[:max_results-1]:
                        if isinstance(topic, dict) and topic.get('Text'):
                            results.append(SearchResult(
                                title=topic.get('FirstURL', '').split('/')[-1] or 'Related Topic',
                                url=topic.get('FirstURL', ''),
                                snippet=topic.get('Text', ''),
                                source="duckduckgo",
                                relevance_score=0.6,
                                timestamp=datetime.now()
                            ))
                    
                    return results[:max_results]
                else:
                    logger.warning(f"DuckDuckGo поиск вернул статус {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Ошибка DuckDuckGo поиска: {e}")
            return []
    
    async def _search_news(self, query: str, max_results: int = 4) -> List[SearchResult]:
        """Поиск новостей через RSS"""
        try:
            session = await self._get_session()
            results = []
            
            for rss_url in self.news_sources[:3]:  # Ограничиваем количество источников
                try:
                    async with session.get(rss_url) as response:
                        if response.status == 200:
                            content = await response.text()
                            feed = feedparser.parse(content)
                            
                            for entry in feed.entries[:max_results//len(self.news_sources[:3])]:
                                # Проверяем релевантность
                                if self._is_relevant(entry.title + " " + entry.get('summary', ''), query):
                                    results.append(SearchResult(
                                        title=entry.title,
                                        url=entry.link,
                                        snippet=entry.get('summary', '')[:200],
                                        source="news",
                                        relevance_score=0.8,
                                        timestamp=datetime.now()
                                    ))
                except Exception as e:
                    logger.warning(f"Ошибка RSS {rss_url}: {e}")
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Ошибка поиска новостей: {e}")
            return []
    
    def _is_relevant(self, text: str, query: str) -> bool:
        """Проверка релевантности текста запросу"""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        # Простая проверка по ключевым словам
        common_words = query_words.intersection(text_words)
        return len(common_words) >= len(query_words) * 0.3
    
    async def search_internet(self, query: str, max_total_results: int = 20) -> List[SearchResult]:
        """Комплексный поиск по интернету"""
        logger.info(f"🔍 Начинаем поиск: '{query}'")
        
        # Проверяем кэш
        cache_key = hashlib.md5(query.encode()).hexdigest()
        cached_results = await self._get_cached_results(cache_key)
        if cached_results:
            logger.info("✅ Используем кэшированные результаты")
            return cached_results
        
        all_results = []
        
        # Параллельный поиск по всем движкам
        search_tasks = []
        
        if self.search_engines["google"]["enabled"]:
            search_tasks.append(self._search_google(query, self.search_engines["google"]["max_results"]))
        
        if self.search_engines["bing"]["enabled"]:
            search_tasks.append(self._search_bing(query, self.search_engines["bing"]["max_results"]))
        
        if self.search_engines["duckduckgo"]["enabled"]:
            search_tasks.append(self._search_duckduckgo(query, self.search_engines["duckduckgo"]["max_results"]))
        
        if self.search_engines["news"]["enabled"]:
            search_tasks.append(self._search_news(query, self.search_engines["news"]["max_results"]))
        
        # Выполняем поиск параллельно
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Объединяем результаты
        for results in search_results:
            if isinstance(results, list):
                all_results.extend(results)
            else:
                logger.warning(f"Ошибка поиска: {results}")
        
        # Удаляем дубликаты и сортируем по релевантности
        unique_results = self._deduplicate_results(all_results)
        sorted_results = sorted(unique_results, key=lambda x: x.relevance_score, reverse=True)
        
        # Ограничиваем количество результатов
        final_results = sorted_results[:max_total_results]
        
        # Кэшируем результаты
        await self._cache_results(cache_key, query, final_results)
        
        logger.info(f"✅ Найдено {len(final_results)} результатов")
        return final_results
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Удаление дубликатов результатов"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results
    
    async def _get_cached_results(self, cache_key: str) -> Optional[List[SearchResult]]:
        """Получение кэшированных результатов"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT results, expires_at FROM search_cache 
                WHERE query_hash = ? AND expires_at > ?
            ''', (cache_key, time.time()))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                results_data = json.loads(row[0])
                return [SearchResult(**result) for result in results_data]
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения кэша: {e}")
            return None
    
    async def _cache_results(self, cache_key: str, query: str, results: List[SearchResult]):
        """Кэширование результатов"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            results_data = [result.__dict__ for result in results]
            expires_at = time.time() + self.cache_duration.total_seconds()
            
            cursor.execute('''
                INSERT OR REPLACE INTO search_cache 
                (query_hash, query_text, results, timestamp, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (cache_key, query, json.dumps(results_data), time.time(), expires_at))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка кэширования: {e}")
    
    async def extract_content(self, search_results: List[SearchResult]) -> List[SearchResult]:
        """Извлечение полного контента с веб-страниц (упрощенная версия)"""
        logger.info(f"📄 Извлекаем контент с {len(search_results)} страниц")
        
        async def extract_single(result: SearchResult) -> SearchResult:
            try:
                session = await self._get_session()
                
                async with session.get(result.url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Упрощенное извлечение контента с BeautifulSoup
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Удаляем скрипты и стили
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Извлекаем текст
                        text = soup.get_text()
                        
                        # Очищаем текст
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        if text:
                            result.content = text[:3000]  # Ограничиваем размер
                        else:
                            result.content = result.snippet
                    else:
                        result.content = result.snippet
                        
            except Exception as e:
                logger.warning(f"Ошибка извлечения контента с {result.url}: {e}")
                result.content = result.snippet
            
            return result
        
        # Извлекаем контент параллельно
        tasks = [extract_single(result) for result in search_results]
        results_with_content = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем ошибки
        valid_results = []
        for result in results_with_content:
            if isinstance(result, SearchResult):
                valid_results.append(result)
            else:
                logger.warning(f"Ошибка извлечения контента: {result}")
        
        logger.info(f"✅ Извлечен контент с {len(valid_results)} страниц")
        return valid_results
    
    async def process_with_ai(self, query: str, search_results: List[SearchResult]) -> ProcessedInformation:
        """Обработка информации через AI"""
        logger.info("🧠 Обрабатываем информацию через AI")
        
        start_time = time.time()
        
        # Подготавливаем данные для AI
        combined_content = f"Запрос: {query}\n\n"
        
        for i, result in enumerate(search_results[:10], 1):  # Ограничиваем количество
            if result.content:
                combined_content += f"Источник {i} ({result.source}):\n"
                combined_content += f"Заголовок: {result.title}\n"
                combined_content += f"URL: {result.url}\n"
                combined_content += f"Контент: {result.content[:1000]}\n\n"
        
        # Генерируем AI-выжимку
        ai_summary = await self._generate_ai_summary(query, combined_content)
        
        # Извлекаем ключевые моменты
        key_points = await self._extract_key_points(ai_summary)
        
        # Рассчитываем уверенность
        confidence_score = self._calculate_confidence(search_results, ai_summary)
        
        processing_time = time.time() - start_time
        
        return ProcessedInformation(
            original_query=query,
            search_results=search_results,
            ai_summary=ai_summary,
            key_points=key_points,
            sources=[result.url for result in search_results],
            confidence_score=confidence_score,
            timestamp=datetime.now(),
            processing_time=processing_time
        )
    
    async def _generate_ai_summary(self, query: str, content: str) -> str:
        """Генерация AI-выжимки через OpenRouter"""
        try:
            if not self.openrouter_api_key:
                # Fallback на простую обработку
                return self._simple_summary(content)
            
            # Используем OpenRouter для генерации выжимки
            prompt = f"""
            Запрос пользователя: {query}
            
            Информация из интернета:
            {content[:4000]}
            
            Создай краткую, но информативную выжимку на основе этой информации. 
            Ответ должен быть структурированным и содержать только факты.
            """
            
            # Здесь будет вызов OpenRouter API
            # Пока используем заглушку
            return self._simple_summary(content)
            
        except Exception as e:
            logger.error(f"Ошибка AI обработки: {e}")
            return self._simple_summary(content)
    
    def _simple_summary(self, content: str) -> str:
        """Простая обработка без AI"""
        # Извлекаем ключевые предложения
        sentences = re.split(r'[.!?]+', content)
        important_sentences = []
        
        keywords = ['новости', 'обновление', 'изменения', 'результаты', 'данные', 'статистика']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                important_sentences.append(sentence.strip())
        
        if important_sentences:
            return '. '.join(important_sentences[:5]) + '.'
        else:
            return content[:500] + '...'
    
    async def _extract_key_points(self, summary: str) -> List[str]:
        """Извлечение ключевых моментов"""
        # Простое извлечение ключевых моментов
        sentences = re.split(r'[.!?]+', summary)
        return [s.strip() for s in sentences if len(s.strip()) > 20][:5]
    
    def _calculate_confidence(self, results: List[SearchResult], summary: str) -> float:
        """Расчет уверенности в результатах"""
        if not results:
            return 0.0
        
        # Средняя релевантность результатов
        avg_relevance = sum(r.relevance_score for r in results) / len(results)
        
        # Количество источников
        source_diversity = min(len(set(r.source for r in results)) / 4, 1.0)
        
        # Качество контента
        content_quality = sum(1 for r in results if r.content and len(r.content) > 100) / len(results)
        
        # Длина выжимки
        summary_quality = min(len(summary) / 500, 1.0)
        
        confidence = (avg_relevance * 0.4 + source_diversity * 0.2 + 
                     content_quality * 0.2 + summary_quality * 0.2)
        
        return min(confidence, 1.0)
    
    async def get_internet_intelligence(self, query: str) -> ProcessedInformation:
        """Основная функция получения интернет-интеллекта"""
        logger.info(f"🌐 Запуск интернет-интеллекта для запроса: '{query}'")
        
        # 1. Поиск в интернете
        search_results = await self.search_internet(query)
        
        if not search_results:
            logger.warning("❌ Не найдено результатов поиска")
            return ProcessedInformation(
                original_query=query,
                search_results=[],
                ai_summary="Информация не найдена в интернете.",
                key_points=[],
                sources=[],
                confidence_score=0.0,
                timestamp=datetime.now(),
                processing_time=0.0
            )
        
        # 2. Извлечение контента
        results_with_content = await self.extract_content(search_results)
        
        # 3. AI обработка
        processed_info = await self.process_with_ai(query, results_with_content)
        
        # 4. Сохраняем в историю
        await self._save_to_history(processed_info)
        
        logger.info(f"✅ Интернет-интеллект завершен. Уверенность: {processed_info.confidence_score:.2f}")
        
        return processed_info
    
    async def _save_to_history(self, processed_info: ProcessedInformation):
        """Сохранение в историю"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO search_history 
                (query, results_count, processing_time, confidence_score, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                processed_info.original_query,
                len(processed_info.search_results),
                processed_info.processing_time,
                processed_info.confidence_score,
                time.time()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения в историю: {e}")
    
    async def close(self):
        """Закрытие системы"""
        if self.session and not self.session.closed:
            await self.session.close()

# Глобальный экземпляр системы
internet_system = None

async def get_internet_system() -> InternetIntelligenceSystem:
    """Получение глобального экземпляра системы"""
    global internet_system
    if internet_system is None:
        internet_system = InternetIntelligenceSystem()
    return internet_system

async def main():
    """Тестирование системы"""
    system = await get_internet_system()
    
    # Тестовый запрос
    query = "последние новости о развитии искусственного интеллекта"
    
    print(f"🧠 Тестируем интернет-интеллект: '{query}'")
    
    try:
        result = await system.get_internet_intelligence(query)
        
        print(f"\n📊 РЕЗУЛЬТАТЫ:")
        print(f"Запрос: {result.original_query}")
        print(f"Найдено источников: {len(result.search_results)}")
        print(f"Время обработки: {result.processing_time:.2f}с")
        print(f"Уверенность: {result.confidence_score:.2f}")
        
        print(f"\n🧠 AI-ВЫЖИМКА:")
        print(result.ai_summary)
        
        print(f"\n🔑 КЛЮЧЕВЫЕ МОМЕНТЫ:")
        for i, point in enumerate(result.key_points, 1):
            print(f"{i}. {point}")
        
        print(f"\n📚 ИСТОЧНИКИ:")
        for i, source in enumerate(result.sources[:5], 1):
            print(f"{i}. {source}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await system.close()

if __name__ == "__main__":
    asyncio.run(main()) 