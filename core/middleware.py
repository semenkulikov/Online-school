import time
import logging
from django.conf import settings
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger('core')


class PerformanceMiddleware:
    """Мидлвар для мониторинга производительности"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Начало запроса
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        response = self.get_response(request)
        
        # Конец запроса
        end_time = time.time()
        response_time = end_time - start_time
        
        # Количество SQL запросов
        sql_queries_count = len(connection.queries) - initial_queries
        
        # Логируем медленные запросы
        if response_time > 2.0:  # Если запрос дольше 2 секунд
            logger.warning(
                f"Slow request: {request.path} - {response_time:.2f}s, "
                f"{sql_queries_count} SQL queries"
            )
            
            # Логируем детали SQL запросов для медленных страниц
            if settings.DEBUG and sql_queries_count > 20:
                for query in connection.queries[-sql_queries_count:]:
                    logger.debug(f"SQL: {query['sql'][:200]}... ({query['time']}s)")
        
        # Добавляем заголовки производительности
        response['X-Response-Time'] = f"{response_time:.3f}s"
        response['X-SQL-Queries'] = str(sql_queries_count)
        
        return response


class LogIPMiddleware:
    """Мидлвар для логирования IP адресов"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Получаем IP адрес
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Кэшируем информацию о IP на 1 час
        cache_key = f"ip_logged_{ip}"
        if not cache.get(cache_key):
            logger.info(f"Request from IP: {ip} to {request.path}")
            cache.set(cache_key, True, 3600)
        
        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware:
    """Мидлвар для добавления заголовков безопасности"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Добавляем заголовки безопасности
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CSP для админки
        if request.path.startswith('/admin/'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self';"
            )
        
        return response
