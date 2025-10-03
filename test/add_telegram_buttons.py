import re

# Читаем файл telegram.py
with open('backend/api/telegram.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем функцию отправки сообщений с кнопками
button_function = '''
async def send_telegram_message_with_buttons(chat_id: str, text: str, buttons: list):
    """Отправляет сообщение с inline кнопками."""
    try:
        keyboard = {"inline_keyboard": buttons}
        
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.telegram.org/bot{TELEGRAM_CONFIG['token']}/sendMessage",
                json=data
            ) as response:
                if response.status == 200:
                    logger.info("✅ Сообщение с кнопками отправлено в Telegram")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка отправки сообщения с кнопками: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Исключение при отправке сообщения с кнопками: {e}")
        return False
'''

# Вставляем функцию после других функций отправки
insert_position = content.find('async def send_long_telegram_message(')
content = content[:insert_position] + button_function + '\n' + content[insert_position:]

# Записываем обратно
with open('backend/api/telegram.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Добавлена функция отправки сообщений с кнопками!")