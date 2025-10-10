#!/usr/bin/env python3
import os
import sys
import asyncio
from typing import Optional, List

# Настройка путей
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from backend.utils.table_generator import send_table_to_telegram


def read_env_value(*keys: str) -> Optional[str]:
    for k in keys:
        val = os.getenv(k)
        if val:
            return val
    env_path = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    name, value = line.split('=', 1)
                    name = name.strip(); value = value.strip().strip('"').strip("'")
                    if name in keys and value:
                        return value
        except Exception:
            pass
    return None


def variants() -> List[str]:
    base = [
        ("Экран", "5‑7″ (стандарт) / 10″ (HoReCa)", "7″ / 8″ / 10″"),
        ("Печатная головка", "Встроенная APS SS205‑V4‑LV (57 мм)", "Принтер с автоотрезчиком"),
        ("USB‑порты", "1–6 портов", "4–6 портов"),
        ("Wi‑Fi / GSM", "Да на всех моделях", "Да на всех моделях"),
        ("Батарея", "До 12 ч автономности", "До 5–8 ч автономности"),
        ("Фискальный накопитель", "Встроенный/внешний (FN15/FN36)", "Встроенный/внешний"),
        ("Цена без FN", "24 900–38 900 ₽", "21 500–33 000 ₽"),
    ]

    texts = []
    headings = [
        "📌 Кратко о двух «семействах» касс",
        "📊 Сравнение Evotor vs Atol Sigma",
        "🧾 Итоговая ведомость по Evotor и Atol Sigma",
        "🔍 Быстрый обзор Evotor / Sigma",
        "🧭 Выбор кассы: Evotor или Sigma?",
        "📈 Конфигурации и различия",
        "🛠 Порты, экран, батарея — сравнение",
        "📦 Комплектация и стоимость",
        "🏪 Для торговой точки: что выбрать?",
        "⚖️ Сравним по ключевым критериям",
    ]

    for title in headings:
        rows = ["| Параметр | **Evotor** | **Atol Sigma** |"]
        rows.append("|----------|------------|----------------|")
        for name, ev, at in base:
            rows.append(f"| **{name}** | {ev} | {at} |")
        note = "\n\n*цены указаны без регистрации ФН и налоговых услуг*"
        texts.append(f"{title}\n\n" + "\n".join(rows) + note)
    return texts


async def main():
    chat_id = read_env_value('TELEGRAM_CHANNEL_ID', 'IKAR_TELEGRAM_GROUP_ID', 'TELEGRAM_GROUP_ID')
    if not chat_id:
        raise SystemExit('No chat_id found in env/.env')
    token = read_env_value('TELEGRAM_BOT_TOKEN', 'BOT_TOKEN')
    if token:
        os.environ['TELEGRAM_BOT_TOKEN'] = token

    texts = variants()
    results = []
    for idx, md in enumerate(texts, 1):
        print(f"[ {idx}/10 ] Генерация и отправка…")
        mid = await send_table_to_telegram(chat_id, md, caption=None)
        if mid:
            print(f"✅ Отправлено, message_id={mid}")
        else:
            print(f"❌ Ошибка отправки варианта #{idx}")
        results.append((idx, mid))

    print("\nИТОГО:")
    for idx, mid in results:
        print(f"#{idx}: {'OK '+str(mid) if mid else 'FAIL'}")


if __name__ == '__main__':
    asyncio.run(main())


