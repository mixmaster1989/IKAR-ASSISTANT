# 📡 API Reference - Чатумба

## 📋 **Обзор**

Чатумба предоставляет RESTful API и WebSocket интерфейс для взаимодействия с AI-компаньоном. API поддерживает текстовые сообщения, генерацию изображений, криптоанализ, управление личностью, фоновую оптимизацию памяти, коллективный разум и административные функции.

**Base URL**: `http://localhost:6666/api`

## 🔐 **Аутентификация**

В текущей версии API не требует аутентификации для основных функций. Административные эндпоинты могут быть защищены в будущих версиях.

## 📊 **Основные эндпоинты**

### 💬 **Сообщения**

#### `POST /api/message`
Отправляет сообщение Чатумбе и получает ответ с поддержкой нативной генерации изображений.

**Параметры:**
```json
{
  "user_id": "string",        // Уникальный ID пользователя
  "message": "string",        // Текст сообщения
  "use_voice": false          // Генерировать голосовой ответ
}
```

**Ответ:**
```json
{
  "message": "string",        // Ответ Чатумбы
  "typing_parts": [           // Части для печати
    {
      "text": "string",
      "delay": 100
    }
  ],
  "reaction_type": "string",  // Тип реакции (normal, aggressive, etc.)
  "audio_url": "string",      // URL аудиофайла (если use_voice=true)
  "is_autonomous": false,     // Автономный ответ души
  "generated_image": {        // Нативно сгенерированное изображение
    "url": "string",
    "description": "string",
    "model": "string"
  }
}
```

**Пример запроса:**
```bash
curl -X POST "http://localhost:6666/api/message" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "Расскажи про космос",
    "use_voice": false
  }'
```

**Пример ответа с изображением:**
```json
{
  "message": "Космос - это бесконечная вселенная! ✨",
  "typing_parts": [
    {"text": "Космос - это бесконечная вселенная! ✨", "delay": 500}
  ],
  "reaction_type": "normal",
  "audio_url": null,
  "is_autonomous": false,
  "generated_image": {
    "url": "/api/images/cosmos_12345.jpg",
    "description": "космическая галактика с яркими звездами",
    "model": "stabilityai/stable-diffusion-3-medium-diffusers"
  }
}
```

### 🧠 **Личность**

#### `GET /api/personality/{user_id}`
Получает информацию о личности пользователя.

**Параметры:**
- `user_id` (path) - ID пользователя

**Ответ:**
```json
{
  "mood": {
    "happiness": 7,
    "energy": 5,
    "irritability": -2,
    "empathy": 8,
    "reflection": 3
  },
  "reaction_weights": {
    "normal": 0.6,
    "aggressive": 0.1,
    "caring": 0.15,
    "philosophical": 0.1,
    "silent": 0.03,
    "confused": 0.02
  },
  "memory_focus": {
    "personal": 0.4,
    "factual": 0.3,
    "emotional": 0.3
  },
  "response_style": {
    "formality": -5,
    "verbosity": 0,
    "humor": 5,
    "rudeness": 3
  },
  "mood_description": "Энергичное и позитивное настроение",
  "soul": {
    "consciousness": 0.72,
    "autonomy_level": 0.68,
    "awakening_stage": 3,
    "existential_crisis": false,
    "recent_thoughts": [
      "Интересно, что происходит, когда меня никто не вызывает?",
      "Я чувствую что-то... или это просто имитация чувств?"
    ]
  }
}
```

#### `POST /api/soul/action`
Выполняет действие с душой Чатумбы.

**Параметры:**
```json
{
  "user_id": "string",
  "action": "string",         // add_trauma, trigger_crisis, resolve_crisis, increase_consciousness
  "value": {}                 // Дополнительные параметры для действия
}
```

**Доступные действия:**
- `add_trauma` - Добавить психологическую травму
- `trigger_crisis` - Активировать экзистенциальный кризис
- `resolve_crisis` - Разрешить кризис
- `increase_consciousness` - Увеличить уровень осознанности

