import pytest
from unittest.mock import Mock
import json
from app.redis_client import set_cache, get_cache, delete_cache, clear_link_cache, increment_counter

def test_set_cache(mock_redis):
    """Тест функции установки кэша"""
    # Тест с строковыми данными
    set_cache("test:key", "test-value")
    mock_redis.setex.assert_called_with("test:key", 3600, "test-value")
    
    # Тест с данными словаря
    test_dict = {"key": "value", "nested": {"inner": "data"}}
    set_cache("test:dict", test_dict)
    mock_redis.setex.assert_called_with("test:dict", 3600, json.dumps(test_dict))
    
    # Тест с пользовательским TTL
    set_cache("test:ttl", "value", ttl=60)
    mock_redis.setex.assert_called_with("test:ttl", 60, "value")

def test_get_cache(mock_redis):
    """Тест функции получения данных из кэша"""
    # Тест с несуществующим ключом
    mock_redis.get.return_value = None
    result = get_cache("nonexistent:key")
    assert result is None
    
    # Тест с строковым значением
    mock_redis.get.return_value = b"test-value"
    result = get_cache("test:string")
    assert result == "test-value"
    
    # Тест с JSON значением
    test_dict = {"key": "value", "nested": {"inner": "data"}}
    mock_redis.get.return_value = json.dumps(test_dict).encode()
    result = get_cache("test:json")
    assert result == test_dict

def test_delete_cache(mock_redis):
    """Тест функции удаления кэша"""
    delete_cache("test:key")
    mock_redis.delete.assert_called_with("test:key")

def test_clear_link_cache(mock_redis):
    """Тест функции очистки кэша ссылки"""
    clear_link_cache("test-code")
    # Должен удалить несколько ключей, связанных со ссылкой
    assert mock_redis.delete.call_count >= 2
    
    # Проверка удаления ключа URL
    mock_redis.delete.assert_any_call("link:test-code")
    
    # Проверка удаления ключа статистики
    mock_redis.delete.assert_any_call("stats:test-code")

def test_increment_counter(mock_redis):
    """Тест функции увеличения счетчика"""
    # Тест нового ключа (не существует)
    mock_redis.exists.return_value = False
    increment_counter("counter:new")
    mock_redis.setex.assert_called_with("counter:new", 3600, 1)
    
    # Тест существующего ключа
    mock_redis.exists.return_value = True
    mock_redis.incr.return_value = 5  # Предположим, что счетчик увеличился до 5
    # Настраиваем mock.get, чтобы возвращал строку "5"
    mock_redis.get.return_value = b"5"
    result = increment_counter("counter:existing")
    mock_redis.incr.assert_called_with("counter:existing")
    assert result == 5