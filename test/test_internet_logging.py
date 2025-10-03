#!/usr/bin/env python3
"""
🌐 ТЕСТ ОБНОВЛЕННОГО ЛОГИРОВАНИЯ ИНТЕРНЕТ-ИНТЕЛЛЕКТА
Проверка работы логгера с полной информацией о поиске
"""

import asyncio
import time
from internet_intelligence_logger import get_internet_logger, log_internet_operation

async def test_internet_logging():
    """Тестирование обновленного логирования интернет-интеллекта"""
    print("🌐 ТЕСТ ОБНОВЛЕННОГО ЛОГИРОВАНИЯ ИНТЕРНЕТ-ИНТЕЛЛЕКТА")
    print("=" * 60)
    
    # Получаем логгер
    logger = get_internet_logger()
    
    # Тестовые данные
    test_query = "последние новости о криптовалютах"
    test_user_id = "test_user_123"
    test_chat_id = "test_chat_456"
    
    print("📝 Тестируем логирование поискового запроса...")
    
    # Тестируем поисковый запрос
    log_internet_operation("search_request", 
                          query=test_query,
                          user_id=test_user_id,
                          chat_id=test_chat_id,
                          search_engines=["google", "bing", "duckduckgo"])
    
    print("✅ Поисковый запрос залогирован")
    
    # Тестируем результаты поиска
    print("📝 Тестируем логирование результатов поиска...")
    
    test_results = [
        {
            'title': 'Криптовалюты: последние новости и тренды 2025',
            'url': 'https://example.com/crypto-news-2025',
            'snippet': 'Анализ последних событий в мире криптовалют, включая изменения в регулировании и новые технологии.',
            'source': 'google',
            'relevance_score': 0.95
        },
        {
            'title': 'Bitcoin достиг новых высот в 2025 году',
            'url': 'https://crypto-news.com/bitcoin-2025',
            'snippet': 'Bitcoin показал рекордный рост в начале 2025 года, достигнув новых исторических максимумов.',
            'source': 'bing',
            'relevance_score': 0.88
        },
        {
            'title': 'Эфириум 2.0: обновления и перспективы',
            'url': 'https://ethereum.org/news/eth2-updates',
            'snippet': 'Последние обновления Ethereum 2.0 и их влияние на экосистему децентрализованных приложений.',
            'source': 'duckduckgo',
            'relevance_score': 0.82
        }
    ]
    
    log_internet_operation("search_results",
                          engine="google",
                          results_count=len(test_results),
                          duration=2.5,
                          results=test_results,
                          errors=None,
                          api_url="https://www.google.com/search")
    
    print("✅ Результаты поиска залогированы")
    
    # Тестируем извлечение контента
    print("📝 Тестируем логирование извлечения контента...")
    
    test_content = """Криптовалюты продолжают привлекать внимание инвесторов и технологических энтузиастов в 2025 году. 
    
    Bitcoin, первая и самая известная криптовалюта, показал впечатляющий рост в начале года, достигнув новых исторических максимумов. 
    Эксперты связывают этот рост с растущим принятием криптовалют институциональными инвесторами и улучшением регулирования в различных странах.
    
    Ethereum 2.0, крупнейшее обновление сети Ethereum, продолжает развиваться, предлагая улучшенную масштабируемость и энергоэффективность. 
    Это обновление открывает новые возможности для децентрализованных приложений и смарт-контрактов.
    
    Регулирование криптовалют остается ключевой темой для обсуждения. Многие страны разрабатывают новые законы и правила для 
    обеспечения безопасности инвесторов и предотвращения незаконной деятельности."""
    
    log_internet_operation("content_extraction",
                          url="https://example.com/crypto-news-2025",
                          success=True,
                          content_length=len(test_content),
                          content_preview=test_content[:500] + "...")
    
    print("✅ Извлечение контента залогировано")
    
    # Тестируем AI-обработку
    print("📝 Тестируем логирование AI-обработки...")
    
    ai_summary = """В 2025 году криптовалюты демонстрируют значительный рост, особенно Bitcoin, который достиг новых исторических максимумов. 
    Ethereum 2.0 продолжает развиваться, предлагая улучшенную масштабируемость. Регулирование остается важной темой в отрасли."""
    
    key_points = [
        "Bitcoin достиг новых исторических максимумов в 2025 году",
        "Ethereum 2.0 предлагает улучшенную масштабируемость",
        "Растущее принятие криптовалют институциональными инвесторами",
        "Улучшение регулирования в различных странах",
        "Развитие децентрализованных приложений"
    ]
    
    log_internet_operation("ai_processing",
                          query=test_query,
                          content_length=len(test_content),
                          processing_time=3.2,
                          confidence=0.85,
                          ai_summary=ai_summary,
                          key_points=key_points)
    
    print("✅ AI-обработка залогирована")
    
    # Тестируем ошибки
    print("📝 Тестируем логирование ошибок...")
    
    try:
        raise Exception("Тестовая ошибка поиска: API недоступен")
    except Exception as e:
        log_internet_operation("error",
                              error=e,
                              context="test_search_error",
                              additional_info={
                                  "query": test_query,
                                  "engine": "test_engine",
                                  "timestamp": time.time()
                              })
    
    print("✅ Ошибки залогированы")
    
    # Тестируем производительность
    print("📝 Тестируем логирование производительности...")
    
    log_internet_operation("performance",
                          operation="test_internet_search",
                          duration=8.5,
                          details={
                              "total_results": 15,
                              "successful_extractions": 12,
                              "ai_processing_time": 3.2,
                              "cache_hits": 2
                          })
    
    print("✅ Производительность залогирована")
    
    # Показываем информацию о логах
    print(f"\n📁 Файл логов: {logger.get_log_file_path()}")
    print(f"📏 Размер файла: {logger.get_log_file_size()} байт")
    
    print("\n✅ Тест завершен успешно!")
    print("Теперь вы можете просмотреть логи с полной информацией о поиске, извлечении контента и AI-обработке.")

if __name__ == "__main__":
    asyncio.run(test_internet_logging()) 