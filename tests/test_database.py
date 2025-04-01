import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db, SessionLocal

def test_get_db():
    """Тест функции получения соединения с БД"""
    # Создаем тестовый генератор
    db_generator = get_db()
    
    # Получаем сессию
    db = next(db_generator)
    
    # Проверяем, что получили объект сессии
    assert db is not None
    assert hasattr(db, 'query')
    
    # Закрываем сессию через генератор
    try:
        next(db_generator)
    except StopIteration:
        # Ожидаем StopIteration, так как генератор должен завершиться
        pass