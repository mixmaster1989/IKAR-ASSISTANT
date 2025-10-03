#!/usr/bin/env python3
"""
Простой HTTP прокси сервер для ElevenLabs
"""

import socket
import threading
import requests
import urllib.parse

def handle_client(client_socket, addr):
    """Обрабатывает клиентское соединение"""
    try:
        # Читаем HTTP запрос
        request = client_socket.recv(4096).decode('utf-8')
        if not request:
            return
        
        # Парсим первую строку
        lines = request.split('\n')
        first_line = lines[0]
        method, url, version = first_line.split(' ')
        
        # Парсим URL
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname
        port = parsed.port or 80
        
        print(f"🔗 Прокси: {method} {host}:{port}")
        
        # Создаем соединение к целевому серверу
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((host, port))
        
        # Отправляем запрос
        server_socket.send(request.encode('utf-8'))
        
        # Пересылаем ответ
        while True:
            data = server_socket.recv(4096)
            if not data:
                break
            client_socket.send(data)
            
    except Exception as e:
        print(f"❌ Ошибка прокси: {e}")
    finally:
        client_socket.close()

def start_proxy(port=1080):
    """Запускает прокси сервер"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', port))
    server.listen(5)
    
    print(f"🚀 HTTP прокси запущен на порту {port}")
    
    try:
        while True:
            client, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client, addr))
            thread.start()
    except KeyboardInterrupt:
        print("🛑 Прокси остановлен")
    finally:
        server.close()

if __name__ == '__main__':
    start_proxy()
