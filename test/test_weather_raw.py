#!/usr/bin/env python3
"""
Тест погодного поиска с сырыми данными
"""

import json
from simple_internet_system import SimpleInternetSystem

def test_weather_raw():
    """Тестирование погодного поиска с сырыми данными"""
    
    print("🌤️ ТЕСТ ПОГОДНОГО ПОИСКА С СЫРЫМИ ДАННЫМИ")
    print("=" * 60)
    
    system = SimpleInternetSystem()
    
    # Тест погоды
    print("\n🔍 Поиск погоды в Ростове...")
    result = system.search_internet("погода в Ростове")
    
    print(f"✅ Успех: {result.get('success', False)}")
    print(f"📊 Тип: {result.get('type', 'unknown')}")
    
    if result.get('success'):
        data = result['data']
        print(f"🏙️ Город: {data.get('city', 'N/A')}")
        print(f"📚 Источники: {len(data.get('sources', []))}")
        
        # Показываем сырые данные
        for i, source in enumerate(data.get('sources', [])[:3], 1):
            print(f"\n--- ИСТОЧНИК {i} ---")
            print(f"📰 Заголовок: {source.get('title', 'N/A')}")
            print(f"🔗 URL: {source.get('url', 'N/A')}")
            print(f"📄 Контент (первые 300 символов):")
            content = source.get('content', 'N/A')
            print(f"   {content[:300]}...")
            
            # Показываем сниппет
            snippet = source.get('snippet', '')
            if snippet:
                print(f"📝 Сниппет: {snippet[:200]}...")
        
        print(f"\n📋 Сводка: {data.get('summary', 'N/A')}")
        
        # Показываем, как это будет выглядеть в промпте
        print(f"\n🎯 КАК ЭТО БУДЕТ В ПРОМПТЕ:")
        print("-" * 40)
        
        raw_content = ""
        for i, source in enumerate(data.get('sources', [])[:3], 1):
            raw_content += f"\n--- ИСТОЧНИК {i} ---\n"
            raw_content += f"Заголовок: {source.get('title', 'N/A')}\n"
            raw_content += f"URL: {source.get('url', 'N/A')}\n"
            raw_content += f"Контент: {source.get('content', 'N/A')[:500]}...\n"
        
        prompt_example = f"""
🌐 **ИНФОРМАЦИЯ О ПОГОДЕ В {data.get('city', 'ГОРОД').upper()}:**
{data.get('summary', 'N/A')}

📊 **СЫРЫЕ ДАННЫЕ ИЗ ИНТЕРНЕТА:**
{raw_content}

💡 **ИНСТРУКЦИИ:**
- Извлеки из сырых данных актуальную температуру, описание погоды, влажность, ветер
- Если данные противоречивы, укажи это
- Отвечай на русском языке
- Будь кратким, но информативным"""
        
        print(prompt_example)
        
    else:
        print(f"❌ Ошибка: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТ ЗАВЕРШЕН")
    print("💡 Теперь модель получит сырые данные и сама извлечет нужную информацию!")

if __name__ == "__main__":
    test_weather_raw() 