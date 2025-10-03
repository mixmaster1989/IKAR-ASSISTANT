#!/usr/bin/env python3
"""
Простой тест Argos Translate для диагностики
"""
import sys
import os

def test_argos_installation():
    """Тестирует установку Argos Translate"""
    print("🔍 Проверяем установку Argos Translate...")
    
    try:
        import argostranslate
        print("✅ Argos Translate импортируется успешно")
        # Попробуем получить версию разными способами
        try:
            import pkg_resources
            version = pkg_resources.get_distribution("argostranslate").version
            print(f"📦 Версия: {version}")
        except:
            print("📦 Версия: неизвестна")
    except ImportError as e:
        print(f"❌ Argos Translate не установлен: {e}")
        print("💡 Установите: pip install argostranslate")
        return False
    
    try:
        import argostranslate.translate
        print("✅ Модуль translate импортируется успешно")
    except ImportError as e:
        print(f"❌ Модуль translate не импортируется: {e}")
        return False
    
    try:
        import argostranslate.package
        print("✅ Модуль package импортируется успешно")
    except ImportError as e:
        print(f"❌ Модуль package не импортируется: {e}")
        return False
    
    return True

def test_installed_languages():
    """Тестирует установленные языки"""
    print("\n🌍 Проверяем установленные языки...")
    
    try:
        import argostranslate.translate
        installed_languages = argostranslate.translate.get_installed_languages()
        print(f"📋 Найдено языков: {len(installed_languages)}")
        
        for lang in installed_languages:
            print(f"  - {lang.code}: {lang.name}")
        
        # Проверяем русский и английский
        ru_lang = next((lang for lang in installed_languages if lang.code == "ru"), None)
        en_lang = next((lang for lang in installed_languages if lang.code == "en"), None)
        
        if ru_lang:
            print(f"✅ Русский язык найден: {ru_lang.name}")
        else:
            print("❌ Русский язык не найден")
            
        if en_lang:
            print(f"✅ Английский язык найден: {en_lang.name}")
        else:
            print("❌ Английский язык не найден")
            
        return ru_lang is not None and en_lang is not None
        
    except Exception as e:
        print(f"❌ Ошибка при проверке языков: {e}")
        return False

def test_translation():
    """Тестирует перевод"""
    print("\n🔄 Тестируем перевод...")
    
    try:
        import argostranslate.translate
        installed_languages = argostranslate.translate.get_installed_languages()
        
        from_lang = next((lang for lang in installed_languages if lang.code == "ru"), None)
        to_lang = next((lang for lang in installed_languages if lang.code == "en"), None)
        
        if not (from_lang and to_lang):
            print("❌ Не найдены языки ru->en")
            return False
        
        translation = from_lang.get_translation(to_lang)
        test_text = "привет мир"
        translated = translation.translate(test_text)
        
        print(f"📝 Тест: '{test_text}' -> '{translated}'")
        
        if translated and translated != test_text:
            print("✅ Перевод работает!")
            return True
        else:
            print("❌ Перевод не работает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при переводе: {e}")
        return False

def test_download():
    """Тестирует скачивание модели"""
    print("\n⬇️ Тестируем скачивание модели...")
    
    try:
        import argostranslate.package
        print("🔗 Пытаемся скачать модель ru->en...")
        
        # Попробуем скачать модель напрямую
        try:
            import urllib.request
            import tempfile
            import os
            
            # Актуальный URL для модели ru->en с data.argosopentech.com
            model_url = "https://data.argosopentech.com/argospm/v1/translate-ru_en-1_9.argosmodel"
            
            print(f"🌐 Скачиваем с: {model_url}")
            
            # Создаем временный файл для скачивания
            with tempfile.NamedTemporaryFile(delete=False, suffix='.argosmodel') as tmp_file:
                urllib.request.urlretrieve(model_url, tmp_file.name)
                
                print(f"📦 Модель скачана в: {tmp_file.name}")
                argostranslate.package.install_from_path(tmp_file.name)
                
                # Удаляем временный файл
                os.unlink(tmp_file.name)
                
            print("✅ Модель установлена")
            return True
                
        except Exception as e:
            print(f"❌ Ошибка основного URL: {e}")
            
            # Попробуем альтернативный URL
            try:
                import urllib.request
                import tempfile
                import os
                
                # Альтернативный URL (если основной не работает)
                alt_model_url = "https://data.argosopentech.com/argospm/v1/translate-ru_en-1_0.argosmodel"
                
                print(f"🌐 Пробуем альтернативный URL: {alt_model_url}")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.argosmodel') as tmp_file:
                    urllib.request.urlretrieve(alt_model_url, tmp_file.name)
                    argostranslate.package.install_from_path(tmp_file.name)
                    os.unlink(tmp_file.name)
                
                print("✅ Модель установлена через альтернативный URL")
                return True
                    
            except Exception as e2:
                print(f"❌ Ошибка альтернативного URL: {e2}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка при скачивании: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Диагностика Argos Translate\n")
    
    # Тест 1: Установка
    if not test_argos_installation():
        sys.exit(1)
    
    # Тест 2: Языки
    if not test_installed_languages():
        print("\n📥 Попробуем скачать недостающие языки...")
        if not test_download():
            print("\n❌ Не удалось скачать языки")
            sys.exit(1)
        # Повторная проверка
        if not test_installed_languages():
            print("\n❌ Языки все еще не найдены")
            sys.exit(1)
    
    # Тест 3: Перевод
    if not test_translation():
        print("\n❌ Перевод не работает")
        sys.exit(1)
    
    print("\n🎉 Все тесты пройдены! Argos Translate работает корректно.") 