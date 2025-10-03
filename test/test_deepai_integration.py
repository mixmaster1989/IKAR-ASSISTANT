#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции с DeepAI API
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

async def test_deepai_integration():
    """Тестирует интеграцию с DeepAI API"""
    
    print("🧪 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ С DEEPAI")
    print("=" * 50)
    
    # Проверяем наличие API ключа
    api_key = os.environ.get("DEEPAI_API_KEY", "")
    if not api_key:
        print("❌ DEEPAI_API_KEY не найден в переменных окружения")
        print("   Добавьте DEEPAI_API_KEY=your_key в файл .env")
        return False
    
    print(f"✅ API ключ найден: ...{api_key[-8:] if len(api_key) > 8 else api_key}")
    
    try:
        # Импортируем модуль генерации изображений
        from vision.image_generator import image_generator, get_available_models
        
        print("\n📋 Доступные модели:")
        models = get_available_models()
        for model_id, model_info in models.items():
            print(f"   • {model_id}: {model_info['name']} - {model_info['description']}")
        
        print(f"\n🎨 Тестируем генерацию изображения...")
        print("   Промпт: 'a beautiful sunset over the ocean'")
        print("   Модель: text2img")
        print("   Размер: 512x512")
        
        # Тестируем генерацию
        result = await image_generator(
            prompt="a beautiful sunset over the ocean",
            model="text2img",
            width=512,
            height=512,
            timeout=300
        )
        
        if result:
            print(f"✅ Генерация успешна!")
            print(f"   Размер изображения: {len(result)} bytes")
            
            # Сохраняем тестовое изображение
            test_image_path = Path("temp") / "test_deepai_image.png"
            test_image_path.parent.mkdir(exist_ok=True)
            
            with open(test_image_path, "wb") as f:
                f.write(result)
            
            print(f"   Изображение сохранено: {test_image_path}")
            print(f"   Проверьте файл для оценки качества")
            
            return True
        else:
            print("❌ Генерация не удалась")
            return False
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

async def test_translation():
    """Тестирует перевод промптов"""
    
    print("\n🌍 ТЕСТИРОВАНИЕ ПЕРЕВОДА ПРОМПТОВ")
    print("=" * 40)
    
    try:
        from vision.image_generator import translate_prompt_to_english
        
        test_prompts = [
            "красивый закат над океаном",
            "кот сидит на крыше дома",
            "киберпанк город с неоновыми огнями",
            "a beautiful sunset over the ocean"  # уже на английском
        ]
        
        for prompt in test_prompts:
            print(f"\n📝 Исходный промпт: '{prompt}'")
            translated = await translate_prompt_to_english(prompt)
            print(f"🔄 Переведенный промпт: '{translated}'")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка перевода: {e}")
        return False

async def test_api_endpoints():
    """Тестирует API эндпоинты"""
    
    print("\n🔌 ТЕСТИРОВАНИЕ API ЭНДПОИНТОВ")
    print("=" * 40)
    
    try:
        import aiohttp
        
        # Тестируем эндпоинт моделей
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:6666/api/image/models") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ GET /api/image/models - {len(data.get('models', []))} моделей")
                else:
                    print(f"❌ GET /api/image/models - статус {response.status}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка API тестирования: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    
    print("🚀 ЗАПУСК ТЕСТОВ DEEPAI ИНТЕГРАЦИИ")
    print("=" * 60)
    
    # Тест 1: Базовая интеграция
    test1_result = await test_deepai_integration()
    
    # Тест 2: Перевод промптов
    test2_result = await test_translation()
    
    # Тест 3: API эндпоинты (если сервер запущен)
    try:
        test3_result = await test_api_endpoints()
    except:
        print("\n⚠️  API тестирование пропущено (сервер не запущен)")
        test3_result = True
    
    # Итоговый результат
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"   Базовая интеграция: {'✅' if test1_result else '❌'}")
    print(f"   Перевод промптов: {'✅' if test2_result else '❌'}")
    print(f"   API эндпоинты: {'✅' if test3_result else '❌'}")
    
    overall_result = test1_result and test2_result and test3_result
    
    if overall_result:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("   DeepAI интеграция работает корректно")
    else:
        print("\n❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("   Проверьте настройки и логи")
    
    return overall_result

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 