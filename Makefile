.PHONY: install migrate init run attack

install:
	pip install -r requirements.txt

up:
	docker compose up -d

down:
	docker compose down

clean:
	docker compose down -v

migrate:
	python manage.py migrate

init: clean up
	@echo "Waiting for DB to initialize..."
	@sleep 5
	python manage.py migrate
	python setup_data.py

run:
	python manage.py runserver

celery:
	celery -A config worker --loglevel=info

result:
	python result_example.py

test:
	python manage.py test core