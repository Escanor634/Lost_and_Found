# Campus Lost & Found Web Application

A centralized, responsive web application designed for college campuses to help students, faculty, and campus security report, catalog, and recover lost and found belongings.

---

## Tech Stack

- **Backend**: Python 3, Flask (Application Factory & Blueprints), Flask-Login, Flask-WTF, Flask-SQLAlchemy, Flask-Migrate, Werkzeug
- **Database**: SQLite (managed via SQLAlchemy & Alembic)
- **Frontend**: HTML5, CSS3, Bootstrap 5, Bootstrap Icons
- **Testing**: pytest
- **Configuration**: python-dotenv, environment-based configuration classes

---

## Project Structure

```text
Lost_and_Lost/
├── app/
│   ├── __init__.py           # Application factory, blueprints, core routes
│   ├── extensions.py         # SQLAlchemy, Migrate, LoginManager, CSRF instances
│   ├── models/               # Database models package
│   │   ├── __init__.py       # Exports User, Item, Claim, Notification
│   │   ├── user.py           # User entity (student & admin roles, UserMixin, password hashing)
│   │   ├── item.py           # Item entity (lost/found reports)
│   │   ├── claim.py          # Claim entity (proof, lifecycle, duplicate prevention)
│   │   └── notification.py   # Notification entity (alerts & links)
│   ├── auth/                 # Authentication blueprint package
│   │   ├── __init__.py       # Blueprint definition & route registration
│   │   ├── forms.py          # WTForms registration and login forms
│   │   ├── routes.py         # Registration, login, logout, dashboard, profile
│   │   ├── decorators.py     # Role and admin authorization decorators
│   │   └── utils.py          # Safe redirect URL validator
│   ├── items/                # Items management blueprint package
│   │   ├── __init__.py       # Blueprint definition & route registration
│   │   ├── forms.py          # WTForms item reporting and editing forms
│   │   ├── routes.py         # Report (lost/found), browse, detail, edit, my-items
│   │   └── utils.py          # Secure image content verification and file management
│   ├── claims/               # Claims & verification blueprint package
│   │   └── __init__.py
│   ├── notifications/        # Notifications blueprint package
│   │   └── __init__.py
│   ├── admin/                # Admin & moderation blueprint package
│   │   └── __init__.py
│   ├── templates/            # Jinja2 HTML templates
│   │   ├── base.html         # Base template with Bootstrap 5 navbar, auth links & layout
│   │   ├── index.html        # Responsive homepage with active report & catalog links
│   │   ├── auth/             # Authentication templates
│   │   │   ├── login.html    # Login page
│   │   │   ├── register.html # Registration page
│   │   │   ├── dashboard.html# Student dashboard
│   │   │   └── profile.html  # Profile view
│   │   └── items/            # Items management templates
│   │       ├── report_choice.html # Report type selector
│   │       ├── report.html   # Lost/found item submission form
│   │       ├── browse.html   # Paginated lost and found directories
│   │       ├── detail.html   # Detailed item view with reporter info
│   │       ├── edit.html     # Report edit and photo management form
│   │       └── my_items.html # Personal reports management dashboard
│   └── static/               # Static assets
│       ├── css/
│       │   └── style.css     # Custom styles
│       ├── js/
│       │   └── main.js       # Client-side JavaScript
│       └── uploads/          # Uploaded item photographs (git-ignored)
├── migrations/               # Alembic database migration scripts
├── tests/                    # Automated test suite
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures (app, client, runner)
│   ├── test_app.py           # Tests for factory, homepage, health, init-db
│   ├── test_models.py        # Comprehensive tests for models, constraints & FKs
│   ├── test_auth.py          # Tests for auth, registration, login, logout, roles, CSRF
│   ├── test_ui.py            # Tests for responsive UI, navigation states, accessibility
│   └── test_items.py         # Tests for report forms, Pillow validation, browse & edit

├── instance/                 # Instance folder (SQLite database, git-ignored)
├── config.py                 # Configuration classes (Development, Testing, Production)
├── gunicorn.conf.py          # Production Gunicorn WSGI configuration
├── render.yaml               # Render Blueprint configuration for free web service
├── run.py                    # Application entry point script
├── requirements.txt          # Python dependencies
├── .env.example              # Sample environment variable definitions
├── .gitignore                # Git ignore rules
├── PROJECT_STATUS.md         # Stage tracking and project roadmap
└── README.md                 # Project documentation
```

---

## Getting Started

### Prerequisites

- Python 3.10+ (Python 3.12 recommended)
- `pip` (Python package manager)

### 1. Create and Activate Virtual Environment

From the project root directory, create a virtual environment:

```bash
python3 -m venv .venv
```

Activate the virtual environment:

- **Linux / macOS**:
  ```bash
  source .venv/bin/activate
  ```
- **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

### 2. Install Dependencies

Install all required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file from the provided `.env.example`:

```bash
cp .env.example .env
```

You can customize values in `.env`:

```env
FLASK_APP=run.py
FLASK_DEBUG=1
FLASK_CONFIG=development
SECRET_KEY=your-secure-random-secret-key
DATABASE_URL=sqlite:///lost_and_found.db
```

