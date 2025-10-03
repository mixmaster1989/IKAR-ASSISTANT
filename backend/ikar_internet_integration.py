#!/usr/bin/env python3
"""
🧠 ИНТЕГРАЦИЯ ИНТЕРНЕТ-ИНТЕЛЛЕКТА С IKAR
Автоматическое определение когда нужна свежая информация и интеграция с ответами бота
"""

import asyncio
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from pathlib import Path

from internet_intelligence_system import InternetIntelligenceSystem, ProcessedInformation

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedResponse:
    """Улучшенный ответ с интернет-информацией"""
    original_response: str
    internet_info: Optional[ProcessedInformation]
    combined_response: str
    confidence_score: float
    sources: List[str]
    needs_internet: bool
    processing_time: float

class IKARInternetIntegration:
    """Интеграция интернет-интеллекта с IKAR"""
    
    def __init__(self):
        self.internet_system = None
        self.query_patterns = self._load_query_patterns()
        self.cache = {}
        self.cache_duration = timedelta(minutes=30)
        
    def _load_query_patterns(self) -> Dict[str, List[str]]:
        """Загрузка паттернов для определения необходимости интернет-поиска"""
        return {
            "news": [
                r"последние новости",
                r"что нового",
                r"обновления",
                r"сегодня в мире",
                r"актуальные события",
                r"что происходит",
                r"свежие новости",
                r"последние события"
            ],
            "current_events": [
                r"что происходит с",
                r"статус",
                r"ситуация",
                r"развитие событий",
                r"текущее состояние",
                r"последние изменения"
            ],
            "real_time": [
                r"сейчас",
                r"в данный момент",
                r"реальное время",
                r"живые данные",
                r"актуальная информация",
                r"сегодня"
            ],
            "technical": [
                r"последние версии",
                r"обновления",
                r"новые функции",
                r"технологии",
                r"инновации",
                r"разработка"
            ],
            "market": [
                r"курс валют",
                r"цены",
                r"рынок",
                r"экономика",
                r"финансы",
                r"инвестиции"
            ],
            "weather": [
                r"погода",
                r"климат",
                r"температура",
                r"осадки",
                r"прогноз"
            ],
            "sports": [
                r"спорт",
                r"матч",
                r"соревнования",
                r"результаты",
                r"чемпионат"
            ]
        }
    
    async def _get_internet_system(self) -> InternetIntelligenceSystem:
        """Получение системы интернет-интеллекта"""
        if self.internet_system is None:
            self.internet_system = InternetIntelligenceSystem()
        return self.internet_system
    
    def needs_internet_search(self, user_query: str) -> Tuple[bool, str, float]:
        """
        Определяет, нужен ли интернет-поиск для запроса
        
        Returns:
            (needs_search, search_query, confidence)
        """
        query_lower = user_query.lower()
        
        # Проверяем паттерны
        for category, patterns in self.query_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    confidence = self._calculate_pattern_confidence(pattern, query_lower)
                    return True, user_query, confidence
        
        # Дополнительные проверки
        if self._has_time_indicators(query_lower):
            return True, user_query, 0.7
        
        if self._has_current_events_keywords(query_lower):
            return True, user_query, 0.8
        
        return False, "", 0.0
    
    def _calculate_pattern_confidence(self, pattern: str, query: str) -> float:
        """Расчет уверенности в паттерне"""
        # Более точные совпадения дают большую уверенность
        if re.search(pattern, query):
            return 0.9
        return 0.7
    
    def _has_time_indicators(self, query: str) -> bool:
        """Проверка временных индикаторов"""
        time_indicators = [
            "сегодня", "сейчас", "в данный момент", "недавно", 
            "последние", "новые", "актуальные", "живые"
        ]
        return any(indicator in query for indicator in time_indicators)
    
    def _has_current_events_keywords(self, query: str) -> bool:
        """Проверка ключевых слов текущих событий"""
        current_keywords = [
            "новости", "события", "происшествия", "обновления",
            "изменения", "развитие", "прогресс", "статус"
        ]
        return any(keyword in query for keyword in current_keywords)
    
    async def enhance_response_with_internet(
        self, 
        user_query: str, 
        original_response: str
    ) -> EnhancedResponse:
        """
        Улучшает ответ бота информацией из интернета
        
        Args:
            user_query: Запрос пользователя
            original_response: Оригинальный ответ бота
            
        Returns:
            EnhancedResponse: Улучшенный ответ
        """
        start_time = datetime.now()
        
        # Проверяем, нужен ли интернет-поиск
        needs_search, search_query, confidence = self.needs_internet_search(user_query)
        
        if not needs_search:
            return EnhancedResponse(
                original_response=original_response,
                internet_info=None,
                combined_response=original_response,
                confidence_score=1.0,
                sources=[],
                needs_internet=False,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
        
        logger.info(f"🌐 Интернет-поиск необходим для запроса: '{user_query}'")
        
        try:
            # Получаем интернет-информацию
            internet_system = await self._get_internet_system()
            internet_info = await internet_system.get_internet_intelligence(search_query)
            
            # Объединяем ответы
            combined_response = self._combine_responses(
                original_response, 
                internet_info, 
                user_query
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return EnhancedResponse(
                original_response=original_response,
                internet_info=internet_info,
                combined_response=combined_response,
                confidence_score=internet_info.confidence_score,
                sources=internet_info.sources,
                needs_internet=True,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка интернет-интеграции: {e}")
            
            # Возвращаем оригинальный ответ при ошибке
            return EnhancedResponse(
                original_response=original_response,
                internet_info=None,
                combined_response=original_response,
                confidence_score=0.0,
                sources=[],
                needs_internet=True,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _combine_responses(
        self, 
        original_response: str, 
        internet_info: ProcessedInformation, 
        user_query: str
    ) -> str:
        """Объединяет оригинальный ответ с интернет-информацией"""
        
        # Если интернет-информация имеет низкую уверенность, используем оригинальный ответ
        if internet_info.confidence_score < 0.3:
            return original_response
        
        # Создаем улучшенный ответ
        combined = f"{original_response}\n\n"
        
        # Добавляем интернет-информацию
        if internet_info.ai_summary:
            combined += "🌐 **Актуальная информация из интернета:**\n"
            combined += f"{internet_info.ai_summary}\n\n"
        
        # Добавляем ключевые моменты
        if internet_info.key_points:
            combined += "🔑 **Ключевые моменты:**\n"
            for i, point in enumerate(internet_info.key_points, 1):
                combined += f"{i}. {point}\n"
            combined += "\n"
        
        # Добавляем источники
        if internet_info.sources:
            combined += "📚 **Источники:**\n"
            for i, source in enumerate(internet_info.sources[:3], 1):
                combined += f"{i}. {source}\n"
        
        return combined
    
    async def process_user_message(
        self, 
        user_query: str, 
        bot_response: str,
        user_id: str = None
    ) -> EnhancedResponse:
        """
        Обрабатывает сообщение пользователя с интернет-интеграцией
        
        Args:
            user_query: Запрос пользователя
            bot_response: Ответ бота
            user_id: ID пользователя (для персонализации)
            
        Returns:
            EnhancedResponse: Улучшенный ответ
        """
        logger.info(f"🧠 Обработка сообщения пользователя: '{user_query[:50]}...'")
        
        # Улучшаем ответ интернет-информацией
        enhanced_response = await self.enhance_response_with_internet(
            user_query, 
            bot_response
        )
        
        # Логируем результат
        self._log_enhancement(user_query, enhanced_response, user_id)
        
        return enhanced_response
    
    def _log_enhancement(
        self, 
        user_query: str, 
        enhanced_response: EnhancedResponse, 
        user_id: str = None
    ):
        """Логирование улучшения ответа"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "query": user_query,
            "needs_internet": enhanced_response.needs_internet,
            "confidence_score": enhanced_response.confidence_score,
            "processing_time": enhanced_response.processing_time,
            "sources_count": len(enhanced_response.sources)
        }
        
        logger.info(f"📊 Интернет-интеграция: {json.dumps(log_data, ensure_ascii=False)}")
    
    async def get_internet_stats(self) -> Dict[str, Any]:
        """Получение статистики интернет-интеграции"""
        try:
            internet_system = await self._get_internet_system()
            
            # Получаем статистику из базы данных
            conn = internet_system.db_path
            # Здесь будет код для получения статистики
            
            return {
                "total_searches": 0,
                "successful_enhancements": 0,
                "average_confidence": 0.0,
                "average_processing_time": 0.0,
                "most_common_queries": [],
                "last_enhancement": None
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    async def close(self):
        """Закрытие системы"""
        if self.internet_system:
            await self.internet_system.close()

# Глобальный экземпляр интеграции
ikar_internet_integration = None

async def get_ikar_internet_integration() -> IKARInternetIntegration:
    """Получение глобального экземпляра интеграции"""
    global ikar_internet_integration
    if ikar_internet_integration is None:
        ikar_internet_integration = IKARInternetIntegration()
    return ikar_internet_integration

# Интеграция с основной системой IKAR
async def enhance_ikar_response(user_query: str, bot_response: str, user_id: str = None) -> str:
    """
    Улучшает ответ IKAR интернет-информацией
    
    Args:
        user_query: Запрос пользователя
        bot_response: Ответ бота
        user_id: ID пользователя
        
    Returns:
        str: Улучшенный ответ
    """
    try:
        integration = await get_ikar_internet_integration()
        enhanced = await integration.process_user_message(user_query, bot_response, user_id)
        return enhanced.combined_response
    except Exception as e:
        logger.error(f"Ошибка улучшения ответа: {e}")
        return bot_response

async def main():
    """Тестирование интеграции"""
    integration = await get_ikar_internet_integration()
    
    # Тестовые запросы
    test_cases = [
        "Какие последние новости о развитии ИИ?",
        "Что происходит с криптовалютами сегодня?",
        "Расскажи о погоде в Москве",
        "Как дела?",
        "Какие новые технологии появились в этом году?"
    ]
    
    for query in test_cases:
        print(f"\n🧪 Тестируем: '{query}'")
        
        # Симулируем ответ бота
        bot_response = "Это мой стандартный ответ на основе моих знаний."
        
        # Улучшаем ответ
        enhanced = await integration.process_user_message(query, bot_response, "test_user")
        
        print(f"Нужен интернет: {enhanced.needs_internet}")
        print(f"Уверенность: {enhanced.confidence_score:.2f}")
        print(f"Время обработки: {enhanced.processing_time:.2f}с")
        
        if enhanced.needs_internet:
            print(f"Источники: {len(enhanced.sources)}")
            print(f"Улучшенный ответ:\n{enhanced.combined_response[:200]}...")
        else:
            print("Использован оригинальный ответ")
    
    await integration.close()

if __name__ == "__main__":
    asyncio.run(main()) 