from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Создание таблицы для кэширования в базе данных"

    def handle(self, *args, **options):
        """Создает таблицу cache_table для кэширования"""
        try:
            call_command('createcachetable', verbosity=2)
            self.stdout.write(
                self.style.SUCCESS('✅ Таблица кэша успешно создана!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка создания таблицы кэша: {e}')
            ) 