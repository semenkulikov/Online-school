from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
from django.test import Client
import time
import json

class Command(BaseCommand):
    help = "Мониторинг производительности системы"

    def handle(self, *args, **options):
        """Проверяет производительность основных страниц"""
        
        self.stdout.write('🔍 Запуск мониторинга производительности...\n')
        
        # Тестируемые URL
        urls = [
            '/admin/',
            '/admin/core/student/',
            '/admin/core/course/',
            '/admin/core/assessment/',
            '/admin/core/certificate/',
        ]
        
        client = Client()
        results = {}
        
        for url in urls:
            self.stdout.write(f'Тестирую {url}...')
            
            # Замеряем время
            start_time = time.time()
            
            # Подсчет SQL запросов
            queries_before = len(connection.queries)
            
            try:
                response = client.get(url)
                end_time = time.time()
                
                queries_after = len(connection.queries)
                query_count = queries_after - queries_before
                response_time = end_time - start_time
                
                results[url] = {
                    'status': response.status_code,
                    'time': response_time,
                    'queries': query_count,
                    'size': len(response.content) if hasattr(response, 'content') else 0
                }
                
                # Цветная индикация
                if response_time < 0.1:
                    time_color = self.style.SUCCESS
                elif response_time < 0.5:
                    time_color = self.style.WARNING
                else:
                    time_color = self.style.ERROR
                
                self.stdout.write(
                    f'  ✅ {response.status_code} | '
                    f'{time_color(f"{response_time:.3f}s")} | '
                    f'SQL: {query_count} | '
                    f'Размер: {len(response.content) if hasattr(response, "content") else 0} bytes'
                )
                
            except Exception as e:
                results[url] = {
                    'error': str(e),
                    'time': 0,
                    'queries': 0
                }
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Ошибка: {e}')
                )
        
        # Проверка кэша
        self.stdout.write('\n🗄️  Проверка кэша...')
        cache_test_key = 'performance_test'
        cache.set(cache_test_key, 'test_value', 10)
        cache_value = cache.get(cache_test_key)
        
        if cache_value == 'test_value':
            self.stdout.write(self.style.SUCCESS('  ✅ Кэш работает'))
        else:
            self.stdout.write(self.style.ERROR('  ❌ Кэш не работает'))
        
        # Проверка базы данных
        self.stdout.write('\n🗃️  Проверка базы данных...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM core_student;")
                student_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM core_assessment;")
                assessment_count = cursor.fetchone()[0]
                
                self.stdout.write(
                    f'  📊 Студентов: {student_count} | Оценок: {assessment_count}'
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Ошибка БД: {e}')
            )
        
        # Итоговый отчет
        self.stdout.write('\n📈 Сводка производительности:')
        total_time = sum(r.get('time', 0) for r in results.values() if 'error' not in r)
        total_queries = sum(r.get('queries', 0) for r in results.values() if 'error' not in r)
        
        self.stdout.write(f'  Общее время: {total_time:.3f}s')
        self.stdout.write(f'  Общее количество SQL запросов: {total_queries}')
        self.stdout.write(f'  Среднее время на страницу: {total_time/len(urls):.3f}s')
        
        if total_time < 1.0:
            self.stdout.write(self.style.SUCCESS('🚀 Производительность отличная!'))
        elif total_time < 3.0:
            self.stdout.write(self.style.WARNING('⚠️  Производительность приемлемая'))
        else:
            self.stdout.write(self.style.ERROR('🐌 Требуется оптимизация!')) 