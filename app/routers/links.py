from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import random
import string
from datetime import datetime, timedelta
import asyncio  

from ..database import get_db
from ..models import Link, LinkStat, User
from ..schemas import LinkCreate, Link as LinkResponse, LinkUpdate, LinkStats
from ..tasks import scheduled_cleanup
from .auth import get_current_user, get_current_user_or_none
from ..redis_client import redis_client, set_cache, get_cache, delete_cache, clear_link_cache

router = APIRouter(tags=["links"], prefix="/links")

@router.on_event("startup")
async def start_cleanup_task():
    asyncio.create_task(scheduled_cleanup())

@router.get("/projects", response_model=List[str], summary="Получить все проекты пользователя", description="Получить список всех проектов, созданных аутентифицированным пользователем")
def get_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить список всех проектов пользователя
    
    Returns:
        List[str]: Список названий проектов
    
    Raises:
        HTTPException: Если пользователь не аутентифицирован
    """
    projects = db.query(Link.project).filter(
        Link.owner_id == current_user.id,
        Link.project.isnot(None)
    ).distinct().all()
    
    return [project[0] for project in projects if project[0]]

@router.get("/projects/{project_name}", response_model=List[LinkResponse], summary="Получить ссылки проекта", description="Получить все ссылки, связанные с определенным проектом")
def get_links_by_project(project_name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить все ссылки в определенном проекте
    
    Args:
        project_name (str): Название проекта, из которого нужно получить ссылки
    
    Returns:
        List[LinkResponse]: Список ссылок в проекте
    
    Raises:
        HTTPException: Если пользователь не аутентифицирован
    """
    links = db.query(Link).filter(
        Link.owner_id == current_user.id,
        Link.project == project_name
    ).all()
    
    return links

@router.get("/search", response_model=List[LinkResponse], summary="Поиск ссылок по оригинальному URL", description="Поиск всех ссылок, соответствующих указанному оригинальному URL")
async def search_links(original_url: str, db: Session = Depends(get_db)):
    """Найти ссылки по оригинальному URL
    
    Args:
        original_url (str): Оригинальный URL для поиска (полный или часть)
    
    Returns:
        List[LinkResponse]: Список найденных ссылок
    """
    # Проверяем кэш
    cache_key = f"search:{original_url}"
    cached_results = get_cache(cache_key)
    if cached_results:
        return cached_results

    # Оптимизированный запрос с использованием индекса
    links = db.query(Link).filter(
        Link.original_url.ilike(f'%{original_url}%')
    ).order_by(Link.created_at.desc()).limit(100).all()
    
    # Сериализуем результаты для кэширования
    results = [
        {
            "id": link.id,
            "original_url": link.original_url,
            "short_code": link.short_code,
            "custom_alias": link.custom_alias,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "access_count": link.access_count
        } for link in links
    ]
    
    # Кэшируем результаты на 5 минут
    set_cache(cache_key, results, 300)
    return links

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@router.post("/shorten", response_model=LinkResponse, summary="Создать короткую ссылку", description="Создать новую сокращенную ссылку с опциональным пользовательским алиасом и сроком действия")
async def create_short_link(
    link_data: LinkCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_none)
):
    """Создать новую сокращенную ссылку
    
    Args:
        link_data (LinkCreate): Оригинальный URL и дополнительные настройки
        request (Request): Объект запроса FastAPI
    
    Returns:
        LinkResponse: Детали созданной короткой ссылки
    
    Raises:
        HTTPException: Если пользовательский алиас уже существует
    """
    if link_data.custom_alias:
        existing_link = db.query(Link).filter(Link.custom_alias == link_data.custom_alias).first()
        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom alias already exists"
            )
        short_code = link_data.custom_alias
    else:
        while True:
            short_code = generate_short_code()
            existing_link = db.query(Link).filter(Link.short_code == short_code).first()
            if not existing_link:
                break

    db_link = Link(
        original_url=str(link_data.original_url),
        short_code=short_code,
        custom_alias=link_data.custom_alias,
        expires_at=link_data.expires_at,
        owner_id=current_user.id if current_user else None,
        project=link_data.project 
    )

    db.add(db_link)
    db.commit()
    db.refresh(db_link)

    # Кэшируем ссылку в Redis
    set_cache(f"link:{short_code}", str(link_data.original_url), 86400)  # 24 часа в секундах

    return db_link

@router.get("/{short_code}", response_model=LinkResponse, include_in_schema=False)
@router.get("/{short_code}/", response_model=LinkResponse, summary="Получить детали ссылки", description="Получить информацию о конкретной сокращенной ссылке")
async def get_link_info(short_code: str, db: Session = Depends(get_db)):
    """Получить информацию о конкретной короткой ссылке
    
    Args:
        short_code (str): Короткий код ссылки
    
    Returns:
        LinkResponse: Детали ссылки
    
    Raises:
        HTTPException: Если ссылка не найдена
    """
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    return link


