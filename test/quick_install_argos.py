#!/usr/bin/env python3
"""
Быстрая установка модели Argos Translate ru->en
"""
import urllib.request
from argostranslate import package, translate

def quick_install():
    """Быстрая установка модели ru->en"""
    
    print("🚀 Быстрая установка модели Argos Translate ru->en")
    
    # URL актуальной модели
    url = "https://data.argosopentech.com/argospm/v1/translate-ru_en-1_9.argosmodel"
    fname = url.split("/")[-1]
    
    print(f"📥 Скачиваю {fname}...")
    
    try:
        urllib.request.urlretrieve(url, fname)
        print(f"✅ Скачано: {fname}")
        
        print("🔧 Устанавливаю...")
        package.install_from_path(fname)
        
        # Проверяем установку
        langs = translate.get_installed_languages()
        lang_names = [l.name for l in langs]
        print(f"🌍 Установленные языки: {lang_names}")
        
        # Тестируем перевод
        ru_lang = next((lang for lang in langs if lang.code == "ru"), None)
        en_lang = next((lang for lang in langs if lang.code == "en"), None)
        
        if ru_lang and en_lang:
            translation = ru_lang.get_translation(en_lang)
            test_text = "привет мир"
            translated = translation.translate(test_text)
            print(f"🧪 Тест перевода: '{test_text}' -> '{translated}'")
            print("🎉 Установка завершена успешно!")
            return True
        else:
            print("❌ Языки не найдены после установки")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = quick_install()
    if not success:
        print("\n💡 Попробуйте вручную:")
        print("wget https://data.argosopentech.com/argospm/v1/translate-ru_en-1_9.argosmodel")
        print("python3 -c \"from argostranslate import package; package.install_from_path('translate-ru_en-1_9.argosmodel')\"") 