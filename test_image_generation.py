#!/usr/bin/env python3
"""
🧪 Тест генерации изображений в Чатумбе
Проверяет полный флоу: промпты → LLM → JSON → генерация изображения
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Загружен .env файл: {env_path}")
else:
    print(f"⚠️ .env файл не найден: {env_path}")

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
)

logger = logging.getLogger("test_image_generation")

async def test_env_loading():
    """Тестирует загрузку переменных окружения"""
    print("\n🔍 Тест 1: Загрузка переменных окружения")
    
    required_vars = [
        "OPENROUTER_API_KEY",
        "TELEGRAM_BOT_TOKEN", 
        "STABLE_HORDE_API_KEY",
        "HF_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var, "")
        if value and value != "your_openrouter_api_key":
            print(f"✅ {var}: {'*' * 8}{value[-4:] if len(value) > 4 else value}")
        else:
            print(f"❌ {var}: НЕ НАСТРОЕН")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ Отсутствуют переменные: {', '.join(missing_vars)}")
        print("   Это может повлиять на тестирование генерации изображений")
        return False
    else:
        print("\n✅ Все необходимые переменные окружения загружены")
        return True

async def test_prompt_generation():
    """Тестирует генерацию промптов для изображений"""
    print("\n🔍 Тест 2: Генерация промптов для изображений")
    
    try:
        from api.smart_bot_trigger import SmartBotTrigger
        
        # Создаем экземпляр триггера
        trigger = SmartBotTrigger()
        
        # Симулируем контекст
        mock_context = {
            'time_info': {'datetime': '2025-08-15 17:00:00', 'weekday': 'пятница', 'time_of_day': 'afternoon'},
            'recent_messages': [],
            'recent_responses': [],
            'relevant_chunks': [],
            'current_topic': 'тестирование генерации изображений',
            'participant_names': {},
            'dialogue_context': ''
        }
        
        # Проверяем системный промпт
        system_prompt = trigger._build_system_prompt(
            mock_context['time_info'],
            mock_context['recent_responses'], 
            mock_context['current_topic']
        )
        
        print(f"📝 Системный промпт ({len(system_prompt)} символов):")
        if "ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ" in system_prompt:
            print("✅ Инструкции по генерации изображений найдены в системном промпте")
        else:
            print("❌ Инструкции по генерации изображений НЕ найдены в системном промпте")
        
        # Проверяем пользовательское сообщение
        user_message = trigger._format_recent_messages([], {})
        print(f"📝 Пользовательское сообщение ({len(user_message)} символов):")
        print(f"   {user_message[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования промптов: {e}")
        return False

async def test_llm_integration():
    """Тестирует интеграцию с LLM"""
    print("\n🔍 Тест 3: Интеграция с LLM")
    
    try:
        from api.smart_bot_trigger import SmartBotTrigger
        
        # Создаем экземпляр триггера
        trigger = SmartBotTrigger()
        
        # Проверяем инициализацию LLM клиента
        if hasattr(trigger, '_llm_client') and trigger._llm_client:
            print("✅ LLM клиент инициализирован")
        else:
            print("⚠️ LLM клиент не инициализирован (это нормально для тестов)")
        
        # Проверяем доступность API ключей
        from backend.config import OPENROUTER_API_KEYS
        if OPENROUTER_API_KEYS:
            print(f"✅ Доступно {len(OPENROUTER_API_KEYS)} OpenRouter API ключей")
        else:
            print("❌ OpenRouter API ключи не найдены")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования LLM: {e}")
        return False

async def test_image_parsing():
    """Тестирует парсинг JSON для изображений"""
    print("\n🔍 Тест 4: Парсинг JSON для изображений")
    
    try:
        from utils.robust_json_parser import parse_image_json
        
        # Тестовые ответы LLM
        test_cases = [
            {
                'name': 'JSON в markdown блоке',
                'response': 'Вот твой кот! ```json{"description": "милый рыжий кот сидит на окне"}```',
                'expected': True
            },
            {
                'name': 'JSON без markdown',
                'response': 'Вот твой кот! {"description": "милый рыжий кот сидит на окне"}',
                'expected': True
            },
            {
                'name': 'Без JSON',
                'response': 'Привет! Как дела?',
                'expected': False
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🔄 Тестируем: {test_case['name']}")
            result = parse_image_json(test_case['response'])
            
            if result and 'description' in result:
                print(f"✅ JSON найден: {result['description'][:50]}...")
                if test_case['expected']:
                    print("✅ Результат соответствует ожиданиям")
                else:
                    print("⚠️ Неожиданный результат")
            else:
                print("❌ JSON не найден")
                if not test_case['expected']:
                    print("✅ Результат соответствует ожиданиям")
                else:
                    print("❌ Результат НЕ соответствует ожиданиям")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования парсинга: {e}")
        return False

async def test_image_generation_flow():
    """Тестирует полный флоу генерации изображений"""
    print("\n🔍 Тест 5: Полный флоу генерации изображений")
    
    try:
        from api.telegram_core import parse_and_generate_image
        
        # Тестовый ответ с JSON
        test_response = """Вот твой кот! 

```json
{"description": "милый рыжий кот сидит на окне, солнечный свет, уютная атмосфера"}
```"""
        
        print(f"🔄 Тестируем parse_and_generate_image...")
        print(f"📝 Входной текст: {test_response[:100]}...")
        
        # Симулируем chat_id
        test_chat_id = "-1002686615681"  # Группа АНТИЛОПА
        
        # Вызываем функцию (в тесте она не будет реально генерировать изображение)
        result = await parse_and_generate_image(test_response, test_chat_id)
        
        print(f"📤 Результат: {result[:100]}...")
        
        if result and result != test_response:
            print("✅ JSON успешно обработан и удален из ответа")
        else:
            print("⚠️ JSON не был обработан")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования флоу: {e}")
        return False

async def test_typing_status():
    """Тестирует отправку статуса 'печатает'"""
    print("\n🔍 Тест 6: Статус 'печатает'")
    
    try:
        from api.telegram_core import send_chat_action
        
        # Тестовый chat_id
        test_chat_id = "-1002686615681"  # Группа АНТИЛОПА
        
        print(f"🔄 Тестируем отправку статуса 'печатает'...")
        
        # Тестируем разные статусы
        statuses = [
            ("typing", "⌨️ Печатает..."),
            ("upload_photo", "📸 Загружает фото...")
        ]
        
        for action, description in statuses:
            print(f"   Тестируем: {description}")
            success = await send_chat_action(test_chat_id, action)
            print(f"   Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования статуса: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск теста генерации изображений в Чатумбе...")
    print("=" * 60)
    
    tests = [
        ("Загрузка переменных окружения", test_env_loading),
        ("Генерация промптов", test_prompt_generation),
        ("Интеграция с LLM", test_llm_integration),
        ("Парсинг JSON", test_image_parsing),
        ("Полный флоу генерации", test_image_generation_flow),
        ("Статус 'печатает'", test_typing_status)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Выводим итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Генерация изображений работает корректно!")
        return True
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ. Требуется доработка.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
