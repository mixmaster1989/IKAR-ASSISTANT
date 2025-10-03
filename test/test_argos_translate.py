#!/usr/bin/env python3
"""
Тест Argos Translate для перевода промптов
"""
import asyncio
import sys
import os

# Добавляем путь к backend
sys.path.append('backend')

async def test_argos_translate():
    """Тестирует работу Argos Translate"""
    
    print("🧪 Тестируем Argos Translate...")
    
    # Тестовые промпты
    test_prompts = [
        "робот-механик бьёт кувалдой по серверу",
        "девушка в красном платье на фоне заката",
        "киберпанк город с неоновыми огнями",
        "космический корабль в открытом космосе"
    ]
    
    try:
        from backend.vision.image_generator import translate_prompt_to_english
        
        for prompt in test_prompts:
            print(f"\n📝 Исходный промпт: {prompt}")
            translated = await translate_prompt_to_english(prompt)
            print(f"🌍 Перевод: {translated}")
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Установите Argos Translate: pip install argostranslate")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_argos_translate()) 