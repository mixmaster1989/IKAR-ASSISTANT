#!/usr/bin/env python3
import os
import sys
import asyncio
from typing import Optional

# Настраиваем путь для импортов
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from backend.utils.table_generator import send_table_to_telegram

def read_env_value(*keys: str) -> Optional[str]:
    """Читает значения из переменных окружения или из файла .env в корне проекта."""
    # 1) Сначала пытаемся из env
    for k in keys:
        val = os.getenv(k)
        if val:
            return val
    # 2) Пробуем прочитать .env вручную
    env_path = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    name, value = line.split('=', 1)
                    name = name.strip()
                    value = value.strip().strip('"').strip("'")
                    if name in keys and value:
                        return value
        except Exception:
            pass
    return None

# Текст с таблицей
TABLE_MARKDOWN = """| Параметр | **Evotor** | **Atol Sigma** |
|----------|------------|----------------|
| **Экран** | 5‑7″ (стандарт) / 10″ (HoReCa) | 7″ / 8″ / 10″ |
| **Печатная головка** | Встроенная термопринтер‑APS SS205‑V4‑LV (57 мм) | Встроенная принтер‑прототип с автоотрезчиком |
| **USB‑порты** | 1–6 портов (зависит от модели) | 4–6 портов |
| **Wi‑Fi / GSM** | Да на всех моделях | Да на всех моделях |
| **Батарея** | До 12 ч автономности (модели с аккумулятором) | До 5–8 ч автономности |
| **Фискальный накопитель** | Встроенный или внешний по выбору (FN15/FN36) | Встроенный или внешний по выбору |
| **Цена без FN** | От 24 900 ₽ до 38 900 ₽* | От 21 500 ₽ до 33 000 ₽* |"""

CAPTION = """📌 **Сравнение кассовых систем Evotor и Atol Sigma**

*цены указаны без регистрации ФН и налоговых услуг*

**Evotor** - мобильность и простота регистрации
**Atol Sigma** - гибкость портов и экономичность

🤝 **Выбор:**
• Киоск/малая точка → Evotor 5/7.x
• Средний ритейл → Atol Sigma 8/10  
• HoReCa → Evotor 10

> _Икар советует учитывать количество рабочих мест и периферию_"""

async def main():
    chat_id = read_env_value('TELEGRAM_CHANNEL_ID', 'IKAR_TELEGRAM_GROUP_ID', 'TELEGRAM_GROUP_ID')
    if not chat_id:
        raise SystemExit('No chat_id found in env or .env')
    
    # Установим токен в окружение
    bot_token = read_env_value('TELEGRAM_BOT_TOKEN', 'BOT_TOKEN')
    if bot_token:
        os.environ['TELEGRAM_BOT_TOKEN'] = bot_token
    
    print("Создаю таблицу как изображение...")
    result = await send_table_to_telegram(chat_id, TABLE_MARKDOWN, CAPTION)
    
    if result:
        print(f"✅ Таблица отправлена! Message ID: {result}")
    else:
        print("❌ Ошибка отправки таблицы")

if __name__ == '__main__':
    asyncio.run(main())
