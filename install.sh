#!/bin/bash

# 1. Установка Docker
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce docker-compose

# 2. Клонирование твоего проекта
git clone https://github.com/ZenithSolitude/core-system.git
cd core-system

# 3. Запуск в фоне
sudo docker-compose up -d --build

echo "=========================================="
echo "СИСТЕМА УСТАНОВЛЕНА!"
echo "IP: 81.90.25.247"
echo "API Docs: http://81.90.25.247/docs"
echo "=========================================="
