all:
	docker compose up --build

clean:
	docker compose down -v --rmi all