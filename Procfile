release: cd deploy && python manage.py migrate && python manage.py migrate_clickhouse
web: cd deploy && NEW_RELIC_CONFIG_FILE=../newrelic.ini newrelic-admin run-program gunicorn posthog.wsgi --log-file -
worker: cd deploy && NEW_RELIC_CONFIG_FILE=../newrelic.ini newrelic-admin run-program ./bin/docker-worker
