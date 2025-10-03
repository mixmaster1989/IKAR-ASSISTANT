"""
Модуль для очистки сырых данных из интернета
Преобразует сырые данные в структурированную информацию через LLM
"""

import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DataCleaner:
    """Класс для очистки и структурирования сырых данных"""
    
    def __init__(self):
        # Используем LLM клиент из менеджера
        from utils.component_manager import get_component_manager
        component_manager = get_component_manager()
        self.llm_client = component_manager.get_llm_client()
    
    async def clean_weather_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Очищает сырые данные погоды и извлекает структурированную информацию
        
        Args:
            raw_data: Сырые данные от интернет-системы
            
        Returns:
            Очищенная структурированная информация
        """
        try:
            # Формируем промпт для очистки данных погоды
            sources_text = ""
            if isinstance(raw_data, dict) and raw_data.get('sources'):
                # New format: raw_data has 'city' and 'sources' keys
                city = raw_data.get('city', 'НЕИЗВЕСТНО')
                for i, source in enumerate(raw_data['sources'][:5], 1):  # Берем первые 5 источников
                    sources_text += f"\n--- Источник {i} ---\n"
                    sources_text += f"Заголовок: {source.get('title', 'НЕТ')}\n"
                    sources_text += f"URL: {source.get('url', 'НЕТ')}\n"
                    sources_text += f"Контент: {source.get('content', 'НЕТ КОНТЕНТА')[:1000]}\n"
            elif isinstance(raw_data, dict) and raw_data.get('data', {}).get('sources'):
                # Fallback for old format
                for i, source in enumerate(raw_data['data']['sources'][:5], 1):  # Берем первые 5 источников
                    sources_text += f"\n--- Источник {i} ---\n"
                    sources_text += f"Заголовок: {source.get('title', 'НЕТ')}\n"
                    sources_text += f"URL: {source.get('url', 'НЕТ')}\n"
                    sources_text += f"Контент: {source.get('content', 'НЕТ КОНТЕНТА')[:1000]}\n"
            else:
                logger.warning(f"Неожиданный формат данных погоды: {type(raw_data)}")
                return {"error": f"Неожиданный формат данных: {type(raw_data)}"}
            
            prompt = f"""
Ты - эксперт по извлечению информации о погоде из веб-страниц.

Перед тобой сырые данные с разных сайтов о погоде. Извлеки из них структурированную информацию.

СЫРЫЕ ДАННЫЕ:
{sources_text}

ИНСТРУКЦИИ:
1. Проанализируй все источники
2. Найди актуальную информацию о погоде
3. Извлеки: город, температуру, описание, ветер, влажность, давление
4. Если информация противоречивая, укажи это
5. Если данных недостаточно, укажи "НЕТ ДАННЫХ"

ОТВЕТЬ СТРОГО В ФОРМАТЕ JSON:
{{
    "city": "название города",
    "temperature": "температура с единицами измерения",
    "description": "описание погоды",
    "wind": "информация о ветре",
    "humidity": "влажность",
    "pressure": "давление",
    "source": "основной источник информации",
    "confidence": "уверенность в данных (высокая/средняя/низкая)",
    "notes": "дополнительные заметки или предупреждения"
}}

ВАЖНО: Отвечай только JSON, без дополнительного текста!
"""
            
            # Отправляем запрос к модели
            response = await self.llm_client.chat_completion(
                user_message=prompt,
                system_prompt="",
                temperature=0.1,
                max_tokens=1000
            )
            
            if response and response.get('choices'):
                content = response['choices'][0]['message']['content']
                
                # Пытаемся извлечь JSON из ответа
                try:
                    # Ищем JSON в ответе
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start != -1 and end != 0:
                        json_str = content[start:end]
                        cleaned_data = json.loads(json_str)
                        logger.info(f"✅ Данные погоды очищены: {cleaned_data.get('city', 'НЕИЗВЕСТНО')}")
                        return cleaned_data
                    else:
                        logger.warning("❌ JSON не найден в ответе модели")
                        return {"error": "Не удалось извлечь JSON из ответа"}
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Ошибка парсинга JSON: {e}")
                    logger.error(f"Ответ модели: {content}")
                    return {"error": f"Ошибка парсинга JSON: {e}"}
            else:
                logger.error("❌ Нет ответа от модели")
                return {"error": "Нет ответа от модели"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка очистки данных погоды: {e}")
            return {"error": f"Ошибка обработки: {e}"}
    
    async def clean_news_data(self, raw_data: List[Dict]) -> Dict[str, Any]:
        """
        Очищает сырые данные новостей и извлекает структурированную информацию
        """
        try:
            # Формируем промпт для очистки данных новостей
            sources_text = ""
            if isinstance(raw_data, list):
                # raw_data is a list of news items
                for i, source in enumerate(raw_data[:5], 1):
                    sources_text += f"\n--- Источник {i} ---\n"
                    sources_text += f"Заголовок: {source.get('title', 'НЕТ')}\n"
                    sources_text += f"URL: {source.get('url', 'НЕТ')}\n"
                    sources_text += f"Контент: {source.get('content', 'НЕТ КОНТЕНТА')[:1000]}\n"
            elif isinstance(raw_data, dict) and raw_data.get('data', {}).get('sources'):
                # Fallback for old format
                for i, source in enumerate(raw_data['data']['sources'][:5], 1):
                    sources_text += f"\n--- Источник {i} ---\n"
                    sources_text += f"Заголовок: {source.get('title', 'НЕТ')}\n"
                    sources_text += f"URL: {source.get('url', 'НЕТ')}\n"
                    sources_text += f"Контент: {source.get('content', 'НЕТ КОНТЕНТА')[:1000]}\n"
            else:
                logger.warning(f"Неожиданный формат данных новостей: {type(raw_data)}")
                return {"error": f"Неожиданный формат данных: {type(raw_data)}"}
            
            prompt = f"""
