"""
🧠 НЕЙРОСУД - Многоэтапный анализ с разными AI моделями
Отдельный модуль для проведения глубокого анализа группы
"""

import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger("chatumba.neurosud")

class NeurosudAnalyzer:
    """Анализатор НЕЙРОСУД - многоэтапный анализ с разными AI моделями"""
    
    def __init__(self):
        self.temp_dir = Path(__file__).parent.parent.parent / "temp"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def analyze_group(self, chat_id: str) -> str:
        """
        Проводит полный НЕЙРОСУД анализ группы
        
        Args:
            chat_id: ID чата для анализа
            
        Returns:
            str: Путь к созданному txt файлу с результатами
        """
        try:
            # Импорты
            from memory.sqlite import sqlite_storage
            from utils.component_manager import get_component_manager
            
            component_manager = get_component_manager()
            llm_client = component_manager.get_llm_client()
            
            logger.info(f"🧠 НЕЙРОСУД: Начинаю анализ группы {chat_id}")
            
            # 1. Собираем историю группы
            logger.info("📁 Собираю историю группы...")
            
            # Получаем ВСЕ сообщения за последние 24 часа
            day_ago = int((datetime.now() - timedelta(days=1)).timestamp())
            messages = sqlite_storage.get_group_messages(chat_id)
            day_messages = []
            
            for msg in messages:
                try:
                    msg_timestamp = msg.get('timestamp', 0)
                    if isinstance(msg_timestamp, str):
                        msg_timestamp = int(msg_timestamp)
                    if msg_timestamp >= day_ago:
                        day_messages.append(msg)
                except:
                    continue
            
            if not day_messages:
                logger.warning("⚠️ Нет сообщений за последние 24 часа для анализа")
                return None
            
            # Формируем историю
            history_lines = []
            for msg in day_messages:
                content = msg.get('content', '').strip()
                if not content or content.startswith('/'):
                    continue
                
                user_id = msg.get('user_id', 'Unknown')
                name = sqlite_storage.get_group_user_name(chat_id, user_id) or f"User_{user_id[-4:]}"
                history_lines.append(f"{name}: {content}")
            
            history_text = "\n".join(history_lines)
            
            logger.info(f"📊 Собрано {len(day_messages)} сообщений за последние 24 часа")
            
            # 2. ПЕРВАЯ ПОЗИЦИЯ
            logger.info("🔥 Формирую ПЕРВУЮ ПОЗИЦИЮ...")
            
            first_prompt = f"""🎯 Ты — первый оппонент в НЕЙРОСУДЕ! 💪

📊 Проанализируй историю чата и сформируй СВОЮ ПОЗИЦИЮ на основе того, что видишь:
🔍 — Какие проблемы/возможности ты замечаешь?
💡 — Какое решение предлагаешь?
🚀 — Почему именно твой подход правильный?

📝 Используй эмодзи, будь убедительным и конкретным!

💬 История группы:
{history_text}"""
            
            opinion_first = await llm_client.chat_completion(
                user_message=first_prompt,
                system_prompt="🎭 Ты первый оппонент в дебатах. Формируй позицию на основе данных. Используй эмодзи! 🔥",
                temperature=0.7,
                max_tokens=1000
            )
            
            # 3. ВТОРАЯ ПОЗИЦИЯ
            logger.info("⚡ Формирую ВТОРУЮ ПОЗИЦИЮ...")
            
            second_prompt = f"""⚡ Ты — второй оппонент в НЕЙРОСУДЕ! 🎪

🔄 Проанализируй ту же историю чата, но сформируй АЛЬТЕРНАТИВНУЮ ПОЗИЦИЮ:
🎯 — Какие аспекты видишь по-другому?
🛠️ — Какой подход предлагаешь ты?
💥 — Почему твоя точка зрения лучше?

🎨 Используй эмодзи, будь креативным и аргументированным!

💬 История группы:
{history_text}"""
            
            opinion_second = await llm_client.chat_completion(
                user_message=second_prompt,
                system_prompt="🎪 Ты второй оппонент в дебатах. Предлагай альтернативу! Используй эмодзи! ⚡",
                temperature=0.7,
                max_tokens=1000
            )
            
            # 4. СУДЬЯ
            logger.info("⚖️ Суд идёт! Анализирую позиции...")
            
            judge_prompt = f"""⚖️ Ты — третейский НЕЙРОСУДЬЯ! 🧑‍⚖️

🔍 Перед тобой два противоположных мнения. Проанализируй их:
📊 — Сравни позиции: что сильного, что слабого?
💥 — Где кроется главный конфликт?
🤝 — Какой путь объединяет оба подхода?
🎯 — Что делать команде ПРЯМО СЕЙЧАС?

🎨 Используй эмодзи и будь справедливым судьёй!

💬 История группы:
{history_text}

🔥 Первая позиция:
{opinion_first}

⚡ Вторая позиция:
{opinion_second}"""
            
            judgement = await llm_client.chat_completion(
                user_message=judge_prompt,
                system_prompt="⚖️ Ты справедливый нейросудья. Анализируй объективно! Используй эмодзи! 🧑‍⚖️",
                temperature=0.6,
                max_tokens=1500
            )
            
            # 5. МЕТА-НАБЛЮДАТЕЛЬ
            logger.info("🧠 Мета-анализ от высшего разума...")
            
            meta_prompt = f"""🧠 Ты — МЕТА-НАБЛЮДАТЕЛЬ! Высший разум! 🌟

🔮 Получи полную картину происходящего. Проанализируй ВСЁ:
🎯 — Высокоуровневое понимание ситуации
🔄 — Какие паттерны видишь в группе?
🚧 — Где узкие места и проблемы?
🚀 — Какую ГЛОБАЛЬНУЮ стратегию выбрать?
💎 — Какие принципы зафиксировать?

🎨 Используй эмодзи и дай мудрый совет!

💬 История группы:
{history_text}

🔥 Первая позиция:
{opinion_first}

⚡ Вторая позиция:
{opinion_second}

⚖️ Вердикт судьи:
{judgement}"""
            
            meta_reflection = await llm_client.chat_completion(
                user_message=meta_prompt,
                system_prompt="🧠 Ты мета-аналитик высшего уровня! Дай глубокий анализ! Используй эмодзи! 🌟",
                temperature=0.5,
                max_tokens=2000
            )
            
            # 6. Создаем txt файл с результатами
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"neurosud_analysis_{chat_id}_{timestamp}.txt"
            filepath = self.temp_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("🧠 НЕЙРОСУД - МНОГОЭТАПНЫЙ АНАЛИЗ ГРУППЫ\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"📅 Дата анализа: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write(f"💬 Группа: {chat_id}\n")
                f.write(f"📊 Проанализировано сообщений: {len(day_messages)}\n")
                f.write(f"⏰ Период: последние 24 часа\n\n")
                
                f.write("🔥 ПЕРВАЯ ПОЗИЦИЯ:\n")
                f.write("-" * 30 + "\n")
                f.write(f"{opinion_first}\n\n")
                
                f.write("⚡ ВТОРАЯ ПОЗИЦИЯ:\n")
                f.write("-" * 30 + "\n")
                f.write(f"{opinion_second}\n\n")
                
                f.write("⚖️ ВЕРДИКТ СУДЬИ:\n")
                f.write("-" * 30 + "\n")
                f.write(f"{judgement}\n\n")
                
                f.write("🧠 МЕТА-АНАЛИЗ:\n")
                f.write("-" * 30 + "\n")
                f.write(f"{meta_reflection}\n\n")
                
                f.write("=" * 60 + "\n")
                f.write("✅ НЕЙРОСУД ЗАВЕРШЁН!\n")
            
            logger.info(f"✅ НЕЙРОСУД завершён! Файл сохранён: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Ошибка НЕЙРОСУДА: {e}")
            return None

# Глобальный экземпляр
neurosud_analyzer = NeurosudAnalyzer()

async def run_neurosud_analysis(chat_id: str) -> str:
    """Запускает НЕЙРОСУД анализ для группы"""
    return await neurosud_analyzer.analyze_group(chat_id)
