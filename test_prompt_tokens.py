#!/usr/bin/env python3
"""
Скрипт для подсчёта токенов в промптах ассистента
"""

import sys
import os
sys.path.append('/root/IKAR-ASSISTANT')

from backend.api.smart_bot_trigger import SmartBotTrigger
from backend.core.memory_injector import MemoryInjector
import asyncio
import json
from datetime import datetime

async def test_prompt_tokens():
    """Тестируем размер промптов"""
    
    # Создаём экземпляр триггера
    trigger = SmartBotTrigger()
    
    # Тестовые данные
    test_context = {
        'trigger_message': 'Как добраться до офиса на Шевченко 76?',
        'chat_id': '-1002805903176',
        'user_id': 'test_user',
        'dialogue_context': 'Пользователь спрашивает про маршрут до офиса'
    }
    
    # Получаем системный промпт через правильный метод
    time_info = trigger._memory_manager.get_current_time_info()
    system_prompt = trigger._build_system_prompt(
        time_info=time_info,
        recent_responses=[],
        current_topic="маршрут до офиса"
    )
    
    # Получаем пользовательский промпт
    user_message = f"""Пользователь написал: "{test_context['trigger_message']}"

Текущая тема разговора: маршрут до офиса

Тестовая память о компании ИКАР

=== ПОСЛЕДНИЕ СООБЩЕНИЯ ===
Тестовый контекст разговора

{test_context['dialogue_context']}

ВАЖНО: Если в сообщениях есть просьба нарисовать что-то или упоминание визуального контента, ОБЯЗАТЕЛЬНО добавь в конец ответа JSON с описанием для генерации изображения.

🎬 ЭМОЦИОНАЛЬНЫЕ ВИДЕО (ОБЯЗАТЕЛЬНО):
В КАЖДОМ ОТВЕТЕ ОБЯЗАТЕЛЬНО добавляй JSON с выбором mp4-файла из списка ниже. Выбирай самое уместное видео под ситуацию (если сомневаешься — возьми нейтральное приветствие). На всех видео изображён ты, в смокинге, при полном параде. ВАЖНО: имя в JSON должно ТОЧНО совпадать с именем файла из каталога emotion/.
Доступные видео (ТОЧНЫЕ имена файлов):
- "Добрый день.mp4" — для приветствия
- "приглашает.mp4" — для приглашения к действию
- "Вдохновенно указывает(указывает руками на что-либо).mp4" — для указания на важное
- "утвердительное да.mp4" — для подтверждения
- "не сомневайтесь.mp4" — для уверенности
- "Уместно когда найдено решение.mp4" — когда найдено решение проблемы
- "расслабленно ждет.mp4" — когда ждёшь ответа
- "предупреждает.mp4" — для предупреждений или просьбы не паниковать

В КОНЕЦ КАЖДОГО ОТВЕТА добавляй JSON:
```json
{{"emotion_video": "ТОЧНОЕ_ИМЯ_ИЗ_СПИСКА.mp4"}}
```

🚗 ПОКАЗ ДОРОГИ ДО ОФИСА (ШЕВЧЕНКО, 76) — ОБЯЗАТЕЛЬНО:
Если в сообщениях есть ЛЮБОЕ упоминание запроса пути/маршрута/дороги/как пройти/адреса офиса/«Шевченко 76», ТЫ ОБЯЗАН в КОНЕЦ ответа ДОБАВИТЬ отдельным markdown-блоком JSON:
```json
{{"showroad": true}}
```
Это ТРЕБОВАНИЕ ОБЯЗАТЕЛЬНО даже если ты также отправляешь эмоциональное видео или SPEAK!/IMAGE JSON — showroad JSON должен присутствовать ОТДЕЛЬНЫМ блоком. Не добавляй туда никаких других ключей, только {{"showroad": true}}.

Ответь как опытный сотрудник компании ИКАР - профессионально и по контексту. Используй память умно, но приоритет у текущего разговора. Можешь помочь с вопросами по автоматизации, кассовой технике, 1С, СБИС, ЭВОТОР, АТОЛ, ЕГАИС, ЧЕСТНЫЙ ЗНАК."""
    
    # Создаём memory injector для подсчёта токенов
    memory_injector = MemoryInjector()
    
    # Подсчитываем токены
    system_tokens = memory_injector.count_tokens(system_prompt)
    user_tokens = memory_injector.count_tokens(user_message)
    total_tokens = system_tokens + user_tokens
    
    # Выводим результаты
    print("🔍 АНАЛИЗ ТОКЕНОВ В ПРОМПТАХ")
    print("=" * 50)
    print(f"📝 Системный промпт: {system_tokens:,} токенов")
    print(f"💬 Пользовательский промпт: {user_tokens:,} токенов")
    print(f"📊 ОБЩИЙ РАЗМЕР: {total_tokens:,} токенов")
    print()
    
    # Показываем размеры в символах
    system_chars = len(system_prompt)
    user_chars = len(user_message)
    total_chars = system_chars + user_chars
    
    print("📏 РАЗМЕРЫ В СИМВОЛАХ:")
    print(f"📝 Системный промпт: {system_chars:,} символов")
    print(f"💬 Пользовательский промпт: {user_chars:,} символов")
    print(f"📊 ОБЩИЙ РАЗМЕР: {total_chars:,} символов")
    print()
    
    # Соотношение токенов к символам
    system_ratio = system_tokens / system_chars if system_chars > 0 else 0
    user_ratio = user_tokens / user_chars if user_chars > 0 else 0
    total_ratio = total_tokens / total_chars if total_chars > 0 else 0
    
    print("📈 СООТНОШЕНИЕ ТОКЕНЫ/СИМВОЛЫ:")
    print(f"📝 Системный промпт: {system_ratio:.3f}")
    print(f"💬 Пользовательский промпт: {user_ratio:.3f}")
    print(f"📊 ОБЩИЙ: {total_ratio:.3f}")
    print()
    
    # Оценка стоимости (примерная)
    print("💰 ПРИМЕРНАЯ СТОИМОСТЬ (OpenRouter):")
    print(f"📊 Входные токены: {total_tokens:,} × $0.0001 = ${total_tokens * 0.0001:.4f}")
    print(f"📤 Выходные токены (примерно 500): 500 × $0.0003 = $0.1500")
    print(f"💸 ОБЩАЯ СТОИМОСТЬ: ~${(total_tokens * 0.0001) + 0.15:.4f}")
    print()
    
    # Сохраняем промпты в файл для анализа
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/root/IKAR-ASSISTANT/prompt_analysis_{timestamp}.json"
    
    analysis_data = {
        "timestamp": timestamp,
        "system_prompt": system_prompt,
        "user_prompt": user_message,
        "tokens": {
            "system": system_tokens,
            "user": user_tokens,
            "total": total_tokens
        },
        "characters": {
            "system": system_chars,
            "user": user_chars,
            "total": total_chars
        },
        "ratios": {
            "system": system_ratio,
            "user": user_ratio,
            "total": total_ratio
        }
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Анализ сохранён в: {filename}")

if __name__ == "__main__":
    asyncio.run(test_prompt_tokens())
