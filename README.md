# Online School

Django приложение для управления онлайн школой.

## Быстрый старт

### Разработка

```bash
# Клонируем репозиторий
git clone <repository-url>
cd Online-school

# Создаем .env файл
cp .env.example .env

# Запускаем в режиме разработки
docker-compose up --build
```

### Продакшн

```bash
# Генерируем SSL сертификат (для тестирования)
./generate_ssl.sh

# Запускаем продакшн версию
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### CI/CD деплой

Настроен автоматический деплой через GitHub Actions при пуше в `main` ветку.

**Необходимые GitHub Secrets:**
- `DOCKERHUB_USERNAME` - имя пользователя Docker Hub
- `DOCKERHUB_TOKEN` - токен Docker Hub
- `SERVER_HOST` - IP адрес или домен сервера
- `SERVER_USER` - пользователь для SSH подключения
- `SERVER_SSH_KEY` - приватный SSH ключ
- `DJANGO_SECRET_KEY` - секретный ключ Django
- `DEBUG_MODE` - режим отладки (False для продакшена)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - настройки БД
- `ALLOWED_HOSTS` - разрешенные хосты (через запятую)
- `LANGUAGE_CODE` - код языка

**Процесс CI/CD:**
1. Тестирование кода и миграций
2. Сборка и пуш Docker образа
3. Деплой на сервер с автоматической генерацией SSL
4. Запуск миграций и проверка системы

## Решение проблем с производительностью

### WORKER TIMEOUT ошибки

Проблема: Gunicorn воркеры получают таймауты из-за HTTPS запросов на HTTP порт.

**Решение:**
1. Используем nginx как reverse proxy для обработки HTTPS
2. Увеличиваем таймауты gunicorn до 120 секунд
3. Используем gevent воркеры для асинхронной обработки
4. Добавляем фильтрацию невалидных запросов

### Конфигурация Gunicorn

```bash
gunicorn Online_school.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class gevent \
  --worker-connections 1000 \
  --timeout 120 \
  --keepalive 10 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --preload
```

### Nginx конфигурация

- Обрабатывает HTTPS на порту 443
- Проксирует запросы на HTTP backend (порт 8000)
- Добавляет правильные заголовки для Django
- Фильтрует подозрительные запросы

### Django настройки

```python
# Настройки для работы за прокси
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
FORWARDED_ALLOW_IPS = "*"
```

## Мониторинг

### Логи производительности

```bash
# Просмотр логов gunicorn
docker logs online-school-web-1

# Просмотр логов nginx
docker logs online-school-nginx-1
```

### Команды мониторинга

```bash
# Проверка производительности
docker-compose exec web python manage.py monitor_performance

# Проверка переменных окружения
docker-compose exec web python manage.py check_env
```

## Архитектура

```
Internet → Nginx (443/80) → Gunicorn (8000) → Django → PostgreSQL
```

- **Nginx**: SSL терминация, статические файлы, rate limiting
- **Gunicorn**: WSGI сервер с gevent воркерами
- **Django**: Веб-приложение
- **PostgreSQL**: База данных

## Безопасность

- SSL/TLS шифрование
- Rate limiting для API и админки
- Фильтрация невалидных запросов
- Заголовки безопасности
- CSRF защита

## Производительность

- Кэширование в базе данных
- Сжатие статических файлов (WhiteNoise)
- Переиспользование соединений БД
- Асинхронные воркеры (gevent)
- Мониторинг медленных запросов 