### 4. Database Initialization

Initialize the SQLite database using the built-in Flask CLI command:

```bash
flask init-db
```

Or via Python:

```bash
python -c "from app import create_app, init_db; init_db(create_app())"
```

This creates the SQLite database file inside the `instance/` folder.

### 5. Run the Application

Start the development server using either method:

**Method A: Using `run.py`**
```bash
python run.py
```

**Method B: Using Flask CLI**
```bash
flask run --port=5000
```

Once running, access the application in your browser:
- Homepage: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- Health Check: [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health)

### 6. Run the Test Suite

Execute all tests using `pytest`:

```bash
pytest -v
```

All tests should pass.

---

## Health Check Endpoint

- **Endpoint**: `GET /health`
- **Response**: `200 OK`
- **Format**: JSON
- **Sample Payload**:
  ```json
  {
    "service": "campus-lost-and-found",
    "status": "healthy"
  }
  ```

---

## Deploying to Render (Free Web Service)

This application is fully prepared for fast deployment to Render's **Free Web Service** tier using Gunicorn and automated database migrations.

> [!NOTE]
> **Free Tier Ephemeral Filesystem Notice**:
> Render's free tier uses an ephemeral filesystem without persistent disks. SQLite database records and uploaded photographs are stored in the service instance filesystem. Any data created during testing will be reset whenever the service instance spins down due to inactivity (after ~15 minutes of idle time) or is redeployed. This is completely standard and suitable for temporary academic project demonstrations.

### Option A: Automated Deployment via `render.yaml` (Recommended)

1. Push your repository to GitHub or GitLab.
2. Log into your [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** $\rightarrow$ **Blueprint**.
4. Connect your repository. Render will automatically detect [`render.yaml`](file:///home/anu/Desktop/Lost_and_Lost/render.yaml) and configure:
   - **Service Name**: `campus-lost-and-found`
   - **Environment**: `Python`
   - **Plan**: `Free`
   - **Build Command**: `pip install -r requirements.txt && flask db upgrade`
   - **Start Command**: `gunicorn run:app`
   - **Health Check Path**: `/health`
   - **Environment Variables**:
     - `FLASK_CONFIG`: `production`
     - `FLASK_DEBUG`: `false`
     - `SECRET_KEY`: Automatically generated cryptographically secure key
     - `PYTHON_VERSION`: `3.12.3`
5. Click **Apply**. Render will automatically run the build, apply the database schema via migrations, start Gunicorn, and allocate a public HTTPS URL (e.g. `https://campus-lost-and-found.onrender.com`).

---

### Option B: Manual Web Service Setup via Render Dashboard

If you prefer to configure the Web Service manually:

1. **Push your code to GitHub**:
   Ensure all files (including `requirements.txt`, `gunicorn.conf.py`, `render.yaml`) are pushed to your remote repository.
2. **Create New Web Service**:
   - In the Render Dashboard, click **New +** $\rightarrow$ **Web Service**.
   - Connect your GitHub repository.
3. **Configure Service Settings**:
   - **Name**: `campus-lost-and-found` (or your preferred name)
   - **Region**: Choose the region closest to you (e.g. `Oregon (US West)` or `Frankfurt (EU)`)
   - **Branch**: `main` (or your default branch)
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && flask db upgrade
     ```
   - **Start Command**:
     ```bash
     gunicorn run:app
     ```
   - **Instance Type**: `Free`
4. **Configure Environment Variables**:
   Under the **Environment Variables** tab, add the following key-value pairs:
   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `SECRET_KEY` | *(Click "Generate" or paste a random string)* | Required for session & CSRF security |
   | `FLASK_CONFIG` | `production` | Enforces production mode and disables debug mode |
   | `FLASK_DEBUG` | `false` | Explicitly disables Flask debug reloader |
   | `PYTHON_VERSION` | `3.12.3` | Matches runtime Python version |
5. **Set Health Check Path**:
   Under **Advanced** $\rightarrow$ **Health Check Path**, enter:
   ```text
   /health
   ```
6. **Deploy**:
   Click **Create Web Service**.

---

### Verification After Deployment

Once Render finishes deploying:
1. **Health Check**:
   Open `https://<your-service-name>.onrender.com/health` in your browser. It should return HTTP 200 with:
   ```json
   {
     "service": "campus-lost-and-found",
     "status": "healthy"
   }
   ```
2. **Homepage**:
   Open `https://<your-service-name>.onrender.com/` to verify the homepage renders with the navigation bar, categories, and report actions.
3. **Registration & Reporting**:
   - Register a new student account at `/auth/register`.
   - Log in and report a lost or found item.
   - Browse listings at `/items/lost` and `/items/found`.

---

## Current Status

- **Stage 1 (Project Setup & Architecture)**: Completed
- **Stage 2 (Database Design & Models)**: Completed
- **Stage 3 (User Authentication & Roles)**: Completed
- **Stage 4 (Frontend UI and Dashboard)**: Completed
- **Stage 5 (Lost & Found Item Management)**: Completed
- **Deployment Preparation**: Ready for Render Free Tier (WSGI Gunicorn + SQLite Alembic Migrations)

