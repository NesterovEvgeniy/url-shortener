import pytest
import asyncio
from datetime import datetime, timedelta
from app.tasks import cleanup_inactive_links, cleanup_expired_links, scheduled_cleanup
from app.models import Link, LinkStat

@pytest.mark.asyncio
async def test_cleanup_inactive_links(db_session):
    """Тест очистки неактивных ссылок"""
    # Создаем тестовую ссылку
    link = Link(
        original_url="https://example.com",
        short_code="test123",
        owner_id=1
    )
    db_session.add(link)
    db_session.commit()
    
    # Создаем статистику с устаревшей датой доступа
    old_date = datetime.utcnow() - timedelta(days=31)
    stat = LinkStat(
        link_id=link.id,
        accessed_at=old_date
    )
    db_session.add(stat)
    db_session.commit()
    
    # Запускаем очистку
    deleted_count = await cleanup_inactive_links(db_session, days_inactive=30)
    
    # Проверяем результаты
    assert deleted_count == 1
    assert db_session.query(Link).filter_by(short_code="test123").first() is None

@pytest.mark.asyncio
async def test_cleanup_expired_links(db_session):
    """Тест очистки истекших ссылок"""
    # Создаем тестовую ссылку с истекшим сроком
    expired_date = datetime.utcnow() - timedelta(days=1)
    link = Link(
        original_url="https://example.com",
        short_code="expired123",
        owner_id=1,
        expires_at=expired_date
    )
    db_session.add(link)
    db_session.commit()
    
    # Запускаем очистку
    deleted_count = await cleanup_expired_links(db_session)
    
    # Проверяем результаты
    assert deleted_count == 1
    assert db_session.query(Link).filter_by(short_code="expired123").first() is None

@pytest.mark.asyncio
async def test_no_cleanup_for_active_links(db_session):
    """Тест сохранения активных ссылок"""
    # Создаем активную ссылку
    link = Link(
        original_url="https://example.com",
        short_code="active123",
        owner_id=1
    )
    db_session.add(link)
    db_session.commit()
    
    # Создаем недавнюю статистику
    recent_date = datetime.utcnow() - timedelta(days=1)
    stat = LinkStat(
        link_id=link.id,
        accessed_at=recent_date
    )
    db_session.add(stat)
    db_session.commit()
    
    # Запускаем очистку
    deleted_count = await cleanup_inactive_links(db_session, days_inactive=30)
    
    # Проверяем что ссылка сохранилась
    assert deleted_count == 0
    assert db_session.query(Link).filter_by(short_code="active123").first() is not None

@pytest.mark.asyncio
async def test_scheduled_cleanup(db_session, monkeypatch):
    """Тест планировщика задач очистки"""
    
    # Счетчик вызовов функций очистки
    cleanup_calls = {"expired": 0, "inactive": 0, "sleep": 0}
    
    # Мокируем функции очистки и sleep
    async def mock_cleanup_expired(db):
        cleanup_calls["expired"] += 1
        return 1
    
    async def mock_cleanup_inactive(db, days_inactive=30):
        cleanup_calls["inactive"] += 1
        return 2
    
    async def mock_sleep(seconds):
        cleanup_calls["sleep"] += 1
        # Вызываем исключение после первого вызова sleep,
        # чтобы выйти из бесконечного цикла
        if cleanup_calls["sleep"] >= 1:
            raise asyncio.CancelledError()
    
    # Применяем моки
    monkeypatch.setattr("app.tasks.cleanup_expired_links", mock_cleanup_expired)
    monkeypatch.setattr("app.tasks.cleanup_inactive_links", mock_cleanup_inactive)
    monkeypatch.setattr("asyncio.sleep", mock_sleep)
    
    # Запускаем функцию, которая должна вызвать наши мокированные функции
    with pytest.raises(asyncio.CancelledError):
        await scheduled_cleanup()
    
    # Проверяем, что функции очистки были вызваны
    assert cleanup_calls["expired"] == 1
    assert cleanup_calls["inactive"] == 1
    assert cleanup_calls["sleep"] == 1

@pytest.mark.asyncio
async def test_cleanup_empty_results(db_session):
    """Тест очистки без данных для удаления"""
    
    # Проверка, что функция корректно работает с пустой базой
    deleted_expired = await cleanup_expired_links(db_session)
    deleted_inactive = await cleanup_inactive_links(db_session, days_inactive=30)
    
    assert deleted_expired == 0
    assert deleted_inactive == 0