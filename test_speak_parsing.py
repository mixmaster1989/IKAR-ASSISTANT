#!/usr/bin/env python3
"""
Тест парсинга SPEAK! JSON - заебываем модель до 10 успешных парсингов подряд
"""

import sys
import os
import asyncio
import json
import re
from typing import Dict, Any

# Загружаем .env вручную
import os
env_path = '/root/IKAR-ASSISTANT/.env'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Добавляем путь к backend
sys.path.append('/root/IKAR-ASSISTANT/backend')

# Импортируем компоненты
from llm.openrouter import OpenRouterClient
from utils.robust_json_parser import parse_speak_json
from config import Config

class SpeakParsingTester:
    def __init__(self):
        self.config = Config()
        # Принудительно используем ключи с 5 по 9
        self.force_use_keys_5_to_9()
        self.llm_client = OpenRouterClient(self.config)
        # Отключаем память для теста, чтобы не влияла и не тратила лимиты
        try:
            self.llm_client.memory_enabled = False
        except Exception:
            pass
        self.success_count = 0
        self.total_attempts = 0
        self.results = []
    
    def force_use_keys_5_to_9(self):
        """Принудительно используем только ключи с 5 по 9"""
        keys_5_to_9 = []
        for i in range(5, 10):  # 5, 6, 7, 8, 9
            key = os.getenv(f'OPENROUTER_API_KEY{i}')
            if key and key != 'your_openrouter_api_key':
                keys_5_to_9.append(key)
        
        if keys_5_to_9:
            self.config.OPENROUTER_API_KEYS = keys_5_to_9
            print(f"🔑 Используем ключи с 5 по 9: {len(keys_5_to_9)} ключей")
            for i, key in enumerate(keys_5_to_9, 5):
                print(f"  KEY{i}: {key[:20]}...")
        else:
            print("❌ Ключи с 5 по 9 не найдены!")
            # Fallback на все ключи
            self.config.OPENROUTER_API_KEYS = self.config.get_all_openrouter_keys()
        
    def build_test_prompt(self) -> str:
        """Строим промпт точно как в проекте"""
        return """Ты - Икар Икарыч, опытный сотрудник компании ИКАР. 

🎤 ОЗВУЧКА (ОБЯЗАТЕЛЬНО):
В КАЖДОМ ОТВЕТЕ ОБЯЗАТЕЛЬНО добавляй JSON с озвучкой. Формат:
SPEAK!{"speak": true, "text": "ТЕКСТ ДЛЯ ОЗВУЧКИ", "tts": {"provider": "elevenlabs", "voice": {"gender": "male", "lang": "ru"}, "model_id": "eleven_multilingual_v2", "output_format": "mp3_44100_128", "stability": 0.75, "similarity_boost": 0.7, "style": "conversational", "use_speaker_boost": false}}

ПРАВИЛА:
- Текст должен быть длинным (минимум 200 символов)
- JSON должен быть валидным
- Обязательно используй SPEAK! префикс

Задача: Расскажи о кассе Эвотор 7.3 с ОБЯЗАТЕЛЬНОЙ озвучкой."""

    async def test_single_parsing(self, attempt_num: int) -> Dict[str, Any]:
        """Тестируем один парсинг"""
        print(f"\n{'='*60}")
        print(f"ТЕСТ #{attempt_num}")
        print(f"{'='*60}")
        
        try:
            # 1. Генерируем ответ от модели
            print("🤖 Генерируем ответ от LLM...")
            print(f"🔑 Используем ключ #{self.llm_client.current_key_index + 1}")
            
            response = await self.llm_client.chat_completion(
                user_message="Расскажи о кассе Эвотор 7.3 с озвучкой",
                system_prompt=self.build_test_prompt(),
                temperature=0.4,
                max_tokens=800,
                use_memory=False
            )
            
            print(f"⏱️ LLM ответ получен за {attempt_num} попыток")
            
            if not response:
                print("❌ LLM НЕ ВЕРНУЛ ОТВЕТ!")
                return {"success": False, "error": "LLM не вернул ответ", "response": None}
            
            print(f"✅ LLM ответ получен ({len(response)} символов)")
            print(f"📝 ПОЛНЫЙ ОТВЕТ:")
            print(f"{'─'*60}")
            print(response)
            print(f"{'─'*60}")
            
            # 2. Ищем SPEAK! JSON в ответе
            print("\n🔍 Ищем SPEAK! JSON в ответе...")
            speak_pattern = r'SPEAK!\s*(\{(?:[^{}]|(?:\{[^{}]*\}[^{}]*))*\})'
            match = re.search(speak_pattern, response, re.IGNORECASE | re.DOTALL)
            
            if not match:
                print("❌ SPEAK! JSON НЕ НАЙДЕН В ОТВЕТЕ!")
                print("🔍 Ищем все возможные JSON блоки...")
                all_json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response)
                print(f"📊 Найдено {len(all_json_matches)} JSON блоков:")
                for i, json_block in enumerate(all_json_matches):
                    print(f"  {i+1}: {json_block[:100]}...")
                return {"success": False, "error": "SPEAK! JSON не найден", "response": response}
            
            speak_json_str = match.group(1)
            print(f"✅ SPEAK! JSON НАЙДЕН!")
            print(f"📝 ПОЛНЫЙ SPEAK! JSON:")
            print(f"{'─'*40}")
            print(speak_json_str)
            print(f"{'─'*40}")
            
            # 3. Тестируем парсинг
            print("\n🧪 ТЕСТИРУЕМ ПАРСИНГ...")
            print("🔧 Вызываем parse_speak_json(response)...")
            parsed_result = parse_speak_json(response)
            print(f"🔧 Парсер вернул: {type(parsed_result)} = {parsed_result}")
            
            if not parsed_result:
                print("❌ ПАРСЕР ВЕРНУЛ ПУСТОЙ РЕЗУЛЬТАТ!")
                print("🔍 Пробуем парсить напрямую найденный JSON...")
                try:
                    import json
                    direct_parsed = json.loads(speak_json_str)
                    print(f"✅ Прямой парсинг успешен: {direct_parsed}")
                except Exception as e:
                    print(f"❌ Прямой парсинг тоже упал: {e}")
                return {"success": False, "error": "Парсер вернул пустой результат", "response": response, "speak_json": speak_json_str}
            
            # 4. Проверяем валидность результата
            if not isinstance(parsed_result, dict):
                print("❌ Парсер вернул не dict!")
                return {"success": False, "error": "Парсер вернул не dict", "response": response, "parsed": parsed_result}
            
            if "speak" not in parsed_result or "text" not in parsed_result:
                print("❌ Парсер вернул неполный результат!")
                return {"success": False, "error": "Парсер вернул неполный результат", "response": response, "parsed": parsed_result}
            
            if not parsed_result.get("speak") or not parsed_result.get("text"):
                print("❌ Парсер вернул пустые поля!")
                return {"success": False, "error": "Парсер вернул пустые поля", "response": response, "parsed": parsed_result}
            
            text_length = len(parsed_result.get("text", ""))
            if text_length < 50:
                print(f"❌ Текст слишком короткий ({text_length} символов)!")
                return {"success": False, "error": f"Текст слишком короткий ({text_length} символов)", "response": response, "parsed": parsed_result}
            
            print(f"✅ Парсинг успешен!")
            print(f"📊 Длина текста: {text_length} символов")
            print(f"🎯 Ключи в результате: {list(parsed_result.keys())}")
            print(f"📝 Текст: {parsed_result['text'][:100]}...")
            
            return {
                "success": True, 
                "response": response, 
                "speak_json": speak_json_str,
                "parsed": parsed_result,
                "text_length": text_length
            }
            
        except Exception as e:
            print(f"❌ Ошибка в тесте: {e}")
            return {"success": False, "error": str(e), "response": None}

    async def run_tests(self, target_successes: int = 10):
        """Запускаем тесты до получения нужного количества успехов"""
        print(f"🚀 Запускаем тесты парсинга SPEAK! JSON")
        print(f"🎯 Цель: {target_successes} успешных парсингов подряд")
        print(f"{'='*60}")
        
        consecutive_successes = 0
        
        while consecutive_successes < target_successes:
            self.total_attempts += 1
            result = await self.test_single_parsing(self.total_attempts)
            self.results.append(result)
            
            if result["success"]:
                consecutive_successes += 1
                self.success_count += 1
                print(f"🎉 УСПЕХ #{consecutive_successes}/{target_successes}")
            else:
                consecutive_successes = 0
                print(f"💥 СБОЙ! Сбрасываем счетчик успехов")
                print(f"🔍 Ошибка: {result.get('error', 'Неизвестная ошибка')}")
            
            print(f"📊 Статистика: {self.success_count}/{self.total_attempts} успехов")
            
            # Пауза между тестами
            await asyncio.sleep(0.5)
        
        print(f"\n🎊 ДОСТИГНУТО! {target_successes} успешных парсингов подряд!")
        self.print_final_report()

    def print_final_report(self):
        """Выводим финальный отчет"""
        print(f"\n{'='*60}")
        print(f"ФИНАЛЬНЫЙ ОТЧЕТ")
        print(f"{'='*60}")
        print(f"📊 Всего попыток: {self.total_attempts}")
        print(f"✅ Успешных: {self.success_count}")
        print(f"❌ Неудачных: {self.total_attempts - self.success_count}")
        print(f"📈 Процент успеха: {(self.success_count/self.total_attempts)*100:.1f}%")
        
        # Анализируем ошибки
        errors = {}
        for result in self.results:
            if not result["success"]:
                error = result.get("error", "Неизвестная ошибка")
                errors[error] = errors.get(error, 0) + 1
        
        if errors:
            print(f"\n🔍 АНАЛИЗ ОШИБОК:")
            for error, count in errors.items():
                print(f"  - {error}: {count} раз")
        
        # Сохраняем результаты
        with open('/root/IKAR-ASSISTANT/speak_parsing_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Результаты сохранены в speak_parsing_test_results.json")

async def main():
    """Главная функция"""
    tester = SpeakParsingTester()
    await tester.run_tests(target_successes=10)

if __name__ == "__main__":
    asyncio.run(main())