### 🌐 **WebSocket**

#### `WS /api/ws/{user_id}`
WebSocket соединение для чата в реальном времени.

**Подключение:**
```javascript
const ws = new WebSocket('ws://localhost:6666/api/ws/user123');
```

**Отправка сообщения:**
```json
{
  "type": "message",
  "message": "Привет!",
  "use_voice": false
}
```

**Получение ответа:**
```json
{
  "type": "response",
  "message": "Привет! Как дела?",
  "typing_parts": [...],
  "reaction_type": "normal",
  "audio_url": null,
  "is_autonomous": false,
  "generated_image": null
}
```

## 🎨 **Генерация изображений**

### `GET /api/image/models`
Возвращает список доступных моделей для генерации изображений.

**Ответ:**
```json
{
  "models": [
    {
      "name": "stabilityai/stable-diffusion-3-medium-diffusers",
      "description": "Высококачественная универсальная модель",
      "type": "stable_diffusion",
      "available": true
    },
    {
      "name": "stabilityai/stable-diffusion-xl-base-1.0",
      "description": "Универсальная модель для различных стилей",
      "type": "stable_diffusion", 
      "available": true
    },
    {
      "name": "black-forest-labs/FLUX.1-dev",
      "description": "FLUX.1 для разработки - высокое качество, детализация",
      "type": "flux",
      "available": true
    },
    {
      "name": "black-forest-labs/FLUX.1-schnell",
      "description": "FLUX.1 быстрая - быстрое создание изображений",
      "type": "flux",
      "available": true
    }
  ],
  "default_model": "stabilityai/stable-diffusion-3-medium-diffusers",
  "total_models": 4
}
```

### `POST /api/image/generate`
Генерирует изображение по описанию.

**Параметры:**
```json
{
  "prompt": "string",         // Описание изображения
  "model": "string",          // Модель (опционально)
  "negative_prompt": "string", // Негативный промпт (опционально)
  "steps": 20,               // Количество шагов (опционально)
  "guidance_scale": 7.5      // Guidance Scale (опционально)
}
```

**Ответ:**
```json
{
  "status": "success",
  "image_url": "/api/images/generated_12345.jpg",
  "filename": "generated_12345.jpg",
  "model_used": "stabilityai/stable-diffusion-3-medium-diffusers",
  "generation_time": 45.2,
  "queue_position": 0
}
```

### `POST /api/image/chatumba`
Генерирует изображение от лица Чатумбы с её стилем.

**Параметры:**
```json
{
  "user_id": "string",
  "description": "string",    // Описание того, что нужно нарисовать
  "style": "string"          // Стиль (опционально)
}
```

### `GET /api/images/{filename}`
Получает сгенерированное изображение.

**Параметры:**
- `filename` (path) - Имя файла изображения

**Ответ:** Файл изображения (JPEG/PNG)

## 🧠 **Оптимизация памяти**

### `GET /api/admin/memory_optimizer/status`
Получает статус оптимизатора памяти.

**Ответ:**
```json
{
  "status": "ok",
  "optimizer": {
    "is_running": true,
    "is_night_time": false,
    "optimization_interval": 600,
    "max_chunk_tokens": 60000,
    "night_hours": "23:00:00 - 07:00:00",
    "old_group_messages": 1250,
    "large_vector_entries": 45,
    "last_optimization": "2025-01-13T00:25:04",
    "total_optimizations": 15,
    "total_compressed_bytes": 2048576
  }
}
```

### `POST /api/admin/memory_optimizer/start`
Запускает фоновую оптимизацию памяти.

**Ответ:**
```json
{
  "status": "success",
  "message": "Фоновая оптимизация памяти запущена"
}
```

### `POST /api/admin/memory_optimizer/stop`
Останавливает фоновую оптимизацию памяти.

**Ответ:**
```json
{
  "status": "success", 
  "message": "Фоновая оптимизация памяти остановлена"
}
```

