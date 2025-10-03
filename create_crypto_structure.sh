#!/bin/bash

# Создание структуры крипто-модулей
echo "Создаю структуру крипто-модулей..."

# Создаем папки
mkdir -p backend/api/telegram/crypto

# Создаем файлы
touch backend/api/telegram/crypto/__init__.py
touch backend/api/telegram/crypto/detector.py
touch backend/api/telegram/crypto/data_fetcher.py
touch backend/api/telegram/crypto/analyzer.py
touch backend/api/telegram/crypto/cryptosud.py
touch backend/api/telegram/crypto/telegram_handler.py

echo "Структура создана!"
ls -la backend/api/telegram/crypto/ 