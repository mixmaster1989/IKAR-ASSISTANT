#!/usr/bin/env python3
"""
🔗 ИНТЕГРАЦИЯ ИНТЕРНЕТ-ИНТЕЛЛЕКТА С ОСНОВНОЙ СИСТЕМОЙ IKAR
Автоматическая интеграция всех компонентов
"""

import os
import sys
import shutil
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def integrate_with_main_system():
    """Интеграция с основной системой IKAR"""
    print("🔗 ИНТЕГРАЦИЯ ИНТЕРНЕТ-ИНТЕЛЛЕКТА С IKAR")
    print("=" * 60)
    
    # Проверяем структуру проекта
    if not Path("backend").exists():
        print("❌ Папка 'backend' не найдена. Убедитесь, что вы в корне проекта IKAR.")
        return False
    
    # Копируем файлы в нужные места
    files_to_copy = [
        ("internet_intelligence_system.py", "backend/"),
        ("ikar_internet_integration.py", "backend/"),
        ("integrate_with_ikar.py", "backend/"),
        ("internet_api.py", "backend/api/"),
        ("test_internet_intelligence.py", "./"),
        ("run_internet_intelligence.py", "./"),
        ("INTERNET_INTELLIGENCE_README.md", "./"),
        ("requirements_internet_intelligence.txt", "./")
    ]
    
    print("📁 Копирование файлов...")
    for src, dst in files_to_copy:
        if Path(src).exists():
            dst_path = Path(dst)
            dst_path.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src, dst_path / Path(src).name)
            print(f"✅ {src} -> {dst}")
        else:
            print(f"⚠️  Файл {src} не найден")
    
    # Копируем веб-интерфейс
    if Path("frontend/public/internet-intelligence.html").exists():
        print("✅ Веб-интерфейс уже на месте")
    else:
        print("⚠️  Веб-интерфейс не найден")
    
    # Обновляем requirements.txt
    print("📦 Обновление зависимостей...")
    update_requirements()
    
    # Создаем папку для данных
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    print("✅ Папка data создана")
    
    # Интеграция с основными файлами IKAR
    print("🔧 Интеграция с основными файлами...")
    integrate_with_routes()
    integrate_with_telegram()
    integrate_with_main()
    
    print("\n🎉 ИНТЕГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("\n📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Установите зависимости: pip install -r requirements_internet_intelligence.txt")
    print("2. Запустите тест: python run_internet_intelligence.py")
    print("3. Откройте веб-интерфейс: http://localhost:6666/internet-intelligence.html")
    print("4. Интеграция автоматически активирована в основной системе IKAR")
    
    return True

def update_requirements():
    """Обновление файла requirements.txt"""
    try:
        # Читаем существующие зависимости
        main_req_file = Path("requirements.txt")
        internet_req_file = Path("requirements_internet_intelligence.txt")
        
        if main_req_file.exists() and internet_req_file.exists():
            with open(main_req_file, 'r', encoding='utf-8') as f:
                main_deps = f.read()
            
            with open(internet_req_file, 'r', encoding='utf-8') as f:
                internet_deps = f.read()
            
            # Добавляем интернет-зависимости
            if "# Интернет-интеллект" not in main_deps:
                with open(main_req_file, 'a', encoding='utf-8') as f:
                    f.write("\n# Интернет-интеллект\n")
                    f.write("aiohttp>=3.8.0\n")
                    f.write("beautifulsoup4>=4.11.0\n")
                    f.write("feedparser>=6.0.0\n")
                    f.write("trafilatura>=5.0.0\n")
                    f.write("newspaper3k>=0.2.8\n")
                    f.write("flask>=2.3.0\n")
                
                print("✅ requirements.txt обновлен")
            else:
                print("✅ Зависимости уже добавлены")
        
    except Exception as e:
        print(f"⚠️  Ошибка обновления requirements.txt: {e}")

def integrate_with_routes():
    """Интеграция с routes.py"""
    try:
        routes_file = Path("backend/api/routes.py")
        if not routes_file.exists():
            print("⚠️  routes.py не найден")
            return
        
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, есть ли уже интеграция
        if "internet_api" in content:
            print("✅ Интернет-API уже интегрирован в routes.py")
            return
        
        # Добавляем импорт
        if "from . import internet_api" not in content:
            # Находим место для импорта
            import_section = content.find("from . import")
            if import_section != -1:
                # Находим конец импортов
                end_import = content.find("\n\n", import_section)
                if end_import != -1:
                    new_content = (
                        content[:end_import] + 
                        "\nfrom . import internet_api" +
                        content[end_import:]
                    )
                    
                    with open(routes_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print("✅ Интернет-API добавлен в routes.py")
        
    except Exception as e:
        print(f"⚠️  Ошибка интеграции с routes.py: {e}")

def integrate_with_telegram():
    """Интеграция с telegram.py"""
    try:
        telegram_file = Path("backend/api/telegram.py")
        if not telegram_file.exists():
            print("⚠️  telegram.py не найден")
            return
        
        with open(telegram_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, есть ли уже интеграция
        if "enhance_telegram_message" in content:
            print("✅ Интернет-интеллект уже интегрирован в telegram.py")
            return
        
        # Добавляем импорт
        if "from integrate_with_ikar import enhance_telegram_message" not in content:
            # Находим место для импорта
            import_section = content.find("import")
            if import_section != -1:
                # Находим конец импортов
                end_import = content.find("\n\n", import_section)
                if end_import != -1:
                    new_content = (
                        content[:end_import] + 
                        "\nfrom integrate_with_ikar import enhance_telegram_message" +
                        content[end_import:]
                    )
                    
                    # Находим функцию обработки сообщений
                    message_handler = content.find("async def handle_message")
                    if message_handler != -1:
                        # Добавляем улучшение ответа
                        response_section = content.find("await bot.send_message", message_handler)
                        if response_section != -1:
                            # Находим конец функции
                            func_end = content.find("\n\n", response_section)
                            if func_end != -1:
                                # Вставляем улучшение перед отправкой
                                enhanced_content = (
                                    new_content[:response_section] +
                                    "\n        # Улучшаем ответ интернет-информацией\n" +
                                    "        enhanced_response = await enhance_telegram_message(message.text, response, str(message.from_user.id))\n" +
                                    "        response = enhanced_response\n" +
                                    new_content[response_section:func_end] +
                                    new_content[func_end:]
                                )
                                
                                with open(telegram_file, 'w', encoding='utf-8') as f:
                                    f.write(enhanced_content)
                                
                                print("✅ Интернет-интеллект интегрирован в telegram.py")
                                return
        
        print("⚠️  Не удалось найти место для интеграции в telegram.py")
        
    except Exception as e:
        print(f"⚠️  Ошибка интеграции с telegram.py: {e}")

def integrate_with_main():
    """Интеграция с main.py"""
    try:
        main_file = Path("backend/main.py")
        if not main_file.exists():
            print("⚠️  main.py не найден")
            return
        
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, есть ли уже интеграция
        if "register_internet_api" in content:
            print("✅ Интернет-API уже интегрирован в main.py")
            return
        
        # Добавляем импорт
        if "from api.internet_api import register_internet_api" not in content:
            # Находим место для импорта
            import_section = content.find("from api import")
            if import_section != -1:
                # Находим конец импортов
                end_import = content.find("\n\n", import_section)
                if end_import != -1:
                    new_content = (
                        content[:end_import] + 
                        "\nfrom api.internet_api import register_internet_api" +
                        content[end_import:]
                    )
                    
                    # Находим место для регистрации API
                    app_creation = new_content.find("app = Flask")
                    if app_creation != -1:
                        # Находим конец инициализации
                        init_end = new_content.find("\n\n", app_creation)
                        if init_end != -1:
                            # Добавляем регистрацию API
                            final_content = (
                                new_content[:init_end] +
                                "\n\n# Регистрация интернет-API\nregister_internet_api(app)" +
                                new_content[init_end:]
                            )
                            
                            with open(main_file, 'w', encoding='utf-8') as f:
                                f.write(final_content)
                            
                            print("✅ Интернет-API интегрирован в main.py")
                            return
        
        print("⚠️  Не удалось найти место для интеграции в main.py")
        
    except Exception as e:
        print(f"⚠️  Ошибка интеграции с main.py: {e}")

def create_integration_script():
    """Создание скрипта для быстрой интеграции"""
    script_content = '''#!/usr/bin/env python3
"""
🚀 БЫСТРЫЙ ЗАПУСК IKAR С ИНТЕРНЕТ-ИНТЕЛЛЕКТОМ
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "backend"))

async def main():
    """Главная функция с интернет-интеллектом"""
    try:
        # Импортируем основную систему IKAR
        from main import app
        
        # Импортируем интернет-интеллект
        from integrate_with_ikar import get_ikar_enhancer
        
        # Инициализируем интернет-интеллект
        enhancer = await get_ikar_enhancer()
        print("✅ Интернет-интеллект инициализирован")
        
        # Запускаем основное приложение
        print("🚀 Запуск IKAR с интернет-интеллектом...")
        app.run(host='0.0.0.0', port=6666, debug=False)
        
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open("run_ikar_with_internet.py", 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Скрипт run_ikar_with_internet.py создан")

def main():
    """Главная функция интеграции"""
    print("🔗 ИНТЕГРАЦИЯ ИНТЕРНЕТ-ИНТЕЛЛЕКТА С IKAR")
    print("=" * 60)
    
    # Проверяем, что мы в правильной директории
    if not Path("README.md").exists():
        print("❌ README.md не найден. Убедитесь, что вы в корне проекта IKAR.")
        return
    
    # Выполняем интеграцию
    if integrate_with_main_system():
        # Создаем скрипт запуска
        create_integration_script()
        
        print("\n🎉 ИНТЕГРАЦИЯ ПОЛНОСТЬЮ ЗАВЕРШЕНА!")
        print("\n📋 КОМАНДЫ ДЛЯ ЗАПУСКА:")
        print("1. Установка зависимостей:")
        print("   pip install -r requirements_internet_intelligence.txt")
        print("\n2. Тестирование системы:")
        print("   python run_internet_intelligence.py")
        print("\n3. Запуск IKAR с интернет-интеллектом:")
        print("   python run_ikar_with_internet.py")
        print("\n4. Веб-интерфейс:")
        print("   http://localhost:6666/internet-intelligence.html")
        
        print("\n🌟 Теперь IKAR автоматически улучшает ответы свежей информацией из интернета!")

if __name__ == "__main__":
    main() 