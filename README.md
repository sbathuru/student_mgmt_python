# Student Management System (Python backend)

A Flask-based backend API for student management, now separated from the React frontend. The API is implemented in `src/app.py` and persists student records to an Oracle database using the connection settings from `.env`.

## Project structure

Notes:
- The container runs `gunicorn` serving the Flask app on port `5000`.
- This application requires an Oracle database for both students and user accounts. Set `ORACLE_USER`, `ORACLE_PASSWORD`, and `ORACLE_DSN` before running.
- The Docker image must include Oracle Instant Client and the `oracledb` Python package to connect to Oracle. The supplied Dockerfile does not install Instant Client — update the image if you intend to run the container with Oracle.
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

## Docker

Build the image:

```bash
cd /Users/srinivas/github/student_mgmt_python
docker build -t student-mgmt-python:latest .
```

Run the container (set Oracle env vars):

```bash
docker run -p 5000:5000 \
  -e ORACLE_USER=system \
  -e ORACLE_PASSWORD=your_password \
  -e ORACLE_DSN=localhost/XEPDB1 \
  --name student-mgmt-python student-mgmt-python:latest
```

Notes:
- The container runs `gunicorn` serving the Flask app on port `5000`.
- If your app requires Oracle Instant Client, you may need to extend the Dockerfile to install it and set `LD_LIBRARY_PATH` accordingly.
 - Registered users are persisted in a local SQLite file `users.db` inside the container by default. To persist users across container recreations, mount a host volume:

- By default registrations persist to a local SQLite file `users.db` inside the container. If you configure Oracle connection environment variables (`ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_DSN`), the application will persist users into the Oracle database instead.

To persist the default SQLite `users.db` across container recreations, mount a host volume:

```bash
docker run -p 5000:5000 \
  -v $(pwd)/users.db:/app/users.db \
  -e ORACLE_USER=system \
  -e ORACLE_PASSWORD=your_password \
  -e ORACLE_DSN=localhost/XEPDB1 \
  --name student-mgmt-python student-mgmt-python:latest
```

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
