# Foodgram

Проект **Foodgram** позволяет пользователям публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Добавлять новые ингредиенты и теги на сайт могут только **администраторы**.

Для **всех** пользователей реализованы следующие возможности:
- просмотр рецептов на главной и отдельных страниц рецептов;
- просмотр страниц пользователей;
- создание аккаунта;
- фильтрация рецептов по тегам;
  
**Авторизованным** пользователям дополнительно доступны:
- вход в систему под своим логином и паролем и выход из системы;
- создание, редактирование и удаление собственных рецептов;
- работа с персональным списком покупок;
- работа с персональным списком избранного;
- подписка на публикации других авторов и отмена подписки, просмотр своей страницы подписок.

## Содержание
- [Технологии](https://github.com/TimyrPahomov/foodgram#технологии)
- [Локальный запуск](https://github.com/TimyrPahomov/foodgram#локальный-запуск)
- [Автор](https://github.com/TimyrPahomov/foodgram#автор)

## Технологии
- [Python](https://www.python.org/)
- [Django](https://www.djangoproject.com/)
- [Django REST framework](https://www.django-rest-framework.org/)
- [Djoser](https://djoser.readthedocs.io/en/latest/)
- [Docker](https://docs.docker.com/)

## Локальный запуск
1. Необходимо клонировать репозиторий и перейти в него:

```sh
git clone https://github.com/TimyrPahomov/foodgram.git
cd foodgram/
```

2. Далее нужно создать и активировать виртуальное окружение:

```sh
python -m venv venv
source venv/Scripts/activate
```

3. Обновить пакетный менеджер и установить зависимости из файла _requirements.txt_:

```sh
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Затем следует перейти в директорию с файлом _manage.py_ и выполнить миграции:

```sh
cd backend/
python manage.py migrate
```

5. Наконец, запустить проект:

```sh
python manage.py runserver
```

## Автор
[Пахомов Тимур](<https://github.com/TimyrPahomov/>)