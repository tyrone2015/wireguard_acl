#!/bin/bash

# 启动后端服务

if [ -f "manage.py" ]; then
  echo "检测到 Django 项目，启动后端..."
  source .venv/bin/activate
  python manage.py runserver 0.0.0.0:8000
else
  echo "检测到 FastAPI 项目，启动后端..."
  uvicorn app.main:app --host 0.0.0.0 --port 8000
fi

echo "后端服务已退出，按 Ctrl+C 可中断。"

echo "启动前端服务..."
cd frontend
npm run dev
cd ..

echo "前端服务已退出，按 Ctrl+C 可中断。"
echo "访问前端：http://localhost:5173"
echo "访问后端：http://localhost:8000"
