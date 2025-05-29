from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = "Очистка старых переменных окружения"

    def handle(self, *args, **options):
        """Очищает старые переменные окружения"""
        
        self.stdout.write('🧹 Очистка переменных окружения...')
        
        # Показываем все переменные с y40l5
        self.stdout.write('\n🔍 Поиск переменных с y40l5...')
        y40l5_vars = []
        for key, value in os.environ.items():
            if 'y40l5' in str(value).lower():
                y40l5_vars.append((key, value))
                self.stdout.write(f'Найдена: {key} = {value[:50]}...')
        
        if not y40l5_vars:
            self.stdout.write('✅ Переменных с y40l5 не найдено')
        
        # Список переменных для удаления
        vars_to_clean = [
            'y40l5',  # Странная переменная из старого SECRET_KEY
        ]
        
        cleaned = 0
        for var in vars_to_clean:
            if var in os.environ:
                del os.environ[var] 
                cleaned += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Удалена переменная: {var}'))
        
        if cleaned == 0:
            self.stdout.write(self.style.SUCCESS('✅ Нет переменных для очистки'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Очищено переменных: {cleaned}'))
        
        # Проверяем текущий SECRET_KEY
        secret = os.getenv('DJANGO_SECRET_KEY', '')
        if 'y40l5' in secret:
            self.stdout.write(self.style.WARNING('⚠️ В DJANGO_SECRET_KEY все еще есть y40l5!'))
            self.stdout.write(f'Текущий SECRET_KEY: {secret[:20]}...{secret[-10:]}')
            self.stdout.write('Нужно обновить секрет в GitHub Secrets')
        else:
            self.stdout.write(self.style.SUCCESS('✅ DJANGO_SECRET_KEY чистый')) 