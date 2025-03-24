import pytest
from unittest.mock import Mock
from app.redis_client import redis_client

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