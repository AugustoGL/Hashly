.PHONY: up down logs test seed smoke api web worker

up:        ## Levanta todo con Docker (web :3000, API :8000)
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

test:      ## Tests del backend
	cd api && python -m pytest -q

seed:      ## Usuario demo + API key (dentro del contenedor)
	docker compose exec api python seed.py

smoke:     ## Recorre el flujo completo contra el API en marcha
	python3 scripts/smoke.py

# --- Sin Docker ---
api:
	cd api && uvicorn main:app --reload --port 8000

worker:
	cd api && python worker.py

web:
	cd web && npm run dev
