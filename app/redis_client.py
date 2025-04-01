import redis
import json
import os
from typing import Any, Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL)

# Стандартное время жизни кеша в секундах
DEFAULT_TTL = 3600

def set_cache(key: str, data: Any, ttl: int = DEFAULT_TTL):
    """Хранить данные в кэше

    Args:
        key (str): Ключ для хранения данных
        data (Any): Данные для хранения
        ttl (int, optional): Время жизни данных в секундах. По умолчанию DEFAULT_TTL.

    Returns:
        None
    """
    if isinstance(data, dict) or isinstance(data, list):
        # Преобразуем словарь или список в JSON строку с обработкой datetime
        try:
            json_str = json.dumps(data, default=lambda obj: obj.isoformat() if hasattr(obj, 'isoformat') else str(obj))
            redis_client.setex(key, ttl, json_str)
        except Exception as e:
            print(f"Ошибка кэширования данных: {e}")
    else:
        redis_client.setex(key, ttl, data)

def get_cache(key: str) -> Optional[Any]:
    """Получить данные из кэша

    Args:
        key (str): Ключ для получения данных
    Returns:
        Optional[Any]: Данные из кэша или None, если данные не найдены
    """
    data = redis_client.get(key)
    if not data:
        return None
    
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return data.decode('utf-8')

def delete_cache(key: str):
    """Удалить данные из кэша
    
    Args:
        key (str): Ключ для удаления данных
    Returns:
        None
    """
    redis_client.delete(key)

def clear_link_cache(short_code: str):
    """Очистить кэш ссылки и статистики

    Args:
        short_code (str): Ключ для очистки кэша
    Returns:
        None
    """
    keys_to_delete = [
        f"link:{short_code}",
        f"stats:{short_code}"
    ]
    for key in keys_to_delete:
        delete_cache(key)

def increment_counter(key: str, ttl: int = DEFAULT_TTL):
    """Увеличить счетчик и установить TTL, если ключ не существует
    
    Args:
        key (str): Ключ для счетчика
        ttl (int, optional): Время жизни данных в секундах. По умолчанию DEFAULT_TTL.
    Returns:
        int: Текущее значение счетчика
    """
    if not redis_client.exists(key):
        redis_client.setex(key, ttl, 1)
    else:
        redis_client.incr(key)
    
    # Получаем текущее значение как строку и преобразуем в int
    value = redis_client.get(key)
    if value is None:
        return 0  # Защита от None
    return int(value)