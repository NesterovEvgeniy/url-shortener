# Скрипт для создания таблиц в базе данных
import os
from sqlalchemy import create_engine
from app.database import Base
from app.models import User, Link, LinkStat

# Используем переменную окружения или значение по умолчанию
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/urlshortener")
print(f"Подключение к базе данных: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)

# Создание всех таблиц
Base.metadata.create_all(bind=engine)
print("Таблицы успешно созданы")