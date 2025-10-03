#!/usr/bin/env python3
"""
Localtunnel Manager - Управление множественными localtunnel сервисами
"""

import json
import time
import subprocess
import requests
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import threading
import signal

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/localtunnel-manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TunnelStatus:
    """Статус туннеля"""
    name: str
    subdomain: str
    port: int
    url: str
    status: str  # 'running', 'stopped', 'error', 'checking'
    uptime: float
    last_check: float
    response_time: float
    error_count: int
    last_error: str
    enabled: bool

class LocaltunnelManager:
    """Менеджер localtunnel сервисов"""
    
    def __init__(self, config_file: str = "localtunnel-manager.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.tunnels: Dict[str, TunnelStatus] = {}
        self.running = False
        self.monitor_thread = None
        
        # Создаем директорию для логов
        os.makedirs('logs', exist_ok=True)
        
        logger.info("Localtunnel Manager инициализирован")
    
    def load_config(self) -> dict:
        """Загрузка конфигурации"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Конфигурационный файл {self.config_file} не найден")
            return {"tunnels": [], "settings": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга конфигурации: {e}")
            return {"tunnels": [], "settings": {}}
    
    def save_config(self):
        """Сохранение конфигурации"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")
    
    def start_tunnel(self, tunnel_config: dict) -> bool:
        """Запуск туннеля через PM2"""
        try:
            name = tunnel_config['name']
            subdomain = tunnel_config['subdomain']
            port = tunnel_config['port']
            
            # Создаем конфигурацию PM2 для туннеля
            pm2_config = {
                "apps": [{
                    "name": f"localtunnel-{name}",
                    "script": "lt",
                    "args": f"--port {port} --subdomain {subdomain}",
                    "instances": 1,
                    "autorestart": True,
                    "watch": False,
                    "max_memory_restart": "1G",
                    "env": {"NODE_ENV": "production"},
                    "error_file": f"./logs/localtunnel-{name}-error.log",
                    "out_file": f"./logs/localtunnel-{name}-out.log",
                    "log_file": f"./logs/localtunnel-{name}-combined.log",
                    "time": True
                }]
            }
            
            # Сохраняем конфигурацию PM2
            config_file = f"ecosystem-{name}.config.js"
            with open(config_file, 'w') as f:
                f.write(f"module.exports = {json.dumps(pm2_config, indent=2)};")
            
            # Запускаем через PM2
            result = subprocess.run(
                ['pm2', 'start', config_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Туннель {name} запущен успешно")
                return True
            else:
                logger.error(f"Ошибка запуска туннеля {name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка запуска туннеля {tunnel_config.get('name', 'unknown')}: {e}")
            return False
    
    def stop_tunnel(self, name: str) -> bool:
        """Остановка туннеля"""
        try:
            result = subprocess.run(
                ['pm2', 'stop', f'localtunnel-{name}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Туннель {name} остановлен")
                return True
            else:
                logger.error(f"Ошибка остановки туннеля {name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка остановки туннеля {name}: {e}")
            return False
    
    def restart_tunnel(self, name: str) -> bool:
        """Перезапуск туннеля"""
        try:
            result = subprocess.run(
                ['pm2', 'restart', f'localtunnel-{name}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Туннель {name} перезапущен")
                return True
            else:
                logger.error(f"Ошибка перезапуска туннеля {name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка перезапуска туннеля {name}: {e}")
            return False
    
    def get_tunnel_status(self, name: str) -> Optional[TunnelStatus]:
        """Получение статуса туннеля"""
        try:
            # Получаем статус из PM2
            result = subprocess.run(
                ['pm2', 'show', f'localtunnel-{name}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"PM2 процесс для туннеля {name} не найден")
                return None
            
            # Парсим вывод PM2
            lines = result.stdout.split('\n')
            status = "stopped"
            uptime = 0.0
            
            for line in lines:
                line_lower = line.lower().strip()
                # Поддерживаем оба формата: с : и с │
                if "status" in line_lower:
                    if "│" in line:
                        # Формат PM2 с символами │
                        parts = line.split('│')
                        if len(parts) >= 3:
                            status_value = parts[2].strip().lower()
                            if "online" in status_value:
                                status = "running"
                            elif "stopped" in status_value:
                                status = "stopped"
                            elif "error" in status_value:
                                status = "error"
                    elif ":" in line:
                        # Старый формат с :
                        status_value = line.split(':')[1].strip().lower()
                        if "online" in status_value:
                            status = "running"
                        elif "stopped" in status_value:
                            status = "stopped"
                        elif "error" in status_value:
                            status = "error"
                elif "uptime" in line_lower:
                    # Парсим uptime
                    try:
                        if "│" in line:
                            # Формат PM2 с символами │
                            parts = line.split('│')
                            if len(parts) >= 3:
                                uptime_str = parts[2].strip()
                                # Конвертируем в секунды
                                if 'd' in uptime_str:
                                    days = int(uptime_str.split('d')[0])
                                    uptime = days * 86400
                                elif 'h' in uptime_str:
                                    hours = int(uptime_str.split('h')[0])
                                    uptime = hours * 3600
                                elif 'm' in uptime_str:
                                    minutes = int(uptime_str.split('m')[0])
                                    uptime = minutes * 60
                                elif 's' in uptime_str:
                                    seconds = int(uptime_str.split('s')[0])
                                    uptime = seconds
                        elif ":" in line:
                            # Старый формат с :
                            uptime_str = line.split(':')[1].strip()
                            # Конвертируем в секунды
                            if 'd' in uptime_str:
                                days = int(uptime_str.split('d')[0])
                                uptime = days * 86400
                            elif 'h' in uptime_str:
                                hours = int(uptime_str.split('h')[0])
                                uptime = hours * 3600
                            elif 'm' in uptime_str:
                                minutes = int(uptime_str.split('m')[0])
                                uptime = minutes * 60
                            elif 's' in uptime_str:
                                seconds = int(uptime_str.split('s')[0])
                                uptime = seconds
                    except:
                        uptime = 0.0
            
            # Находим конфигурацию туннеля
            tunnel_config = None
            for tunnel in self.config['tunnels']:
                if tunnel['name'] == name:
                    tunnel_config = tunnel
                    break
            
            if not tunnel_config:
                logger.error(f"Конфигурация туннеля {name} не найдена")
                return None
            
            # Проверяем доступность туннеля только если процесс запущен
            url = f"https://{tunnel_config['subdomain']}.loca.lt"
            response_time = 0.0
            error_count = 0
            last_error = ""
            
            if status == "running":
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=10, headers={'User-Agent': 'LocaltunnelManager/1.0'})
                    response_time = time.time() - start_time
                    
                    # Считаем ошибкой только серьезные проблемы
                    if response.status_code >= 500:
                        error_count = 1
                        last_error = f"HTTP {response.status_code}"
                    elif response.status_code == 404:
                        # 404 может быть нормальным для некоторых эндпоинтов
                        error_count = 0
                        last_error = ""
                    else:
                        error_count = 0
                        last_error = ""
                        
                except requests.exceptions.Timeout:
                    error_count = 1
                    last_error = "Timeout"
                except requests.exceptions.ConnectionError:
                    error_count = 1
                    last_error = "Connection Error"
                except Exception as e:
                    error_count = 1
                    last_error = str(e)
            else:
                # Если процесс не запущен, считаем это ошибкой
                error_count = 1
                last_error = f"Process status: {status}"
            
            return TunnelStatus(
                name=name,
                subdomain=tunnel_config['subdomain'],
                port=tunnel_config['port'],
                url=url,
                status=status,
                uptime=uptime,
                last_check=time.time(),
                response_time=response_time,
                error_count=error_count,
                last_error=last_error,
                enabled=tunnel_config.get('enabled', True)
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса туннеля {name}: {e}")
            return None
    
    def update_all_statuses(self):
        """Обновление статусов всех туннелей"""
        for tunnel_config in self.config['tunnels']:
            if tunnel_config.get('enabled', True):
                name = tunnel_config['name']
                status = self.get_tunnel_status(name)
                if status:
                    self.tunnels[name] = status
    
    def health_check(self):
        """Проверка здоровья туннелей"""
        error_counts = {}  # Счетчик ошибок для каждого туннеля
        
        while self.running:
            try:
                self.update_all_statuses()
                
                # Проверяем туннели на ошибки
                for name, status in self.tunnels.items():
                    if status.error_count > 0:
                        # Увеличиваем счетчик ошибок
                        error_counts[name] = error_counts.get(name, 0) + 1
                        logger.warning(f"Туннель {name} имеет проблемы: {status.last_error} (ошибка #{error_counts[name]})")
                        
                        # Автоматический перезапуск только после 3 последовательных ошибок
                        if error_counts[name] >= 3 and self.config['settings'].get('auto_restart', True):
                            logger.info(f"Автоматический перезапуск туннеля {name} после {error_counts[name]} ошибок")
                            if self.restart_tunnel(name):
                                error_counts[name] = 0  # Сбрасываем счетчик после успешного перезапуска
                    else:
                        # Если ошибок нет, сбрасываем счетчик
                        if name in error_counts:
                            logger.info(f"Туннель {name} восстановился, сбрасываем счетчик ошибок")
                            error_counts[name] = 0
                
                # Ждем следующей проверки
                interval = self.config['settings'].get('health_check_interval', 30)
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Ошибка в health check: {e}")
                time.sleep(60)
    
    def start_monitoring(self):
        """Запуск мониторинга"""
        if self.running:
            logger.warning("Мониторинг уже запущен")
            return
        
        self.running = True
        
        # Запускаем поток мониторинга
        self.monitor_thread = threading.Thread(target=self.health_check, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Мониторинг туннелей запущен")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Мониторинг туннелей остановлен")
    
    def get_stats(self) -> dict:
        """Получение статистики"""
        total_tunnels = len(self.config['tunnels'])
        enabled_tunnels = sum(1 for t in self.config['tunnels'] if t.get('enabled', True))
        running_tunnels = sum(1 for s in self.tunnels.values() if s.status == "running")
        error_tunnels = sum(1 for s in self.tunnels.values() if s.status == "error")
        
        return {
            "total_tunnels": total_tunnels,
            "enabled_tunnels": enabled_tunnels,
            "running_tunnels": running_tunnels,
            "error_tunnels": error_tunnels,
            "monitoring_active": self.running,
            "last_update": datetime.now().isoformat()
        }
    
    def start_all_enabled(self):
        """Запуск всех включенных туннелей"""
        for tunnel_config in self.config['tunnels']:
            if tunnel_config.get('enabled', True):
                name = tunnel_config['name']
                logger.info(f"Запуск туннеля {name}")
                self.start_tunnel(tunnel_config)
    
    def stop_all(self):
        """Остановка всех туннелей"""
        for tunnel_config in self.config['tunnels']:
            name = tunnel_config['name']
            logger.info(f"Остановка туннеля {name}")
            self.stop_tunnel(name)

def main():
    """Основная функция"""
    manager = LocaltunnelManager()
    
    # Обработка сигналов для корректного завершения
    def signal_handler(signum, frame):
        logger.info("Получен сигнал завершения")
        manager.stop_monitoring()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запускаем все включенные туннели
    manager.start_all_enabled()
    
    # Запускаем мониторинг
    manager.start_monitoring()
    
    # Держим программу запущенной
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Завершение работы")
        manager.stop_monitoring()

if __name__ == "__main__":
    main() 