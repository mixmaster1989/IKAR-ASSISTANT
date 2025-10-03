"""
Модуль для управления рабочими прокси
Содержит проверенные прокси, которые работают с различными API
"""

import random
import logging
from typing import List, Dict, Optional, Tuple
import requests
import asyncio
import aiohttp

logger = logging.getLogger("chatumba.proxy_manager")

class ProxyManager:
    """
    Менеджер для работы с проверенными прокси
    """
    
    def __init__(self):
        """Инициализирует менеджер прокси"""
        
        # HTTP прокси (работают с большинством API)
        self.http_proxies = [
            "http://43.156.66.39:8080",      # Сингапур - ЛУЧШИЙ
            "http://65.21.34.102:80",        # Финляндия
            "http://103.156.75.213:8787",    # Индонезия
            "http://109.135.16.145:8789",    # Бельгия
            "http://47.89.184.18:3128",      # США
        ]
        
        # SOCKS4 прокси (работают с Google AI API)
        self.socks4_proxies = [
            "socks4://192.252.208.70:14282",  # США - САМЫЙ БЫСТРЫЙ
            "socks4://198.8.84.3:4145",       # Канада
            "socks4://72.211.46.124:4145",    # США
            "socks4://199.116.112.6:4145",    # США
            "socks4://67.201.59.70:4145",     # США
        ]
        
        # SOCKS5 прокси (если понадобятся)
        self.socks5_proxies = [
            "socks5://128.199.202.122:1080",  # Сингапур
        ]
        
        # Статистика использования
        self.usage_stats = {
            "http": {proxy: {"success": 0, "failures": 0} for proxy in self.http_proxies},
            "socks4": {proxy: {"success": 0, "failures": 0} for proxy in self.socks4_proxies},
            "socks5": {proxy: {"success": 0, "failures": 0} for proxy in self.socks5_proxies},
        }
    
    def get_random_http_proxy(self) -> str:
        """Возвращает случайный HTTP прокси"""
        return random.choice(self.http_proxies)
    
    def get_random_socks4_proxy(self) -> str:
        """Возвращает случайный SOCKS4 прокси"""
        return random.choice(self.socks4_proxies)
    
    def get_best_http_proxy(self) -> str:
        """Возвращает лучший HTTP прокси (Сингапур)"""
        return "http://43.156.66.39:8080"
    
    def get_best_socks4_proxy(self) -> str:
        """Возвращает лучший SOCKS4 прокси (США)"""
        return "socks4://192.252.208.70:14282"
    
    def get_proxies_for_requests(self, proxy_type: str = "http") -> Dict[str, str]:
        """
        Возвращает прокси в формате для requests
        
        Args:
            proxy_type: "http", "socks4", "socks5"
            
        Returns:
            Dict с прокси для requests
        """
        if proxy_type == "http":
            proxy = self.get_best_http_proxy()
        elif proxy_type == "socks4":
            proxy = self.get_best_socks4_proxy()
        elif proxy_type == "socks5":
            proxy = self.socks5_proxies[0] if self.socks5_proxies else self.get_best_http_proxy()
        else:
            proxy = self.get_best_http_proxy()
        
        return {
            "http": proxy,
            "https": proxy
        }
    
    def get_proxy_for_aiohttp(self, proxy_type: str = "http") -> str:
        """
        Возвращает прокси для aiohttp
        
        Args:
            proxy_type: "http", "socks4", "socks5"
            
        Returns:
            Строка с прокси для aiohttp
        """
        if proxy_type == "http":
            return self.get_best_http_proxy()
        elif proxy_type == "socks4":
            return self.get_best_socks4_proxy()
        elif proxy_type == "socks5":
            return self.socks5_proxies[0] if self.socks5_proxies else self.get_best_http_proxy()
        else:
            return self.get_best_http_proxy()
    
    async def test_proxy_async(self, proxy: str, test_url: str = "http://httpbin.org/ip") -> bool:
        """
        Тестирует прокси асинхронно
        
        Args:
            proxy: URL прокси
            test_url: URL для тестирования
            
        Returns:
            True если прокси работает
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Прокси {proxy} работает")
                        return True
                    else:
                        logger.warning(f"⚠️ Прокси {proxy} вернул статус {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Прокси {proxy} не работает: {e}")
            return False
    
    def test_proxy_sync(self, proxy: str, test_url: str = "http://httpbin.org/ip") -> bool:
        """
        Тестирует прокси синхронно
        
        Args:
            proxy: URL прокси
            test_url: URL для тестирования
            
        Returns:
            True если прокси работает
        """
        try:
            proxies = {"http": proxy, "https": proxy}
            response = requests.get(test_url, proxies=proxies, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ Прокси {proxy} работает")
                return True
            else:
                logger.warning(f"⚠️ Прокси {proxy} вернул статус {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Прокси {proxy} не работает: {e}")
            return False
    
    async def test_all_proxies(self) -> Dict[str, List[str]]:
        """
        Тестирует все прокси
        
        Returns:
            Dict с рабочими прокси по типам
        """
        working_proxies = {
            "http": [],
            "socks4": [],
            "socks5": []
        }
        
        # Тестируем HTTP прокси
        logger.info("🔍 Тестируем HTTP прокси...")
        for proxy in self.http_proxies:
            if await self.test_proxy_async(proxy):
                working_proxies["http"].append(proxy)
        
        # Тестируем SOCKS4 прокси
        logger.info("🔍 Тестируем SOCKS4 прокси...")
        for proxy in self.socks4_proxies:
            if await self.test_proxy_async(proxy):
                working_proxies["socks4"].append(proxy)
        
        # Тестируем SOCKS5 прокси
        logger.info("🔍 Тестируем SOCKS5 прокси...")
        for proxy in self.socks5_proxies:
            if await self.test_proxy_async(proxy):
                working_proxies["socks5"].append(proxy)
        
        return working_proxies
    
    def get_stats(self) -> Dict[str, Dict[str, Dict[str, int]]]:
        """Возвращает статистику использования прокси"""
        return self.usage_stats
    
    def record_success(self, proxy: str, proxy_type: str):
        """Записывает успешное использование прокси"""
        if proxy_type in self.usage_stats and proxy in self.usage_stats[proxy_type]:
            self.usage_stats[proxy_type][proxy]["success"] += 1
    
    def record_failure(self, proxy: str, proxy_type: str):
        """Записывает неудачное использование прокси"""
        if proxy_type in self.usage_stats and proxy in self.usage_stats[proxy_type]:
            self.usage_stats[proxy_type][proxy]["failures"] += 1

# Глобальный экземпляр менеджера прокси
proxy_manager = ProxyManager()

def get_proxy_manager() -> ProxyManager:
    """Возвращает глобальный экземпляр менеджера прокси"""
    return proxy_manager
