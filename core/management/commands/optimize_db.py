from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger('core')


class Command(BaseCommand):
    help = "Оптимизация базы данных и создание индексов для повышения производительности"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Очистить кэш',
        )

    def handle(self, *args, **options):
        """Оптимизирует базу данных"""
        
        if options['clear_cache']:
            self.clear_cache()
        
        self.create_indexes()
        self.analyze_database()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Оптимизация базы данных завершена!')
        )

    def clear_cache(self):
        """Очищает кэш"""
        try:
            cache.clear()
            self.stdout.write('🗑️  Кэш очищен')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка очистки кэша: {e}')
            )

    def create_indexes(self):
        """Создает индексы для оптимизации запросов"""
        indexes = [
            # Индексы для студентов
            "CREATE INDEX IF NOT EXISTS idx_student_status ON core_student(status);",
            "CREATE INDEX IF NOT EXISTS idx_student_email ON core_student(email);",
            
            # Индексы для зачислений
            "CREATE INDEX IF NOT EXISTS idx_enrollment_student_session ON core_enrollment(student_id, session_id);",
            "CREATE INDEX IF NOT EXISTS idx_enrollment_status ON core_enrollment(status);",
            
            # Индексы для оценок
            "CREATE INDEX IF NOT EXISTS idx_assessment_enrollment ON core_assessment(enrollment_id);",
            "CREATE INDEX IF NOT EXISTS idx_assessment_course ON core_assessment(course_id);",
            "CREATE INDEX IF NOT EXISTS idx_assessment_final_grade ON core_assessment(is_final_grade);",
            "CREATE INDEX IF NOT EXISTS idx_assessment_date ON core_assessment(date);",
            
            # Индексы для сертификатов
            "CREATE INDEX IF NOT EXISTS idx_certificate_student ON core_certificate(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_certificate_course ON core_certificate(course_id);",
            "CREATE INDEX IF NOT EXISTS idx_certificate_type ON core_certificate(type);",
            
            # Индексы для посещаемости
            "CREATE INDEX IF NOT EXISTS idx_attendance_enrollment ON core_attendance(enrollment_id);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_session ON core_attendance(session_id);",
            
            # Индексы для курсов
            "CREATE INDEX IF NOT EXISTS idx_course_session ON core_course(session_id);",
            
            # Составные индексы для частых запросов
            "CREATE INDEX IF NOT EXISTS idx_assessment_enrollment_final ON core_assessment(enrollment_id, is_final_grade);",
            "CREATE INDEX IF NOT EXISTS idx_certificate_student_course ON core_certificate(student_id, course_id);",
        ]
        
        with connection.cursor() as cursor:
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    index_name = index_sql.split()[5]  # Извлекаем имя индекса
                    self.stdout.write(f'📈 Создан индекс: {index_name}')
                except Exception as e:
                    logger.warning(f"Ошибка создания индекса: {e}")

    def analyze_database(self):
        """Анализирует статистику базы данных"""
        with connection.cursor() as cursor:
            try:
                # PostgreSQL ANALYZE для обновления статистики
                cursor.execute("ANALYZE;")
                self.stdout.write('📊 Статистика базы данных обновлена')
                
                # Получаем размеры таблиц
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10;
                """)
                
                results = cursor.fetchall()
                self.stdout.write('\n📏 Размеры таблиц:')
                for schema, table, size in results:
                    self.stdout.write(f'  {table}: {size}')
                    
            except Exception as e:
                logger.warning(f"Ошибка анализа базы данных: {e}")
                self.stdout.write(
                    self.style.WARNING('⚠️  Не удалось проанализировать базу данных')
                ) 