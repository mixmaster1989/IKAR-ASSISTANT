"""
Модуль для обработки групповых функций Telegram.
Вынесен из telegram_polling.py для улучшения структуры кода.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from backend.config import TELEGRAM_CONFIG
from backend.memory.lazy_memory import get_lazy_memory
from backend.utils.component_manager import get_component_manager
from backend.core.soul import ChatumbaSoul

logger = logging.getLogger("chatumba.group_handler")

async def show_collective_memory(chat_id: str):
    """
    Показывает коллективную память всех пользователей.
    """
    try:
        lazy_memory = get_lazy_memory()
        component_manager = get_component_manager()
        
        # Получаем статистику коллективной памяти
        memory_stats = lazy_memory.get_memory_stats()
        
        # Формируем отчет
        report = "🧠 **КОЛЛЕКТИВНАЯ ПАМЯТЬ ЧАТУМБЫ**\n\n"
        
        # Общая статистика
        report += "**📊 ОБЩАЯ СТАТИСТИКА:**\n"
        report += f"• Всего сообщений: {memory_stats.get('total_messages', 0)}\n"
        report += f"• Уникальных пользователей: {memory_stats.get('unique_users', 0)}\n"
        report += f"• Активных чатов: {memory_stats.get('active_chats', 0)}\n"
        report += f"• Размер базы данных: {memory_stats.get('db_size_mb', 0):.2f} МБ\n\n"
        
        # Последние активные пользователи
        if 'recent_users' in memory_stats:
            report += "**👥 ПОСЛЕДНИЕ АКТИВНЫЕ ПОЛЬЗОВАТЕЛИ:**\n"
            for user in memory_stats['recent_users'][:10]:
                report += f"• {user.get('user_id', 'Неизвестно')}: {user.get('message_count', 0)} сообщений\n"
            report += "\n"
        
        # Популярные темы
        if 'popular_topics' in memory_stats:
            report += "**🔥 ПОПУЛЯРНЫЕ ТЕМЫ:**\n"
            for topic, count in memory_stats['popular_topics'][:10]:
                report += f"• {topic}: {count} упоминаний\n"
            report += "\n"
        
        # Временная активность
        if 'activity_by_hour' in memory_stats:
            report += "**⏰ АКТИВНОСТЬ ПО ЧАСАМ:**\n"
            for hour, count in memory_stats['activity_by_hour']:
                report += f"• {hour:02d}:00 - {count} сообщений\n"
            report += "\n"
        
        # Отправляем отчет
        await send_telegram_message(chat_id, report)
        
    except Exception as e:
        logger.error(f"Ошибка при показе коллективной памяти: {e}")
        await send_telegram_message(chat_id, "❌ Произошла ошибка при получении коллективной памяти.")

async def show_full_chunks_with_buttons(chat_id: str):
    """
    Показывает полные чанки памяти с кнопками для управления.
    """
    try:
        lazy_memory = get_lazy_memory()
        
        # Получаем все чанки памяти
        all_memories = lazy_memory.get_all_memories()
        
        if not all_memories:
            await send_telegram_message(chat_id, "📝 Память пуста. Нет сохраненных сообщений.")
            return
        
        # Группируем по пользователям
        users_memories = {}
        for memory in all_memories:
            user_id = memory.get('user_id', 'unknown')
            if user_id not in users_memories:
                users_memories[user_id] = []
            users_memories[user_id].append(memory)
        
        # Сортируем по времени
        def get_timestamp(chunk):
            return chunk.get('timestamp', datetime.min)
        
        for user_id in users_memories:
            users_memories[user_id].sort(key=get_timestamp, reverse=True)
        
        # Формируем сообщение
        message = "🧠 **ПОЛНАЯ КОЛЛЕКТИВНАЯ ПАМЯТЬ**\n\n"
        
        # Показываем последние 20 сообщений
        recent_memories = []
        for user_memories in users_memories.values():
            recent_memories.extend(user_memories[:5])  # Берем по 5 последних от каждого пользователя
        
        recent_memories.sort(key=get_timestamp, reverse=True)
        recent_memories = recent_memories[:20]  # Ограничиваем 20 сообщениями
        
        for i, memory in enumerate(recent_memories, 1):
            user_id = memory.get('user_id', 'Неизвестно')
            content = memory.get('content', '')
            timestamp = memory.get('timestamp', 'Неизвестно')
            
            # Обрезаем длинный контент
            if len(content) > 100:
                content = content[:100] + "..."
            
            # Экранируем HTML
            def escape_html(text):
                return text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            
            content = escape_html(content)
            
            message += f"**{i}. Пользователь {user_id}** ({timestamp})\n"
            message += f"`{content}`\n\n"
        
        # Создаем кнопки для управления
        keyboard = []
        
        # Кнопки для удаления
        delete_row = []
        for i in range(1, min(6, len(recent_memories) + 1)):
            delete_row.append({
                "text": f"🗑️ {i}",
                "callback_data": f"delete_chunk_{i}"
            })
        keyboard.append(delete_row)
        
        # Кнопки для просмотра
        view_row = []
        for i in range(1, min(6, len(recent_memories) + 1)):
            view_row.append({
                "text": f"👁️ {i}",
                "callback_data": f"view_chunk_{i}"
            })
        keyboard.append(view_row)
        
        # Кнопка очистки
        keyboard.append([{
            "text": "🧹 Очистить всю память",
            "callback_data": "clear_all_memory"
        }])
        
        # Отправляем сообщение с кнопками
        await send_telegram_message_with_buttons(chat_id, message, keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка при показе чанков памяти: {e}")
        await send_telegram_message(chat_id, "❌ Произошла ошибка при получении чанков памяти.")

async def handle_chunk_deletion(callback_query, callback_data, chat_id, message_id):
    """
    Обрабатывает удаление чанка памяти.
    """
    try:
        lazy_memory = get_lazy_memory()
        
        # Извлекаем номер чанка
        chunk_number = int(callback_data.split('_')[2])
        
        # Получаем все чанки
        all_memories = lazy_memory.get_all_memories()
        
        if chunk_number > len(all_memories):
            await answer_callback_query(callback_query.id, "❌ Чанк не найден.")
            return
        
        # Получаем чанк для удаления
        chunk_to_delete = all_memories[chunk_number - 1]
        
        # Удаляем чанк
        success = lazy_memory.delete_memory(chunk_to_delete.get('id'))
        
        if success:
            await answer_callback_query(callback_query.id, f"✅ Чанк {chunk_number} удален.")
            
            # Обновляем сообщение
            await show_full_chunks_with_buttons(chat_id)
        else:
            await answer_callback_query(callback_query.id, "❌ Ошибка при удалении чанка.")
        
    except Exception as e:
        logger.error(f"Ошибка при удалении чанка: {e}")
        await answer_callback_query(callback_query.id, "❌ Произошла ошибка при удалении.")

async def handle_chunk_view(callback_query, callback_data, chat_id, message_id):
    """
    Обрабатывает просмотр полного чанка памяти.
    """
    try:
        lazy_memory = get_lazy_memory()
        
        # Извлекаем номер чанка
        chunk_number = int(callback_data.split('_')[2])
        
        # Получаем все чанки
        all_memories = lazy_memory.get_all_memories()
        
        if chunk_number > len(all_memories):
            await answer_callback_query(callback_query.id, "❌ Чанк не найден.")
            return
        
        # Получаем чанк для просмотра
        chunk = all_memories[chunk_number - 1]
        
        # Формируем детальное сообщение
        user_id = chunk.get('user_id', 'Неизвестно')
        content = chunk.get('content', '')
        timestamp = chunk.get('timestamp', 'Неизвестно')
        message_type = chunk.get('message_type', 'text')
        
        # Экранируем HTML
        def escape_html(text):
            return text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        
        content = escape_html(content)
        
        detail_message = f"🧠 **ДЕТАЛЬНЫЙ ПРОСМОТР ЧАНКА {chunk_number}**\n\n"
        detail_message += f"**Пользователь:** {user_id}\n"
        detail_message += f"**Тип сообщения:** {message_type}\n"
        detail_message += f"**Время:** {timestamp}\n\n"
        detail_message += f"**Содержание:**\n`{content}`"
        
        # Создаем кнопки для действий
        keyboard = [
            [{
                "text": "🗑️ Удалить этот чанк",
                "callback_data": f"delete_chunk_{chunk_number}"
            }],
            [{
                "text": "🔙 Назад к списку",
                "callback_data": "back_to_chunks"
            }]
        ]
        
        # Отправляем детальное сообщение
        await send_telegram_message_with_buttons(chat_id, detail_message, keyboard)
        await answer_callback_query(callback_query.id, "✅ Детали чанка загружены.")
        
    except Exception as e:
        logger.error(f"Ошибка при просмотре чанка: {e}")
        await answer_callback_query(callback_query.id, "❌ Произошла ошибка при просмотре.")

# Импорты для совместимости
from ..telegram_core import send_telegram_message, send_telegram_message_with_buttons, answer_callback_query 