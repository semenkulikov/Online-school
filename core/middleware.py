import logging

class LogIPMiddleware:
    """
    Middleware для дописывания IP клиента в лог django.server.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Логгер, который выводит стандартные access‑логи
        self.logger = logging.getLogger('django.server')  # :contentReference[oaicite:0]{index=0}

    def __call__(self, request):
        # Обрабатываем запрос, получаем ответ
        response = self.get_response(request)

        # Получаем IP: сначала X‑Forwarded-For, потом REMOTE_ADDR
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '-')

        # Собираем данные для лог‑сообщения
        method   = request.method
        path     = request.get_full_path()
        proto    = request.META.get('SERVER_PROTOCOL', '')
        status   = response.status_code
        # попытаемся определить размер тела ответа
        size     = getattr(response, 'content', b'')
        length   = len(size) if isinstance(size, (bytes, str)) else '-'

        # Формируем и пишем лог
        self.logger.info(
            f'"{method} {path} {proto}" ({ip}) - {status} {length}'
        )

        return response
