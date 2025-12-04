## Docker Quickstart

```bash
# build image
docker compose build

# run server (http://localhost:8000)
docker compose up

# the container runs:
# python manage.py makemigrations prompts
# python manage.py migrate
# python manage.py runserver 0.0.0.0:8000
```

Environment variables are read from `.env`. Update it with your secrets before running the container.
