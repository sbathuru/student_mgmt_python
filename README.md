# Student Management System (Python backend)

A Flask-based backend API for student management, now separated from the React frontend. The API is implemented in `src/app.py` and persists student records to an Oracle database using the connection settings from `.env`.

## Project structure

```text
app.py
src/
  __init__.py
  app.py
  db_interface.py
  models.py
  student_service.py
requirements.txt
tests/
  test_api.py
.env.example
```

## Backend setup

```bash
cd /Users/srinivas/github/student_mgmt_python
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure your Oracle connection settings:

```bash
cp .env.example .env
```

## Run the backend

```bash
cd /Users/srinivas/github/student_mgmt_python
source .venv/bin/activate
python3 app.py
```

Set the following in `.env` before starting the app:

```env
ORACLE_USER=system
ORACLE_PASSWORD=your_password
ORACLE_DSN=localhost/XEPDB1
```

Then open:

- Swagger UI: http://localhost:5000/swagger/
- OpenAPI JSON: http://localhost:5000/static/swagger.json

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/students | List all students |
| GET | /api/students/<id> | Get one student |
| POST | /api/students | Create a student |
| PUT | /api/students/<id> | Update a student |
| DELETE | /api/students/<id> | Delete a student |

## Frontend

The React frontend now lives in a separate sibling project folder:

- `/Users/srinivas/github/student_mgmt_react`

Run it independently with `npm install` and `npm run dev` from that directory.

## Testing

Run backend tests with:

```bash
python3 -m unittest discover -s tests -v
```
