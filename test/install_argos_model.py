#!/usr/bin/env python3
"""
Скрипт для ручной установки модели Argos Translate ru->en
"""
import urllib.request
import tempfile
import os
import sys

def install_argos_model():
    """Устанавливает модель ru->en для Argos Translate"""
    
    print("🔧 Установка модели Argos Translate ru->en")
    
    try:
        import argostranslate.package, argostranslate.translate
        print("✅ Argos Translate найден")
    except ImportError:
        print("❌ Argos Translate не установлен")
        print("💡 Установите: pip install argostranslate")
        return False
    
    # Проверяем, установлена ли уже модель
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((lang for lang in installed_languages if lang.code == "ru"), None)
    to_lang = next((lang for lang in installed_languages if lang.code == "en"), None)
    
    if from_lang and to_lang:
        print("✅ Модель ru->en уже установлена")
        print(f"🌍 Найдены языки: {from_lang.name} -> {to_lang.name}")
        return True
    
    # Скачиваем и устанавливаем модель
    model_url = "https://data.argosopentech.com/argospm/v1/translate-ru_en-1_9.argosmodel"
    
    print(f"📥 Скачиваем модель с: {model_url}")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.argosmodel') as tmp_file:
            urllib.request.urlretrieve(model_url, tmp_file.name)
            print(f"📦 Модель скачана в: {tmp_file.name}")
            
            print("🔧 Устанавливаем модель...")
            argostranslate.package.install_from_path(tmp_file.name)
            
            # Удаляем временный файл
            os.unlink(tmp_file.name)
            print("🗑️ Временный файл удален")
        
        # Проверяем установку
        installed_languages = argostranslate.translate.get_installed_languages()
        from_lang = next((lang for lang in installed_languages if lang.code == "ru"), None)
        to_lang = next((lang for lang in installed_languages if lang.code == "en"), None)
        
        if from_lang and to_lang:
            print("✅ Модель успешно установлена!")
            print(f"🌍 Доступны языки: {from_lang.name} -> {to_lang.name}")
            
            # Тестируем перевод
            translation = from_lang.get_translation(to_lang)
            test_text = "привет мир"
            translated = translation.translate(test_text)
            print(f"🧪 Тест перевода: '{test_text}' -> '{translated}'")
            
            return True
        else:
            print("❌ Модель установлена, но языки не найдены")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при установке: {e}")
        print("\n💡 Попробуйте установить вручную:")
        print("1. Скачайте файл: https://data.argosopentech.com/argospm/v1/translate-ru_en-1_9.argosmodel")
        print("2. Установите: argostranslate.package.install_from_path('translate-ru_en-1_9.argosmodel')")
        return False

if __name__ == "__main__":
    success = install_argos_model()
    if success:
        print("\n🎉 Установка завершена успешно!")
    else:
        print("\n❌ Установка не удалась")
        sys.exit(1) 