# Auth & Access Control System

Backend-приложение с собственной системой **аутентификации** и **авторизации** на базе **FastAPI + SQLAlchemy + PostgreSQL**.  
Проект реализует управление пользователями, а также гибкую модель разграничения прав доступа к ресурсам.

---

## 📌 Функциональность

### 🔑 Аутентификация
- Регистрация нового пользователя (ФИО, email, пароль).
- Вход в систему (**login**) по email и паролю.
- Выход из системы (**logout**) с инвалидированием токена.
- Обновление профиля.
- Мягкое удаление аккаунта (`is_active=False`).
- Хранение паролей в зашифрованном виде (`bcrypt`).
- Использование **JWT** (access + refresh токены) с поддержкой **revocation** через таблицу `sessions`.
- **Refresh-токен хранится в защищённом HTTP-only cookie** и используется для обновления `access`-токена.

### 🔒 Авторизация
- Реализована собственная **система ролей и правил доступа**:
  - `roles` — роли пользователей (admin, manager, user, guest).
  - `business_objects` — объекты приложения (пользователи, товары, заказы и т.п.).
  - `access_rules` — правила доступа (чтение, создание, обновление, удаление — свои/чужие записи).
- Проверка прав выполняется через dependency `require_permission(...)`.
- Ошибки доступа:
  - `401 Unauthorized` — пользователь не аутентифицирован.
  - `403 Forbidden` — у пользователя нет прав для действия.

### 🛠 Mock-объекты
Для демонстрации есть **тестовые бизнес-объекты**, к которым применяются правила доступа.  
Например, пользователь с ролью `admin` может управлять всеми пользователями, а `user` — только своими записями.

---

## ⚙️ Технологии

- [FastAPI](https://fastapi.tiangolo.com/) — REST API
- [SQLAlchemy + Alembic](https://www.sqlalchemy.org/) — ORM и миграции
- [PostgreSQL](https://www.postgresql.org/) — БД
- [bcrypt](https://pypi.org/project/bcrypt/) — хэширование паролей
- [python-jose](https://python-jose.readthedocs.io/) — работа с JWT
- [Docker + docker-compose](https://www.docker.com/) — контейнеризация
- [nginx](https://nginx.org/) — reverse proxy
- [GitHub Actions](https://github.com/features/actions) — CI/CD

---

## 🚀 Запуск

### 1. Клонировать репозиторий
```bash
git clone https://github.com/AlexXxShurik/AuthExample
cd project
```

### 2. Настроить .env в корневой папке проверки

Создай файл `.env` в корне проекта и вставь туда пример:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=email@example.com
SMTP_PASSWORD=#################

POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret_password
POSTGRES_DB=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

SECRET_KEY=super-secret-key
ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=60
VERIFY_EMAIL_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
```

### 3. Запуск через Docker Compose

```bash
  docker-compose up --build
```

## После запуска

- **Backend**: [http://localhost:8000](http://localhost:8000)  
- **Swagger-документация**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)


## 🧩 Пример работы системы

- **Пользователь `admin`**  
  Может читать, обновлять и удалять **все записи**.

- **Пользователь `user`**  
  Может управлять **только своими записями**.

- **Пользователь без роли**  
  При попытке доступа получает ошибку **403 Forbidden**.

## 📜 Схема управления доступом

| Таблица            | Описание                                                                 |
|--------------------|---------------------------------------------------------------------------|
| **roles**          | Роли пользователей (`admin`, `manager`, `user`, `guest`).                 |
| **business_objects** | Объекты системы (`users`, `orders`, `products` и т.д.).                  |
| **access_rules**   | Связь роли с объектом и набором разрешений (`can_read`, `can_update`, `can_delete`, …). |
| **user_roles**     | Связь пользователя с ролями (многие-ко-многим).                          |
| **sessions**       | Сессии пользователей для работы с JWT (**revocation**).                   |

