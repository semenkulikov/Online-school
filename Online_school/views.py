from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError
import logging

logger = logging.getLogger('core')


def handler404(request, exception):
    """Красивая страница 404"""
    logger.warning(f"404 error for URL: {request.path}")
    
    context = {
        'title': 'Страница не найдена',
        'message': 'Запрашиваемая страница не существует или была перемещена.',
        'error_code': '404',
        'suggestion': 'Перейдите в админ-панель или проверьте правильность адреса.'
    }
    
    return render(request, 'errors/error.html', context, status=404)


def handler500(request):
    """Красивая страница 500"""
    logger.error(f"500 error for URL: {request.path}")
    
    context = {
        'title': 'Внутренняя ошибка сервера',
        'message': 'Произошла ошибка при обработке вашего запроса.',
        'error_code': '500',
        'suggestion': 'Попробуйте обновить страницу или обратитесь к администратору.'
    }
    
    return render(request, 'errors/error.html', context, status=500) 