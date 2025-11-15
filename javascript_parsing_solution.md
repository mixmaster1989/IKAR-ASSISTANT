# 🔧 РЕШЕНИЕ: ПАРСИНГ JAVASCRIPT-HEAVY ЯНДЕКС.УСЛУГИ

## 🎯 ПРОБЛЕМА:
Яндекс.Услуги загружает заказы через JavaScript, поэтому простой BeautifulSoup не находит контент.

## ✅ РЕШЕНИЕ: 2 РАБОЧИХ ВАРИАНТА

### ВАРИАНТ 1: Playwright (РЕКОМЕНДУЕТСЯ) ⚡ БЫСТРО
**Почему:** 2.3x быстрее, чем Selenium, меньше памяти, лучше для JS-сайтов[88][89][91][92]

**Плюсы:**
- 2-3x быстрее чем Selenium на JS-тяжелых сайтах
- Встроенная поддержка сетевого перехвата
- Auto-waiting (меньше ошибок)
- Параллельное выполнение

**Минусы:**
- Новый инструмент (но быстро распространяется)

### ВАРИАНТ 2: Selenium (ПРОВЕРЕНО)
**Почему:** Надежен, работает везде, много документации

**Плюсы:**
- Стабильный и проверенный
- Широкая поддержка браузеров
- Много примеров в интернете

**Минусы:**
- ~2x медленнее, чем Playwright[88][89]
- Больше памяти
- Требует явное управление waits

---

## 💻 КОД: PLAYWRIGHT РЕШЕНИЕ (РЕКОМЕНДУЕТСЯ)

### Шаг 1: Добавить Playwright в requirements.txt

```
playwright==1.48.0
playwright-stealth==1.0.1
```

### Шаг 2: Обновить parsers/yandex_uslugi.py

