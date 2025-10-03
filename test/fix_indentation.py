import re

# Читаем файл
with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Исправляем отступы в строке 640 и окружающих
fixed_lines = []
for i, line in enumerate(lines):
    line_num = i + 1
    
    # Исправляем проблемные строки с неправильными отступами
    if 'await send_telegram_message(chat_id, "🐂 Бычий аналитик завершил анализ!", None)' in line:
        # Убираем лишние пробелы в начале
        fixed_lines.append('        await send_telegram_message(chat_id, "🐂 Бычий аналитик завершил анализ!", None)\n')
    elif 'await send_telegram_message(chat_id, "🐻 Медвежий аналитик завершил анализ!", None)' in line:
        fixed_lines.append('        await send_telegram_message(chat_id, "🐻 Медвежий аналитик завершил анализ!", None)\n')
    elif 'await send_telegram_message(chat_id, "📊 Технический судья вынес вердикт!", None)' in line:
        fixed_lines.append('        await send_telegram_message(chat_id, "📊 Технический судья вынес вердикт!", None)\n')
    elif 'await send_telegram_message(chat_id, "🌍 Макроэксперт завершил глобальный анализ!", None)' in line:
        fixed_lines.append('        await send_telegram_message(chat_id, "🌍 Макроэксперт завершил глобальный анализ!", None)\n')
    elif 'await send_telegram_message(chat_id, "😂 Криптомемы готовы!", None)' in line:
        fixed_lines.append('        await send_telegram_message(chat_id, "😂 Криптомемы готовы!", None)\n')
    elif 'await send_telegram_message(chat_id, "💰 Торговый сигнал сформирован!", None)' in line:
        fixed_lines.append('        await send_telegram_message(chat_id, "💰 Торговый сигнал сформирован!", None)\n')
    else:
        fixed_lines.append(line)

# Записываем исправленный файл
with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("Исправлены отступы в файле!")