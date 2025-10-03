#!/usr/bin/env python3
"""
🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА
Тестирование всех компонентов системы
"""

import asyncio
import time
import json
from datetime import datetime
from typing import List, Dict, Any
import logging

from internet_intelligence_system import InternetIntelligenceSystem
from ikar_internet_integration import IKARInternetIntegration
from integrate_with_ikar import IKARInternetEnhancer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InternetIntelligenceTester:
    """Комплексный тестер системы интернет-интеллекта"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ СИСТЕМЫ ИНТЕРНЕТ-ИНТЕЛЛЕКТА")
        print("=" * 80)
        
        self.start_time = datetime.now()
        
        # Тестируем каждый компонент
        await self.test_internet_system()
        await self.test_integration_system()
        await self.test_ikar_enhancer()
        await self.test_end_to_end()
        
        self.end_time = datetime.now()
        
        # Выводим результаты
        self.print_test_summary()
    
    async def test_internet_system(self):
        """Тестирование системы интернет-поиска"""
        print("\n🌐 ТЕСТИРОВАНИЕ СИСТЕМЫ ИНТЕРНЕТ-ПОИСКА")
        print("-" * 50)
        
        try:
            system = InternetIntelligenceSystem()
            
            # Тест 1: Поиск новостей
            print("📰 Тест 1: Поиск новостей о технологиях")
            start_time = time.time()
            
            results = await system.search_internet("последние новости о технологиях", max_total_results=5)
            
            test_time = time.time() - start_time
            
            self.record_test_result(
                "internet_search_news",
                len(results) > 0,
                test_time,
                f"Найдено {len(results)} результатов"
            )
            
            print(f"✅ Найдено {len(results)} результатов за {test_time:.2f}с")
            
            # Тест 2: Извлечение контента
            if results:
                print("📄 Тест 2: Извлечение контента")
                start_time = time.time()
                
                results_with_content = await system.extract_content(results[:3])
                
                test_time = time.time() - start_time
                content_count = sum(1 for r in results_with_content if r.content)
                
                self.record_test_result(
                    "content_extraction",
                    content_count > 0,
                    test_time,
                    f"Извлечен контент с {content_count} страниц"
                )
                
                print(f"✅ Извлечен контент с {content_count} страниц за {test_time:.2f}с")
                
                # Тест 3: AI обработка
                print("🧠 Тест 3: AI обработка информации")
                start_time = time.time()
                
                processed_info = await system.process_with_ai(
                    "новости о технологиях", 
                    results_with_content
                )
                
                test_time = time.time() - start_time
                
                self.record_test_result(
                    "ai_processing",
                    processed_info.confidence_score > 0.3,
                    test_time,
                    f"Уверенность: {processed_info.confidence_score:.2f}"
                )
                
                print(f"✅ AI обработка завершена за {test_time:.2f}с")
                print(f"   Уверенность: {processed_info.confidence_score:.2f}")
                print(f"   Ключевых моментов: {len(processed_info.key_points)}")
            
            await system.close()
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования интернет-системы: {e}")
            self.record_test_result("internet_system", False, 0, str(e))
    
    async def test_integration_system(self):
        """Тестирование системы интеграции"""
        print("\n🔗 ТЕСТИРОВАНИЕ СИСТЕМЫ ИНТЕГРАЦИИ")
        print("-" * 50)
        
        try:
            integration = IKARInternetIntegration()
            
            # Тест 1: Анализ запросов
            print("🔍 Тест 1: Анализ запросов")
            
            test_queries = [
                ("Как дела?", False),
                ("Последние новости", True),
                ("Что происходит с криптовалютами?", True),
                ("Расскажи анекдот", False),
                ("Погода сегодня", True)
            ]
            
            correct_analyses = 0
            
            for query, expected_needs_internet in test_queries:
                needs_search, search_query, confidence = integration.needs_internet_search(query)
                
                if needs_search == expected_needs_internet:
                    correct_analyses += 1
                
                print(f"   '{query}' -> Нужен интернет: {needs_search} (ожидалось: {expected_needs_internet})")
            
            accuracy = correct_analyses / len(test_queries)
            
            self.record_test_result(
                "query_analysis",
                accuracy > 0.7,
                0,
                f"Точность: {accuracy:.2f}"
            )
            
            print(f"✅ Точность анализа: {accuracy:.2f}")
            
            # Тест 2: Улучшение ответов
            print("🚀 Тест 2: Улучшение ответов")
            
            user_query = "Какие последние новости о технологиях?"
            bot_response = "Я знаю общие факты о технологиях."
            
            start_time = time.time()
            
            enhanced = await integration.process_user_message(user_query, bot_response, "test_user")
            
            test_time = time.time() - start_time
            
            improvement_ratio = len(enhanced.combined_response) / len(bot_response)
            
            self.record_test_result(
                "response_enhancement",
                enhanced.needs_internet and improvement_ratio > 1.5,
                test_time,
                f"Улучшение: {improvement_ratio:.2f}x"
            )
            
            print(f"✅ Ответ улучшен в {improvement_ratio:.2f} раза за {test_time:.2f}с")
            
            await integration.close()
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования интеграции: {e}")
            self.record_test_result("integration_system", False, 0, str(e))
    
    async def test_ikar_enhancer(self):
        """Тестирование улучшителя IKAR"""
        print("\n🤖 ТЕСТИРОВАНИЕ УЛУЧШИТЕЛЯ IKAR")
        print("-" * 50)
        
        try:
            enhancer = IKARInternetEnhancer()
            
            # Инициализация
            print("🔧 Тест 1: Инициализация")
            start_time = time.time()
            
            initialized = await enhancer.initialize()
            
            test_time = time.time() - start_time
            
            self.record_test_result(
                "enhancer_initialization",
                initialized,
                test_time,
                "Система инициализирована"
            )
            
            print(f"✅ Инициализация: {'успешна' if initialized else 'неудачна'} за {test_time:.2f}с")
            
            if initialized:
                # Тест 2: Улучшение ответов
                print("📝 Тест 2: Улучшение ответов")
                
                test_cases = [
                    ("Как дела?", "У меня все хорошо!", False),
                    ("Новости о технологиях", "Технологии развиваются.", True),
                    ("Курс Bitcoin", "Bitcoin - криптовалюта.", True)
                ]
                
                successful_enhancements = 0
                
                for user_query, bot_response, should_enhance in test_cases:
                    start_time = time.time()
                    
                    enhanced = await enhancer.enhance_bot_response(user_query, bot_response, "test_user")
                    
                    test_time = time.time() - start_time
                    
                    if should_enhance:
                        if len(enhanced) > len(bot_response) * 1.2:
                            successful_enhancements += 1
                    else:
                        if len(enhanced) <= len(bot_response) * 1.1:
                            successful_enhancements += 1
                    
                    print(f"   '{user_query}' -> Улучшен: {len(enhanced) > len(bot_response)}")
                
                enhancement_accuracy = successful_enhancements / len(test_cases)
                
                self.record_test_result(
                    "enhancer_accuracy",
                    enhancement_accuracy > 0.6,
                    0,
                    f"Точность: {enhancement_accuracy:.2f}"
                )
                
                print(f"✅ Точность улучшения: {enhancement_accuracy:.2f}")
                
                # Тест 3: Статус системы
                print("📊 Тест 3: Статус системы")
                
                status = await enhancer.get_system_status()
                
                self.record_test_result(
                    "enhancer_status",
                    status.get("status") == "active",
                    0,
                    f"Статус: {status.get('status')}"
                )
                
                print(f"✅ Статус системы: {status.get('status')}")
            
            await enhancer.close()
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования улучшителя: {e}")
            self.record_test_result("ikar_enhancer", False, 0, str(e))
    
    async def test_end_to_end(self):
        """End-to-end тестирование"""
        print("\n🔄 END-TO-END ТЕСТИРОВАНИЕ")
        print("-" * 50)
        
        try:
            # Полный цикл: запрос -> поиск -> обработка -> улучшение
            print("🔄 Тест полного цикла")
            
            user_query = "Какие последние новости о развитии ИИ?"
            bot_response = "Искусственный интеллект активно развивается."
            
            start_time = time.time()
            
            # Улучшаем ответ
            enhanced = await enhance_ikar_message(user_query, bot_response, "e2e_test")
            
            test_time = time.time() - start_time
            
            # Проверяем результат
            is_enhanced = len(enhanced) > len(bot_response) * 1.5
            has_internet_info = "интернета" in enhanced.lower() or "новости" in enhanced.lower()
            
            self.record_test_result(
                "end_to_end",
                is_enhanced and has_internet_info,
                test_time,
                f"Улучшение: {len(enhanced)/len(bot_response):.2f}x"
            )
            
            print(f"✅ Полный цикл завершен за {test_time:.2f}с")
            print(f"   Улучшение: {len(enhanced)/len(bot_response):.2f}x")
            print(f"   Содержит интернет-информацию: {has_internet_info}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка end-to-end тестирования: {e}")
            self.record_test_result("end_to_end", False, 0, str(e))
    
    def record_test_result(self, test_name: str, success: bool, duration: float, details: str):
        """Запись результата теста"""
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "duration": duration,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def print_test_summary(self):
        """Вывод сводки тестов"""
        print("\n" + "=" * 80)
        print("📊 СВОДКА ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        total_duration = sum(result["duration"] for result in self.test_results)
        
        print(f"Всего тестов: {total_tests}")
        print(f"Успешных: {successful_tests}")
        print(f"Неудачных: {total_tests - successful_tests}")
        print(f"Успешность: {successful_tests/total_tests*100:.1f}%")
        print(f"Общее время: {total_duration:.2f}с")
        
        if self.start_time and self.end_time:
            total_time = (self.end_time - self.start_time).total_seconds()
            print(f"Время выполнения: {total_time:.2f}с")
        
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print("-" * 80)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")
            if result["duration"] > 0:
                print(f"   Время: {result['duration']:.2f}с")
        
        # Сохраняем результаты в файл
        self.save_test_results()
    
    def save_test_results(self):
        """Сохранение результатов тестов"""
        try:
            results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_summary": {
                        "total_tests": len(self.test_results),
                        "successful_tests": sum(1 for r in self.test_results if r["success"]),
                        "total_duration": sum(r["duration"] for r in self.test_results),
                        "start_time": self.start_time.isoformat() if self.start_time else None,
                        "end_time": self.end_time.isoformat() if self.end_time else None
                    },
                    "test_results": self.test_results
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Результаты сохранены в {results_file}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения результатов: {e}")

async def main():
    """Главная функция тестирования"""
    tester = InternetIntelligenceTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 