```python
from parsers.base_parser import BaseParser
from typing import List, Dict, Optional
import re
import logging
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class YandexUslugiParser(BaseParser):
    def __init__(self):
        super().__init__(
            name="yandex_uslugi",
            base_url="https://uslugi.yandex.ru",
            timeout=30,
            delay=1.5  # Менее напряженный на Playwright
        )
        self.categories_map = {
            "santehnika": "Сантехника",
            "elektrika": "Электрика",
            "uborka": "Уборка",
            "remont": "Ремонт",
            "master-na-chas": "Мастер на час"
        }
    
    async def parse(self) -> List[Dict]:
        """Парсинг через Playwright с JavaScript поддержкой"""
        orders = []
        
        try:
            async with async_playwright() as p:
                # Запустить браузер
                browser = await p.chromium.launch(headless=True)
                
                for category_slug, category_name in self.categories_map.items():
                    self.logger.info(f"Parsing {category_name} with Playwright...")
                    
                    for city in ["moscow", "spb"]:
                        try:
                            # Создать новую страницу (context для параллелизма)
                            page = await browser.new_page()
                            
                            # Установить User-Agent (Яндекс может блокировать ботов)
                            await page.set_extra_http_headers({
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            })
                            
                            # URL для категории в городе
                            url = f"{self.base_url}/{city}/category/{category_slug}"
                            
                            self.logger.debug(f"Navigating to {url}...")
                            
                            # Перейти на страницу и дождаться загрузки
                            # waitUntil='networkidle' ждет пока все network запросы завершатся
                            await page.goto(url, wait_until='networkidle', timeout=30000)
                            
                            # ⏳ Дополнительное ожидание (JS может генерировать контент асинхронно)
                            await page.wait_for_timeout(2000)
                            
                            # Получить полностью отрендеренный HTML
                            page_html = await page.content()
                            
                            # Парсить HTML через BeautifulSoup
                            category_orders = await self._parse_category_page(
                                page_html, 
                                category_name, 
                                city
                            )
                            
                            orders.extend(category_orders)
                            
                            self.logger.info(f"Found {len(category_orders)} orders in {city}")
                            
                            await page.close()
                            
                            # Rate limiting
                            await self._rate_limit()
                        
                        except Exception as e:
                            self.logger.error(f"Error parsing {city}/{category_slug}: {e}")
                            if page:
                                await page.close()
                
                await browser.close()
        
        except Exception as e:
            self.logger.error(f"Playwright error: {e}")
        
        self.logger.info(f"Total orders parsed: {len(orders)}")
        return orders
    
    async def _parse_category_page(self, html: str, category: str, city: str) -> List[Dict]:
        """Парсить HTML после того как JavaScript выполнился"""
        orders = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Попробовать несколько селекторов (разные версии сайта)
        selectors = [
            'div[class*="Order"]',
            'div[class*="order"]',
            'article[class*="order"]',
            'div[data-testid*="order"]'
        ]
        
        cards = []
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                self.logger.debug(f"Found {len(cards)} cards with selector: {selector}")
                break
        
        if not cards:
            self.logger.warning(f"No order cards found for {city}/{category}")
            return orders
        
        for card in cards:
            try:
                order = self._parse_order(card)
                if order:
                    order['category'] = category
                    order['location'] = city
                    order['platform'] = 'yandex_uslugi'
                    orders.append(order)
            
            except Exception as e:
                self.logger.debug(f"Error parsing card: {e}")
        
        return orders
    
    def _parse_order(self, item) -> Optional[Dict]:
        """Парсить отдельный заказ из HTML"""
        try:
            # Попробовать найти ID (может быть в разных местах)
            order_id = None
            
            # Вариант 1: data атрибут
            for attr in ['data-id', 'data-order-id', 'data-testid']:
                if item.get(attr):
                    order_id = item.get(attr)
                    break
            
            # Вариант 2: в href ссылки
            if not order_id:
                link = item.find('a', href=re.compile(r'/zakazy/|/order'))
                if link:
                    href = link.get('href', '')
                    match = re.search(r'(\d+)', href)
                    order_id = match.group(1) if match else None
            
            if not order_id:
                return None
            
            # Получить заголовок (попробовать несколько селекторов)
            title = None
            for tag in ['h3', 'h2', 'a']:
                title_elem = item.find(tag)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 3:
                        break
            
            # Получить описание
            description = None
            for class_name in ['description', 'text', 'content', 'body']:
                desc_elem = item.find('p', class_=re.compile(f'.*{class_name}.*', re.I))
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    break
            
            # Получить бюджет
            budget = None
            for class_name in ['price', 'budget', 'amount']:
                price_elem = item.find(re.compile('span|div'), class_=re.compile(f'.*{class_name}.*', re.I))
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    budget = self._parse_budget(price_text)
                    if budget:
                        break
            
            # Фильтр спама
            if self._is_spam(title, description):
                self.logger.debug(f"Spam detected: {title}")
                return None
            
            # Минимальная валидация
            if not title or not description:
                return None
            
            return {
                'platform_order_id': str(order_id),
                'title': title[:500],
                'description': description[:2000],
                'budget': budget,
                'raw_data': str(item)[:1000]
            }
        
        except Exception as e:
            self.logger.error(f"Parse order error: {e}")
            return None
    
    def _parse_budget(self, budget_text: str) -> Optional[int]:
        """Извлечь бюджет из текста"""
        if not budget_text:
            return None
        
        # Удалить всё кроме цифр и точек
        numbers = re.findall(r'\d+', budget_text)
        
        if numbers:
            # Если несколько чисел (диапазон) - вернуть среднее
            if len(numbers) > 1:
                return (int(numbers[0]) + int(numbers[1])) // 2
            return int(numbers[0])
        
        return None
    
    def _is_spam(self, title: str, description: str) -> bool:
        """Фильтр спама"""
        if not title or not description:
            return True
        
        spam_keywords = [
            r'\bкупи\b', r'\bпродай\b', r'\bссылка\b', r'\bклик\b',
            r'\b(whatsapp|telegram|viber)\b', r'\bhttps?://'
        ]
        
        text = (title + ' ' + description).lower()
        
        for pattern in spam_keywords:
            if re.search(pattern, text):
                return True
        
        # Минимум символов (очень короткие объявления - спам)
        if len(description) < 20:
            return True
        
        return False
```

### Шаг 3: Обновить requirements.txt

```bash
# Добавить в конец requirements.txt:
echo "playwright==1.48.0" >> requirements.txt
echo "playwright-stealth==1.0.1" >> requirements.txt

# Установить Playwright браузеры
docker-compose exec bot playwright install chromium
```

### Шаг 4: Обновить docker-compose.yml

```yaml
# В сервисе bot добавить:
environment:
  - PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
volumes:
  - ./ms-playwright:/ms-playwright  # Сохранять браузеры между перезагрузками
```

---

## 🔄 АЛЬТЕРНАТИВА: SELENIUM (Если Playwright не работает)

### Шаг 1: Обновить requirements.txt

```
selenium==4.15.2
```

### Шаг 2: Парсер через Selenium

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import asyncio

