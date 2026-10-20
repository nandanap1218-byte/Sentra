# SENTRA — User & Access Management System

SENTRA is a web-based user and access management application designed to manage users, roles, permissions, and audit activities through a centralized dashboard. It uses a Django REST Framework backend and a React frontend.

## Features

- **Authentication:** User registration, login, logout, token refresh, and current-user information.
- **Dashboard:** Overview of users, active users, roles, permissions, and recent audit activity.
- **User Management:** View, search, create, update, and manage users.
- **Role Management:** Manage system roles and custom roles.
- **Permission Management:** Control access to features based on assigned permissions.
- **Role Assignment:** Assign roles to users according to access permissions.
- **Audit Logs:** Track important activities, including authentication and changes to users and roles.
- **Protected Routes:** Restrict access to application pages based on authentication.
- **Responsive Interface:** A clean dashboard built with React.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React |
| Frontend tooling | Vite |
| Backend | Python, Django |
| REST API | Django REST Framework |
| Authentication | JWT |
| Database | SQLite |
| HTTP client | Axios |
| Version control | Git and GitHub |

## Project Structure

```text
SENTRA/
├── backend/
│   ├── config/
│   ├── users/
│   │   ├── management/
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── permissions.py
│   │   ├── serializers.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   └── manage.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── components/
│   │   └── pages/
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Prerequisites

Install the following before running SENTRA:

- Python
- Node.js and npm
- Git

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/nandanap1218-byte/Sentra.git
cd Sentra
```

### 2. Set up the backend

Open a terminal in the project root.

Create and activate a Python virtual environment:

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install the backend dependencies:

```powershell
cd backend
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers
```

Apply database migrations:

```powershell
python manage.py migrate
```

Start the Django development server:

```powershell
python manage.py runserver
```

The backend will normally be available at:

`http://127.0.0.1:8000/`

Keep this terminal running.

> Note: Use your project's complete dependency list if one is available. Configure the required Django settings, CORS, cookie security, and environment variables before running the application in another environment.

### 3. Set up the frontend

Open a second terminal in the project root and run:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite in your terminal. It is commonly:

`http://localhost:5173/`

## Authentication and Access Control

SENTRA uses JWT-based authentication and permission-based access control.

- Access tokens are used to authorize API requests.
- Refresh tokens are handled through an HTTP-only cookie in the configured authentication flow.
- Roles determine which permissions a user receives.
- Protected frontend routes restrict access to authenticated users.
- Audit logs record selected application activities.

Available roles and permissions depend on the configured database and role-seeding process.

## Development

To run SENTRA locally, keep the Django backend and Vite frontend running in separate terminals.

Before making changes, check the project's current configuration and dependencies. Never commit environment secrets, production credentials, or local database files to GitHub.

## Future Improvements

Potential improvements include:

- Automated testing for authentication and permissions.
- Enhanced reporting and audit-log filtering.
- Additional security and deployment configuration.
- Production deployment and database configuration.

## Author

**SENTRA Project**

Repository: https://github.com/nandanap1218-byte/Sentra

## License

No license has been specified yet. All rights are reserved by default unless a license is added to this repository.
