# HealthConnect - Healthcare Management Platform

HealthConnect is a Laravel-based healthcare management Platform for connecting patients, doctors, and administrators through one appointment and prescription workflow. The application combines doctor discovery, schedule management, patient booking, booking approval, prescription records, role-based administration, notifications, and an optional machine-learning specialist recommendation service.

## What the project provides

The project currently contains:

- A public healthcare landing page with featured specialists
- Doctor search, filtering, and autocomplete endpoints for names, locations, and specialties
- Registration, login, logout, email verification, password reset, password confirmation, and profile management
- Role-based access for `admin`, `doctor`, and `patient` users
- Doctor registration requests with administrative approval or rejection
- Doctor profiles containing qualifications, specialty, experience, clinic information, consultation fees, and profile images
- Doctor-created appointment schedules with date, time, capacity, fee, status, and notes
- Patient browsing of available schedules and doctor-specific schedules
- Patient appointment booking and cancellation
- Doctor approval or rejection of appointment bookings
- Admin appointment and user management
- Prescription creation by doctors and prescription viewing/downloads by doctors and patients
- In-app database notifications for important events
- A guest symptom-prediction page backed by a separate FastAPI machine-learning service

## Main user workflows

### Guest

Guests can visit the public home page, browse featured doctors, use doctor discovery routes, and submit symptoms through the prediction form. The prediction workflow is advisory only and is intended to recommend a relevant specialist; it is not a medical diagnosis.

### Patient

Patients can register, verify their email, update their profile, browse doctors and schedules, book available appointments, cancel their own bookings, and view or download prescriptions associated with their appointments.

### Doctor

Doctors can submit or maintain their professional profile, create and manage appointment schedules, review bookings, approve or reject patient requests, and create or download prescriptions for completed consultations.

### Admin

Administrators can view dashboard statistics, approve or reject doctor registration requests, manage users, review and update appointments, manage doctor specialties, and view notification information.

## Technology stack

- PHP 8.2+
- Laravel 12
- Laravel Breeze authentication
- Laravel Octane support
- Blade templates for the primary web interface
- Inertia.js v2 with Vue 3 for selected frontend pages
- Tailwind CSS 3 and Vite
- MySQL/MariaDB by default
- PHPUnit 11 for automated tests
- Optional Python FastAPI service for machine-learning predictions

## Repository structure

```text
app/
├── Http/
│   ├── Controllers/
│   │   ├── Admin/
│   │   ├── Auth/
│   │   ├── Doctor/
│   │   ├── Guest/
│   │   └── Patient/
│   ├── Middleware/
│   └── Requests/
├── Models/
├── Notifications/
└── Providers/
bootstrap/                 Laravel application bootstrap and middleware aliases
config/                    Application and service configuration
database/
├── factories/
├── migrations/
└── seeders/
resources/
├── css/
├── js/                    Vue/Inertia entry point and pages
└── views/                 Blade layouts, pages, and components
routes/
├── auth.php
└── web.php
Healthcare_training_ml/    Optional Python training and prediction service
tests/                     PHPUnit feature and unit tests
```

## Requirements

Install the following before setting up the application:

- PHP 8.2 or newer with PDO, OpenSSL, Mbstring, Tokenizer, XML, Ctype, JSON, and Fileinfo
- Composer
- Node.js and npm
- MySQL or MariaDB
- Git
- Python 3.10+ and `pip` if the ML service will be used

## Local Laravel setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd Hms1
```

### 2. Install dependencies

```bash
composer install
npm install
```

### 3. Create and configure the environment

```bash
cp .env.example .env
php artisan key:generate
```

Update the database values in `.env`:

```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=hms1
DB_USERNAME=root
DB_PASSWORD=
```

The default environment also uses database-backed sessions, cache, and queues. Run the migrations before starting the application.

### 4. Create the database schema and seed demo data

```bash
php artisan migrate --seed
```

The default `DatabaseSeeder` calls `BangladeshiDoctorSeeder`, which creates sample doctor records and specialties. `AdminSeeder` is available separately but is not called automatically by `DatabaseSeeder`; run it explicitly only when an administrator account is needed:

```bash
php artisan db:seed --class=AdminSeeder
```

For a full development reset:

```bash
php artisan migrate:fresh --seed
```

### 5. Link public storage

```bash
php artisan storage:link
```

### 6. Start the application

For a simple Laravel server:

```bash
php artisan serve
```

In a second terminal, start the Vite development server:

```bash
npm run dev
```

Alternatively, the Composer development script starts the Laravel server, database queue listener, and Vite together:

```bash
composer run dev
```

Open the application at `http://127.0.0.1:8000`.