class YandexUslugiSeleniumParser(BaseParser):
    def __init__(self):
        super().__init__(
            name="yandex_uslugi_selenium",
            base_url="https://uslugi.yandex.ru",
            timeout=30
        )
    
    async def parse(self) -> List[Dict]:
        """Парсинг через Selenium"""
        orders = []
        
        # Настройки Chrome
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        
        driver = None
        try:
            # Запустить браузер
            driver = webdriver.Chrome(options=options)
            
            for category_slug, category_name in self.categories_map.items():
                self.logger.info(f"Parsing {category_name} with Selenium...")
                
                for city in ["moscow", "spb"]:
                    try:
                        url = f"{self.base_url}/{city}/category/{category_slug}"
                        driver.get(url)
                        
                        # ⏳ Ждать загрузки элементов (явное ожидание)
                        wait = WebDriverWait(driver, 15)
                        
                        # Попробовать подождать пока контейнер с заказами загрузится
                        try:
                            wait.until(
                                EC.presence_of_all_elements_located((By.CLASS_NAME, "OrderCard"))
                            )
                        except:
                            self.logger.warning(f"Elements not found with selector OrderCard")
                        
                        # Дополнительное ожидание для асинхронного контента
                        await asyncio.sleep(2)
                        
                        # Получить HTML после выполнения JavaScript
                        page_html = driver.page_source
                        
                        # Парсить через BeautifulSoup
                        soup = BeautifulSoup(page_html, 'html.parser')
                        cards = soup.find_all('div', class_=re.compile(r'.*order.*', re.I))
                        
                        for card in cards:
                            order = self._parse_order(card)
                            if order:
                                order['category'] = category_name
                                order['location'] = city
                                order['platform'] = 'yandex_uslugi'
                                orders.append(order)
                        
                        self.logger.info(f"Found {len(orders)} orders")
                        
                        await asyncio.sleep(self.delay)
                    
                    except Exception as e:
                        self.logger.error(f"Selenium parse error: {e}")
        
        finally:
            if driver:
                driver.quit()
        
        return orders
```

---

## 🎯 СРАВНЕНИЕ: Playwright vs Selenium

| Критерий | Playwright | Selenium |
|----------|-----------|----------|
| **Скорость** | 2.3x быстрее | Базовая скорость |
| **Память** | 30% меньше | Больше памяти |
| **Стабильность** | Auto-wait (лучше) | Требует явный wait |
| **JS-сайты** | Оптимизирован | Хорошо, но медленнее |
| **Network перехват** | Встроен | Требует доп. код |
| **Параллелизм** | Встроен | Требует Grid |
| **Кривая обучения** | Пологая | Крутая |

**Вердикт:** Playwright для парсинга JS-тяжелых сайтов (вроде Яндекс.Услуг)[88][89][91][92]

---

## 🚀 ДЕПЛОЙ НА VPS (для Playwright)

### На VPS установить зависимости:

```bash
# SSH на VPS
ssh ubuntu@your-vps-ip

# Установить Chrome для headless парсинга
sudo apt-get update
sudo apt-get install -y \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libpango-cairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    fonts-liberation \
    libnss3 \
    libopensc2

# В docker-compose.yml браузер установится автоматически
```

---

## 🔍 ОТЛАДКА

### Если Playwright не находит элементы:

```python
# 1. Увеличить ожидание
await page.wait_for_timeout(5000)  # 5 секунд

# 2. Дождаться конкретного селектора
await page.wait_for_selector('div.OrderCard', timeout=20000)

# 3. Сохранить скриншот для отладки
await page.screenshot(path='debug.png')

# 4. Сохранить HTML для анализа
html = await page.content()
with open('debug.html', 'w') as f:
    f.write(html)
```

### Если Selenium зависает:

```python
# Увеличить timeout
driver = webdriver.Chrome()
driver.set_page_load_timeout(30)

# Использовать явное ожидание
wait = WebDriverWait(driver, 15)
element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "OrderCard")))
```

---

## 📊 ТЕСТ

```bash
# Запустить парсер локально
docker-compose up --build

# Проверить логи
docker-compose logs -f bot | grep -i "yandex\|playwright"

# Проверить БД
docker-compose exec postgres psql -U verticalai_user -d verticalai_db -c \
  "SELECT COUNT(*) FROM orders WHERE platform='yandex_uslugi';"
```

---

**Рекомендация:** Используй **Playwright** - это будущее парсинга JS-сайтов. 2.3x быстрее, надежнее, меньше кода.[88][89][91][92]

Если что-то не работает - дай мне скриншот ошибки или HTML код со страницы, доделаем! 🚀
