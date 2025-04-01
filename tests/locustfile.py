from locust import HttpUser, task, between, events
from faker import Faker
import random
import time

fake = Faker()

class URLShortenerUser(HttpUser):
    host = "http://localhost:8000"
    wait_time = between(1, 3)
    
    def on_start(self):
        """Авторизация пользователя перед началом тестов"""
        # Генерируем данные пользователя
        self.user_email = fake.email()
        self.user_password = "test_password123"
        
        # Регистрация тестового пользователя
        register_response = self.client.post(
            "/auth/register",
            json={
                "email": self.user_email,
                "password": self.user_password
            }
        )
        
        if register_response.status_code != 200:
            # Если пользователь уже существует, пробуем войти
            response = self.client.post(
                "/auth/token",
                data={
                    "username": self.user_email,
                    "password": self.user_password
                }
            )
        else:
            response = register_response
        
        # Сохраняем токен для последующих запросов
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.my_links = []
    
    @task(3)
    def create_short_link(self):
        """Создание короткой ссылки"""
        response = self.client.post(
            "/links/shorten",
            headers=self.headers,
            json={
                "original_url": fake.url(),
                "custom_alias": fake.slug()
            }
        )
        if response.status_code == 200:
            self.my_links.append(response.json()["short_code"])
    
    @task(5)
    def redirect_to_original(self):
        """Переход по короткой ссылке"""
        if not self.my_links:
            # Если нет своих ссылок, создаем новую
            response = self.client.post(
                "/links/shorten",
                headers=self.headers,
                json={"original_url": fake.url()}
            )
            if response.status_code == 200:
                short_code = response.json()["short_code"]
                self.my_links.append(short_code)
        else:
            # Используем случайную существующую ссылку
            short_code = random.choice(self.my_links)
        
        # Выполняем редирект
        self.client.get(
            f"/{short_code}",
            name="/redirect"
        )
    
    @task(2)
    def search_links(self):
        """Поиск ссылок"""
        self.client.get(
            "/links/search?original_url=example",  # Исправлено: query -> original_url
            headers=self.headers,
            name="/links/search"
        )
    
    @task(1)
    def get_link_info(self):
        """Получение информации о ссылке"""
        if self.my_links:
            short_code = random.choice(self.my_links)
            self.client.get(
                f"/links/{short_code}",
                headers=self.headers,
                name="/links/info"
            )
    
    @task(1)
    def update_link(self):
        """Обновление ссылки"""
        if self.my_links:
            short_code = random.choice(self.my_links)
            self.client.put(
                f"/links/{short_code}",
                headers=self.headers,
                json={"original_url": fake.url()},
                name="/links/update"
            )

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Начало нагрузочного тестирования...")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Завершение нагрузочного тестирования...")