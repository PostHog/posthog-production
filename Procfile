release: cd deploy && python manage.py migrate
web: cd deploy && gunicorn posthog.wsgi --log-file -
worker: cd deploy && ./bin/docker-worker