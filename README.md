# AI-Powered Customer Query Management System

A Django REST API to manage customer queries. Users can register, log in, add queries, update them, change their status and run AI analysis on them. The AI (Google Gemini) finds the category, the priority and writes a short suggested reply. If Gemini is not available, a simple keyword based fallback is used so the API keeps working.

## Tech Stack

- Python 3.11+ (tested on 3.13)
- Django 5.2
- Django REST Framework (Token Authentication)
- SQLite
- Google Gemini API (called with `requests`)
- drf-spectacular for Swagger docs

## Project Structure

```
assignment/
    core/            project settings and main urls
    accounts/        register, login, logout
    queries/         customer query model, APIs, AI service, tests
        ai_service.py    Gemini call + response parsing + fallback
    frontend/        simple HTML pages + JS that call the API
    API.md           endpoint docs with sample requests/responses
    AI_INTEGRATION.md  short explanation of the AI part
    requirements.txt
    .env.example
```

## Setup

1. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac / Linux
```

2. Install packages

```bash
pip install -r requirements.txt
```

3. Create the `.env` file

```bash
copy .env.example .env       # Windows
cp .env.example .env         # Mac / Linux
```

Open `.env` and put your Gemini API key in `GEMINI_API_KEY`. You can get a free key from https://aistudio.google.com/app/apikey. The project still runs without a key, it will just use the fallback analysis.

4. Run migrations and start the server

```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin
python manage.py runserver
```

Server runs on http://127.0.0.1:8000

## Web UI

A basic UI is included. After starting the server open http://127.0.0.1:8000/ and register or login.

Pages: login, register, query list (dashboard counts, search, filters, pagination), add / edit query, query details (run AI analysis, change status, delete).

The pages are plain HTML. A small JavaScript file (`frontend/static/frontend/app.js`) calls the same `/api/` endpoints with `fetch()` and keeps the token in `localStorage`, so all validation and logic stays in the API.

## How to Use the API

1. Register at `POST /api/register/` or login at `POST /api/login/`. Both return a token.
2. Send the token in every request header:

```
Authorization: Token <your_token>
```

3. Swagger docs: http://127.0.0.1:8000/api/docs/ (click Authorize and enter `Token <your_token>`)

Full endpoint list with examples is in [API.md](API.md).

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/register/ | Register new user |
| POST | /api/login/ | Login, returns token |
| POST | /api/logout/ | Logout (deletes token) |
| POST | /api/queries/ | Create query |
| GET | /api/queries/ | List queries (search, filter, pagination) |
| GET | /api/queries/{id}/ | Query details |
| PUT / PATCH | /api/queries/{id}/ | Update query |
| DELETE | /api/queries/{id}/ | Delete query |
| PATCH | /api/queries/{id}/status/ | Update only the status |
| POST | /api/queries/{id}/analyze/ | Run AI analysis |
| GET | /api/dashboard/ | Total, pending, in progress, resolved counts |

## Bonus Features Done

- Search by customer name or email (`?search=`)
- Filter by category, priority, status (`?category=Billing&priority=High&status=Pending`)
- Pagination (10 per page, `?page=2`)
- Dashboard API with counts
- Unit tests for APIs and AI parsing
- Fallback when AI service is not available

## Running Tests

```bash
python manage.py test
```

The tests mock the Gemini call, so no API key or internet is needed.

## Notes

- Each user only sees the queries they created.
- API keys and the secret key are read from `.env` file.
