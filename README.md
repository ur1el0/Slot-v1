# SlotV1

SlotV1 is a Django appointment-booking platform with public service browsing, user accounts, appointment scheduling, and staff tools for managing services, schedules, and bookings.

## Features

- User registration, login, logout, and dashboard views
- Service listing with active/inactive control
- Schedule-based appointment booking with slot limits
- Appointment history and cancellation for users
- Staff dashboard for managing services, schedules, and appointments
- REST API endpoints for user and admin workflows

## Tech Stack

- Django
- Django REST Framework
- Django templates and static assets
- MySQL in the current project settings

## Project Structure

- `manage.py` - Django command entry point
- `SlotV1/` - Project settings, URL routing, and ASGI/WSGI config
- `slot/` - Main app with models, forms, views, API views, templates, and static files

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure the database settings in `SlotV1/settings.py` for your local environment.
4. Apply migrations:

```bash
python manage.py migrate
```

5. Create an admin user:

```bash
python manage.py createsuperuser
```

6. Start the server:

```bash
python manage.py runserver
```

## Main Pages

- `/` - Home page
- `/login/` - Login page
- `/register/` - Registration page
- `/dashboard/` - User dashboard
- `/services/` - Active service listings
- `/book/` - Appointment booking form
- `/appointments/` - User appointment history
- `/admin-dashboard/` - Staff dashboard
- `/manage-services/` - Service management
- `/manage-schedules/` - Schedule management
- `/manage-appointments/` - Appointment management

## API Endpoints

The API is mounted under `/api/` and is split into user and admin routes:

- `/api/user/services/`
- `/api/user/schedules/`
- `/api/user/slots/`
- `/api/admin/services/`
- `/api/admin/schedules/`
- `/api/admin/slots/`

## Notes

- The project currently uses the database configuration defined in `SlotV1/settings.py`.
- If you want to use SQLite or another database locally, update the Django settings first.