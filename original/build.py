# build.py
import subprocess
import sys
import os
import locale

def setup_encoding():
    """Настраивает кодировку для Windows"""
    try:
        # Пытаемся установить UTF-8
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
    except:
        # Если не получается, используем системную кодировку
        try:
            encoding = locale.getpreferredencoding()
            sys.stdout.reconfigure(encoding=encoding)
        except:
            pass

def print_msg(message):
    """Безопасный вывод сообщений"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Заменяем Unicode символы на текстовые
        safe_message = message.replace('✅', '[OK]').replace('⏳', '[WAIT]').replace('🏗️', '[BUILD]')
        safe_message = safe_message.replace('📁', '[FOLDER]').replace('🚀', '[ROCKET]').replace('🎉', '[PARTY]')
        safe_message = safe_message.replace('💡', '[TIP]').replace('❌', '[ERROR]')
        print(safe_message)

def install_dependencies():
    """Устанавливает необходимые зависимости"""
    dependencies = [
        'yt-dlp',
        'pyinstaller',
        'requests'
    ]
    
    for package in dependencies:
        try:
            __import__(package.replace('-', '_'))
            print_msg(f"✅ {package} уже установлен")
        except ImportError:
            print_msg(f"⏳ Устанавливаем {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print_msg(f"✅ {package} успешно установлен")

def build_executable():
    """Собирает EXE файл"""
    print_msg("🏗️ Собираем исполняемый файл...")
    
    # Команда для PyInstaller
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name', 'UniversalDownloader',
        '--hidden-import', 'yt_dlp',
        '--hidden-import', 'yt_dlp.extractor',
        '--hidden-import', 'yt_dlp.downloader',
        '--hidden-import', 'yt_dlp.postprocessor',
        '--collect-all', 'yt_dlp',
        'universal_downloader.py'
    ]
    
    # Добавляем иконку если существует
    if os.path.exists('icon.ico'):
        cmd.extend(['--icon', 'icon.ico'])
    
    try:
        subprocess.check_call(cmd)
        print_msg("✅ Сборка завершена успешно!")
        print_msg("📁 EXE файл находится в: dist/UniversalDownloader.exe")
        print_msg("🚀 Теперь можно распространять этот файл!")
        
    except subprocess.CalledProcessError as e:
        print_msg(f"❌ Ошибка сборки: {e}")
        return False
    except Exception as e:
        print_msg(f"❌ Неожиданная ошибка: {e}")
        return False
    
    return True

def main():
    setup_encoding()
    
    print_msg("=" * 50)
    print_msg("Universal Downloader - Автоматическая сборка")
    print_msg("=" * 50)
    
    # Устанавливаем зависимости
    install_dependencies()
    print_msg("")
    
    # Собираем EXE
    success = build_executable()
    
    print_msg("")
    if success:
        print_msg("🎉 Все готово! Ваше приложение собрано.")
        print_msg("💡 Файл UniversalDownloader.exe можно запускать на любом компьютере")
    else:
        print_msg("❌ Сборка не удалась. Проверьте ошибки выше.")

if __name__ == "__main__":
    main()
