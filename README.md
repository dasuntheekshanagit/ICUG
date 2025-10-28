# PPGI FastAPI UI

This is a lightweight FastAPI + static frontend replacement for the previous Streamlit app. It reproduces the same inputs and provides a `/api/predict` endpoint that returns a placeholder PPGI prediction. Replace the placeholder logic with your model call.

Run locally using your virtualenv `iacu`:

```bash
source iacu/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in your browser.

Notes:

-   Static frontend is in `static/` and served at `/`.
-   Replace the logic in `app/main.py` with your actual model inference logic.

## Deploying to a cloud provider

Most PaaS platforms (Render, Railway, Fly.io, Heroku-like) ask for a Start Command. Use the included portable launcher:

Start Command (portable):

```
sh ./start.sh
```

Notes:

-   Ensure `requirements.txt` includes `gunicorn` and `uvicorn[standard]`.
-   The app entrypoint is `app.main:app` (module:variable).
-   If your cloud sets a different env var for port, adapt `$PORT` accordingly.
-   A `Procfile` is included with a `web` process using this command.

## Docker (recommended for cloud)

This repo includes a `Dockerfile` that installs LightGBM’s system dependency and runs the app with Gunicorn via `start.sh`:

```
FROM python:3.13-slim
# Install OpenMP runtime required by LightGBM
RUN apt-get update \
	&& apt-get install -y --no-install-recommends libgomp1 \
	&& rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8000
ENV WEB_CONCURRENCY=2
CMD ["sh", "./start.sh"]
```

Build and run locally:

```
docker build -t ppgi-app .
docker run -p 8000:8000 ppgi-app
```

### Troubleshooting LightGBM on cloud images

If deployment fails with an error like:

```
OSError: libgomp.so.1: cannot open shared object file: No such file or directory
```

Install the OpenMP runtime in your container or build image:

-   Debian/Ubuntu: `apt-get update && apt-get install -y libgomp1`
-   Alpine Linux: `apk add --no-cache libgomp`
-   Red Hat/CentOS: `yum install -y libgomp`

Alternatively, deploy with the included Dockerfile so `libgomp1` is installed in the container.

For buildpack-based PaaS (e.g., Heroku), ensure the OpenMP runtime is installed by adding the apt buildpack and an `Aptfile` with:

```
libgomp1
```

Then place the apt buildpack before the Python buildpack.

Environment variables:

-   `PORT`: listening port (platforms set this automatically). Default 8000.
-   `WEB_CONCURRENCY`: Gunicorn worker processes. Default 2.
