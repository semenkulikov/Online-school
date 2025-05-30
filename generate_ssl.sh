#!/bin/bash

# Скрипт для генерации самоподписанного SSL сертификата

echo "🔐 Генерация SSL сертификата..."

# Создаем директории
mkdir -p ssl/certs ssl/private

# Генерируем приватный ключ
openssl genrsa -out ssl/private/server.key 2048

# Генерируем самоподписанный сертификат
openssl req -new -x509 -key ssl/private/server.key -out ssl/certs/server.crt -days 365 -subj "/C=RU/ST=Moscow/L=Moscow/O=Online School/CN=localhost"

# Устанавливаем права доступа
chmod 600 ssl/private/server.key
chmod 644 ssl/certs/server.crt

echo "✅ SSL сертификат создан:"
echo "   Сертификат: ssl/certs/server.crt"
echo "   Приватный ключ: ssl/private/server.key"
echo ""
echo "⚠️  Это самоподписанный сертификат для тестирования!"
echo "   Для продакшена используйте сертификат от доверенного CA." 