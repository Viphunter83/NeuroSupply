#!/bin/bash

# Скрипт для проверки готовности проекта к демонстрации

echo "🔍 Проверка структуры проекта..."

if [ -d "src/dashboard" ] && [ -d "src/mini-app" ]; then
    echo "✅ Фронтенд компоненты на месте (src/dashboard, src/mini-app)"
else
    echo "❌ Ошибка: Фронтенд компоненты не найдены в src/"
    exit 1
fi

if [ ! -d "web" ]; then
    echo "✅ Старая папка 'web' удалена"
else
    echo "⚠️ Внимание: Папка 'web' всё еще существует в корне"
fi

echo "🔍 Проверка конфигурации..."
if [ -f ".env" ]; then
    echo "✅ Файл .env найден"
else
    echo "❌ Ошибка: Файл .env отсутствует"
    exit 1
fi

echo "🔍 Проверка Docker сервисов (если запущены)..."
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    echo "⚠️ docker-compose не найден, пропускаю проверку контейнеров"
fi

echo "🚀 Проект готов к демонстрации!"
echo "Следуйте инструкциям в walkthrough.md"
