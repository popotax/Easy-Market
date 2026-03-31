---
title: Brawl Calculator
emoji: "🎮"
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Brawl-Data

Proyecto para estimar el precio de cuentas de Brawl Stars con scraping, analisis de datos y regresion.

## Objetivo
Identificar las variables que mas impactan el precio de venta y construir un predictor inicial en USD.

## Estado actual
- Setup del proyecto completado.
- Scraping implementado para SkyCoach, PlayerAuctions, EloBoost24 y Gamer Markt.
- Parsers mejorados con reglas por dominio (precios, trofeos, brawlers y niveles con rangos validos).
- Fallback dinamico con Selenium para paginas con mayor dependencia de renderizado.
- Limpieza y normalizacion a USD implementadas.
- Feature engineering implementado.
- Entrenamiento de modelo y prediccion por CLI implementados.
- EDA automatizado con generacion de graficos y resumen.
- Comparacion automatica de metricas before/after mejoras.

## Fuentes de datos
- SkyCoach: https://skycoach.gg/brawl-stars-boost/accounts
- PlayerAuctions: https://www.playerauctions.com/brawl-stars-account/
- EloBoost24: https://eloboost24.eu/es/marketplace?filter%5Bgame_type%5D=bs
- Gamer Markt: https://www.gamermarkt.com/listings/brawl-stars-account

## Estructura
- src/scrapers: scrapers y utilidades de parsing
- src/preprocessing: limpieza y features
- src/ml: modelos, entrenamiento y evaluacion
- scripts: ejecucion por fases
- data/raw: datos scrapeados
- data/processed: dataset limpio
- data/models: modelo y metadatos
- artifacts/eda: graficos y reportes EDA

## Setup
```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Ejecucion por fases

### 1) Scraping
```bash
. .venv/bin/activate
python scripts/01_scrape_data.py
```

### 2) Limpieza
```bash
. .venv/bin/activate
python scripts/02_process_data.py
```

### 3) Entrenamiento
```bash
. .venv/bin/activate
python scripts/03_train_model.py
```

### 4) Prediccion de ejemplo
```bash
. .venv/bin/activate
python scripts/04_predict.py \
	--num_brawlers 65 \
	--avg_level 9 \
	--total_trophies 42000 \
	--rare_skins 18 \
	--site_source SkyCoach
```

### 5) EDA
```bash
. .venv/bin/activate
python scripts/05_eda_report.py
```

### 6) Comparar metricas (before vs after)
```bash
. .venv/bin/activate
python scripts/06_compare_metrics.py
```

## Web App (Tag -> Estimated Value)

This project now includes a web app where a user enters a player tag and gets an estimated account value.

### Setup token
1. Copy `.env.example` to `.env`
2. Set `BRAWL_API_TOKEN` with your official Brawl Stars API token

### Run the web app
```bash
. .venv/bin/activate
export BRAWL_API_TOKEN="your_token_here"
flask --app web/app.py run --debug --port 5001
```

Open `http://127.0.0.1:5001` and paste a player tag.

The app will:
- Fetch player profile data from the Brawl Stars API
- Build model features from API data
- Predict estimated value in USD and show a confidence range

## Deploy gratis (Hugging Face Spaces)

Puedes desplegar este backend gratis con Docker en Hugging Face Spaces.

### Archivos listos para deploy
- Dockerfile
- requirements-web.txt
- .dockerignore

### Pasos
1. Crea una cuenta en Hugging Face y entra a Spaces.
2. Crea un Space nuevo con SDK = Docker.
3. Conecta o sube este repositorio al Space.
4. En Settings -> Variables and secrets agrega:
	- BRAWL_API_TOKEN = tu token oficial de Brawl Stars API
5. Espera el build y abre la URL publica del Space.

### Comando de arranque en contenedor
El contenedor arranca con:
`gunicorn web.app:app --bind 0.0.0.0:${PORT}`

Hugging Face asigna `PORT=7860` por defecto y el Dockerfile ya esta configurado para eso.

## Deploy estable de produccion (IP fija)