## Frontend commands

Run the Vite development server with hot reload:

```bash
npm run dev
```

Create an optimized production asset build:

```bash
npm run build
```

## Machine-learning service

The [`Healthcare_training_ml`](./Healthcare_training_ml) directory is a separate Python component of HMS1. It contains the healthcare training dataset, a model-training and evaluation workflow, SHAP explainability analysis, serialized model files in `saved_models/`, and a FastAPI inference application in `main.py`. The service accepts symptoms and basic patient details, returns matched and unmatched symptoms, predicts likely diseases, assigns confidence and urgency levels, and maps predictions to recommended specialists.

### Run the ML API

```bash
cd Healthcare_training_ml
python -m venv .venv
```

Activate the environment:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the pinned API dependencies and start FastAPI:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Useful endpoints:

- `GET /health` - service and loaded-model status
- `GET /symptoms` - supported symptom names
- `GET /specialists` - available specialist recommendations
- `POST /predict` - symptom-based prediction
- `GET /docs` - interactive Swagger documentation

The Laravel controller currently calls `http://127.0.0.1:5000/predict`. If the FastAPI service runs on another port, update the Laravel prediction service URL or run FastAPI on the configured port. Keep the ML service separate from the Laravel server to avoid port conflicts.

The current Laravel and FastAPI prediction contracts are not completely identical: Laravel submits symptoms, age, and gender only, while FastAPI also supports blood group, division, and `top_n`; Laravel accepts `Other` as a gender value, while the checked-in FastAPI validator accepts only `Male` and `Female`; and the response field names consumed by Laravel differ from the fields returned by FastAPI. Treat the integration as an active development feature and verify both sides of the contract before relying on production predictions.

The training notebook/script requires additional data-science packages, including pandas, matplotlib, seaborn, and SHAP. It is intended for model development and evaluation; the saved models and `main.py` are the runtime prediction path.

## Testing and code quality

Run the PHPUnit suite:

```bash
php artisan test --compact
```

Run one test file or filter:

```bash
php artisan test --compact tests/Feature/Auth/AuthenticationTest.php
php artisan test --compact --filter=test_users_can_authenticate_using_the_login_screen
```

Format modified PHP files with Laravel Pint:

```bash
vendor/bin/pint --dirty
```

The current automated tests primarily cover authentication, email verification, password flows, profile management, and baseline application responses. Appointment, prescription, admin, and ML integration flows should be covered with additional feature and integration tests as the project evolves.

## Useful Artisan commands

```bash
php artisan route:list
php artisan migrate:status
php artisan db:seed
php artisan storage:link
php artisan optimize:clear
php artisan queue:listen --tries=1
```

## Configuration and operational notes

- Do not commit `.env`, credentials, or generated production keys.
- Configure mail settings before relying on email verification or password-reset delivery. The example environment uses the log mailer for local development.
- The application uses the database queue connection by default; run a queue worker when queued work is enabled.
- The prediction service should be treated as an assistive recommendation feature, not a replacement for professional medical evaluation.
- Review and restrict CORS origins in `Healthcare_training_ml/main.py` before deploying the ML API publicly.
- Change seeded credentials and review all demo data before using the application outside local development.
- The checked-in `DatabaseSeeder` loads the doctor demo seeder but does not automatically call `AdminSeeder`; create an administrator explicitly when setting up a local environment.
- The frontend is hybrid: Blade is the primary UI, while selected patient and admin surfaces use Inertia/Vue.

## Docker

The repository includes a `Dockerfile` and `docker-compose.yaml` for container-based development. Review the service names, ports, volume mounts, database configuration, and application commands in those files before use, then run:

```bash
docker compose up --build
```

After the containers are ready, run the required Laravel setup commands inside the application container:

```bash
docker compose exec <app-service> php artisan migrate --seed
docker compose exec <app-service> php artisan storage:link
```

## Contributing

1. Create a feature branch.
2. Implement the change with validation and authorization.
3. Add or update PHPUnit coverage.
4. Run the relevant tests and `vendor/bin/pint --dirty`.
5. Open a pull request with a clear description and testing notes.

```bash
git checkout -b feature/your-feature
```

## License

No project-specific license has been declared. Confirm the intended license and update this section before distributing or reusing the project.
