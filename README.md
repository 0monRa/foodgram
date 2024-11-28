### Описание:

Проект Foodgram - сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

### Технологии:

- Python 3.11
- Django 3.2.3
- Django REST Framework 3.12.4
- Docker 3.3

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/0monRa/api_yamdb.git
```

Перейти в папку `/infra/`

Выполнить команду

```
sudo docker compose up -d
```

Выполнить миграции:

```
sudo docker exec -it foodgram-back python manage.py migrate
```

Згрузить статику:

```
sudo docker exec -it foodgram-back python manage.py collectstatic
```

Згрузить фикстуры ингредиентов:

```
sudo docker exec -it foodgram-back python manage.py loaddata ./data/ingredients.json
```

Далее, необходимо перйти в админ-панель и создать несколько тэгов
