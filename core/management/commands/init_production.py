from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import time

class Command(BaseCommand):
    help = "Инициализация системы для продакшена: оптимизация БД, прогрев кэша, настройка"

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-optimization',
            action='store_true',
            help='Пропустить оптимизацию БД',
        )
        parser.add_argument(
            '--skip-cache-warmup',
            action='store_true', 
            help='Пропустить прогрев кэша',
        )

    def handle(self, *args, **options):
        """Полная инициализация системы"""
        
        self.stdout.write(self.style.SUCCESS('🚀 Запуск инициализации продакшен системы...'))
        
        start_time = time.time()
        
        # 1. Создание миграций
        self.stdout.write('\n📝 Создание миграций...')
        try:
            call_command('makemigrations', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Миграции созданы'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Нет новых миграций: {e}'))
        
        # 2. Применение миграций
        self.stdout.write('\n📦 Применение миграций...')
        try:
            call_command('migrate', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Миграции применены'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка миграций: {e}'))
            return
        
        # 3. Сбор статических файлов
        
        self.stdout.write('\n📁 Сбор статических файлов...')
        try:
            call_command('collectstatic', '--noinput', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Статические файлы собраны'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Ошибка статических файлов: {e}'))
        
        # 4. Оптимизация БД
        if not options['skip_optimization']:
            self.stdout.write('\n🗃️ Оптимизация базы данных...')
            try:
                call_command('optimize_db', verbosity=0)
                self.stdout.write(self.style.SUCCESS('✅ БД оптимизирована'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка оптимизации БД: {e}'))
        
        # 5. Очистка кэша
        self.stdout.write('\n🗄️ Очистка кэша...')
        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS('✅ Кэш очищен'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Ошибка очистки кэша: {e}'))
        
        # 6. Прогрев кэша (если не пропускаем)
        if not options['skip_cache_warmup']:
            self.stdout.write('\n🔥 Прогрев кэша...')
            try:
                self._warmup_cache()
                self.stdout.write(self.style.SUCCESS('✅ Кэш прогрет'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️ Ошибка прогрева кэша: {e}'))
        
        # 7. Проверка производительности
        self.stdout.write('\n📈 Проверка производительности...')
        try:
            call_command('monitor_performance')
            self.stdout.write(self.style.SUCCESS('✅ Проверка завершена'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Ошибка мониторинга: {e}'))
        
        # Итоговый отчет
        total_time = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Инициализация завершена за {total_time:.2f} секунд!'
            )
        )
        self.stdout.write('Система готова к работе! 🚀')
    
    def _warmup_cache(self):
        """Прогрев кэша наиболее используемых данных"""
        
        from core.models import Student, Course, Assessment
        
        # Прогреваем кэш для первых 20 студентов
        students = Student.objects.select_related('statistic')[:20]
        for student in students:
            try:
                # Кэшируем статистику студента
                cache_key = f"student_quick_stats_{student.id}"
                if not cache.get(cache_key):
                    # Запускаем метод который создаст кэш
                    if hasattr(student, 'statistic'):
                        pass  # Статистика уже загружена
                
                # Кэшируем средний балл
                cache_key = f"student_avg_score_{student.id}"
                if not cache.get(cache_key):
                    scores = Assessment.objects.filter(
                        enrollment__student=student, 
                        is_final_grade=True
                    ).values_list('score', flat=True)
                    
                    if scores:
                        avg_score = sum(float(score) for score in scores) / len(scores)
                        cache.set(cache_key, avg_score, 600)
                        
            except Exception:
                pass  # Игнорируем ошибки прогрева
        
        # Прогреваем кэш для курсов
        courses = Course.objects.all()[:20]
        for course in courses:
            try:
                cache_key = f"course_students_{course.id}"
                if not cache.get(cache_key):
                    count = course.assessments.values('enrollment__student').distinct().count()
                    cache.set(cache_key, count, 300)
                    
                cache_key = f"course_avg_{course.id}"
                if not cache.get(cache_key):
                    final_assessments = course.assessments.filter(is_final_grade=True)
                    if final_assessments.exists():
                        avg = sum(float(a.score) for a in final_assessments) / final_assessments.count()
                        cache.set(cache_key, avg, 300)
            except Exception:
                pass