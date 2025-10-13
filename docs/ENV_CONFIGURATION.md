# ⚙️ Конфигурация переменных окружения

## 📋 **Обзор**

Чатумба использует переменные окружения для настройки всех компонентов системы. Все настройки хранятся в файле `.env` в корне проекта для безопасности и гибкости конфигурации.

## 🚀 **Быстрая настройка**

### **1. Создание .env файла**
```bash
# Скопируйте шаблон
cp .env.example .env

# Или создайте новый файл
touch .env
```

### **2. Базовая конфигурация**
```bash
# === ОСНОВНЫЕ API КЛЮЧИ ===
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ

# === ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ ===
STABLE_HORDE_API_KEY=your-stable-horde-key
```

### **3. Проверка настройки**
```bash
# Запустите сервер
python run.py

# При успешной настройке вы увидите:
# 🔑 Найдено API ключей OpenRouter: 1
# 🤖 TELEGRAM BOT АКТИВЕН: @your_bot_name
# 🎨 Stable Horde API настроен
```

## 🔑 **Основные API ключи**

### **OpenRouter (LLM модели)**
```bash
# === МНОЖЕСТВЕННЫЕ КЛЮЧИ OPENROUTER ===
# Система автоматически обнаруживает все ключи
OPENROUTER_API_KEY=sk-or-v1-primary-key
OPENROUTER_API_KEY2=sk-or-v1-secondary-key  
OPENROUTER_API_KEY3=sk-or-v1-tertiary-key
OPENROUTER_API_KEY4=sk-or-v1-fourth-key
OPENROUTER_API_KEY5=sk-or-v1-fifth-key
# ... можно добавлять до OPENROUTER_API_KEY_N
```

**Особенности:**
- Автоматическое переключение при лимитах
- Балансировка нагрузки между ключами
- Graceful fallback при недоступности
- Поддержка любого количества ключей

**Получение ключей:**
### **Платный ключ для Grok (OpenRouter)**
```bash
# Используется для модели x-ai/grok-4-fast
OPENROUTER_API_KEY_PAID=sk-or-paid-your-key
```

