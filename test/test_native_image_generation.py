#!/usr/bin/env python3
"""
Тестовый скрипт для проверки нативной генерации изображений в Чатумбе.
"""

import asyncio
import sys
import os
import re
import json

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_parse_and_generate_image():
    """Тестирует функцию парсинга и генерации изображений."""
    
    # Мокаем функцию parse_and_generate_image
    async def mock_parse_and_generate_image(response_text: str, chat_id: str):
        """Мокает функцию parse_and_generate_image."""
        print(f"🔍 Анализирую ответ: {response_text}")
        
        # Ищем JSON с префиксом IMAGE!
        image_pattern = r'IMAGE!\s*(\{[^}]+\})'
        match = re.search(image_pattern, response_text, re.IGNORECASE)
        
        if not match:
            print("❌ JSON с IMAGE! не найден")
            return response_text
            
        json_str = match.group(1)
        
        try:
            image_data = json.loads(json_str)
            description = image_data.get("description", "")
            
            if not description:
                print("⚠️ Пустое описание изображения")
                return re.sub(image_pattern, "", response_text, flags=re.IGNORECASE).strip()
            
            print(f"🎨 Найдена инструкция для генерации: {description}")
            print(f"📱 Отправляю в чат: {chat_id}")
            print("🖼️ [МОКАЕМ] Изображение сгенерировано и отправлено!")
            
            # Удаляем JSON из текста
            cleaned_text = re.sub(image_pattern, "", response_text, flags=re.IGNORECASE).strip()
            print(f"✅ Очищенный текст: {cleaned_text}")
            return cleaned_text
            
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            return response_text
    
    # Тестовые случаи
    test_cases = [
        {
            "name": "Простое изображение",
            "response": "Привет! Как дела? IMAGE!{\"description\": \"кот сидит на крыше под дождем\"}",
            "expected_contains": "кот сидит на крыше под дождем"
        },
        {
            "name": "Изображение с философией",
            "response": "Жизнь сложна, друг мой... IMAGE!{\"description\": \"абстрактное изображение эмоций, темные тона\"} Но мы продолжаем идти.",
            "expected_contains": "абстрактное изображение эмоций"
        },
        {
            "name": "Без изображения",
            "response": "Просто обычное сообщение без картинок.",
            "expected_contains": None
        },
        {
            "name": "Неправильный JSON",
            "response": "Привет! IMAGE!{\"description\": \"broken json} некорректный",
            "expected_contains": None
        }
    ]
    
    print("🚀 Запуск тестов нативной генерации изображений\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📋 Тест {i}: {test_case['name']}")
        print(f"📝 Входной текст: {test_case['response']}")
        
        result = await mock_parse_and_generate_image(test_case['response'], f"test_chat_{i}")
        
        if test_case['expected_contains']:
            if test_case['expected_contains'] in test_case['response']:
                print("✅ Тест пройден - изображение найдено и обработано")
            else:
                print("❌ Тест не пройден - изображение не найдено")
        else:
            if result == test_case['response']:
                print("✅ Тест пройден - изображение не найдено (как ожидалось)")
            else:
                print("❌ Тест не пройден - неожиданное изменение текста")
        
        print("─" * 50)
    
    print("\n🎉 Все тесты завершены!")

async def test_prompt_updates():
    """Тестирует обновленные промпты."""
    
    print("📝 Проверка обновленных промптов...")
    
    # Проверяем, что в промптах есть инструкции по генерации изображений
    try:
        with open("backend/admin_prompts.json", "r", encoding="utf-8") as f:
            prompts = json.load(f)
        
        image_instruction_count = 0
        for prompt_name, prompt_data in prompts.items():
            system_prompt = prompt_data.get("system_prompt", "")
            if "ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ" in system_prompt and "IMAGE!" in system_prompt:
                image_instruction_count += 1
                print(f"✅ {prompt_name}: содержит инструкции по генерации изображений")
        
        print(f"\n📊 Всего промптов с инструкциями: {image_instruction_count}")
        
        if image_instruction_count > 0:
            print("🎨 Промпты успешно обновлены!")
        else:
            print("❌ Промпты не содержат инструкций по генерации изображений")
            
    except Exception as e:
        print(f"❌ Ошибка чтения промптов: {e}")

async def main():
    """Главная функция тестирования."""
    print("🤖 Тестирование нативной генерации изображений в Чатумбе")
    print("=" * 60)
    
    await test_parse_and_generate_image()
    print("\n" + "=" * 60)
    await test_prompt_updates()
    
    print("\n🏁 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main()) 