import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import re
import webbrowser

class UniversalDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Video Downloader")
        # Фиксированная ширина, растягиваемость по вертикали
        self.root.geometry("700x500")
        self.root.resizable(False, True)
        
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
        
        # Кнопки примеров для разных платформ
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
        
        # Настройка веса строк для растягивания
        main_frame.grid_rowconfigure(10, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Проверка зависимостей
        self.check_dependencies()
        
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
        
        Поддерживаемые платформы:
        - YouTube
        - Rutube
        - VK (ВКонтакте)
        - Odnoklassniki (Одноклассники)
        - Dzen (Дзен)
        - Vimeo
        - Twitter
        - Instagram
        - TikTok
        - И многие другие через автоопределение
        
        Советы:
        - Для плейлистов создается подпапка с названием плейлиста
        - Используйте кнопки примеров для быстрой вставки ссылок
        - Формат имени файла можно изменить в выпадающем списке
        
        Требования:
        - Установленный Python 3.6+
        - Установленные yt-dlp и ffmpeg
        - Интернет-соединение
        """
        messagebox.showinfo("Помощь", help_text)
    
    def check_dependencies(self):
        self.log_message("Проверка зависимостей...")
        
        # Проверка yt-dlp
        try:
            result = subprocess.run(["yt-dlp", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.log_message(f"✅ yt-dlp установлен (версия: {result.stdout.strip()})")
        except:
            self.log_message("❌ yt-dlp не найден! Попытка установки...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], check=True)
                self.log_message("✅ yt-dlp успешно установлен!")
            except:
                self.log_message("❌ Ошибка установки yt-dlp. Установите вручную: pip install yt-dlp")
        
        # Проверка ffmpeg
        try:
            result = subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # Получаем первую строку вывода для отображения версии
            first_line = result.stdout.split('\n')[0] if result.stdout else "unknown version"
            self.log_message(f"✅ ffmpeg установлен ({first_line})")
        except:
            self.log_message("❌ ffmpeg не найден! Установите вручную:")
            self.log_message("1. Скачайте: https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z")
            self.log_message("2. Распакуйте в C:\\ffmpeg")
            self.log_message("3. Добавьте C:\\ffmpeg\\bin в переменную PATH")
            self.log_message("4. Перезапустите программу")
        
        self.log_message("\nПроверка завершена. Введите параметры и нажмите 'Начать скачивание'")
    
    def start_download(self):
        if self.is_downloading:
            return
            
        content_url = self.url_entry.get().strip()
        if not content_url:
            messagebox.showerror("Ошибка", "Введите URL видео или плейлиста")
            return
            
        # Общая проверка URL (любой HTTP/HTTPS)
        if not re.match(r'^https?://', content_url):
            messagebox.showerror("Ошибка", "Некорректный URL. Должен начинаться с http:// или https://")
            return
            
        quality = self.quality_var.get().split()[0] if self.quality_var.get() != "Авто" else "best"
        speed_limit = self.speed_var.get()
        output_folder = self.folder_var.get()
        name_format = self.name_format_var.get()
        
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
            except:
                messagebox.showerror("Ошибка", f"Невозможно создать папку: {output_folder}")
                return
        
        # Формирование команды
        command = [
            "yt-dlp",
            "--merge-output-format", "mp4",
            "--hls-prefer-ffmpeg",
            "--postprocessor-args", "ffmpeg:-c copy -movflags +faststart",
            "--ignore-errors",
            "--retries", "10",
            "--fragment-retries", "10",
            "--concurrent-fragments", "4",
            "--sleep-interval", "5",
            "-o", os.path.join(output_folder, name_format),
            content_url
        ]
        
        # Добавляем качество, если не авто
        if quality != "best":
            command.insert(1, "-f")
            command.insert(2, f"best[height<={quality}]")
        
        # Добавляем ограничение скорости, если выбрано
        if speed_limit != "Без ограничений":
            command.insert(1, "--limit-rate")
            command.insert(2, speed_limit)
        
        # Для плейлистов создаем подпапку
        if any(x in content_url for x in ["/playlist/", "/plst/", "list="]):
            command.insert(1, "-o")
            command.insert(2, os.path.join(output_folder, "%(playlist_title)s", name_format))
        
        # Специфичные настройки для разных платформ
        platform = self.platform_var.get()
        if platform != "Автоопределение":
            if platform == "Instagram":
                command.insert(1, "--cookies")
                command.insert(2, "cookies.txt")  # Instagram часто требует cookies
                self.log_message("⚠ Для Instagram могут потребоваться cookies в файле cookies.txt")
        
        self.log_message("\n" + "="*80)
        self.log_message(f"Начало скачивания: {content_url}")
        self.log_message(f"Платформа: {platform}")
        self.log_message(f"Качество: {'Авто' if quality == 'best' else f'до {quality}p'}")
        self.log_message(f"Папка сохранения: {output_folder}")
        self.log_message(f"Ограничение скорости: {speed_limit if speed_limit != 'Без ограничений' else 'Нет'}")
        self.log_message(f"Формат имени: {name_format}")
        self.log_message("Команда: " + " ".join(command))
        self.log_message("="*80 + "\n")
        
        # Обновление интерфейса
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.is_downloading = True
        self.status_var.set("Скачивание началось...")
        
        # Запуск в отдельном потоке
        threading.Thread(target=self.run_download, args=(command,), daemon=True).start()
    
    def run_download(self, command):
        try:
            self.download_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # Чтение вывода в реальном времени
            for line in self.download_process.stdout:
                self.root.after(0, self.log_message, line.strip())
                
            self.download_process.wait()
            
            if self.download_process.returncode == 0:
                self.root.after(0, self.log_message, "\n✅ Скачивание успешно завершено!")
                self.root.after(0, self.status_var.set, "Скачивание завершено успешно")
            else:
                self.root.after(0, self.log_message, f"\n❌ Ошибка скачивания (код: {self.download_process.returncode})")
                self.root.after(0, self.status_var.set, "Ошибка скачивания")
                
        except Exception as e:
            self.root.after(0, self.log_message, f"\n❌ Критическая ошибка: {str(e)}")
            self.root.after(0, self.status_var.set, "Критическая ошибка")
            
        finally:
            self.root.after(0, self.download_complete)
    
    def stop_download(self):
        if self.is_downloading and self.download_process:
            self.download_process.terminate()
            self.log_message("\n⛔ Скачивание принудительно остановлено пользователем")
            self.status_var.set("Скачивание остановлено")
            self.download_complete()
    
    def download_complete(self):
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.download_process = None

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalDownloaderApp(root)
    root.mainloop()
