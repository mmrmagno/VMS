# VMS (Visitor Management System)

## Overview
VMS is a modern web-based visitor management system built with FastAPI and PostgreSQL. It provides an efficient way to track visitors, manage check-ins/check-outs, and maintain a secure log of all visits.

## Features
- 🔐 Visitor check-in/check-out process
- 👥 Admin dashboard for visitor management
- 🌓 Modern, responsive user interface
- 🔒 Session-based authentication
- 📱 Mobile-friendly design

## Tech Stack
- Backend: FastAPI (Python)
- Database: PostgreSQL
- Frontend: HTML, CSS, JavaScript
- Authentication: JWT tokens
- Template Engine: Jinja2

## Installation

### Prerequisites
- Python 3.12+
- PostgreSQL
- pip (Python package manager)

### Setup

1. Clone the repository
```bash
git clone https://github.com/mmrmagno/VMS.git
cd VMS
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Setup PostgreSQL
```bash
# Login as postgres user
sudo -iu postgres

# Create database and user
psql
CREATE USER yourusername WITH PASSWORD 'yourpassword';
CREATE DATABASE visitor_db OWNER yourusername;
ALTER USER yourusername WITH SUPERUSER;
GRANT ALL PRIVILEGES ON DATABASE visitor_db TO yourusername;
```

5. Create .env file
```env
DATABASE_URL=postgresql://yourusername:yourpassword@localhost:5432/visitor_db
ADMIN_USERNAME=youradminusername
ADMIN_PASSWORD=youradminpass
SECRET_KEY=yoursecretkeyhere
ENVIRONMENT=development
```

## Running the Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Project Structure
```
VMS/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── database.py
├── static/
│   └── css/
│       └── styles.css
├── templates/
│   ├── admin.html
│   ├── base.html
│   ├── check_in.html
│   ├── login.html
│   └── visitor_status.html
├── .env
├── requirements.txt
└── README.md
```

## Usage

### Visitor Flow
1. Visitors access the main page and fill in their details
2. Upon check-in, they receive a unique status page
3. Visitors can check out by using the swipe gesture
4. Session maintains security throughout the visit

### Admin Flow
1. Access admin login through the navigation
2. View all visitors in the admin dashboard
3. Perform administrative actions like manual checkout
4. Monitor current and past visitors

## Security Features
- Session-based authentication
- Secure cookie handling
- Protected admin routes
- JWT token authentication
- CSRF protection
- HTTP-only cookies

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## Author
- Your Name (@mmrmagno)

## Acknowledgments
- FastAPI for the amazing web framework
