.PHONY: up down logs backend-dev frontend-dev worker beat streamlit-dev

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

backend-dev:
	cd backend && uvicorn app.main:app --reload

frontend-dev:
	cd frontend && npm install && npm run dev

streamlit-dev:
	cd streamlit_app && python3 -m pip install -r requirements.txt && STREAMLIT_API_BASE_URL=http://localhost:8000/api streamlit run app.py

worker:
	cd backend && celery -A app.celery_app.celery_app worker --loglevel=info

beat:
	cd backend && celery -A app.celery_app.celery_app beat --loglevel=info
