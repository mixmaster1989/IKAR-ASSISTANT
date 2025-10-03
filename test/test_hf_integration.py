#!/usr/bin/env python3
"""
Простой тест интеграции Hugging Face в систему IKAR.
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к backend
sys.path.append(str(Path(__file__).parent / "backend"))

async def test_huggingface_integration():
    """Тестирует интеграцию Hugging Face"""
    print("🤖 ТЕСТ ИНТЕГРАЦИИ HUGGING FACE")
    print("="*50)
    
    try:
        # Импортируем модуль генерации изображений
        from backend.vision.image_generator import image_generator, get_available_models
        
        print("✅ Модуль image_generator успешно импортирован")
        
        # Получаем доступные модели
        models = get_available_models()
        print(f"📋 Доступные модели: {len(models)}")
        for model_id, model_info in models.items():
            print(f"  • {model_id}: {model_info['name']}")
        
        # Тестируем генерацию изображения
        print("\n🎨 Тестируем генерацию изображения...")
        
        test_prompt = "a beautiful sunset over the ocean, high quality, detailed"
        
        result = await image_generator(
            prompt=test_prompt,
            model="stabilityai/stable-diffusion-3-medium-diffusers",
            width=512,
            height=512
        )
        
        if result:
            print(f"✅ Генерация успешна! Размер изображения: {len(result)} bytes")
            
            # Сохраняем тестовое изображение
            test_file = Path("test_hf_image.png")
            with open(test_file, 'wb') as f:
                f.write(result)
            print(f"💾 Тестовое изображение сохранено: {test_file}")
            
            return True
        else:
            print("❌ Генерация не удалась")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_huggingface_integration())
    
    if success:
        print("\n🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print("Hugging Face интеграция работает корректно.")
    else:
        print("\n💥 ТЕСТ ПРОВАЛЕН!")
        print("Есть проблемы с Hugging Face интеграцией.")
        sys.exit(1) 