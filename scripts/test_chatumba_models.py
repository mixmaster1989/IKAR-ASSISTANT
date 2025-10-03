#!/usr/bin/env python3
"""
🧪 Тест всех доступных моделей генерации изображений в Чатумбе
- Тестирует каждую модель из конфигурации
- Генерирует кота через каждую модель
- Отправляет результаты в Telegram
- Показывает производительность каждой модели
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv

# Загрузка .env
load_dotenv(Path(__file__).resolve().parents[1] / '.env')

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Настройка логирования
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s')
logger = logging.getLogger("test_chatumba_models")

async def test_all_chatumba_models():
    """Тестирует все доступные модели в Чатумбе"""
    print("🧪 ТЕСТ ВСЕХ МОДЕЛЕЙ ГЕНЕРАЦИИ ИЗОБРАЖЕНИЙ В ЧАТУМБЕ")
    print("=" * 70)
    
    try:
        # Импортируем генератор изображений
        from vision.image_generator import HF_MODELS, generate_image_huggingface
        
        print(f"🔍 Найдено {len(HF_MODELS)} моделей в конфигурации:")
        for i, (model_id, model_info) in enumerate(HF_MODELS.items(), 1):
            print(f"   {i}. {model_id}")
            print(f"      📝 {model_info['name']}")
            print(f"      ⏱️  {model_info['average_wait_time']}")
            print()
        
        # Тестируем каждую модель
        test_prompt = "A cute red cat sitting on a windowsill, sunlight, photorealistic, 4k, high detail"
        results = []
        
        print("🚀 НАЧИНАЕМ ТЕСТИРОВАНИЕ ВСЕХ МОДЕЛЕЙ...")
        print("=" * 70)
        
        for i, (model_id, model_info) in enumerate(HF_MODELS.items(), 1):
            print(f"\n📊 ТЕСТ {i}/{len(HF_MODELS)}: {model_id}")
            print(f"   📝 {model_info['name']}")
            print(f"   🎯 Промпт: {test_prompt[:50]}...")
            
            start_time = time.time()
            
            try:
                # Генерируем изображение
                image_data = await generate_image_huggingface(
                    prompt=test_prompt,
                    model=model_id,
                    width=512,
                    height=512,
                    timeout=60
                )
                
                elapsed = time.time() - start_time
                
                if image_data:
                    # Сохраняем изображение
                    output_dir = Path(__file__).resolve().parents[1] / 'temp' / 'test_images'
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    filename = f"test_cat_{model_id.replace('/', '_')}_{int(time.time())}.jpg"
                    output_path = output_dir / filename
                    
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    
                    # Отправляем в Telegram
                    telegram_result = await send_to_telegram(image_data, f"🧪 Тест модели: {model_id}")
                    
                    result = {
                        'model_id': model_id,
                        'status': 'success',
                        'elapsed_time': elapsed,
                        'image_size': len(image_data),
                        'output_path': str(output_path),
                        'telegram_sent': telegram_result
                    }
                    
                    print(f"   ✅ УСПЕХ! Изображение сгенерировано за {elapsed:.2f}с")
                    print(f"   📁 Сохранено: {filename}")
                    print(f"   📱 Telegram: {'✅' if telegram_result else '❌'}")
                    
                else:
                    result = {
                        'model_id': model_id,
                        'status': 'failed',
                        'elapsed_time': elapsed,
                        'error': 'No image data returned'
                    }
                    print(f"   ❌ ОШИБКА: Изображение не сгенерировано")
                    
            except Exception as e:
                elapsed = time.time() - start_time
                result = {
                    'model_id': model_id,
                    'status': 'error',
                    'elapsed_time': elapsed,
                    'error': str(e)
                }
                print(f"   ❌ ИСКЛЮЧЕНИЕ: {e}")
            
            results.append(result)
            
            # Пауза между тестами
            if i < len(HF_MODELS):
                print("   ⏳ Пауза 3 секунды...")
                await asyncio.sleep(3)
        
        # Финальная статистика
        print("\n" + "=" * 70)
        print("📊 ФИНАЛЬНАЯ СТАТИСТИКА ТЕСТИРОВАНИЯ:")
        print("=" * 70)
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] != 'success']
        
        print(f"✅ Успешно: {len(successful)}/{len(results)}")
        print(f"❌ Ошибки: {len(failed)}/{len(results)}")
        
        if successful:
            print(f"\n🏆 ЛУЧШИЕ МОДЕЛИ:")
            # Сортируем по времени
            sorted_successful = sorted(successful, key=lambda x: x['elapsed_time'])
            for i, result in enumerate(sorted_successful[:3], 1):
                print(f"   {i}. {result['model_id']} - {result['elapsed_time']:.2f}с")
        
        if failed:
            print(f"\n⚠️ ПРОБЛЕМНЫЕ МОДЕЛИ:")
            for result in failed:
                print(f"   ❌ {result['model_id']}: {result.get('error', 'Unknown error')}")
        
        # Сохраняем результаты
        results_file = Path(__file__).resolve().parents[1] / 'reports' / 'chatumba_models_test_results.json'
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 Результаты сохранены в: {results_file}")
        
        return len(successful) > 0
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

async def send_to_telegram(image_data: bytes, caption: str) -> bool:
    """Отправляет изображение в Telegram для тестирования"""
    try:
        from api.telegram_core import send_telegram_photo
        
        # Получаем chat_id из переменных окружения или используем тестовый
        test_chat_id = os.environ.get("TELEGRAM_TEST_CHAT_ID", "-1002686615681")  # Группа АНТИЛОПА
        
        # Сохраняем временно
        temp_path = Path(__file__).resolve().parents[1] / 'temp' / f'temp_test_{int(time.time())}.jpg'
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_path, 'wb') as f:
            f.write(image_data)
        
        # Отправляем
        await send_telegram_photo(test_chat_id, str(temp_path), caption)
        
        # Удаляем временный файл
        temp_path.unlink(missing_ok=True)
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")
        return False

async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования всех моделей Чатумбы...")
    
    success = await test_all_chatumba_models()
    
    if success:
        print("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("   Все рабочие модели протестированы и готовы к использованию!")
    else:
        print("\n⚠️ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
        print("   Проверьте логи и настройки.")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