Ты - эксперт по извлечению новостной информации из веб-страниц.

Перед тобой сырые данные с разных новостных сайтов. Извлеки из них структурированную информацию.

СЫРЫЕ ДАННЫЕ:
{sources_text}

ИНСТРУКЦИИ:
1. Проанализируй все источники
2. Найди актуальные новости
3. Извлеки: заголовки, краткое содержание, даты, источники
4. Если информация противоречивая, укажи это
5. Если данных недостаточно, укажи "НЕТ ДАННЫХ"

ОТВЕТЬ СТРОГО В ФОРМАТЕ JSON:
{{
    "news": [
        {{
            "title": "заголовок новости",
            "summary": "краткое содержание",
            "source": "источник",
            "date": "дата если есть",
            "url": "ссылка если есть"
        }}
    ],
    "total_found": "количество найденных новостей",
    "confidence": "уверенность в данных (высокая/средняя/низкая)",
    "notes": "дополнительные заметки"
}}

ВАЖНО: Отвечай только JSON, без дополнительного текста!
"""
            
            # Отправляем запрос к модели
            response = await self.llm_client.chat_completion(
                user_message=prompt,
                system_prompt="",
                model="deepseek/deepseek-r1-0528:free",
                temperature=0.1,
                max_tokens=1500
            )
            
            if response and response.get('choices'):
                content = response['choices'][0]['message']['content']
                
                try:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start != -1 and end != 0:
                        json_str = content[start:end]
                        cleaned_data = json.loads(json_str)
                        logger.info(f"✅ Данные новостей очищены: {len(cleaned_data.get('news', []))} новостей")
                        return cleaned_data
                    else:
                        logger.warning("❌ JSON не найден в ответе модели")
                        return {"error": "Не удалось извлечь JSON из ответа"}
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Ошибка парсинга JSON: {e}")
                    return {"error": f"Ошибка парсинга JSON: {e}"}
            else:
                logger.error("❌ Нет ответа от модели")
                return {"error": "Нет ответа от модели"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка очистки данных новостей: {e}")
            return {"error": f"Ошибка обработки: {e}"}
    
    async def clean_general_data(self, raw_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Очищает общие данные поиска и извлекает структурированную информацию
        """
        try:
            sources_text = ""
            if isinstance(raw_data, dict) and raw_data.get('content'):
                # New format: raw_data has 'content' and 'sources' keys
                sources_text = f"ОБЩИЙ КОНТЕНТ:\n{raw_data.get('content', 'НЕТ КОНТЕНТА')[:2000]}\n"
                sources_text += f"\nИСТОЧНИКИ:\n"
                for i, source in enumerate(raw_data.get('sources', [])[:3], 1):
                    sources_text += f"{i}. {source}\n"
            elif isinstance(raw_data, dict) and raw_data.get('data', {}).get('sources'):
                # Fallback for old format
                for i, source in enumerate(raw_data['data']['sources'][:5], 1):
                    sources_text += f"\n--- Источник {i} ---\n"
                    sources_text += f"Заголовок: {source.get('title', 'НЕТ')}\n"
                    sources_text += f"URL: {source.get('url', 'НЕТ')}\n"
                    sources_text += f"Контент: {source.get('content', 'НЕТ КОНТЕНТА')[:1000]}\n"
            else:
                logger.warning(f"Неожиданный формат общих данных: {type(raw_data)}")
                return {"error": f"Неожиданный формат данных: {type(raw_data)}"}
            
            prompt = f"""
Ты - эксперт по извлечению информации из веб-страниц.

Пользователь искал: "{query}"

Перед тобой сырые данные с разных сайтов. Извлеки из них релевантную информацию.

СЫРЫЕ ДАННЫЕ:
{sources_text}

ИНСТРУКЦИИ:
1. Проанализируй все источники
2. Найди информацию, релевантную запросу пользователя
3. Извлеки ключевые факты и данные
4. Если информация противоречивая, укажи это
5. Если данных недостаточно, укажи "НЕТ ДАННЫХ"

ОТВЕТЬ СТРОГО В ФОРМАТЕ JSON:
{{
    "query": "оригинальный запрос",
    "key_facts": ["ключевые факты"],
    "summary": "краткое резюме найденной информации",
    "sources": ["основные источники"],
    "confidence": "уверенность в данных (высокая/средняя/низкая)",
    "notes": "дополнительные заметки или предупреждения"
}}

ВАЖНО: Отвечай только JSON, без дополнительного текста!
"""
            
            # Отправляем запрос к модели
            response = await self.llm_client.chat_completion(
                user_message=prompt,
                system_prompt="",
                temperature=0.1,
                max_tokens=1500
            )
            
            if response and response.get('choices'):
                content = response['choices'][0]['message']['content']
                
                try:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start != -1 and end != 0:
                        json_str = content[start:end]
                        cleaned_data = json.loads(json_str)
                        logger.info(f"✅ Общие данные очищены для запроса: {query}")
                        return cleaned_data
                    else:
                        logger.warning("❌ JSON не найден в ответе модели")
                        return {"error": "Не удалось извлечь JSON из ответа"}
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Ошибка парсинга JSON: {e}")
                    return {"error": f"Ошибка парсинга JSON: {e}"}
            else:
                logger.error("❌ Нет ответа от модели")
                return {"error": "Нет ответа от модели"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка очистки общих данных: {e}")
            return {"error": f"Ошибка обработки: {e}"} 