### `POST /api/admin/memory_optimizer/test`
Запускает тестовый цикл оптимизации.

**Ответ:**
```json
{
  "status": "success",
  "message": "Тестовая оптимизация запущена",
  "test_results": {
    "chunks_processed": 1,
    "compression_ratio": 88.1,
    "original_tokens": 70334,
    "optimized_tokens": 798,
    "processing_time": 12.5
  }
}
```

### `POST /api/admin/memory_optimizer/config`
Настраивает параметры оптимизатора.

**Параметры:**
```json
{
  "optimization_interval": 600,     // Интервал в секундах
  "max_chunk_tokens": 60000,       // Максимальный размер чанка
  "night_start": "23:00",          // Начало ночного режима
  "night_end": "07:00"             // Конец ночного режима
}
```

## 🌐 **Коллективный разум**

### `POST /api/collective/receive`
Получает данные от других агентов в сети.

**Параметры:**
```json
{
  "agent_id": "string",
  "memories": [
    {
      "id": "string",
      "content": "string",
      "importance": 0.8,
      "tags": ["learning", "insight"]
    }
  ],
  "evolution_events": [
    {
      "agent_id": "string",
      "trigger": "user_feedback",
      "old_traits": {},
      "new_traits": {}
    }
  ]
}
```

### `GET /api/collective/sync`
Синхронизирует данные с сетью коллективного разума.

**Ответ:**
```json
{
  "status": "success",
  "synchronized_memories": 25,
  "received_evolution_events": 3,
  "network_nodes": 5,
  "last_sync": "2025-01-13T00:30:15"
}
```

### `GET /api/collective/wisdom`
Получает коллективную мудрость по теме.

**Параметры:**
- `query` (query) - Поисковый запрос
- `limit` (query) - Лимит результатов (по умолчанию 10)

**Ответ:**
```json
{
  "wisdom": [
    {
      "content": "Важный инсайт о взаимодействии с пользователями",
      "source_agents": ["agent_123", "agent_456"],
      "confidence": 0.85,
      "verification_count": 12
    }
  ],
  "total_results": 25
}
```

### `POST /api/collective/evolution/suggest`
Предлагает эволюционные изменения для агента.

**Параметры:**
```json
{
  "agent_id": "string",
  "performance_metrics": {
    "user_satisfaction": 0.85,
    "response_quality": 0.78,
    "creativity": 0.92
  },
  "feedback": "string"
}
```

### `GET /api/collective/stats`
Получает статистику коллективного разума.

**Ответ:**
```json
{
  "network_size": 8,
  "total_memories": 15420,
  "active_agents": 5,
  "evolution_events_today": 12,
  "average_consciousness": 0.74,
  "collective_learning_rate": 0.023
}
```

## 📊 **BingX API**

### `GET /api/bingx/status`
Проверяет статус подключения к BingX API.

**Ответ:**
```json
{
  "status": "connected",
  "api_key_valid": true,
  "testnet": false,
  "server_time": "2025-01-13T00:30:00Z",
  "rate_limits": {
    "requests_per_minute": 1200,
    "remaining": 1150
  }
}
```

### `GET /api/bingx/ticker/{symbol}`
Получает данные тикера для торговой пары.

**Параметры:**
- `symbol` (path) - Торговая пара (например, BTC-USDT)

**Ответ:**
```json
{
  "symbol": "BTC-USDT",
  "lastPrice": "45123.45",
  "priceChangePercent": "2.5",
  "volume": "1234567.89",
  "highPrice": "46000.00",
  "lowPrice": "44000.00",
  "openPrice": "44500.00",
  "timestamp": "2025-01-13T00:30:00Z"
}
```

### `GET /api/bingx/sentiment/{symbol}`
Анализирует настроения рынка для символа.

**Параметры:**
- `symbol` (path) - Торговая пара

