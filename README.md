# Intelligent Healthcare Platform — HMS1 (Laravel)

Intelligent Healthcare Platform (HMS1) is a Laravel-based application providing a feature-rich appointment and prescription management system with admin, doctor, and patient roles. It includes scheduling, booking, prescription workflows, notifications, and an integrated prediction endpoint for guest users.

## Quick overview

- **Project name:** Intelligent Healthcare Platform (HMS1)
- **Framework:** Laravel 12
- **PHP:** 8.2+
- **Frontend:** Vite + Tailwind + Inertia (assets in `resources/js`, `resources/css`)
- **Database:** MySQL / MariaDB (default), migrations and seeders provided
- **Primary domain:** appointment scheduling, doctor & clinic management, prescriptions, patient workflows, and basic predictive features


## Implemented features

- Role-based authentication and user management (Admin, Doctor, Patient)
- Admin dashboard: manage users, specializations, and appointments
- Doctor dashboard: manage schedules, view bookings, create prescriptions, and respond to requests
- Patient flows: browse doctors by specialization, book appointments, view prescriptions
- Appointment scheduling: doctors define `AppointmentSchedule` slots; patients create `AppointmentBooking`s
- Booking & request handling: booking lifecycle and request management
- Prescription management: doctors create prescriptions and patients can view them
- Guest prediction endpoint: basic prediction controller for demo/ML integrations (`Guest/PredictionController`)
- Notifications: in-app or queued notifications for key events
- Full auth features: registration, login, email verification, password reset
- Database seeders and factories for demo data (doctors, users)

## Requirements

- PHP 8.2+ with required extensions (PDO, OpenSSL, Mbstring, Tokenizer, XML, Ctype, JSON)
- Composer
- Node.js (16+) and npm or yarn
- A database (MySQL / MariaDB / Postgres supported via config)
- Optional: Docker & Docker Compose (dev convenience)

## Quick install (local)

1. Clone the repository:

```bash
git clone <your-repo-url>
cd Hms1
```

2. Copy environment file and set values:

```bash
cp .env.example .env
# Edit .env and set DB_DATABASE, DB_USERNAME, DB_PASSWORD, APP_URL, etc.
```

3. Install PHP dependencies and Node packages:

```bash
composer install --no-interaction --prefer-dist
npm install
```

4. Generate app key and run migrations + seeders:

```bash
php artisan key:generate
php artisan migrate --seed
```

5. Create storage symlink and build assets:

```bash
php artisan storage:link
npm run dev   # or `npm run build` for production
```

6. Run the app locally:

```bash
php artisan serve --host=127.0.0.1 --port=8000
# or use Docker Compose (see below)
```

## Docker (optional)

This project includes a `docker-compose.yaml` that can be used for a containerized dev environment.

```bash
# Build and start services
docker compose up --build -d
# Then exec into the app container to run migrations, composer, etc.
docker compose exec app php artisan migrate --seed
```

## Running tests

Run the project's PHPUnit test suite (or filter to specific tests while developing):

```bash
php artisan test --compact
# or to run a single test file
php artisan test --filter=SomeTestName
```

## Common artisan commands

- `php artisan migrate` — Run database migrations
- `php artisan db:seed` — Run seeders
- `php artisan tinker` — Interactively test models and code
- `php artisan route:list` — View registered routes

## Project structure (high level)

- `app/Models` — Eloquent models (User, Doctor, Appointment, AppointmentSchedule, AppointmentBooking, Prescription)
- `app/Http/Controllers` — HTTP controllers
- `app/Http/Requests` — Form request validation classes
- `database/migrations` — Migrations that define the schema
- `database/seeders` — Seeders to populate example data
- `resources/js` & `resources/css` — Frontend assets (Vite + Tailwind)
- `routes/web.php`, `routes/auth.php` — Route definitions

## Database & Seeders

The repository includes migrations for users, doctors, appointments, appointment schedules, bookings, and prescriptions. Seeders provide sample users and doctors to simplify local testing.

If you need to reset the DB during development:

```bash
php artisan migrate:fresh --seed
```

## Notes for reviewers / employers

- This project is included in my portfolio to demonstrate a Laravel-based CRUD and scheduling system with migrations, seeders, authorization, and front-end integration.
- Key implemented features: user registration, doctor management, appointment schedules, booking flow, prescription creation.

## Contribution and development

If you'd like to contribute or extend the project:

- Fork the repository
- Create a feature branch
- Open a pull request with a clear description and tests for new features

## Useful links & commands

- Build assets (dev): `npm run dev`
- Build assets (prod): `npm run build`
- Format PHP code (Pint): `vendor/bin/pint` (project requires Pint)

## Contact

If you want to see this project running or want more details for my CV, reach me via the contact info on my GitHub profile.

---
_README generated for portfolio use. Edit environment-sensitive values in `.env` before deploying._
<p align="center"><a href="https://laravel.com" target="_blank"><img src="https://raw.githubusercontent.com/laravel/art/master/logo-lockup/5%20SVG/2%20CMYK/1%20Full%20Color/laravel-logolockup-cmyk-red.svg" width="400" alt="Laravel Logo"></a></p>

<p align="center">
<a href="https://github.com/laravel/framework/actions"><img src="https://github.com/laravel/framework/workflows/tests/badge.svg" alt="Build Status"></a>
<a href="https://packagist.org/packages/laravel/framework"><img src="https://img.shields.io/packagist/dt/laravel/framework" alt="Total Downloads"></a>
<a href="https://packagist.org/packages/laravel/framework"><img src="https://img.shields.io/packagist/v/laravel/framework" alt="Latest Stable Version"></a>
<a href="https://packagist.org/packages/laravel/framework"><img src="https://img.shields.io/packagist/l/laravel/framework" alt="License"></a>
</p>

