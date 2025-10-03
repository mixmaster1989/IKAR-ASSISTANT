import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.telegram_polling import detect_crypto_content

# Тест с реальным описанием
real_description = "На изображении показан график криптовалютной пары PEPE/USDT на бирже OKX. График отображает динамику цены за последние 15 минут."

print("ТЕСТ ДЕТЕКТОРА КРИПТОКОНТЕНТА")
print("=" * 40)
print(f"Текст: {real_description}")
print()

is_crypto, found_terms = detect_crypto_content(real_description)

print(f"Результат: {'CRYPTO НАЙДЕНО' if is_crypto else 'CRYPTO НЕ НАЙДЕНО'}")
print(f"Найдено терминов: {len(found_terms)}")
print(f"Термины: {found_terms}")