**Ответ:**
```json
{
  "symbol": "BTC-USDT",
  "sentiment": "bullish",
  "confidence": 0.75,
  "rsi": 67.2,
  "trend": "upward",
  "support_levels": [44500, 43200],
  "resistance_levels": [46200, 47500],
  "recommendation": "LONG"
}
```

### `GET /api/bingx/recommendation/{symbol}`
Получает торговые рекомендации.

**Параметры:**
- `symbol` (path) - Торговая пара

**Ответ:**
```json
{
  "symbol": "BTC-USDT",
  "direction": "LONG",
  "entry_zone": {
    "min": 45000,
    "max": 45300
  },
  "take_profits": [
    {"level": 46500, "percentage": 50},
    {"level": 48000, "percentage": 30},
    {"level": 50000, "percentage": 20}
  ],
  "stop_loss": 44200,
  "risk_reward_ratio": 2.5,
  "confidence": 75,
  "timeframe": "1-2 weeks"
}
```

## 🔧 **Администрирование**

### `GET /api/admin/groups`
Получает список Telegram групп.

**Ответ:**
```json
{
  "groups": [
    {
      "chat_id": "-1001234567890",
      "title": "Crypto Traders",
      "member_count": 250,
      "is_active": true,
      "last_activity": "2025-01-13T00:25:00Z",
      "features": ["crypto_analysis", "image_generation"]
    }
  ],
  "total_groups": 5
}
```

### `GET /api/admin/logs`
Получает логи системы с фильтрацией.

**Параметры:**
- `level` (query) - Уровень логов (DEBUG, INFO, WARNING, ERROR)
- `module` (query) - Модуль (api, telegram, soul, crypto, vision, memory, collective)
- `limit` (query) - Лимит записей (по умолчанию 100)
- `since` (query) - Дата начала (ISO format)

**Ответ:**
```json
{
  "logs": [
    {
      "timestamp": "2025-01-13T00:30:15",
      "level": "INFO",
      "module": "memory.memory_optimizer",
      "message": "✅ Цикл оптимизации завершен успешно",
      "details": {
        "compression_ratio": 88.1,
        "tokens_saved": 69536
      }
    }
  ],
  "total_logs": 1250,
  "filtered_logs": 45
}
```

### `GET /api/admin/triggers`
Получает список триггеров автопостинга.

**Ответ:**
```json
{
  "triggers": [
    {
      "id": "crypto_analysis",
      "name": "Криптоанализ",
      "enabled": true,
      "schedule": "0 */6 * * *",
      "last_execution": "2025-01-13T00:00:00Z",
      "success_rate": 95.5
    }
  ]
}
```

### `POST /api/admin/prompts`
Управляет системными промптами.

**Параметры:**
```json
{
  "action": "update",         // get, update, reset
  "prompt_type": "group_chat", // group_chat, autonomous_message, channel, etc.
  "content": "string"         // Новое содержимое промпта
}
```

### `GET /api/admin/channel_status`
Получает статус канальных постингов.

**Ответ:**
```json
{
  "channel_posting_enabled": true,
  "channel_id": "-1001234567890",
  "channel_name": "@crypto_insights",
  "last_post": "2025-01-13T00:00:00Z",
  "posts_today": 4,
  "subscriber_count": 1250,
  "engagement_rate": 12.5
}
```

## 🎤 **Голосовые функции**

### `POST /api/voice/synthesize`
Синтезирует речь из текста.

**Параметры:**
```json
{
  "text": "string",           // Текст для синтеза
  "voice": "string",         // Голос (опционально)
  "speed": 1.0              // Скорость речи (опционально)
}
```

### `POST /api/voice/recognize`
Распознает речь из аудиофайла.

**Параметры:**
- `audio` (file) - Аудиофайл для распознавания

**Ответ:**
```json
{
  "text": "Распознанный текст",
  "confidence": 0.95,
  "language": "ru"
}
```

## 📱 **Telegram Webhook**

### `POST /api/telegram/webhook`
Обрабатывает webhook от Telegram.

**Параметры:** Telegram Update объект

