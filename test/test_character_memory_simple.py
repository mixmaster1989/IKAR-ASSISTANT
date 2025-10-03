#!/usr/bin/env python3
"""
🧠 ПРОСТОЙ ТЕСТ СИСТЕМЫ ПАМЯТИ ХАРАКТЕРА
Локальная версия без зависимостей от БД
"""

import time
import json
from pathlib import Path

class SimpleCharacterMemory:
    """Упрощенная версия системы памяти характера"""
    
    def __init__(self):
        self.character_memory = {}  # {chat_id: {"personality_traits": [], "key_events": [], "relationships": {}, "last_update": timestamp}}
    
    def _get_character_memory(self, chat_id: str) -> dict:
        """Получение памяти характера для чата"""
        if chat_id not in self.character_memory:
            self.character_memory[chat_id] = {
                "personality_traits": [],
                "key_events": [],
                "relationships": {},
                "last_update": time.time()
            }
        return self.character_memory[chat_id]

    def _update_character_memory(self, chat_id: str, message_text: str, response: str):
        """Обновление памяти характера на основе взаимодействия"""
        memory = self._get_character_memory(chat_id)
        
        # Обновляем время последнего взаимодействия
        memory["last_update"] = time.time()
        
        # Простой анализ сообщения для извлечения черт характера
        message_lower = message_text.lower()
        response_lower = response.lower()
        
        # Анализируем настроение в сообщении
        if any(word in message_lower for word in ["грустно", "печально", "тоска", "устал", "грустный"]):
            if "меланхоличный" not in memory["personality_traits"]:
                memory["personality_traits"].append("меланхоличный")
        
        if any(word in message_lower for word in ["весело", "радость", "смех", "оптимист", "оптимистом"]):
            if "оптимистичный" not in memory["personality_traits"]:
                memory["personality_traits"].append("оптимистичный")
        
        if any(word in message_lower for word in ["злость", "раздражение", "бесит", "агрессия", "раздражаешь"]):
            if "раздражительный" not in memory["personality_traits"]:
                memory["personality_traits"].append("раздражительный")
        
        if any(word in message_lower for word in ["философия", "смысл", "жизнь", "глубоко", "философствуй"]):
            if "философский" not in memory["personality_traits"]:
                memory["personality_traits"].append("философский")
        
        if any(word in message_lower for word in ["крипта", "биткоин", "трейдинг", "деньги", "крипте"]):
            if "технарь" not in memory["personality_traits"]:
                memory["personality_traits"].append("технарь")
        
        # Ограничиваем количество черт (храним последние 5)
        if len(memory["personality_traits"]) > 5:
            memory["personality_traits"] = memory["personality_traits"][-5:]
        
        # Добавляем ключевое событие
        event = f"Взаимодействие: {message_text[:50]}..."
        if event not in memory["key_events"]:
            memory["key_events"].append(event)
        
        # Ограничиваем количество событий (храним последние 10)
        if len(memory["key_events"]) > 10:
            memory["key_events"] = memory["key_events"][-10:]

    def _build_character_context(self, chat_id: str) -> str:
        """Создание контекста характера без упоминания конкретных событий"""
        memory = self._get_character_memory(chat_id)
        
        # Если память пустая, возвращаем базовый контекст
        if not memory["personality_traits"] and not memory["key_events"]:
            return ""
        
        context_parts = []
        
        # Добавляем черты характера, если они есть
        if memory["personality_traits"]:
            traits = ", ".join(memory["personality_traits"][-3:])  # Последние 3 черты
            context_parts.append(f"Ты проявляешь себя как: {traits}")
        
        # Добавляем общие отношения, если они есть
        if memory["relationships"]:
            relationship_desc = []
            for user, relation in list(memory["relationships"].items())[:3]:  # Максимум 3 отношения
                relationship_desc.append(f"к {user}: {relation}")
            if relationship_desc:
                context_parts.append(f"Твои отношения: {', '.join(relationship_desc)}")
        
        if context_parts:
            return f"\n\n🎭 КОНТЕКСТ ТВОЕГО ХАРАКТЕРА:\n" + "\n".join(context_parts) + "\n\nВАЖНО: Не упоминай конкретные прошлые события в ответе. Просто будь собой, учитывая свой характер."
        
        return ""

def test_character_memory():
    """Тест системы памяти характера"""
    print("🧠 ПРОСТОЙ ТЕСТ СИСТЕМЫ ПАМЯТИ ХАРАКТЕРА")
    print("=" * 60)
    
    memory_system = SimpleCharacterMemory()
    chat_id = "test_chat_123"
    
    # Симулируем несколько взаимодействий
    test_messages = [
        "бот, как дела?",
        "бот, что думаешь о крипте?",
        "бот, ты грустный сегодня",
        "бот, расскажи анекдот",
        "бот, как настроение?",
        "бот, философствуй о жизни",
        "бот, ты раздражаешь меня",
        "бот, будь оптимистом"
    ]
    
    print("📝 Симулируем последовательные взаимодействия:")
    print()
    
    for i, message in enumerate(test_messages, 1):
        print(f"💬 Сообщение {i}: {message}")
        
        # Симулируем ответ (в реальности это будет AI)
        fake_response = f"Ответ на сообщение {i}: {message}"
        
        # Обновляем память характера
        memory_system._update_character_memory(chat_id, message, fake_response)
        
        # Показываем текущую память
        memory = memory_system._get_character_memory(chat_id)
        print(f"   📚 Память: {len(memory['key_events'])} событий, {len(memory['personality_traits'])} черт характера")
        if memory['personality_traits']:
            print(f"   🎭 Черты: {', '.join(memory['personality_traits'])}")
        
        # Показываем контекст характера
        context = memory_system._build_character_context(chat_id)
        if context:
            print(f"   🎭 Контекст: {context[:150]}...")
        else:
            print(f"   🎭 Контекст: (пустой)")
        print()
    
    print("✅ Тест завершен!")
    print("\n🎯 РЕЗУЛЬТАТ:")
    print("- Бот будет помнить свой характер")
    print("- Не будет упоминать конкретные прошлые события")
    print("- Будет отвечать на текущий момент")
    print("- Сохранит последовательность характера")
    
    # Показываем финальную память
    final_memory = memory_system._get_character_memory(chat_id)
    print(f"\n📊 ФИНАЛЬНАЯ ПАМЯТЬ:")
    print(f"Черты характера: {final_memory['personality_traits']}")
    print(f"Количество событий: {len(final_memory['key_events'])}")

if __name__ == "__main__":
    test_character_memory() 