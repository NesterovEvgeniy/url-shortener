import pytest
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.redis_client import redis_client

@pytest.fixture(scope="function")
def db_session():
    # Создаем временную базу данных для тестов
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    # Создаем новую сессию для теста
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Удаляем все таблицы после теста
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def mock_redis():
    # Создаем мок-клиент Redis
    mock_client = Mock()
    
    # Мокируем метод get с возвратом None по умолчанию
    mock_client.get.return_value = None
    
    # Мокируем метод setex
    mock_client.setex.return_value = True
    
    # Мокируем метод delete
    mock_client.delete.return_value = True
    
    # Мокируем метод exists 
    mock_client.exists.return_value = False
    
    # Мокируем метод incr 
    mock_client.incr.return_value = 1
    
    # Заменяем реальный клиент Redis на мок-клиент
    redis_client.connection_pool = mock_client
    redis_client.get = mock_client.get
    redis_client.setex = mock_client.setex
    redis_client.delete = mock_client.delete
    redis_client.exists = mock_client.exists
    redis_client.incr = mock_client.incr
    
    return mock_client