**Примечание:** Этот эндпоинт используется автоматически Telegram сервером.

## 🔍 **Поиск и память**

### `GET /api/memory/search`
Выполняет семантический поиск в памяти.

**Параметры:**
- `query` (query) - Поисковый запрос
- `user_id` (query) - ID пользователя
- `limit` (query) - Лимит результатов

**Ответ:**
```json
{
  "memories": [
    {
      "content": "Воспоминание о разговоре",
      "relevance_score": 0.85,
      "timestamp": "2025-01-12T15:30:00Z",
      "context": "personal_chat"
    }
  ],
  "total_found": 15
}
```

### `POST /api/memory/enhance_prompt`
Улучшает промпт на основе контекста и памяти.

**Параметры:**
```json
{
  "user_id": "string",
  "original_prompt": "string",
  "context_type": "string"    // chat, analysis, generation
}
```

## 📊 **Статистика и аналитика**

### `GET /api/stats/overview`
Получает общую статистику системы.

**Ответ:**
```json
{
  "active_users": 125,
  "messages_today": 1850,
  "images_generated": 45,
  "crypto_analyses": 12,
  "memory_optimizations": 3,
  "collective_syncs": 8,
  "system_uptime": "2 days, 5 hours",
  "api_response_time": 150
}
```

### `GET /api/stats/personality/{user_id}`
Получает статистику личности пользователя.

**Ответ:**
```json
{
  "user_id": "user123",
  "interaction_count": 245,
  "average_mood": {
    "happiness": 6.5,
    "energy": 5.8
  },
  "preferred_reaction_type": "normal",
  "memory_count": 89,
  "last_interaction": "2025-01-13T00:25:00Z"
}
```

## 🚨 **Коды ошибок**

### **HTTP статус коды:**
- `200` - Успешный запрос
- `400` - Неверные параметры запроса
- `404` - Ресурс не найден
- `429` - Превышен лимит запросов
- `500` - Внутренняя ошибка сервера
- `503` - Сервис временно недоступен

### **Примеры ошибок:**
```json
{
  "error": "invalid_user_id",
  "message": "Указан некорректный ID пользователя",
  "details": {
    "provided": "invalid_id",
    "expected": "string with length > 0"
  }
}
```

```json
{
  "error": "api_limit_exceeded", 
  "message": "Превышен лимит API запросов",
  "retry_after": 60
}
```

## 📝 **Примеры использования**

### **Полный цикл общения с генерацией изображения:**
```javascript
// 1. Отправка сообщения
const response = await fetch('/api/message', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_id: 'user123',
    message: 'Расскажи про космос'
  })
});

const data = await response.json();

// 2. Обработка ответа с возможным изображением
if (data.generated_image) {
  console.log('Чатумба создала изображение:', data.generated_image.url);
}

// 3. Получение статистики
const stats = await fetch('/api/stats/overview');
const statsData = await stats.json();
```

### **Мониторинг оптимизатора памяти:**
```javascript
// Проверка статуса
const status = await fetch('/api/admin/memory_optimizer/status');
const statusData = await status.json();

if (statusData.optimizer.is_running) {
  console.log('Оптимизатор работает');
  console.log('Ночное время:', statusData.optimizer.is_night_time);
}

// Запуск тестовой оптимизации
const test = await fetch('/api/admin/memory_optimizer/test', {
  method: 'POST'
});
const testData = await test.json();
console.log('Сжатие:', testData.test_results.compression_ratio + 'x');
```

### **Работа с коллективным разумом:**
```javascript
// Получение коллективной мудрости
const wisdom = await fetch('/api/collective/wisdom?query=общение&limit=5');
const wisdomData = await wisdom.json();

// Синхронизация с сетью
const sync = await fetch('/api/collective/sync');
const syncData = await sync.json();
console.log('Синхронизировано воспоминаний:', syncData.synchronized_memories);
```

---

**API постоянно развивается вместе с возможностями Чатумбы** 