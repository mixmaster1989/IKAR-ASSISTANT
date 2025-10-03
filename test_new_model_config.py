#!/usr/bin/env python3
"""
Тест новой конфигурации с основной моделью openai/gpt-oss-20b:free и fallback
"""

import asyncio
import sys
import os

# Загружаем переменные окружения из .env файла
def load_env_file(env_path: str = ".env"):
    """Загружает переменные окружения из .env файла"""
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Загружаем .env перед импортами
load_env_file()

# Добавляем путь к backend для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.config import LLM_CONFIG
from backend.llm.openrouter import OpenRouterClient
from backend.utils.logger import get_logger

logger = get_logger('new_model_test')

async def test_new_model_config():
    """Тестирует новую конфигурацию с fallback моделью"""
    
    print("🧪 Тестирование новой конфигурации модели")
    print(f"📋 Основная модель: {LLM_CONFIG.get('model', 'не указана')}")
    print(f"🔄 Fallback модель: {LLM_CONFIG.get('fallback_model', 'не указана')}")
    print()
    
    try:
        # Создаем клиент
        client = OpenRouterClient()
        
        # Тестовый промпт
        test_prompt = "Привет! Как дела? Дай краткий ответ."
        
        print("🚀 Тестируем основную модель...")
        response = await client.generate_response(test_prompt)
        print(f"✅ Ответ: {response[:100]}...")
        print()
        
        # Тестируем с явным указанием fallback модели
        print("🔄 Тестируем fallback модель напрямую...")
        fallback_response = await client.generate_response(
            test_prompt, 
            model=LLM_CONFIG.get('fallback_model')
        )
        print(f"✅ Fallback ответ: {fallback_response[:100]}...")
        print()
        
        print("🎉 Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_new_model_config())
    sys.exit(0 if success else 1) 