1. Зарегистрируйтесь на [OpenRouter.ai](https://openrouter.ai/)
2. Перейдите в раздел "Keys"
3. Создайте новый API ключ
4. Скопируйте ключ в формате `sk-or-v1-...`

### **Embedding API (для векторной памяти)**
```bash
# === EMBEDDINGS ===
EMBEDDING_API_KEY=sk-your-openai-key-here
```

**Назначение:**
- Генерация эмбеддингов для векторной памяти
- Семантический поиск воспоминаний
- Fallback на локальные модели при отсутствии

## 🤖 **Telegram настройки**

### **Основные параметры**
```bash
# === TELEGRAM BOT ===
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ
TELEGRAM_CHANNEL_ID=-1001234567890
TELEGRAM_CHANNEL_NAME=@your_channel_name
```

**Получение токена:**
1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в формате `123:ABC...`

**Получение ID канала:**
```bash
# Способ 1: Через веб-версию
# https://t.me/your_channel → ID будет -1001234567890

# Способ 2: Через @userinfobot
# Перешлите сообщение из канала боту

# Способ 3: Через API
curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
```

### **Webhook настройки**
```bash
# === WEBHOOK (для продакшена) ===
WEBHOOK_URL=https://your-domain.com/api/telegram/webhook
```

**Настройка webhook:**
```bash
# Установка webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-domain.com/api/telegram/webhook"}'

# Проверка webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

## 🎨 **Генерация изображений**

### **DeepAI (основной)**
```bash
# === DEEPAI ===
DEEPAI_API_KEY=your-deepai-api-key-here
```

**Получение ключа:**
1. Перейдите на [deepai.org](https://deepai.org/)
2. Зарегистрируйтесь
3. Войдите в аккаунт
4. Перейдите в раздел "API"
5. Скопируйте API ключ

**Особенности:**
- Быстрая генерация (10-30 секунд)
- 5 специализированных моделей
- Высокое качество
- Простой API
- Бесплатный тайер

### **Альтернативные сервисы**
```bash
# === ДОПОЛНИТЕЛЬНЫЕ СЕРВИСЫ (опционально) ===
HF_API_TOKEN=hf_your-huggingface-token
REPLICATE_API_TOKEN=r8_your-replicate-token
```

## 📊 **Криптотрейдинг (BingX)**

### **API настройки**
```bash
# === BINGX API ===
BINGX_API_KEY=your-bingx-api-key
BINGX_SECRET_KEY=your-bingx-secret-key
BINGX_API_URL=https://open-api.bingx.com
BINGX_TESTNET=false
```

**Получение ключей:**
1. Зарегистрируйтесь на [BingX](https://bingx.com)
2. Перейдите в API Management
3. Создайте новый API ключ
4. Установите необходимые разрешения
5. Скопируйте API Key и Secret Key

**Настройки:**
- `BINGX_TESTNET=true` - для тестовой сети
- `BINGX_TESTNET=false` - для реальной торговли

## 🔧 **Дополнительные настройки**

### **Системные параметры**
```bash
# === СИСТЕМА ===
DEBUG=true
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=6666
```

### **База данных**
```bash
# === DATABASE ===
DATABASE_PATH=data/chatumba.db
VECTOR_DB_PATH=data/memory/vector_store
```

### **Безопасность**
```bash
# === SECURITY ===
SECRET_KEY=your-secret-key-for-sessions
CORS_ORIGINS=*
RATE_LIMIT_ENABLED=true
```

## 📝 **Полный шаблон .env**

```bash
# ===================================================================
# КОНФИГУРАЦИЯ ЧАТУМБЫ - Полный шаблон .env
# ===================================================================

# === ОСНОВНЫЕ API КЛЮЧИ ===
# Поддерживается множественные ключи OpenRouter
OPENROUTER_API_KEY=sk-or-v1-primary-key-here
OPENROUTER_API_KEY2=sk-or-v1-secondary-key-here
OPENROUTER_API_KEY3=sk-or-v1-tertiary-key-here
OPENROUTER_API_KEY4=sk-or-v1-fourth-key-here
OPENROUTER_API_KEY5=sk-or-v1-fifth-key-here
# Платный ключ для Grok
OPENROUTER_API_KEY_PAID=sk-or-paid-key-here

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ
TELEGRAM_CHANNEL_ID=-1001234567890
TELEGRAM_CHANNEL_NAME=@your_channel_name

# === ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ ===
DEEPAI_API_KEY=your-deepai-api-key-here

# === КРИПТОТРЕЙДИНГ ===
BINGX_API_KEY=your-bingx-api-key-here
BINGX_SECRET_KEY=your-bingx-secret-key-here
BINGX_API_URL=https://open-api.bingx.com
BINGX_TESTNET=false

# === ДОПОЛНИТЕЛЬНЫЕ API ===
EMBEDDING_API_KEY=sk-your-openai-embedding-key
HF_API_TOKEN=hf_your-huggingface-token
REPLICATE_API_TOKEN=r8_your-replicate-token

# === WEBHOOK (для продакшена) ===
WEBHOOK_URL=https://your-domain.com/api/telegram/webhook

# === СИСТЕМНЫЕ НАСТРОЙКИ ===
DEBUG=true
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=6666

# === БАЗА ДАННЫХ ===
DATABASE_PATH=data/chatumba.db
VECTOR_DB_PATH=data/memory/vector_store

# === БЕЗОПАСНОСТЬ ===
SECRET_KEY=your-secret-key-for-sessions
CORS_ORIGINS=*
RATE_LIMIT_ENABLED=true

# ===================================================================
# КОНЕЦ КОНФИГУРАЦИИ
# ===================================================================
```

## 🔒 **Безопасность**

### **Защита ключей**
```bash
# Добавьте .env в .gitignore
echo ".env" >> .gitignore

# Установите правильные права доступа
chmod 600 .env

# Никогда не коммитьте .env в git!
```

### **Валидация ключей**
```python
# Система автоматически проверяет:
# - Формат ключей
# - Доступность API
# - Корректность токенов
# - Права доступа
```

### **Ротация ключей**
- Регулярно обновляйте API ключи
- Используйте разные ключи для разных сред
- Мониторьте использование ключей
- Отзывайте скомпрометированные ключи

## 📊 **Мониторинг и диагностика**

### **Проверка конфигурации**
```bash
# Проверка всех ключей
python -c "
from config import *
print(f'OpenRouter keys: {len(OPENROUTER_API_KEYS)}')
print(f'Telegram token: {bool(TELEGRAM_BOT_TOKEN)}')
print(f'Stable Horde key: {bool(STABLE_HORDE_API_KEY)}')
print(f'BingX keys: {bool(BINGX_API_KEY and BINGX_SECRET_KEY)}')
"
```

### **Диагностика проблем**
```bash
# Проверка Telegram
python -c "
import asyncio
from api.telegram import get_bot_info
print(asyncio.run(get_bot_info()))
"

# Проверка BingX
python test_bingx_api.py

# Проверка Stable Horde
python -c "
from vision.image_generator import get_available_models
print(get_available_models())
"
```

## 🚀 **Развертывание**

### **Локальная разработка**
```bash
# 1. Создайте .env с базовыми ключами
# 2. Запустите сервер
python run.py
```

### **Продакшен**
```bash
# 1. Настройте все ключи
# 2. Включите webhook
WEBHOOK_URL=https://your-domain.com/api/telegram/webhook

# 3. Отключите debug
DEBUG=false
LOG_LEVEL=WARNING

# 4. Настройте безопасность
CORS_ORIGINS=https://your-domain.com
RATE_LIMIT_ENABLED=true
```

### **Docker**
```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 6666
CMD ["python", "run.py"]
```

```bash
# docker-compose.yml
version: '3.8'
services:
  chatumba:
    build: .
    ports:
      - "6666:6666"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
```

## 🔧 **Устранение неполадок**

### **Частые проблемы**

#### **OpenRouter ключи не работают**
```bash
# Проверка формата ключа
echo $OPENROUTER_API_KEY | grep -E "^sk-or-v1-"

# Проверка доступности API
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     "https://openrouter.ai/api/v1/models"
```

#### **Telegram бот не отвечает**
```bash
# Проверка токена
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Проверка webhook
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
```

#### **BingX API недоступен**
```bash
# Проверка ключей
python test_bingx_api.py

# Проверка сети
curl "https://open-api.bingx.com/openApi/swap/v2/server/time"
```

### **Логи и отладка**
```bash
# Просмотр логов конфигурации
tail -f logs/config.log

# Отладка переменных окружения
python -c "
import os
for key, value in os.environ.items():
    if any(x in key.upper() for x in ['API', 'TOKEN', 'KEY']):
        print(f'{key}: {value[:10]}...' if value else f'{key}: NOT SET')
"
```

## 📚 **Примеры конфигураций**

### **Минимальная настройка**
```bash
# Только для базового функционала
OPENROUTER_API_KEY=sk-or-v1-your-key
TELEGRAM_BOT_TOKEN=your-bot-token
```

### **Полная настройка**
```bash
# Все функции включены
OPENROUTER_API_KEY=sk-or-v1-primary
OPENROUTER_API_KEY2=sk-or-v1-secondary
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHANNEL_ID=-1001234567890
STABLE_HORDE_API_KEY=your-stable-horde-key
BINGX_API_KEY=your-bingx-key
BINGX_SECRET_KEY=your-bingx-secret
EMBEDDING_API_KEY=sk-your-openai-key
```

### **Продакшен настройка**
```bash
# Оптимизировано для продакшена
OPENROUTER_API_KEY=sk-or-v1-prod-key
TELEGRAM_BOT_TOKEN=prod-bot-token
WEBHOOK_URL=https://api.yoursite.com/telegram/webhook
DEBUG=false
LOG_LEVEL=ERROR
RATE_LIMIT_ENABLED=true
CORS_ORIGINS=https://yoursite.com
```

---

**Правильная настройка переменных окружения - основа стабильной работы Чатумбы. Следуйте инструкциям и регулярно обновляйте ключи для безопасности.** ⚙️🔐 