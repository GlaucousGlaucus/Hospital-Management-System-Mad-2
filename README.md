# CliniTrak

CliniTrak is now structured as a Flask API with a Vue 3 single-page frontend mounted from one Jinja2 entry template. The active stack is:

- Flask for the API layer
- Vue 3 via CDN for the UI
- Jinja2 only for the SPA entry point
- Custom theme CSS in `static/css/style.css` for layout and styling
- SQLite through SQLAlchemy for persistence
- Redis for cache storage
- Redis + Celery for background batch jobs

## Architecture

- `templates/index.html`: the only active template entry point
- `static/js/app.js`: Vue application for auth, dashboards, forms, history, and scheduling
- `routes/auth.py`: logout route plus JSON auth endpoints
- `routes/api_routes.py`: API-first business endpoints for admin, doctor, and patient workflows
- `tasks.py`: Celery batch task for a daily operational summary
- `tasks.py`: Celery beat schedules for reminders and monthly reports, plus async patient CSV exports
- `utils/cache.py`: Redis-backed caching helpers with graceful fallback if Redis is unavailable

## Primary API Endpoints

- `POST /api/auth/login`
- `POST /api/auth/signup`
- `POST /api/auth/logout`
- `GET /api/app-context`
- `GET /api/dashboard`
- `GET /api/departments/<id>`
- `GET /api/patients/<id>/history`
- `GET/PUT /api/appointments/<id>/history`
- `POST /api/appointments/book`
- `POST /api/appointment/<id>/reschedule`
- `POST /api/appointment/<id>/cancel`
- `POST /api/doctor/appointment/<id>/complete`
- `POST /api/doctor/update_availability`
- `GET /api/doctor/<id>/availability_json`
- `GET /api/search`
- `POST /api/batch/reports/daily-summary`
- `POST /api/batch/reports/daily-reminders`
- `POST /api/batch/reports/monthly-activity`
- `GET /api/batch/tasks/<task_id>`
- `GET /api/exports`
- `POST /api/exports/treatments`
- `GET /api/exports/<id>`
- `GET /api/exports/<id>/download`

## Run

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Start Flask:

```bash
python app.py
```

Optional Redis + Celery setup for cache and batch jobs:

```bash
redis-server
celery -A celery_app.celery_app worker --loglevel=info
celery -A celery_app.celery_app beat --loglevel=info
```

Useful environment variables:

```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USERNAME=your-user
export SMTP_PASSWORD=your-password
export MAIL_DEFAULT_SENDER=noreply@example.com
export GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/...
export DAILY_REMINDER_HOUR=8
export DAILY_REMINDER_MINUTE=0
export MONTHLY_REPORT_HOUR=7
export MONTHLY_REPORT_MINUTE=0
```

Then open `http://localhost:5000`.
