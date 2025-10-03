#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

try:
    import readchar
except ImportError:
    print("Установите readchar: pip install readchar")
    sys.exit(1)

class SimpleSSHManager:
    def __init__(self):
        # === ИЗМЕНЕНО: исправлен путь к файлу ===
        self.connections_file = Path("/home/kdp/ssh_manager/ssh_connections")
        self.connections = self.load_connections()
        self.filtered_connections = self.connections[:]  # === ДОБАВЛЕНО: отфильтрованный список ===
        self.selected_index = 0
        self.search_mode = False  # === ДОБАВЛЕНО: режим поиска ===
        self.search_term = ""     # === ДОБАВЛЕНО: строка поиска ===

    def load_connections(self):
        """Загрузка подключений из файла"""
        connections = []
        if self.connections_file.exists():
            try:
                with open(self.connections_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and line.startswith('ssh '):
                            connections.append(line)
            except FileNotFoundError:
                pass
        return connections

    def filter_connections(self, search_term):
        """=== ДОБАВЛЕНО: Фильтрация подключений по поисковому запросу ==="""
        if not search_term:
            return self.connections[:]
        
        search_term = search_term.lower()
        filtered = []
        for conn in self.connections:
            # Ищем в полной строке подключения (без 'ssh ')
            display_name = conn[4:].lower()
            if search_term in display_name:
                filtered.append(conn)
        return filtered

    def show_connections(self):
        """Показать список подключений с выбором стрелочками"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # === ДОБАВЛЕНО: заголовок с информацией о поиске ===
        title = "SSH Менеджер подключений"
        if self.search_mode:
            title += f" [Поиск: {self.search_term}]"
        elif self.search_term:
            title += f" [Найдено: {len(self.filtered_connections)}/{len(self.connections)}]"
        
        print(title)
        print("=" * 50)
        
        # === ДОБАВЛЕНО: подсказки для режима поиска ===
        if self.search_mode:
            print("Введите текст для поиска, Enter - закончить поиск")
            print("Esc - отмена поиска")
        else:
            print("↑/↓ - выбор, / - поиск, Enter - подключиться, q - выход")
        
        print("=" * 50)
        
        # === ИЗМЕНЕНО: показываем отфильтрованные подключения ===
        for i, conn in enumerate(self.filtered_connections):
            display_name = conn[4:]  # Убираем 'ssh '
            prefix = "→ " if i == self.selected_index else "  "
            print(f"{prefix}{i+1}. {display_name}")
        
        # === ДОБАВЛЕНО: сообщение если ничего не найдено ===
        if not self.filtered_connections and self.search_term:
            print("Ничего не найдено")

    def connect(self, index):
        """Подключиться к выбранному серверу"""
        # === ИЗМЕНЕНО: используем отфильтрованный список ===
        ssh_command = self.filtered_connections[index]
        print(f"\nПодключаемся: {ssh_command[4:]}")
        print("Введите пароль когда запросит:")
        print("-" * 50)
        
        try:
            command_parts = ssh_command.split()
            subprocess.run(command_parts, check=True)
        except subprocess.CalledProcessError:
            print("Ошибка подключения!")
        except KeyboardInterrupt:
            print("\nПодключение прервано.")

    def handle_search_mode(self, key):
        """=== ДОБАВЛЕНО: Обработка ввода в режиме поиска ==="""
        if key == readchar.key.ENTER or key == '\r' or key == '\n':
            # Завершаем поиск
            self.search_mode = False
            self.filtered_connections = self.filter_connections(self.search_term)
            self.selected_index = 0
        elif key == readchar.key.ESC:
            # Отменяем поиск
            self.search_mode = False
            self.search_term = ""
            self.filtered_connections = self.connections[:]
            self.selected_index = 0
        elif key == readchar.key.BACKSPACE or key == '\x7f':
            # Удаляем последний символ
            if self.search_term:
                self.search_term = self.search_term[:-1]
                self.filtered_connections = self.filter_connections(self.search_term)
                self.selected_index = 0
        elif len(key) == 1 and key.isprintable():
            # Добавляем символ к поиску
            self.search_term += key
            self.filtered_connections = self.filter_connections(self.search_term)
            self.selected_index = 0

    def handle_normal_mode(self, key):
        """=== ДОБАВЛЕНО: Обработка ввода в обычном режиме ==="""
        if key == readchar.key.UP:
            self.selected_index = (self.selected_index - 1) % len(self.filtered_connections)
        elif key == readchar.key.DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.filtered_connections)
        elif key == readchar.key.ENTER or key == '\r' or key == '\n':
            if self.filtered_connections:
                self.connect(self.selected_index)
                return True  # Завершаем работу
        elif key == '/':
            # Активируем режим поиска
            self.search_mode = True
            self.search_term = ""
        elif key.lower() == 'q':
            print("Выход")
            return True  # Завершаем работу
        return False

    def run_with_arrows(self):
        """Запуск с выбором стрелочками"""
        if not self.connections:
            print("Нет подключений в файле", self.connections_file)
            return
        
        while True:
            self.show_connections()
            key = readchar.readkey()
            
            # === ИЗМЕНЕНО: раздельная обработка режимов ===
            if self.search_mode:
                self.handle_search_mode(key)
            else:
                should_exit = self.handle_normal_mode(key)
                if should_exit:
                    break

def main():
    """Точка входа в программу"""
    manager = SimpleSSHManager()
    
    if not manager.connections:
        print(f"Файл {manager.connections_file} не найден или пуст")
        print("Создайте файл с командами вида: ssh user@server")
        sys.exit(1)
    
    manager.run_with_arrows()

if __name__ == "__main__":
    main()