@router.get("/{short_code}/stats", response_model=LinkStats, summary="Получить статистику ссылки", description="Получить статистику использования конкретной сокращенной ссылки")
async def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    """Получить статистику о конкретной короткой ссылке
    
    Args:
        short_code (str): Короткий код ссылки
    
    Returns:
        LinkStats: Статистика ссылки
    
    Raises:
        HTTPException: Если ссылка не найдена
    """
    # Проверка кэша
    cached_stats = get_cache(f"stats:{short_code}")
    if cached_stats:
        return cached_stats
        
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ссылка не найдена"
        )
    
    # Создаем словарь с данными, явно форматируя datetime объекты
    stats = {
        "original_url": link.original_url,
        "created_at": link.created_at.isoformat() if link.created_at else None,
        "access_count": link.access_count,
        "last_accessed": link.last_accessed.isoformat() if link.last_accessed else None
    }
    
    # Кэшируем статистику как словарь с уже сериализованными датами
    set_cache(f"stats:{short_code}", stats, 300)  # 5 минут
    
    return stats

    
@router.get("/{short_code}/redirect/", name="redirect_to_original", summary="Перенаправление на оригинальный URL", description="Перенаправление на оригинальный URL и запись статистики посещений")
async def redirect_to_original(short_code: str, request: Request, db: Session = Depends(get_db)):
    """Перенаправление на оригинальный URL
    
    Args:
        short_code (str): Короткий код ссылки
        request (Request): Объект запроса FastAPI
    
    Returns:
        dict: Оригинальный URL для перенаправления
    
    Raises:
        HTTPException: Если ссылка не найдена или срок ее действия истек
    """
    # Пытаемся получить URL из кэша Redis
    cached_url = get_cache(f"link:{short_code}")
    original_url = None
    link = None

    if cached_url:
        original_url = cached_url
        # Все равно получаем ссылку из БД для обновления статистики
        link = db.query(Link).filter(Link.short_code == short_code).first()
    else:
        link = db.query(Link).filter(Link.short_code == short_code).first()
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ссылка не найдена"
            )
            
        # Проверка срока истечения
        if link.expires_at and link.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Срок действия ссылки истек"
            )
            
        original_url = link.original_url
        # Кэшируем URL
        set_cache(f"link:{short_code}", original_url, 86400)  # 24 часа в секундах

    if link:
        # Обновляем статистику
        link.access_count += 1
        link.last_accessed = datetime.utcnow()
        
        # Записываем детальную статистику
        stats = LinkStat(
            link_id=link.id,
            ip_address=str(request.client.host),
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer")
        )
        db.add(stats)
        db.commit()

    return {"url": original_url}

@router.delete("/{short_code}", include_in_schema=False)
@router.delete("/{short_code}/", summary="Удалить ссылку", description="Удалить сокращенную ссылку")
async def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить конкретную короткую ссылку
    
    Args:
        short_code (str): Короткий код ссылки для удаления
    
    Returns:
        dict: Сообщение об успешном удалении
    
    Raises:
        HTTPException: Если ссылка не найдена или у пользователя нет прав
    """
    link = db.query(Link).filter(
        Link.short_code == short_code,
        Link.owner_id == current_user.id
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found or you don't have permission"
        )

    db.delete(link)
    db.commit()

    # Clear Redis cache
    clear_link_cache(short_code)

    return {"message": "Link deleted successfully"}

@router.put("/{short_code}", response_model=LinkResponse, summary="Update link", description="Update an existing shortened URL")
async def update_link(
    short_code: str,
    link_update: LinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление существующей сокращенной ссылки

    Args:
        short_code (str): Короткий код ссылки для обновления
        link_update (LinkUpdate): Данные для обновления
        db (Session): Сессия базы данных
        current_user (User): Текущий пользователь
    Returns:
        LinkResponse: Обновленные данные ссылки
    Raises:
        HTTPException: Если ссылка не найдена или у пользователя нет прав
    """
    link = db.query(Link).filter(
        Link.short_code == short_code,
        Link.owner_id == current_user.id
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ссылка не найдена или у пользователя нет прав"
        )

    if link_update.original_url:
        link.original_url = str(link_update.original_url)
    if link_update.custom_alias:
        existing_link = db.query(Link).filter(
            Link.custom_alias == link_update.custom_alias,
            Link.id != link.id
        ).first()
        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Кастомный алиас уже используется"
            )
        link.custom_alias = link_update.custom_alias
    if link_update.expires_at:
        link.expires_at = link_update.expires_at

    db.commit()
    db.refresh(link)

    # Обновляем кэш Redis
    clear_link_cache(short_code)
    set_cache(f"link:{short_code}", str(link.original_url), 86400)  # 24 часа в секундах

    return link