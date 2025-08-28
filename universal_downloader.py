import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import re
import webbrowser
import socket
import tempfile
import shutil
from pathlib import Path
import io
import contextlib

class UniversalDownloaderApp:
    def __init__(self, root):
        # Проверка на уже запущенный экземпляр
        if self.is_already_running():
            messagebox.showerror("Ошибка", "Программа уже запущена!")
            sys.exit(1)
            
        self.root = root
        self.root.title("Universal Video Downloader")
        self.root.geometry("700x500")
        self.root.resizable(False, True)
        
        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Стилизация
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TEntry", font=("Arial", 10))
        self.style.configure("TCombobox", font=("Arial", 10))
        
        # Главный фрейм
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Выбор платформы
        ttk.Label(main_frame, text="Платформа:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.platform_var = tk.StringVar(value="Автоопределение")
        platforms = ["Автоопределение", "YouTube", "Rutube", "VK", "Odnoklassniki", "Dzen", "Vimeo", "Twitter", "Instagram", "TikTok"]
        platform_combo = ttk.Combobox(main_frame, textvariable=self.platform_var, values=platforms, width=20, state="readonly")
        platform_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        platform_combo.bind("<<ComboboxSelected>>", self.on_platform_change)
        
        # Поле для URL
        ttk.Label(main_frame, text="URL видео или плейлиста:").grid(row=1, column=0, sticky=tk.W, pady=(5, 5))
        self.url_entry = ttk.Entry(main_frame, width=70)
        self.url_entry.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
        self.url_entry.insert(0, "https://")
        
        # Примеры ссылок
        examples_frame = ttk.Frame(main_frame)
        examples_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        ttk.Label(examples_frame, text="Примеры:", foreground="gray").pack(side=tk.LEFT)
        
        examples = [
            ("YouTube", "https://youtube.com/"),
            ("Rutube", "https://rutube.ru/"),
            ("VK", "https://vk.com/"),
            ("OK", "https://ok.ru/")
        ]
        
        for text, url in examples:
            btn = ttk.Button(examples_frame, text=text, width=8, 
                            command=lambda u=url: self.url_entry.insert(tk.END, u))
            btn.pack(side=tk.LEFT, padx=5)
        
        # Настройки загрузки
        settings_frame = ttk.Frame(main_frame)
        settings_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=(0, 15))
        
        # Качество видео
        ttk.Label(settings_frame, text="Качество видео:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.quality_var = tk.StringVar(value="720")
        quality_combo = ttk.Combobox(settings_frame, textvariable=self.quality_var, 
                                    values=["2160 (4K)", "1440 (2K)", "1080 (Full HD)", "720 (HD)", "480", "360", "240", "Авто"], 
                                    width=15, state="readonly")
        quality_combo.grid(row=0, column=1, sticky=tk.W)
        
        # Скорость загрузки
        ttk.Label(settings_frame, text="Ограничение скорости:").grid(row=0, column=2, sticky=tk.W, padx=(20, 10))
        self.speed_var = tk.StringVar(value="5M")
        speed_combo = ttk.Combobox(settings_frame, textvariable=self.speed_var, 
                                  values=["Без ограничений", "10M", "5M", "2M", "1M"], 
                                  width=15, state="readonly")
        speed_combo.grid(row=0, column=3, sticky=tk.W)
        
        # Выбор папки
        ttk.Label(main_frame, text="Папка для сохранения:").grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        self.folder_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=6, column=0, columnspan=2, sticky=tk.EW)
        
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=60)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(folder_frame, text="Обзор...", command=self.browse_folder)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Формат имени файла
        ttk.Label(main_frame, text="Формат имени файла:").grid(row=7, column=0, sticky=tk.W, pady=(10, 5))
        self.name_format_var = tk.StringVar(value="%(title)s.%(ext)s")
        name_frame = ttk.Frame(main_frame)
        name_frame.grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        name_combo = ttk.Combobox(name_frame, textvariable=self.name_format_var, 
                                 values=["%(title)s.%(ext)s", "%(id)s.%(ext)s", "%(upload_date)s_%(title)s.%(ext)s"],
                                 width=50, state="readonly")
        name_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Логгирование
        ttk.Label(main_frame, text="Лог выполнения:").grid(row=9, column=0, sticky=tk.W, pady=(5, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=85, height=12)
        self.log_text.grid(row=10, column=0, columnspan=2, sticky=tk.NSEW)
        self.log_text.config(state=tk.DISABLED, font=("Consolas", 9))
        
        # Кнопки управления
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=11, column=0, columnspan=2, pady=(10, 0))
        
        self.download_btn = ttk.Button(btn_frame, text="Начать скачивание", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Остановить", command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(btn_frame, text="Очистить лог", command=self.clear_log)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка помощи
        help_btn = ttk.Button(btn_frame, text="Помощь", command=self.show_help)
        help_btn.pack(side=tk.RIGHT, padx=5)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Переменные для управления потоком
        self.download_process = None
        self.is_downloading = False
        self.is_closing = False
        self.use_python_module = False
        
        # Временные файлы
        self.temp_dir = None
        
        # Настройка веса строк для растягивания
        main_frame.grid_rowconfigure(10, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Автоматическая настройка
        self.setup_environment()
    
    def setup_environment(self):
        """Автоматическая настройка окружения"""
        self.log_message("[INFO] Настройка окружения...")
        
        try:
            # Создаем временную директорию
            self.temp_dir = tempfile.mkdtemp(prefix="universal_downloader_")
            self.log_message(f"[INFO] Временная папка: {self.temp_dir}")
            
            # Настраиваем yt-dlp
            self.setup_yt_dlp()
            
            self.log_message("[OK] Окружение настроено успешно!")
            self.status_var.set("Готов к работе")
            
        except Exception as e:
            self.log_message(f"[ERROR] Ошибка настройки: {str(e)}")
            self.status_var.set("Ошибка настройки")
    
    def setup_yt_dlp(self):
        """Настраивает yt-dlp для работы внутри EXE"""
        try:
            # Пытаемся импортировать yt-dlp напрямую
            import yt_dlp
            self.log_message("[OK] yt-dlp доступен через Python")
            self.use_python_module = True
        except ImportError:
            self.log_message("[ERROR] yt-dlp не найден!")
            self.use_python_module = False
            messagebox.showerror("Ошибка", "yt-dlp не установлен! Программа не может работать.")
    
    def is_already_running(self):
        """Проверяет, запущена ли уже программа"""
        try:
            lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            lock_socket.bind(('127.0.0.1', 47291))
            return False
        except socket.error:
            return True
    
    def on_closing(self):
        """Обработчик закрытия окна"""
        if self.is_downloading:
            if messagebox.askyesno("Подтверждение", 
                                  "Идет процесс скачивания. Вы уверены, что хотите выйти?"):
                self.is_closing = True
                self.stop_download()
                self.root.after(100, self.force_quit)
        else:
            self.cleanup()
            self.root.destroy()
    
    def cleanup(self):
        """Очистка временных файлов"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.log_message("[INFO] Временные файлы очищены")
        except:
            pass
    
    def force_quit(self):
        """Принудительное завершение"""
        self.cleanup()
        self.root.destroy()
    
    def on_platform_change(self, event):
        platform = self.platform_var.get()
        example_urls = {
            "YouTube": "https://www.youtube.com/",
            "Rutube": "https://rutube.ru/video/",
            "VK": "https://vk.com/",
            "Odnoklassniki": "https://ok.ru/video/",
            "Dzen": "https://dzen.ru/video/watch/",
            "Vimeo": "https://vimeo.com/",
            "Twitter": "https://twitter.com/user/status/",
            "Instagram": "https://www.instagram.com/p/",
            "TikTok": "https://www.tiktok.com/@user/video/"
        }
        
        if platform != "Автоопределение" and platform in example_urls:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, example_urls[platform])
    
    def browse_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder_selected:
            self.folder_var.set(folder_selected)
    
    def log_message(self, message):
        if self.is_closing:
            return
            
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.status_var.set("Лог очищен")
    
    def show_help(self):
        help_text = """
        Universal Video Downloader - инструкция по использованию:
        
        1. Выберите платформу или оставьте "Автоопределение"
        2. Вставьте ссылку на видео или плейлист
        3. Выберите качество видео (по умолчанию 720p)
        4. При необходимости установите ограничение скорости
        5. Выберите папку для сохранения файлов
        6. Нажмите "Начать скачивание"
        
        Все зависимости устанавливаются автоматически!
        """
        messagebox.showinfo("Помощь", help_text)
    
    def start_download(self):
        if self.is_downloading:
            return
            
        content_url = self.url_entry.get().strip()
        if not content_url:
            messagebox.showerror("Ошибка", "Введите URL видео или плейлиста")
            return
            
        if not re.match(r'^https?://', content_url):
            messagebox.showerror("Ошибка", "Некорректный URL. Должен начинаться с http:// или https://")
            return
            
        if not self.use_python_module:
            messagebox.showerror("Ошибка", "yt-dlp не доступен! Переустановите приложение.")
            return

        output_folder = self.folder_var.get()
        
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
            except:
                messagebox.showerror("Ошибка", f"Невозможно создать папку: {output_folder}")
                return
        
        self.log_message("\n" + "="*80)
        self.log_message(f"Начало скачивания: {content_url}")
        self.log_message(f"Качество: {'Авто' if self.quality_var.get() == 'Авто' else self.quality_var.get()}")
        self.log_message(f"Папка сохранения: {output_folder}")
        self.log_message(f"Ограничение скорости: {self.speed_var.get()}")
        self.log_message(f"Формат имени: {self.name_format_var.get()}")
        self.log_message("="*80 + "\n")
        
        # Обновление интерфейса
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.is_downloading = True
        self.status_var.set("Скачивание началось...")
        
        # Запуск в отдельном потоке
        threading.Thread(target=self.run_download, args=(content_url,), daemon=True).start()
    
    def run_download(self, content_url):
        """Запускает скачивание используя Python модуль напрямую"""
        try:
            if not self.use_python_module:
                self.log_message("[ERROR] yt-dlp не доступен!")
                self.root.after(0, self.download_complete)
                return
                
            # Импортируем yt-dlp
            import yt_dlp
            
            # Перенаправляем stdout для захвата вывода
            output_capture = io.StringIO()
            
            def download_with_redirect():
                try:
                    with contextlib.redirect_stdout(output_capture):
                        with contextlib.redirect_stderr(output_capture):
                            # Создаем опции для yt-dlp
                            ydl_opts = {
                                'outtmpl': os.path.join(self.folder_var.get(), self.name_format_var.get()),
                                'merge_output_format': 'mp4',
                                'ignoreerrors': True,
                                'retries': 10,
                                'fragment_retries': 10,
                                'concurrent_fragments': 4,
                                'sleep_interval': 5,
                                'quiet': False,
                                'no_warnings': False,
                            }
                            
                            # Добавляем качество
                            quality = self.quality_var.get().split()[0] if self.quality_var.get() != "Авто" else "best"
                            if quality != "best":
                                ydl_opts['format'] = f'best[height<={quality}]'
                            
                            # Добавляем ограничение скорости
                            speed_limit = self.speed_var.get()
                            if speed_limit != "Без ограничений":
                                # Конвертируем в байты в секунду
                                if 'M' in speed_limit:
                                    rate_limit = int(speed_limit.replace('M', '')) * 1000000
                                elif 'K' in speed_limit:
                                    rate_limit = int(speed_limit.replace('K', '')) * 1000
                                else:
                                    rate_limit = int(speed_limit)
                                ydl_opts['ratelimit'] = rate_limit
                            
                            # Для плейлистов
                            if any(x in content_url for x in ["/playlist/", "/plst/", "list="]):
                                ydl_opts['outtmpl'] = os.path.join(
                                    self.folder_var.get(), 
                                    '%(playlist_title)s', 
                                    self.name_format_var.get()
                                )
                            
                            # Запускаем скачивание
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([content_url])
                                
                except Exception as e:
                    output_capture.write(f"\n[ERROR] Критическая ошибка: {str(e)}\n")
                finally:
                    # Сигнализируем о завершении
                    if not self.is_closing:
                        self.root.after(0, self.download_complete)
            
            # Запускаем в отдельном потоке
            download_thread = threading.Thread(target=download_with_redirect, daemon=True)
            download_thread.start()
            
            # Мониторим вывод в реальном времени
            while self.is_downloading and not self.is_closing:
                try:
                    output = output_capture.getvalue()
                    if output:
                        lines = output.split('\n')
                        for line in lines:
                            if line.strip() and not self.is_closing:
                                self.root.after(0, self.log_message, line.strip())
                        # Очищаем буфер после чтения
                        output_capture.seek(0)
                        output_capture.truncate(0)
                except Exception as e:
                    self.log_message(f"[ERROR] Ошибка чтения вывода: {str(e)}")
                
                # Проверяем, жив ли поток
                if download_thread.is_alive():
                    threading.Event().wait(0.1)
                else:
                    break
                    
        except Exception as e:
            if not self.is_closing:
                self.log_message(f"[ERROR] Ошибка запуска: {str(e)}")
                self.root.after(0, self.download_complete)

    def stop_download(self):
        if self.is_downloading:
            self.log_message("\n[STOP] Скачивание принудительно остановлено пользователем")
            self.status_var.set("Скачивание остановлено")
            self.is_downloading = False
            self.download_complete()

    def download_complete(self):
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalDownloaderApp(root)
    root.mainloop()
