#!/usr/bin/env python3
"""
Тест совместимости модели openai/gpt-oss-20b:free с архитектурой проекта IKAR
Проверяет формат ответов и совместимость с существующими компонентами
Использует существующую архитектуру проекта с системой API ключей
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any, List
import requests
from datetime import datetime

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

from backend.config import OPENROUTER_API_KEYS, LLM_CONFIG
from backend.utils.logger import get_logger

logger = get_logger('model_compatibility_test')

class ModelCompatibilityTester:
    """Тестер совместимости моделей с архитектурой проекта"""
    
    def __init__(self):
        # Используем существующую систему API ключей из проекта
        self.api_keys = OPENROUTER_API_KEYS.copy()
        if not self.api_keys:
            raise ValueError("OpenRouter API ключи не найдены в переменных окружения")
        
        logger.info(f"🔑 Найдено {len(self.api_keys)} API ключей OpenRouter")
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.current_key_index = 0
        
        # Тестовые промпты для проверки различных сценариев
        self.test_prompts = {
            "basic_chat": "Привет! Как дела?",
            "json_response": "Отвечай строго в формате JSON: {\"status\": \"ok\", \"message\": \"test\"}",
            "crypto_analysis": "Проанализируй криптовалюту Bitcoin. Дай краткий анализ в 2-3 предложения.",
            "memory_format": "Создай краткое воспоминание о разговоре в формате: тема, важность (0-1), краткое описание",
            "image_generation": "Нарисуй котика. Добавь в конец JSON: {\"description\": \"описание для генерации\"}",
            "system_prompt": "Ты помощник. Отвечай кратко и по делу."
        }
    
    def get_current_api_key(self) -> str:
        """Получение текущего API ключа (как в проекте)"""
        if not self.api_keys:
            raise ValueError("API ключи OpenRouter не настроены")
        return self.api_keys[self.current_key_index]
    
    def rotate_api_key(self):
        """Ротация API ключей (как в проекте)"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"🔄 Переключение на API ключ #{self.current_key_index + 1}")
    
    def get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запроса (как в проекте)"""
        return {
            "Authorization": f"Bearer {self.get_current_api_key()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/ikar",
            "X-Title": "IKAR Collective Mind"
        }
    
    async def test_model_response_format(self, model: str) -> Dict[str, Any]:
        """Тестирует формат ответа модели"""
        logger.info(f"🧪 Тестируем модель: {model}")
        
        results = {}
        
        for test_name, prompt in self.test_prompts.items():
            try:
                logger.info(f"  📝 Тест: {test_name}")
                
                # Подготавливаем сообщения
                messages = []
                if test_name == "system_prompt":
                    messages = [
                        {"role": "system", "content": "Ты помощник. Отвечай кратко и по делу."},
                        {"role": "user", "content": "Привет!"}
                    ]
                else:
                    messages = [{"role": "user", "content": prompt}]
                
                # Отправляем запрос с ротацией ключей при ошибках
                max_retries = len(self.api_keys)
                for attempt in range(max_retries):
                    try:
                        payload = {
                            "model": model,
                            "messages": messages,
                            "temperature": 0.7,
                            "max_tokens": 1000
                        }
                        
                        response = requests.post(
                            url=self.base_url,
                            headers=self.get_headers(),
                            data=json.dumps(payload),
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Анализируем структуру ответа
                            analysis = self._analyze_response_structure(data, test_name)
                            results[test_name] = {
                                "status": "success",
                                "response_time": response.elapsed.total_seconds(),
                                "analysis": analysis,
                                "raw_response": data,
                                "api_key_used": self.current_key_index
                            }
                            
                            logger.info(f"    ✅ Успешно: {analysis['content_length']} символов (ключ #{self.current_key_index + 1})")
                            break  # Успешно, выходим из цикла retry
                            
                        elif response.status_code == 429:  # Rate limit
                            logger.warning(f"    ⚠️ Rate limit для ключа #{self.current_key_index + 1}")
                            self.rotate_api_key()
                            if attempt == max_retries - 1:  # Последняя попытка
                                results[test_name] = {
                                    "status": "error",
                                    "error": f"Rate limit на всех ключах: {response.text}",
                                    "response_time": response.elapsed.total_seconds()
                                }
                        else:
                            logger.error(f"    ❌ Ошибка HTTP {response.status_code} для ключа #{self.current_key_index + 1}")
                            self.rotate_api_key()
                            if attempt == max_retries - 1:  # Последняя попытка
                                results[test_name] = {
                                    "status": "error",
                                    "error": f"HTTP {response.status_code}: {response.text}",
                                    "response_time": response.elapsed.total_seconds()
                                }
                                
                    except requests.exceptions.RequestException as e:
                        logger.error(f"    ❌ Ошибка запроса для ключа #{self.current_key_index + 1}: {e}")
                        self.rotate_api_key()
                        if attempt == max_retries - 1:  # Последняя попытка
                            results[test_name] = {
                                "status": "error",
                                "error": f"Ошибка запроса: {e}"
                            }
                
                # Небольшая пауза между тестами
                await asyncio.sleep(0.5)
                    
            except Exception as e:
                results[test_name] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"    ❌ Исключение: {e}")
        
        return results
    
    def _analyze_response_structure(self, data: Dict[str, Any], test_name: str) -> Dict[str, Any]:
        """Анализирует структуру ответа модели"""
        analysis = {
            "has_choices": "choices" in data,
            "choices_count": len(data.get("choices", [])),
            "has_message": False,
            "has_content": False,
            "content_length": 0,
            "content_type": "unknown",
            "json_compatible": False,
            "has_finish_reason": False,
            "usage_info": "usage" in data
        }
        
        if analysis["has_choices"] and data["choices"]:
            choice = data["choices"][0]
            analysis["has_message"] = "message" in choice
            analysis["has_finish_reason"] = "finish_reason" in choice
            
            if analysis["has_message"]:
                message = choice["message"]
                analysis["has_content"] = "content" in message
                
                if analysis["has_content"]:
                    content = message["content"]
                    analysis["content_length"] = len(content)
                    
                    # Определяем тип контента
                    if content.strip().startswith("{") and content.strip().endswith("}"):
                        analysis["content_type"] = "json"
                        try:
                            json.loads(content)
                            analysis["json_compatible"] = True
                        except:
                            analysis["json_compatible"] = False
                    elif "```json" in content:
                        analysis["content_type"] = "markdown_json"
                    else:
                        analysis["content_type"] = "text"
        
        return analysis
    
    async def test_models_comparison(self) -> Dict[str, Any]:
        """Сравнивает новую модель с текущей"""
        logger.info("🔄 Сравниваем модели...")
        
        models = {
            "new_model": "openai/gpt-oss-20b:free",
            "current_model": "deepseek/deepseek-r1-0528:free"
        }
        
        comparison_results = {}
        
        for model_name, model_id in models.items():
            logger.info(f"🔍 Тестируем {model_name}: {model_id}")
            results = await self.test_model_response_format(model_id)
            comparison_results[model_name] = results
            
            # Небольшая пауза между моделями
            await asyncio.sleep(1)
        
        return comparison_results
    
    def generate_compatibility_report(self, results: Dict[str, Any]) -> str:
        """Генерирует отчет о совместимости"""
        report = []
        report.append("# 📊 ОТЧЕТ О СОВМЕСТИМОСТИ МОДЕЛЕЙ")
        report.append(f"Дата тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"API ключей в системе: {len(self.api_keys)}")
        report.append("")
        
        for model_name, model_results in results.items():
            report.append(f"## 🤖 {model_name.upper()}")
            report.append("")
            
            success_count = 0
            total_count = len(model_results)
            
            for test_name, test_result in model_results.items():
                status = test_result["status"]
                if status == "success":
                    success_count += 1
                    analysis = test_result["analysis"]
                    report.append(f"### ✅ {test_name}")
                    report.append(f"- Статус: {status}")
                    report.append(f"- Время ответа: {test_result['response_time']:.2f}с")
                    report.append(f"- API ключ: #{test_result.get('api_key_used', 0) + 1}")
                    report.append(f"- Длина контента: {analysis['content_length']} символов")
                    report.append(f"- Тип контента: {analysis['content_type']}")
                    report.append(f"- JSON совместимость: {'✅' if analysis['json_compatible'] else '❌'}")
                    report.append("")
                else:
                    report.append(f"### ❌ {test_name}")
                    report.append(f"- Статус: {status}")
                    report.append(f"- Ошибка: {test_result.get('error', 'Неизвестная ошибка')}")
                    report.append("")
            
            report.append(f"**Итого: {success_count}/{total_count} тестов пройдено успешно**")
            report.append("")
        
        # Рекомендации
        report.append("## 💡 РЕКОМЕНДАЦИИ")
        report.append("")
        
        new_model_results = results.get("new_model", {})
        current_model_results = results.get("current_model", {})
        
        if new_model_results and current_model_results:
            new_success = sum(1 for r in new_model_results.values() if r["status"] == "success")
            current_success = sum(1 for r in current_model_results.values() if r["status"] == "success")
            
            if new_success >= current_success:
                report.append("✅ **Новая модель совместима с архитектурой проекта**")
                report.append("- Можно использовать как основную модель")
                report.append("- DeepSeek можно оставить как fallback")
                report.append("- Рекомендуется обновить LLM_CONFIG в config.py")
            else:
                report.append("⚠️ **Новая модель имеет проблемы совместимости**")
                report.append("- Рекомендуется дополнительное тестирование")
                report.append("- Возможно потребуется адаптация кода")
                report.append("- Оставить DeepSeek как основную модель")
        
        return "\n".join(report)

async def main():
    """Основная функция тестирования"""
    try:
        logger.info("🚀 Запуск теста совместимости моделей")
        logger.info(f"🔑 Используем архитектуру проекта с {len(OPENROUTER_API_KEYS)} API ключами")
        
        tester = ModelCompatibilityTester()
        
        # Запускаем сравнение моделей
        results = await tester.test_models_comparison()
        
        # Генерируем отчет
        report = tester.generate_compatibility_report(results)
        
        # Сохраняем отчет
        report_file = "model_compatibility_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info(f"📄 Отчет сохранен в {report_file}")
        
        # Выводим краткую сводку
        print("\n" + "="*50)
        print("КРАТКАЯ СВОДКА ТЕСТИРОВАНИЯ")
        print("="*50)
        
        for model_name, model_results in results.items():
            success_count = sum(1 for r in model_results.values() if r["status"] == "success")
            total_count = len(model_results)
            print(f"{model_name}: {success_count}/{total_count} тестов пройдено")
        
        print(f"\nПолный отчет: {report_file}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 