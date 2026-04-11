# Hospital Management System

This project is a Flask-based hospital management system with a Vue 3 frontend mounted through a single Jinja entry page. It supports three roles:

- `admin`: manage doctors and patients
- `doctor`: manage availability, appointments, and treatments
- `patient`: sign up, book appointments, and review visit history

The app uses SQLite for persistence. Redis and Celery are optional and enable caching, background exports, reminders, and scheduled reports.

## Stack

- Backend: Flask, SQLAlchemy
- Frontend: Vue 3 via CDN, Jinja2 entry template
- Database: SQLite
- Optional services: Redis, Celery
- Optional dev tooling: Gulp + BrowserSync

## Project Structure

- `app.py`: Flask app factory and SPA entry routes
- `routes/auth.py`: login, signup, logout, and session APIs
- `routes/api_routes.py`: admin, doctor, patient, search, history, and export APIs
- `models/main_models.py`: SQLAlchemy models
- `utils/setup.py`: database initialization and first-run seeding
- `utils/sample_data.py`: demo data generation
- `celery_app.py`: Celery setup and beat schedule
- `tasks.py`: background jobs for reports, reminders, and CSV exports
- `templates/index.html`: SPA shell
- `static/js/app.js`: frontend application logic
- `static/css/style.css`: application styling
- `gulpfile.js`: optional BrowserSync live-reload proxy

## Features

- Role-based login for admin, doctor, and patient users
- Patient self-signup flow
- Department and doctor discovery
- Appointment booking, cancellation, and rescheduling
- Doctor availability management
- Patient treatment history and medicine details
- Admin search across doctors, patients, and appointments
- Background CSV exports for patient treatment history
- Scheduled daily reminders and monthly doctor activity reports

## Prerequisites

- Python `3.14+`
- `pip`
- Optional: `redis-server` for cache and Celery jobs
- Optional: `Node.js` and `npm` for BrowserSync
- Optional: `tmux` and `mailhog` if you want to use `run_linux.sh`

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/25f1002206/Hospital-Management-System-Mad-2.git
cd Hospital-Management-System-Mad-2
```

### 2. Create and activate a virtual environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the application

```bash
python app.py
```

Open `http://localhost:5000`.

## First Run Behavior

On first startup, the app automatically creates `hospital.db` and seeds demo data through `utils/setup.py`.

Seeded data includes:

- 1 admin account
- 10 departments
- 30 doctor accounts
- 100 patient accounts
- demo availability, appointments, treatments, and medicines

If `hospital.db` already exists, seeding is skipped.

## Demo Credentials

All seeded users use password `123`.

- Admin: `admin@admin.com`
- Doctor examples: `doc1@h.com`, `doc2@h.com`, `doc3@h.com`
- Patient examples: `pat1@h.com`, `pat2@h.com`, `pat3@h.com`

Patients can also create new accounts from the signup flow in the app.

## Optional Redis and Celery

Redis is not required for the core app to start, but it is required for background tasks and intended cache behavior.

Start Redis:

```bash
redis-server
```

Start the Celery worker:

```bash
celery -A celery_app.celery_app worker --loglevel=info
```

Start Celery beat for scheduled jobs:

```bash
celery -A celery_app.celery_app beat --loglevel=info
```

Background jobs include:

- daily summary report generation
- daily patient reminders
- monthly doctor activity reports
- patient treatment CSV exports

## Environment Variables

The app runs with defaults, but these variables are supported for mail, Redis, exports, and scheduler timing:

```bash
export FLASK_SECRET_KEY=change-me
export REDIS_URL=redis://localhost:6379/0
export CELERY_BROKER_URL=redis://localhost:6379/0
export CELERY_RESULT_BACKEND=redis://localhost:6379/0

export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USERNAME=your-user
export SMTP_PASSWORD=your-password
export SMTP_USE_TLS=true
export MAIL_DEFAULT_SENDER=noreply@example.com

export CELERY_TIMEZONE=Asia/Kolkata
export DAILY_REMINDER_HOUR=8
export DAILY_REMINDER_MINUTE=0
export MONTHLY_REPORT_HOUR=7
export MONTHLY_REPORT_MINUTE=0

export EXPORTS_DIR=exports
```

Notes:

- Mail delivery is skipped unless `SMTP_HOST` is configured.
- `EXPORTS_DIR` is created automatically when an export runs.
- Redis URLs default to `redis://localhost:6379/0`.

## Optional Frontend Live Reload

This project includes a minimal BrowserSync setup that proxies the Flask app on port `5001`.

Install Node dependencies:

```bash
npm install
```

Run BrowserSync:

```bash
npx gulp
```

Then use `http://localhost:5001` while Flask is running on `http://localhost:5000`.

## Linux Helper Script

`run_linux.sh` starts a `tmux` workspace with:

- Redis
- MailHog
- Flask app
- Celery worker
- Celery beat

Before using it, make sure:

- `.venv` exists and contains the installed Python dependencies
- `tmux` is installed
- `redis-server` is installed
- `mailhog` is installed and available on your `PATH`

Run it with:

```bash
bash run_linux.sh
```

## API Overview

Primary routes exposed by the app:

- `POST /api/auth/login`
- `POST /api/auth/signup`
- `POST /api/auth/logout`
- `GET /api/auth/session`
- `GET /api/app-context`
- `GET /api/dashboard`
- `GET /api/departments/<id>`
- `GET /api/search`
- `GET /api/patients/<id>/history`
- `POST /api/appointments/book`
- `POST /api/appointment/<id>/reschedule`
- `POST /api/appointment/<id>/cancel`
- `POST /api/doctor/appointment/<id>/complete`
- `POST /api/doctor/update_availability`
- `GET /api/doctor/<id>/availability_json`
- `POST /api/batch/reports/daily-summary`
- `POST /api/batch/reports/daily-reminders`
- `POST /api/batch/reports/monthly-activity`
- `GET /api/batch/tasks/<task_id>`
- `GET /api/exports`
- `POST /api/exports/treatments`
- `GET /api/exports/<id>`
- `GET /api/exports/<id>/download`

## Development Notes

- The root route `/` and non-API paths render `templates/index.html`.
- API and static paths are excluded from the SPA fallback.
- The SQLite database file is stored at `hospital.db` in the project root.
- Exported CSV files are written under `exports/`.

## Troubleshooting

### App starts but seeded users do not appear

`hospital.db` already exists, so first-run seeding was skipped. Delete the database file and restart the app if you want a fresh seeded dataset.

### Celery commands fail

Make sure Redis is running and your virtual environment is active.

### Emails are not being sent

This is expected unless valid SMTP environment variables are configured. The notification code returns without sending mail when `SMTP_HOST` is empty.

### BrowserSync does not start

Run `npm install` first to install the `gulp` and `browser-sync` dev dependencies.
