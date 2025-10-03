# 🔧 РУКОВОДСТВО ПО УСТАНОВКЕ ИНТЕРНЕТ-ИНТЕЛЛЕКТА

## ⚡ **БЫСТРАЯ УСТАНОВКА (Исправленная версия)**

### **Проблема с зависимостями решена!**

Используйте исправленные файлы зависимостей:

```bash
# Минимальные зависимости (рекомендуется)
pip install -r requirements_internet_minimal.txt

# Или установите вручную
pip install aiohttp requests beautifulsoup4 lxml feedparser flask python-dotenv
```

---

## 🚀 **ПОШАГОВАЯ УСТАНОВКА**

### **Шаг 1: Установка зависимостей**
```bash
# Установите минимальные зависимости
pip install aiohttp requests beautifulsoup4 lxml feedparser flask python-dotenv

# Попробуйте установить дополнительные (необязательно)
pip install trafilatura newspaper3k
```

### **Шаг 2: Копирование файлов**
```bash
# Скопируйте исправленную систему
cp internet_intelligence_system_fixed.py backend/internet_intelligence_system.py

# Скопируйте остальные файлы
cp ikar_internet_integration.py backend/
cp integrate_with_ikar.py backend/
cp internet_api.py backend/api/
```

### **Шаг 3: Создание папки данных**
```bash
mkdir -p data
```

### **Шаг 4: Тестирование**
```bash
# Простой тест
python simple_test_internet.py

# Полный тест
python test_internet_intelligence.py
```

---

## 🔧 **АВТОМАТИЧЕСКАЯ УСТАНОВКА**

Используйте скрипт автоматической установки:

```bash
# Сделайте скрипт исполняемым
chmod +x quick_install_internet_intelligence.sh

# Запустите установку
./quick_install_internet_intelligence.sh
```

---

## 🧪 **ТЕСТИРОВАНИЕ**

### **Быстрый тест**
```bash
python simple_test_internet.py
```

### **Полный тест**
```bash
python test_internet_intelligence.py
```

### **Демонстрация**
```bash
python run_internet_intelligence.py
```

---

## 🚨 **УСТРАНЕНИЕ ПРОБЛЕМ**

### **Проблема: "trafilatura>=5.0.0 не найден"**
**Решение:** Используйте исправленный файл зависимостей:
```bash
pip install -r requirements_internet_minimal.txt
```

### **Проблема: "ModuleNotFoundError"**
**Решение:** Убедитесь, что файлы скопированы в правильные места:
```bash
ls backend/internet_intelligence_system.py
ls backend/ikar_internet_integration.py
ls backend/integrate_with_ikar.py
ls backend/api/internet_api.py
```

### **Проблема: "Permission denied"**
**Решение:** Используйте пользовательскую установку:
```bash
pip install --user aiohttp requests beautifulsoup4 lxml feedparser flask python-dotenv
```

### **Проблема: "Connection error"**
**Решение:** Проверьте интернет-соединение:
```bash
curl -I https://www.google.com
```

---

## 📋 **ПРОВЕРКА УСТАНОВКИ**

После установки выполните проверку:

```bash
python -c "
import aiohttp
import requests
import bs4
import feedparser
import flask
print('✅ Все основные зависимости установлены')
"
```

---

## 🎯 **ЗАПУСК СИСТЕМЫ**

### **1. Простой тест**
```bash
python simple_test_internet.py
```

### **2. Демонстрация**
```bash
python run_internet_intelligence.py
```

### **3. Интеграция с IKAR**
```bash
python integrate_to_main_ikar.py
```

### **4. Запуск IKAR с интернет-интеллектом**
```bash
python run_ikar_with_internet.py
```

---

## 🌐 **ВЕБ-ИНТЕРФЕЙС**

После запуска откройте:
- **Главная**: `http://localhost:6666/`
- **Интернет-интеллект**: `http://localhost:6666/internet-intelligence.html`

---

## 📊 **ПРОВЕРКА РАБОТЫ**

### **Тест 1: Поиск**
```python
import asyncio
from backend.internet_intelligence_system import InternetIntelligenceSystem

async def test():
    system = InternetIntelligenceSystem()
    results = await system.search_internet("новости о технологиях")
    print(f"Найдено: {len(results)} результатов")
    await system.close()

asyncio.run(test())
```

### **Тест 2: Улучшение ответов**
```python
import asyncio
from backend.integrate_with_ikar import enhance_ikar_message

async def test():
    enhanced = await enhance_ikar_message(
        "Новости о технологиях",
        "Технологии развиваются.",
        "test_user"
    )
    print(f"Улучшенный ответ: {enhanced[:100]}...")

asyncio.run(test())
```

---

## 🎉 **ГОТОВО!**

После успешной установки IKAR будет автоматически:

✅ **Определять** когда нужна свежая информация  
✅ **Искать** в интернете по множественным источникам  
✅ **Обрабатывать** информацию через AI  
✅ **Улучшать** ответы актуальными данными  
✅ **Сохранять** личность и стиль общения  

**Система готова к использованию!** 🚀 