from typing import Dict


def classify_intent(message_text: str) -> Dict[str, object]:
    text = (message_text or "").lower()

    # Явные сигналы веб-поиска
    web_markers = [
        'поищи в интернете', 'в интернете', 'проверь новости', 'новости',
        'погода', 'какая погода', 'курс', 'котировки', 'сегодня', 'вчера', 'сейчас',
        'текущая дата', 'какая дата', 'что нового', 'breaking'
    ]

    need_web = any(m in text for m in web_markers)

    intent = 'general'
    if 'погода' in text or 'weather' in text:
        intent = 'weather'
    elif 'новост' in text or 'news' in text:
        intent = 'news'
    elif 'дата' in text or 'today' in text or 'сегодня' in text:
        intent = 'date'
    elif 'курс' in text or 'котиров' in text or 'price' in text:
        intent = 'finance'

    fresh = 'none'
    if any(w in text for w in ['сейчас', 'прямо сейчас', 'now', 'текущ', 'сегодня']):
        fresh = 'now'
    elif any(w in text for w in ['вчера', 'yesterday']):
        fresh = 'yesterday'

    # TTL по умолчанию
    ttl_map = {
        'weather': 600,   # 10 мин
        'news': 1200,     # 20 мин
        'date': 0,        # не кэшируем
        'finance': 300,   # 5 мин
        'general': 1800,  # 30 мин
    }
    ttl_sec = ttl_map.get(intent, 900)
    if fresh == 'now':
        ttl_sec = min(ttl_sec, 600)

    return {
        'need_web': need_web,
        'intent': intent,
        'fresh': fresh,
        'ttl_sec': ttl_sec,
    }


