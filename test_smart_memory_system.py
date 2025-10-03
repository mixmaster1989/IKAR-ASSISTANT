"""
🧪 Comprehensive тесты новой системы умной памяти
Тестирует все компоненты с синтетическими данными
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
)

logger = logging.getLogger("test_smart_memory")

class MockLLMClient:
    """Мок LLM клиента для тестирования"""
    
    async def chat_completion(self, user_message: str, system_prompt: str = "", **kwargs) -> str:
        """Мокирует ответы LLM"""
        
        # Если это запрос на сжатие сообщений
        if "JSON резюме" in user_message or "РАЗГОВОР В ГРУППЕ" in user_message:
            # Анализируем содержимое для создания релевантного резюме
            if "проект" in user_message.lower():
                return json.dumps({
                    "topic": "Обсуждение проекта",
                    "summary": "Команда обсуждала текущий проект, распределяли задачи и планировали дедлайны. Иван взял на себя backend, Мария - frontend.",
                    "importance": 0.8,
                    "key_points": ["распределение задач", "дедлайны проекта", "технические решения"],
                    "participants_activity": {"user1": "координировал задачи", "user2": "предложила решения"}
                })
            elif "встреча" in user_message.lower():
                return json.dumps({
                    "topic": "Планирование встречи",
                    "summary": "Участники планировали встречу на завтра в 18:00 в офисе. Обсуждали повестку дня и подготовку материалов.",
                    "importance": 0.7,
                    "key_points": ["время встречи", "место проведения", "повестка дня"],
                    "participants_activity": {"user1": "предложил время", "user2": "подтвердила участие"}
                })
            elif "обед" in user_message.lower():
                return json.dumps({
                    "topic": "Планы на обед",
                    "summary": "Группа обсуждала где пообедать, рассматривали несколько вариантов кафе. Решили встретиться в 13:00.",
                    "importance": 0.4,
                    "key_points": ["выбор кафе", "время обеда"],
                    "participants_activity": {"user1": "предложил варианты", "user2": "выбрала кафе"}
                })
            else:
                return json.dumps({
                    "topic": "Общее обсуждение",
                    "summary": "Участники обсуждали различные темы в неформальной обстановке.",
                    "importance": 0.3,
                    "key_points": ["общение", "обмен мнениями"],
                    "participants_activity": {"user1": "активно участвовал", "user2": "поддерживала беседу"}
                })
        
        # Если это запрос на генерацию ответа бота
        else:
            responses = [
                "🤖 Привет! Вижу, что вы обсуждаете интересные вещи. Чем могу помочь?",
                "👋 Здравствуйте! Судя по контексту, у вас активное обсуждение. Что нового?",
                "🔥 Отличная беседа! Могу поделиться своими мыслями по теме.",
                "💡 Интересно! А что если попробовать другой подход к этому вопросу?",
                "📊 Судя по истории, эта тема вас часто волнует. Есть прогресс?"
            ]
            # Возвращаем разные ответы в зависимости от контекста
            import hashlib
            hash_val = int(hashlib.md5(user_message.encode()).hexdigest(), 16)
            return responses[hash_val % len(responses)]

class SmartMemoryTester:
    """Класс для тестирования системы умной памяти"""
    
    def __init__(self):
        self.mock_llm = MockLLMClient()
        self.test_chat_id = "test_chat_123"
        self.test_users = ["user_alice", "user_bob", "user_charlie"]
        
    async def run_all_tests(self):
        """Запускает все тесты"""
        logger.info("🚀 Начинаем comprehensive тестирование системы умной памяти")
        
        try:
            # Тест 1: Инициализация системы
            await self.test_system_initialization()
            
            # Тест 2: Добавление сообщений
            await self.test_message_storage()
            
            # Тест 3: Ночная оптимизация
            await self.test_night_optimization()
            
            # Тест 4: Поиск с временным затуханием
            await self.test_smart_retrieval()
            
            # Тест 5: Умный триггер бота
            await self.test_smart_bot_trigger()
            
            # Тест 6: Интеграция компонентов
            await self.test_integration()
            
            logger.info("✅ Все тесты пройдены успешно!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в тестах: {e}")
            raise
    
    async def test_system_initialization(self):
        """Тест инициализации системы"""
        logger.info("🔧 Тест 1: Инициализация системы")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from memory.smart_memory_manager import get_smart_memory_manager
        from memory.night_optimizer import get_night_optimizer
        from memory.smart_retriever import get_smart_retriever
        
        # Инициализируем компоненты
        memory_manager = get_smart_memory_manager()
        smart_retriever = get_smart_retriever(memory_manager)
        night_optimizer = get_night_optimizer(memory_manager, self.mock_llm)
        
        # Проверяем статистику
        stats = memory_manager.get_stats()
        assert isinstance(stats, dict), "Статистика должна быть словарем"
        
        logger.info("✅ Система инициализирована успешно")
    
    async def test_message_storage(self):
        """Тест сохранения сообщений"""
        logger.info("📝 Тест 2: Сохранение сообщений")
        
        from memory.smart_memory_manager import get_smart_memory_manager
        memory_manager = get_smart_memory_manager()
        
        # Создаем синтетические сообщения
        test_messages = self.generate_synthetic_messages()
        
        # Добавляем сообщения
        for msg in test_messages:
            success = memory_manager.add_group_message(
                self.test_chat_id, 
                msg['user_id'], 
                msg['content'], 
                msg['timestamp']
            )
            assert success, f"Не удалось добавить сообщение: {msg['content']}"
        
        # Проверяем получение сообщений
        recent_messages = memory_manager.get_recent_messages(self.test_chat_id, limit=10)
        assert len(recent_messages) > 0, "Должны быть сохранены сообщения"
        
        logger.info(f"✅ Сохранено и получено {len(recent_messages)} сообщений")
    
    async def test_night_optimization(self):
        """Тест ночной оптимизации"""
        logger.info("🌙 Тест 3: Ночная оптимизация")
        
        from memory.night_optimizer import get_night_optimizer
        from memory.smart_memory_manager import get_smart_memory_manager
        
        memory_manager = get_smart_memory_manager()
        night_optimizer = get_night_optimizer(memory_manager, self.mock_llm)
        
        # Принудительно запускаем оптимизацию для тестового чата
        result = await night_optimizer.force_optimize_chat(self.test_chat_id)
        
        assert result['status'] in ['success', 'no_messages'], f"Неожиданный статус: {result}"
        
        if result['status'] == 'success':
            logger.info(f"✅ Оптимизация завершена: {result['message']}")
        else:
            logger.info("ℹ️ Нет сообщений для оптимизации (это нормально для теста)")
    
    async def test_smart_retrieval(self):
        """Тест умного поиска с временным затуханием"""
        logger.info("🔍 Тест 4: Умный поиск")
        
        from memory.smart_retriever import get_smart_retriever
        from memory.smart_memory_manager import get_smart_memory_manager
        
        memory_manager = get_smart_memory_manager()
        smart_retriever = get_smart_retriever(memory_manager)
        
        # Тестируем поиск релевантных чанков
        relevant_chunks = await smart_retriever.find_relevant_chunks(
            self.test_chat_id, 
            "проект работа задачи", 
            "обсуждение планов"
        )
        
        # Проверяем временное затухание
        current_time = time.time()
        for chunk_data in relevant_chunks:
            age_days = (current_time - chunk_data.chunk.created_at) / (24 * 3600)
            threshold = memory_manager.calculate_relevance_threshold(age_days)
            
            assert chunk_data.relevance_score >= threshold, \
                f"Чанк не должен был пройти порог: {chunk_data.relevance_score} < {threshold}"
        
        logger.info(f"✅ Найдено {len(relevant_chunks)} релевантных чанков")
        
        # Тестируем статистику поисковика
        stats = await smart_retriever.get_retriever_stats(self.test_chat_id)
        logger.info(f"📊 Статистика поисковика: {stats}")
    
    async def test_smart_bot_trigger(self):
        """Тест умного триггера бота"""
        logger.info("🤖 Тест 5: Умный триггер бота")
        
        from api.smart_bot_trigger import process_smart_bot_trigger
        
        # Тестируем срабатывание триггера
        response = await process_smart_bot_trigger(
            self.test_chat_id,
            "Привет бот, как дела?",
            "user_alice"
        )
        
        assert response is not None, "Триггер должен вернуть ответ"
        assert len(response) > 0, "Ответ не должен быть пустым"
        
        logger.info(f"✅ Триггер сработал: {response[:50]}...")
        
        # Тестируем cooldown
        response2 = await process_smart_bot_trigger(
            self.test_chat_id,
            "бот, еще вопрос",
            "user_bob"
        )
        
        assert "cooldown" in response2.lower() or "активен" in response2.lower(), \
            "Должен сработать cooldown"
        
        logger.info("✅ Cooldown работает корректно")
    
    async def test_integration(self):
        """Тест интеграции всех компонентов"""
        logger.info("🔗 Тест 6: Интеграция компонентов")
        
        from memory.memory_integration import get_memory_integration
        
        integration = get_memory_integration()
        await integration.initialize()
        
        # Тестируем добавление сообщения через интеграцию
        success = integration.add_group_message(
            self.test_chat_id,
            "user_test",
            "Тестовое сообщение через интеграцию",
            time.time()
        )
        
        assert success, "Интеграция должна успешно добавлять сообщения"
        
        # Тестируем получение контекста
        context = await integration.get_smart_context_for_bot(
            self.test_chat_id,
            "тестовый запрос",
            "user_test"
        )
        
        assert isinstance(context, dict), "Контекст должен быть словарем"
        assert 'time_info' in context, "Контекст должен содержать информацию о времени"
        
        # Тестируем статистику
        stats = await integration.get_memory_stats(self.test_chat_id)
        assert isinstance(stats, dict), "Статистика должна быть словарем"
        
        logger.info("✅ Интеграция работает корректно")
    
    def generate_synthetic_messages(self) -> List[Dict[str, Any]]:
        """Генерирует синтетические сообщения для тестирования"""
        base_time = time.time() - (7 * 24 * 3600)  # 7 дней назад
        
        messages = [
            # Обсуждение проекта (7 дней назад)
            {"user_id": "user_alice", "content": "Привет! Как дела с проектом?", "timestamp": base_time},
            {"user_id": "user_bob", "content": "Работаю над backend частью", "timestamp": base_time + 300},
            {"user_id": "user_charlie", "content": "А я делаю frontend", "timestamp": base_time + 600},
            {"user_id": "user_alice", "content": "Отлично! Когда планируем дедлайн?", "timestamp": base_time + 900},
            {"user_id": "user_bob", "content": "Думаю, к концу недели успеем", "timestamp": base_time + 1200},
            
            # Планирование встречи (3 дня назад)
            {"user_id": "user_charlie", "content": "Нужно встретиться и обсудить прогресс", "timestamp": base_time + (4 * 24 * 3600)},
            {"user_id": "user_alice", "content": "Давайте завтра в 18:00?", "timestamp": base_time + (4 * 24 * 3600) + 300},
            {"user_id": "user_bob", "content": "Мне подходит, где встречаемся?", "timestamp": base_time + (4 * 24 * 3600) + 600},
            {"user_id": "user_alice", "content": "В офисе, в переговорной", "timestamp": base_time + (4 * 24 * 3600) + 900},
            
            # Обсуждение обеда (1 день назад)
            {"user_id": "user_bob", "content": "Кто идет на обед?", "timestamp": base_time + (6 * 24 * 3600)},
            {"user_id": "user_charlie", "content": "Я с вами! Куда пойдем?", "timestamp": base_time + (6 * 24 * 3600) + 300},
            {"user_id": "user_alice", "content": "Есть новое кафе рядом", "timestamp": base_time + (6 * 24 * 3600) + 600},
            {"user_id": "user_bob", "content": "Звучит хорошо, в 13:00?", "timestamp": base_time + (6 * 24 * 3600) + 900},
            
            # Недавние сообщения (сегодня)
            {"user_id": "user_alice", "content": "Доброе утро всем!", "timestamp": time.time() - 3600},
            {"user_id": "user_charlie", "content": "Привет! Как настроение?", "timestamp": time.time() - 3000},
            {"user_id": "user_bob", "content": "Отлично! Готов к работе", "timestamp": time.time() - 2400},
            {"user_id": "user_alice", "content": "Тогда за дело!", "timestamp": time.time() - 1800},
        ]
        
        return messages

async def main():
    """Главная функция тестирования"""
    tester = SmartMemoryTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())