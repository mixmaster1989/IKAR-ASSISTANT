#!/usr/bin/env python3
"""
Тест интеграции Pollinations.ai в проект IKAR
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
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

logger = logging.getLogger("test_pollinations_integration")

async def test_pollinations_primary():
    """Тестирует Pollinations как основной генератор"""
    print("\n🎨 Тест 1: Pollinations как основной генератор")
    print("=" * 60)
    
    try:
        from backend.vision.image_generator import image_generator, get_available_models
        
        # Получаем список моделей
        models = await get_available_models()
        print(f"📋 Доступно моделей: {len(models)}")
        
        # Показываем Pollinations модели
        pollinations_models = [k for k, v in models.items() if v.get('type') == 'pollinations']
        print(f"🎨 Pollinations модели: {pollinations_models}")
        
        # Тестируем генерацию через Pollinations
        test_prompt = "Robot holding a red skateboard"
        print(f"📝 Тестовый промпт: {test_prompt}")
        
        image_data = await image_generator(
            prompt=test_prompt,
            model="pollinations_flux",  # Явно указываем Pollinations
            width=1024,
            height=1024
        )
        
        if image_data:
            print(f"✅ Pollinations успешно сгенерировал изображение! Размер: {len(image_data)} bytes")
            
            # Сохраняем изображение
            os.makedirs("test_images", exist_ok=True)
            with open("test_images/pollinations_test.png", "wb") as f:
                f.write(image_data)
            print("💾 Изображение сохранено: test_images/pollinations_test.png")
            return True
        else:
            print("❌ Pollinations не смог сгенерировать изображение")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования Pollinations: {e}")
        return False

async def test_huggingface_fallback():
    """Тестирует HuggingFace как fallback"""
    print("\n🤖 Тест 2: HuggingFace как fallback")
    print("=" * 60)
    
    try:
        from backend.vision.image_generator import image_generator
        
        # Тестируем генерацию через HuggingFace
        test_prompt = "A beautiful sunset over mountains"
        print(f"📝 Тестовый промпт: {test_prompt}")
        
        image_data = await image_generator(
            prompt=test_prompt,
            model="hf_stabilityai/stable-diffusion-3-medium-diffusers",  # Явно указываем HuggingFace
            width=512,
            height=512
        )
        
        if image_data:
            print(f"✅ HuggingFace успешно сгенерировал изображение! Размер: {len(image_data)} bytes")
            
            # Сохраняем изображение
            os.makedirs("test_images", exist_ok=True)
            with open("test_images/huggingface_test.jpg", "wb") as f:
                f.write(image_data)
            print("💾 Изображение сохранено: test_images/huggingface_test.jpg")
            return True
        else:
            print("❌ HuggingFace не смог сгенерировать изображение")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования HuggingFace: {e}")
        return False

async def test_auto_fallback():
    """Тестирует автоматический fallback"""
    print("\n🔄 Тест 3: Автоматический fallback")
    print("=" * 60)
    
    try:
        from backend.vision.image_generator import image_generator
        
        # Тестируем без указания модели (должен использовать Pollinations по умолчанию)
        test_prompt = "A cyberpunk city at night"
        print(f"📝 Тестовый промпт: {test_prompt}")
        
        image_data = await image_generator(
            prompt=test_prompt,
            width=1024,
            height=1024
        )
        
        if image_data:
            print(f"✅ Автоматический генератор успешно сгенерировал изображение! Размер: {len(image_data)} bytes")
            
            # Сохраняем изображение
            os.makedirs("test_images", exist_ok=True)
            with open("test_images/auto_test.png", "wb") as f:
                f.write(image_data)
            print("💾 Изображение сохранено: test_images/auto_test.png")
            return True
        else:
            print("❌ Автоматический генератор не смог сгенерировать изображение")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования автоматического fallback: {e}")
        return False

async def test_backward_compatibility():
    """Тестирует обратную совместимость"""
    print("\n🔄 Тест 4: Обратная совместимость")
    print("=" * 60)
    
    try:
        from backend.vision.image_generator import (
            generate_image_hf,
            generate_image_stable_horde,
            generate_image_replicate,
            generate_image_deepai
        )
        
        test_prompt = "A cute cat"
        print(f"📝 Тестовый промпт: {test_prompt}")
        
        # Тестируем старые функции
        functions_to_test = [
            ("generate_image_hf", generate_image_hf),
            ("generate_image_stable_horde", generate_image_stable_horde),
            ("generate_image_replicate", generate_image_replicate),
            ("generate_image_deepai", generate_image_deepai)
        ]
        
        success_count = 0
        
        for func_name, func in functions_to_test:
            try:
                print(f"🔄 Тестируем {func_name}...")
                image_data = await func(test_prompt, width=512, height=512)
                
                if image_data:
                    print(f"✅ {func_name} работает! Размер: {len(image_data)} bytes")
                    success_count += 1
                else:
                    print(f"❌ {func_name} не сработал")
                    
            except Exception as e:
                print(f"❌ {func_name} ошибка: {e}")
        
        print(f"📊 Обратная совместимость: {success_count}/{len(functions_to_test)} функций работают")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Ошибка тестирования обратной совместимости: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование интеграции Pollinations.ai в проект IKAR")
    print("=" * 80)
    
    tests = [
        ("Pollinations основной", test_pollinations_primary),
        ("HuggingFace fallback", test_huggingface_fallback),
        ("Автоматический fallback", test_auto_fallback),
        ("Обратная совместимость", test_backward_compatibility)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"🧪 {test_name}")
        print('='*80)
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: ПРОШЕЛ")
            else:
                print(f"❌ {test_name}: НЕ ПРОШЕЛ")
                
        except Exception as e:
            print(f"❌ {test_name}: ОШИБКА - {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print(f"\n{'='*80}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print('='*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОШЕЛ" if result else "❌ НЕ ПРОШЕЛ"
        print(f"{test_name}: {status}")
    
    print(f"\n📈 Результат: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно! Интеграция работает!")
    elif passed > 0:
        print("⚠️ Частично работает. Проверьте ошибки выше.")
    else:
        print("❌ Интеграция не работает. Требуется исправление.")

if __name__ == "__main__":
    asyncio.run(main())
