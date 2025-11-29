# CliniTrak — Hospital Management System

CliniTrak is a full-stack Hospital Management System (HMS) built using Flask, SQLite, SQLAlchemy ORM, Bootstrap, and Jinja2. It provides operational workflows for Admins, Doctors, and Patients, including appointment scheduling, departmental management, patient history, and availability handling.

This project is fully modular, organized using Flask Blueprints, and includes a supporting REST-style API for asynchronous front-end interactions.

---

## Features Overview

### Admin

* Manage departments, doctors, and patients
* View and audit all appointments
* Blacklist or unblacklist users
* Adjust doctor availability
* Global search across system data

### Doctor

* View upcoming appointments
* Update patient history
* Reschedule appointments
* Manage availability slots

### Patient

* Book new appointments
* Reschedule or cancel existing ones
* View medical history
* Manage profile details

---

## Technology Stack

| Technology         | Purpose                                  |
| ------------------ | ---------------------------------------- |
| Flask              | Backend framework                        |
| SQLite             | Database                                 |
| SQLAlchemy         | ORM for Python–DB mapping                |
| Jinja2             | Templating engine                        |
| Bootstrap 5        | Styling and layout                       |
| Chart.js           | Dashboard charts                         |
| BrowserSync + Gulp | Front-end auto-reload during development |

---

## Project Structure

```
Hospital-Management-System/
│
├── app.py
├── gulpfile.js
├── hospital.db
├── package.json
├── package-lock.json
├── requirements.txt
├── README.md
├── .gitignore
│
├── models/
│   └── main_models.py
│
├── routes/
│   ├── __init__.py
│   ├── api_routes.py
│   ├── auth.py
│   └── dashboard.py
│
├── services/
│   └── doctor_service.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── Resources/
│
├── templates/
│   ├── admin/
│   │   ├── new_doctor.html
│   │   └── patient_update.html
│   │
│   ├── components/
│   │   ├── availability_modal.html
│   │   └── doctor_modal.html
│   │
│   ├── dashboard/
│   │   └── (dashboard templates...)
│   │
│   ├── doctor/
│   │   └── (doctor templates...)
│   │
│   ├── patient/
│   │   ├── base.html
│   │   ├── base_account_login.html
│   │   ├── index.html
│   │   ├── login.html
│   │   └── signup.html
│
└── utils/
    ├── constants.py
    ├── helper_functions.py
    ├── sample_data.py
    └── setup.py
```

---

## API Routes (Important Endpoints)

The project is organized into modular Flask blueprints:

### **Authentication**

* `/login` – login
* `/logout` – logout
* `/signup` – patient registration

### **Dashboard**

* `/dashboard` – loads Admin / Doctor / Patient dashboard based on role

### **Admin**

* `/admin/new/doctor` – add doctor
* `/admin/edit/doctor/<id>` – edit doctor
* `/admin/new/patient` – add patient
* `/admin/edit/patient/<id>` – edit patient

### **Doctor**

* `/doctor/update_history/<appointment_id>` – update patient treatment
* `/doctor/edit` – edit own profile (redirects to admin edit)

### **Patient**

* `/patient/department/<id>` – view department
* `/patient/edit/profile` – edit profile

### **API (`/api/...`)**

* `/api/<entity>/all` – list doctors/patients/appointments
* `/api/book_appointment` – book appointment
* `/api/appointment/<id>/reschedule`
* `/api/appointment/<id>/cancel`
* `/api/doctor/update_availability`
* `/api/doctor/<id>/availability_json`
* `/api/search` – admin/patient search
* `/api/blacklist/<entity>/<id>`
* `/api/unblacklist/<entity>/<id>`


---

## Running the Project

### 1. Install Dependencies

The project uses a standard `requirements.txt` file.

Install everything using:

```bash
pip install -r requirements.txt
```

If using a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Running the Flask Application

Run the development server:

```bash
python app.py
```

The backend will run on:

```
http://localhost:5000
```

---

## Gulp + BrowserSync Auto-Reload Setup

This project includes a Gulp pipeline for automatic page reload during development.
Files watched include:

* All HTML templates
* Static CSS and JS files
* Python source files

### Running Gulp

Install Node dependencies once:

```bash
npm install
```

Run BrowserSync:

```bash
gulp
```

Now access:

```
http://localhost:5001
```

BrowserSync will proxy Flask’s server and automatically reload the browser when templates, static files, or Python files change.
