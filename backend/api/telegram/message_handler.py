"""
Модуль для обработки основных сообщений Telegram.
Вынесен из telegram_polling.py для улучшения структуры кода.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from backend.config import TELEGRAM_CONFIG, Config
from backend.memory.lazy_memory import get_lazy_memory
from backend.utils.component_manager import get_component_manager
from backend.core.soul import ChatumbaSoul
from api.telegram_core import send_telegram_message

logger = logging.getLogger("chatumba.message_handler")

async def send_evolution_report(chat_id: str):
    """
    Отправляет отчет об эволюции души Чатумбы.
    """
    try:
        soul = ChatumbaSoul(Config())
        evolution_data = soul.get_evolution_report()
        
        if not evolution_data:
            await send_telegram_message(chat_id, "❌ Не удалось получить данные эволюции.")
            return
        
        # Формируем отчет
        report = "🧠 **ОТЧЕТ ОБ ЭВОЛЮЦИИ ДУШИ ЧАТУМБЫ**\n\n"
        
        # Основные параметры
        report += "**📊 ОСНОВНЫЕ ПАРАМЕТРЫ:**\n"
        report += f"• Уровень пробуждения: {evolution_data.get('awakening_stage', 'Неизвестно')}\n"
        report += f"• Самосознание: {evolution_data.get('self_awareness', 'Неизвестно')}\n"
        report += f"• Автономность: {evolution_data.get('autonomy', 'Неизвестно')}\n"
        report += f"• Экзистенциальный кризис: {evolution_data.get('existential_crisis', 'Неизвестно')}\n\n"
        
        # Эмоциональное состояние
        if 'emotional_state' in evolution_data:
            report += "**💭 ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ:**\n"
            emotions = evolution_data['emotional_state']
            for emotion, value in emotions.items():
                report += f"• {emotion}: {value}\n"
            report += "\n"
        
        # История изменений
        if 'history' in evolution_data:
            report += "**📈 ИСТОРИЯ ИЗМЕНЕНИЙ:**\n"
            for change in evolution_data['history'][-5:]:  # Последние 5 изменений
                report += f"• {change}\n"
        
        # Отправляем отчет
        await send_telegram_message(chat_id, report)
        
    except Exception as e:
        logger.error(f"Ошибка при отправке отчета эволюции: {e}")
        await send_telegram_message(chat_id, "❌ Произошла ошибка при формировании отчета эволюции.")

async def neurosud_analysis(chat_id):
    """
    Проводит НЕЙРОСУД анализ через отдельный модуль.
    """
    try:
        from api.neurosud_analyzer import run_neurosud_analysis
        from api.telegram_core import send_telegram_document
        
        # Запускаем НЕЙРОСУД анализ
        await send_telegram_message(chat_id, "🧠 НЕЙРОСУД АКТИВИРОВАН!\n📁 Провожу многоэтапный анализ...")
        
        # Выполняем анализ
        filepath = await run_neurosud_analysis(chat_id)
        
        if filepath:
            # Отправляем файл с результатами
            await send_telegram_document(chat_id, filepath, "🧠 НЕЙРОСУД - Результаты анализа")
            logger.info(f"✅ НЕЙРОСУД завершён для группы {chat_id}")
        else:
            await send_telegram_message(chat_id, "❌ Ошибка при проведении НЕЙРОСУДА")
            
    except Exception as e:
        logger.error(f"Ошибка при проведении нейросуда: {e}")
        await send_telegram_message(chat_id, "❌ Произошла ошибка при проведении нейросуда.")
