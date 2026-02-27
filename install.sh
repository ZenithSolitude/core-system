#!/bin/bash
# install.sh - Установка системы одной командой

echo "--- Обновление системы и установка Docker ---"
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y docker.io docker-compose git curl

echo "--- Клонирование репозитория ---"
git clone https://github.com/ZenithSolitude/core-system.git
cd core-system

echo "--- Запуск контейнеров ---"
sudo docker-compose up -d --build

echo "--- Готово! Сайт доступен на http://81.90.25.247 ---"