Si quieres evitar problemas de whitelist por IP con la API de Brawl, usa backend en VM con IP publica fija.

### Arquitectura recomendada
- Backend Flask en Oracle Cloud Always Free (VM) con IP reservada
- Reverse proxy HTTPS con Caddy
- Frontend opcional en hosting estatico (Cloudflare Pages/GitHub Pages)

### Archivos de infraestructura
- deploy/docker-compose.prod.yml
- deploy/Caddyfile
- .env.production.example
- scripts/infra/bootstrap_oracle_vm.sh
- scripts/infra/deploy_prod.sh

### Pasos resumidos
1. Crear VM en Oracle Always Free y reservar IP publica.
2. Apuntar tu dominio/subdominio a esa IP.
3. En la VM, clonar repo y ejecutar `scripts/infra/bootstrap_oracle_vm.sh`.
4. Copiar `.env.production.example` a `.env.production` y definir `BRAWL_API_TOKEN`.
5. Editar `deploy/Caddyfile` con tu dominio real.
6. Ejecutar `scripts/infra/deploy_prod.sh`.
7. Registrar la IP fija de la VM en Brawl Developers al crear la API key.

### Health check
La app expone `GET /healthz` para monitoreo y validacion de despliegue.

## Deploy hibrido: Netlify (frontend) + tu computadora (backend)

Este modo publica el frontend siempre y usa un backend privado que solo el owner levanta cuando quiera.

### Componentes
- Frontend estatico: `netlify-frontend/`
- Config Netlify: `netlify.toml`
- Backend API local: `POST /api/estimate` en `web/app.py`

### Flujo
1. Subes `netlify-frontend/` a Netlify.
2. Configuras una URL fija de backend en `netlify-frontend/main.js` (`BACKEND_BASE_URL`).
3. En tu computadora levantas backend solo cuando quieras habilitar la app.

### Backend local (un comando)
`cd /Users/rubenguerrero/Desktop/Brawl-Data && source .venv/bin/activate && ALLOWED_ORIGINS=https://brawl-cacl.netlify.app BRAWL_API_TOKEN=TU_TOKEN flask --app web/app.py run --host 0.0.0.0 --port 5001`

### Ejemplo ALLOWED_ORIGINS
`ALLOWED_ORIGINS=https://tu-sitio.netlify.app`

### Nota importante
Si tu backend corre en casa, la app en Netlify solo funcionara mientras tu PC este encendida y ese comando este corriendo.

## Resultados actuales (2026-03-30)
- Filas scrapeadas combinadas: 61
- Filas limpias para entrenamiento: 56
- Distribucion por sitio en dataset limpio:
	- Gamer Markt: 28
	- PlayerAuctions: 23
	- SkyCoach: 4
	- EloBoost24: 1
- Mejor modelo actual: Random Forest
- Metricas actuales:
	- MAE: 41.10
	- RMSE: 62.97
	- R2: 0.33

## Impacto de mejoras recomendadas
- MAE: 43.84 -> 41.10 (mejora de 6.24%)
- RMSE: 75.06 -> 62.97 (mejora de 16.11%)
- R2: -6.32 -> 0.33 (salto de +6.65)

El pipeline ahora generaliza mejor que la version inicial, aunque todavia hay margen para mejorar precision con selectores mas especificos por sitio.

## Proximos pasos
1. Afinar selectores CSS por sitio para reducir ruido de texto residual.
2. Expandir cobertura de EloBoost24 (paginacion y espera de elementos).
3. Agregar mas snapshots por fecha para estabilizar el modelo.
4. Crear notebook final de analisis para reporte visual detallado.

## Archivos de referencia
- Configuracion: config/config.yaml
- Diccionario de datos: DATA_DICTIONARY.md
- Metricas y configuracion de modelo: data/models/model_config.json
- Reporte de mejora de modelo: data/models/model_improvement_report.md
- Resumen EDA: artifacts/eda/eda_summary.md
- Web app backend: web/app.py
- Web app template: web/templates/index.html
- Web app styles: web/static/styles.css



