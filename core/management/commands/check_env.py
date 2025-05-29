from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = "Проверка переменных окружения"

    def handle(self, *args, **options):
        """Проверяет переменные окружения на наличие проблем"""
        
        self.stdout.write('🔍 Проверка переменных окружения...')
        
        # Требуемые переменные
        required_vars = [
            'DJANGO_SECRET_KEY',
            'DEBUG_MODE', 
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD',
            'DB_HOST',
            'DB_PORT',
            'ALLOWED_HOSTS',
            'LANGUAGE_CODE'
        ]
        
        # Проверяем каждую переменную
        for var in required_vars:
            value = os.getenv(var)
            if value:
                # Скрываем секретные данные
                if 'PASSWORD' in var or 'SECRET' in var:
                    display_value = '*' * len(value) if len(value) < 50 else f'*{len(value)} символов*'
                else:
                    display_value = value
                    
                self.stdout.write(self.style.SUCCESS(f'✅ {var} = {display_value}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ {var} не установлена'))
        
        # Проверяем наличие странных переменных
        self.stdout.write('\n🔍 Поиск подозрительных переменных...')
        suspicious_found = False
        
        for key, value in os.environ.items():
            # Ищем короткие случайные названия
            if len(key) <= 6 and any(char.isdigit() for char in key) and any(char.isalpha() for char in key):
                self.stdout.write(self.style.WARNING(f'⚠️ Подозрительная переменная: {key} = {value}'))
                suspicious_found = True
        
        if not suspicious_found:
            self.stdout.write(self.style.SUCCESS('✅ Подозрительных переменных не найдено'))
        
        # Показываем Django настройки
        self.stdout.write('\n📊 Django настройки:')
        self.stdout.write(f'DEBUG = {settings.DEBUG}')
        self.stdout.write(f'ALLOWED_HOSTS = {settings.ALLOWED_HOSTS}')
        self.stdout.write(f'SECRET_KEY установлен = {bool(settings.SECRET_KEY)}')
        
        self.stdout.write('\n✅ Проверка завершена!') 