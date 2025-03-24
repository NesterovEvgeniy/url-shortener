from fastapi import Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio

from .database import get_db
from .models import Link, LinkStat
from .redis_client import clear_link_cache

async def cleanup_inactive_links(db: Session, days_inactive: int = 30):
    """Удаление ссылок, которые не использовались указанное количество дней
    
    Args:
        days_inactive (int): Количество дней без использования ссылки
        db (Session): Сессия базы данных
        
    Returns:
        int: Количество удаленных ссылок
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
    
    # Получаем ссылки, у которых последний переход был раньше cutoff_date
    inactive_links = db.query(Link).join(
        LinkStat, Link.id == LinkStat.link_id
    ).filter(
        LinkStat.accessed_at < cutoff_date
    ).all()
    
    # Удаляем ссылки и очищаем кэш
    for link in inactive_links:
        clear_link_cache(link.short_code)
        db.delete(link)
    
    db.commit()
    
    return len(inactive_links)

async def cleanup_expired_links(db: Session):
    """Удаление ссылок с истекшим сроком действия
    
    Args:
        db (Session): Сессия базы данных

    Returns:
        int: Количество удаленных ссылок
    """
    now = datetime.utcnow()
    
    # Получаем ссылки с истекшим сроком
    expired_links = db.query(Link).filter(
        Link.expires_at < now,
        Link.expires_at.isnot(None)
    ).all()
    
    # Удаляем ссылки и очищаем кэш
    for link in expired_links:
        clear_link_cache(link.short_code)
        db.delete(link)
    
    db.commit()
    
    return len(expired_links)

async def scheduled_cleanup():
    """Планировщик задач очистки
    
    Returns:
        None
    """
    while True:
        db = next(get_db())
        try:
            await cleanup_expired_links(db)
            await cleanup_inactive_links(db)
        finally:
            db.close()
        
        # Запускаем очистку каждые 24 часа
        await asyncio.sleep(86400)