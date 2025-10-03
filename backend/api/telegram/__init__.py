"""
Пакет для модулей Telegram API.
"""

# Импортируем основные функции из telegram_core
from ..telegram_core import (
    send_telegram_message, 
    send_telegram_message_with_buttons,
    send_telegram_photo,
    download_telegram_file,
    llm_client,
    sqlite_storage,
    init_telegram_bot,
    admin_router,
    parse_and_generate_image,
    send_long_telegram_message
) 