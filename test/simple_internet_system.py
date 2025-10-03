#!/usr/bin/env python3
"""
🌐 ПРОСТАЯ И РАБОЧАЯ СИСТЕМА ИНТЕРНЕТ-ИНТЕЛЛЕКТА
Базовая система поиска и извлечения информации из интернета
"""

import requests
import re
import logging
from typing import Dict, List, Optional
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup
import time
import json
import random

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleInternetSystem:
    """Простая система интернет-поиска и обработки"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def clean_query(self, query: str) -> str:
        """Очистка поискового запроса"""
        # Убираем "бот" и связанные слова
        query = re.sub(r'\bбот\b', '', query, flags=re.IGNORECASE)
        query = re.sub(r'\bботу\b', '', query, flags=re.IGNORECASE)
        query = re.sub(r'\bботом\b', '', query, flags=re.IGNORECASE)
        
        # Убираем лишние символы и слова
        query = re.sub(r'[^\w\sа-яё-]', ' ', query, flags=re.IGNORECASE)
        query = re.sub(r'\s+', ' ', query).strip()
        
        # Если запрос пустой, используем дефолтный
        if not query or len(query) < 3:
            query = "последние новости"
        
        logger.info(f"Очищенный запрос: '{query}'")
        return query
    
    def search_duckduckgo(self, query: str) -> List[Dict]:
        """Поиск через DuckDuckGo API"""
        try:
            search_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            
            logger.info(f"DuckDuckGo поиск: {query}")
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Добавляем основной результат
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', 'Результат поиска'),
                    'url': data.get('AbstractURL', ''),
                    'snippet': data.get('Abstract', ''),
                    'source': 'DuckDuckGo'
                })
            
            # Добавляем связанные темы
            for topic in data.get('RelatedTopics', [])[:8]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'title': topic.get('Text', '')[:100],
                        'url': topic.get('FirstURL', ''),
                        'snippet': topic.get('Text', ''),
                        'source': 'DuckDuckGo'
                    })
            
            logger.info(f"DuckDuckGo найдено {len(results)} результатов")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка DuckDuckGo поиска: {e}")
            return []
    
    def search_bing(self, query: str) -> List[Dict]:
        """Поиск через Bing (используем простой парсинг)"""
        try:
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
            
            logger.info(f"Bing поиск: {query}")
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Ищем результаты поиска Bing
            search_results = soup.find_all('li', class_='b_algo')
            
            for result in search_results[:8]:
                try:
                    # Ищем заголовок
                    title_elem = result.find('h2')
                    if not title_elem:
                        continue
                    
                    # Ищем ссылку
                    link_elem = title_elem.find('a')
                    if not link_elem:
                        continue
                    
                    # Ищем сниппет
                    snippet_elem = result.find('p')
                    
                    title = title_elem.get_text().strip()
                    url = link_elem.get('href', '')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ''
                    
                    if url and not url.startswith('/'):
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'source': 'Bing'
                        })
                
                except Exception as e:
                    continue
            
            logger.info(f"Bing найдено {len(results)} результатов")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка Bing поиска: {e}")
            return []
    
    def search_google(self, query: str) -> List[Dict]:
        """Поиск через Google (с улучшенным парсингом)"""
        try:
            # Используем разные User-Agent для обхода блокировки
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]
            
            self.session.headers['User-Agent'] = random.choice(user_agents)
            
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num=10"
            
            logger.info(f"Google поиск: {query}")
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Ищем результаты поиска
            search_results = soup.find_all('div', class_='g')
            
            for result in search_results[:8]:
                try:
                    # Ищем заголовок
                    title_elem = result.find('h3')
                    if not title_elem:
                        continue
                    
                    # Ищем ссылку
                    link_elem = result.find('a')
                    if not link_elem:
                        continue
                    
                    # Ищем сниппет
                    snippet_elem = result.find('div', class_='VwiC3b')
                    if not snippet_elem:
                        snippet_elem = result.find('span', class_='aCOpRe')
                    
                    title = title_elem.get_text().strip()
                    url = link_elem.get('href', '')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ''
                    
                    # Проверяем, что это не внутренняя ссылка Google
                    if url and not url.startswith('/') and 'google.com' not in url:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'source': 'Google'
                        })
                
                except Exception as e:
                    continue
            
            # Если не нашли результаты через стандартный парсинг, пробуем альтернативный метод
            if not results:
                logger.info("Стандартный парсинг не дал результатов, пробуем альтернативный метод")
                results = self._alternative_search_parsing(soup, query)
            
            logger.info(f"Google найдено {len(results)} результатов")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка Google поиска: {e}")
            return []
    
    def _alternative_search_parsing(self, soup: BeautifulSoup, query: str) -> List[Dict]:
        """Альтернативный метод парсинга результатов поиска"""
        results = []
        
        try:
            # Ищем все ссылки с заголовками
            links = soup.find_all('a')
            
            for link in links:
                try:
                    # Проверяем, что это результат поиска
                    if link.get('href', '').startswith('http') and 'google.com' not in link.get('href', ''):
                        title = link.get_text().strip()
                        
                        # Проверяем, что заголовок не пустой и не слишком короткий
                        if len(title) > 10 and len(title) < 200:
                            url = link.get('href')
                            
                            # Ищем сниппет рядом с ссылкой
                            snippet = ""
                            parent = link.parent
                            if parent:
                                text_elements = parent.find_all(text=True)
                                for text in text_elements:
                                    if text.strip() and text.strip() != title:
                                        snippet = text.strip()[:200]
                                        break
                            
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet,
                                'source': 'Google'
                            })
                            
                            if len(results) >= 8:  # Ограничиваем количество результатов
                                break
                
                except Exception as e:
                    continue
            
        except Exception as e:
            logger.error(f"Ошибка альтернативного парсинга: {e}")
        
        return results
    
    def search_internet_multi(self, query: str) -> List[Dict]:
        """Мультипоиск через несколько движков"""
        all_results = []
        
        # Пробуем разные поисковые движки
        search_methods = [
            ('DuckDuckGo', self.search_duckduckgo),
            ('Bing', self.search_bing),
            ('Google', self.search_google)
        ]
        
        for engine_name, search_func in search_methods:
            try:
                logger.info(f"Пробуем {engine_name}")
                results = search_func(query)
                if results:
                    all_results.extend(results)
                    logger.info(f"{engine_name} дал {len(results)} результатов")
                    # Если получили достаточно результатов, останавливаемся
                    if len(all_results) >= 8:
                        break
                time.sleep(1)  # Небольшая пауза между запросами
            except Exception as e:
                logger.error(f"Ошибка {engine_name}: {e}")
                continue
        
        # Убираем дубликаты
        unique_results = []
        seen_urls = set()
        
        for result in all_results:
            if result['url'] not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result['url'])
        
        # Для погодных запросов приоритизируем погодные сайты
        if any(word in query.lower() for word in ['погода', 'температура', 'градус']):
            weather_sites = [
                'gismeteo.ru', 'yandex.ru/pogoda', 'weather.com', 'accuweather.com', 'rp5.ru',
                'meteoinfo.ru', 'pogoda.ru', 'weather.yandex.ru', 'meteoweb.ru', 'meteo-tv.ru',
                'weather-forecast.com', 'worldweather.org', 'meteo.gov.ua', 'meteo.ua'
            ]
            weather_results = []
            other_results = []
            
            for result in unique_results:
                url = result['url'].lower()
                if any(site in url for site in weather_sites):
                    weather_results.append(result)
                else:
                    other_results.append(result)
            
            # Сначала погодные сайты, потом остальные
            unique_results = weather_results + other_results
        
        logger.info(f"Всего найдено {len(unique_results)} уникальных результатов")
        return unique_results[:8]  # Возвращаем максимум 8 результатов
    
    def search_weather(self, query: str) -> Optional[Dict]:
        """Специальный поиск погоды"""
        # Извлекаем город из запроса
        city_match = re.search(r'погод[аеу]?\s+(?:в\s+)?([а-яё\s-]+)', query, re.IGNORECASE)
        if not city_match:
            city_match = re.search(r'температур[аеу]?\s+(?:в\s+)?([а-яё\s-]+)', query, re.IGNORECASE)
        
        if city_match:
            city = city_match.group(1).strip()
        else:
            city = "Москва"  # По умолчанию
        
        # Исправляем названия городов и добавляем регионы
        city_fixes = {
            "ростове": "Ростов-на-Дону",
            "ростов": "Ростов-на-Дону", 
            "шахт": "Шахты",
            "шахтах": "Шахты",
            "москве": "Москва",
            "москва": "Москва",
            "спб": "Санкт-Петербург",
            "питер": "Санкт-Петербург",
            "екатеринбург": "Екатеринбург",
            "новосибирск": "Новосибирск",
            "казань": "Казань",
            "нижний": "Нижний Новгород",
            "самара": "Самара",
            "омск": "Омск",
            "челябинск": "Челябинск",
            "уфа": "Уфа",
            "волгоград": "Волгоград",
            "пермь": "Пермь",
            "красноярск": "Красноярск",
            "воронеж": "Воронеж",
            "саратов": "Саратов",
            "краснодар": "Краснодар",
            "тольятти": "Тольятти",
            "ижевск": "Ижевск",
            "барнаул": "Барнаул",
            "ульяновск": "Ульяновск",
            "иркутск": "Иркутск",
            "хабаровск": "Хабаровск",
            "ярославль": "Ярославль",
            "владивосток": "Владивосток",
            "махачкала": "Махачкала",
            "томск": "Томск",
            "оренбург": "Оренбург",
            "кемерово": "Кемерово",
            "новокузнецк": "Новокузнецк",
            "рязань": "Рязань",
            "астрахань": "Астрахань",
            "пенза": "Пенза",
            "липецк": "Липецк",
            "киров": "Киров",
            "чебоксары": "Чебоксары",
            "тула": "Тула",
            "калининград": "Калининград",
            "курск": "Курск",
            "улан-удэ": "Улан-Удэ",
            "ставрополь": "Ставрополь",
            "сочи": "Сочи",
            "иваново": "Иваново",
            "брянск": "Брянск",
            "белгород": "Белгород",
            "архангельск": "Архангельск",
            "владимир": "Владимир",
            "севастополь": "Севастополь",
            "чита": "Чита",
            "грозный": "Грозный",
            "калуга": "Калуга",
            "смоленск": "Смоленск",
            "вологда": "Вологда",
            "курган": "Курган",
            "орёл": "Орёл",
            "саранск": "Саранск",
            "владикавказ": "Владикавказ",
            "мурманск": "Мурманск",
            "якутск": "Якутск",
            "петрозаводск": "Петрозаводск",
            "симферополь": "Симферополь"
        }
        
        city_lower = city.lower()
        if city_lower in city_fixes:
            city = city_fixes[city_lower]
        
        logger.info(f"Поиск погоды для города: {city}")
        
        try:
            # Используем несколько вариантов поиска для лучших результатов
            weather_queries = [
                f"погода {city} сейчас температура градусы",
                f"погода {city} сегодня сейчас",
                f"{city} погода сейчас градусы температура",
                f"температура воздуха {city} сейчас градусы",
                f"погода {city} Ростовская область",
                f"{city} погода сейчас точная температура",
                f"прогноз погоды {city} сейчас",
                f"погода {city} градусы сейчас",
                f"температура {city} сейчас точная",
                f"погода {city} сейчас градусы цельсия",
                f"{city} температура воздуха сейчас",
                f"погода {city} сейчас влажность ветер"
            ]
            
            # Добавляем специальные запросы для конкретных городов
            if city == "Шахты":
                weather_queries.extend([
                    "погода Шахты Ростовская область сейчас",
                    "температура Шахты сейчас градусы",
                    "погода Шахты сейчас точная температура",
                    "Шахты погода сейчас градусы цельсия"
                ])
            elif city == "Ростов-на-Дону":
                weather_queries.extend([
                    "погода Ростов-на-Дону сейчас температура",
                    "температура Ростов-на-Дону сейчас градусы",
                    "погода Ростов-на-Дону сейчас точная",
                    "Ростов-на-Дону погода сейчас градусы"
                ])
            
            all_results = []
            for weather_query in weather_queries:
                results = self.search_internet_multi(weather_query)
                all_results.extend(results)
                if len(all_results) >= 8:  # Ограничиваем общее количество
                    break
            
            if all_results:
                # Берем первые 6-8 результатов для более полной информации
                weather_data = []
                
                # Добавляем прямые ссылки на погодные сайты для конкретного города
                direct_weather_urls = [
                    f"https://www.gismeteo.ru/search/{city}/",
                    f"https://yandex.ru/pogoda/{city}",
                    f"https://pogoda.ru/{city}",
                    f"https://rp5.ru/Погода_в_{city}"
                ]
                
                # Пытаемся получить данные с прямых ссылок
                for url in direct_weather_urls:
                    try:
                        response = self.session.get(url, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            text = soup.get_text()
                            content = text[:1000] if len(text) > 1000 else text
                            
                            weather_data.append({
                                'title': f"Прямая ссылка: {url}",
                                'url': url,
                                'content': content,
                                'snippet': f"Прямые данные о погоде в {city}",
                                'source': 'Direct'
                            })
                            break  # Берем только первый успешный
                    except Exception as e:
                        logger.error(f"Ошибка прямой ссылки {url}: {e}")
                        continue
                
                # Добавляем результаты поиска
                for result in all_results[:6]:
                    try:
                        response = self.session.get(result['url'], timeout=10)
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Извлекаем весь текст страницы (без агрессивной очистки)
                        text = soup.get_text()
                        
                        # Берем первые 1000 символов текста
                        content = text[:1000] if len(text) > 1000 else text
                        
                        weather_data.append({
                            'title': result['title'],
                            'url': result['url'],
                            'content': content,
                            'snippet': result.get('snippet', ''),
                            'source': result['source']
                        })
                        
                    except Exception as e:
                        logger.error(f"Ошибка получения контента: {e}")
                        # Добавляем базовую информацию
                        weather_data.append({
                            'title': result['title'],
                            'url': result['url'],
                            'content': result.get('snippet', ''),
                            'snippet': result.get('snippet', ''),
                            'source': result['source']
                        })
                
                return {
                    "city": city,
                    "sources": weather_data,
                    "summary": f"Информация о погоде в {city} найдена в {len(weather_data)} источниках"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка поиска погоды: {e}")
            return None
    
    def search_news(self, query: str) -> List[Dict]:
        """Поиск новостей"""
        try:
            # Добавляем "новости" к запросу если его нет
            if "новости" not in query.lower():
                query = f"новости {query}"
            
            logger.info(f"Поиск новостей: {query}")
            results = self.search_internet_multi(query)
            
            news_results = []
            for result in results[:8]:  # Берем больше результатов
                try:
                    # Пытаемся получить контент новости
                    response = self.session.get(result['url'], timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Извлекаем весь текст страницы (без агрессивной очистки)
                    text = soup.get_text()
                    
                    # Берем первые 800 символов текста
                    content = text[:800] if len(text) > 800 else text
                    
                    news_results.append({
                        'title': result['title'],
                        'url': result['url'],
                        'content': content,
                        'snippet': result.get('snippet', ''),
                        'source': result['source']
                    })
                    
                except Exception as e:
                    logger.error(f"Ошибка получения новости: {e}")
                    # Добавляем базовую информацию
                    news_results.append({
                        'title': result['title'],
                        'url': result['url'],
                        'content': result.get('snippet', ''),
                        'snippet': result.get('snippet', ''),
                        'source': result['source']
                    })
            
            return news_results
            
        except Exception as e:
            logger.error(f"Ошибка поиска новостей: {e}")
            return []
    
    def search_general(self, query: str) -> Dict:
        """Общий поиск информации"""
        try:
            logger.info(f"Общий поиск: {query}")
            results = self.search_internet_multi(query)
            
            if not results:
                return {
                    "found": False,
                    "summary": "Информация не найдена",
                    "sources": []
                }
            
            # Собираем всю информацию из результатов
            all_content = []
            sources = []
            
            for result in results[:8]:  # Берем больше результатов
                try:
                    # Пытаемся получить контент страницы
                    response = self.session.get(result['url'], timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Извлекаем весь текст страницы
                    text = soup.get_text()
                    
                    # Берем первые 600 символов текста
                    content = text[:600] if len(text) > 600 else text
                    
                    all_content.append(f"Источник: {result['title']}\n{content}")
                    sources.append(result['url'])
                    
                except Exception as e:
                    logger.error(f"Ошибка получения контента: {e}")
                    # Добавляем сниппет
                    all_content.append(f"Источник: {result['title']}\n{result.get('snippet', '')}")
                    sources.append(result['url'])
            
            combined_content = '\n\n'.join(all_content)
            
            return {
                "found": True,
                "content": combined_content,
                "sources": sources,
                "results_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Ошибка общего поиска: {e}")
            return {
                "found": False,
                "content": "Ошибка поиска информации",
                "sources": []
            }
    
    def detect_query_type(self, query: str) -> str:
        """Определение типа запроса"""
        query_lower = query.lower()
        
        # Погода
        if any(word in query_lower for word in ['погода', 'температура', 'градус', 'холодно', 'жарко']):
            return 'weather'
        
        # Новости - расширенный список ключевых слов
        news_keywords = [
            'новости', 'новость', 'новостей', 'происходит', 'случилось', 'событие',
            'актуальные', 'сегодня', 'интернете', 'что нового', 'что происходит',
            'последние', 'свежие', 'главные'
        ]
        if any(word in query_lower for word in news_keywords):
            return 'news'
        
        # Общий поиск
        return 'general'
    
    def search_internet(self, query: str) -> Dict:
        """Основная функция поиска в интернете"""
        try:
            # Очищаем запрос
            clean_query = self.clean_query(query)
            
            # Определяем тип запроса
            query_type = self.detect_query_type(clean_query)
            
            logger.info(f"Тип запроса: {query_type}")
            
            if query_type == 'weather':
                result = self.search_weather(clean_query)
                if result:
                    return {
                        "success": True,
                        "type": "weather",
                        "data": result,
                        "query": clean_query
                    }
                else:
                    return {
                        "success": False,
                        "type": "weather",
                        "error": "Информация о погоде не найдена",
                        "query": clean_query
                    }
            
            elif query_type == 'news':
                results = self.search_news(clean_query)
                if results:
                    return {
                        "success": True,
                        "type": "news",
                        "data": results,
                        "query": clean_query
                    }
                else:
                    return {
                        "success": False,
                        "type": "news",
                        "error": "Новости не найдены",
                        "query": clean_query
                    }
            
            else:
                result = self.search_general(clean_query)
                return {
                    "success": result["found"],
                    "type": "general",
                    "data": result,
                    "query": clean_query
                }
                
        except Exception as e:
            logger.error(f"Ошибка поиска в интернете: {e}")
            return {
                "success": False,
                "error": f"Ошибка поиска: {str(e)}",
                "query": query
            }

# Глобальный экземпляр системы
_internet_system = None

def get_internet_system() -> SimpleInternetSystem:
    """Получение глобального экземпляра системы"""
    global _internet_system
    if _internet_system is None:
        _internet_system = SimpleInternetSystem()
    return _internet_system

def search_internet(query: str) -> Dict:
    """Простая функция для поиска в интернете"""
    system = get_internet_system()
    return system.search_internet(query)

# Тестовая функция
if __name__ == "__main__":
    system = SimpleInternetSystem()
    
    # Тест поиска погоды
    print("=== ТЕСТ ПОИСКА ПОГОДЫ ===")
    weather_result = system.search_internet("бот, какая погода в Москве?")
    print(json.dumps(weather_result, indent=2, ensure_ascii=False))
    
    # Тест поиска новостей
    print("\n=== ТЕСТ ПОИСКА НОВОСТЕЙ ===")
    news_result = system.search_internet("бот, какие новости?")
    print(json.dumps(news_result, indent=2, ensure_ascii=False))
    
    # Тест общего поиска
    print("\n=== ТЕСТ ОБЩЕГО ПОИСКА ===")
    general_result = system.search_internet("бот, что такое искусственный интеллект?")
    print(json.dumps(general_result, indent=2, ensure_ascii=False)) 