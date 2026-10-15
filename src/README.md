# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teachers can sign in to register or unregister students
- Students and visitors can view activities and participant lists without signing in

## Getting Started

1. Install the dependencies from the repository root:

   ```
   pip install -r requirements.txt
   ```

2. Create a local teacher credential file from the `src` directory. The app reads `teachers.json` there by default; set `TEACHER_CREDENTIALS_FILE` to use a different path.

   ```
   cd src
   cp teachers.example.json teachers.json
   python -c 'from getpass import getpass; from teacher_auth import hash_password; print(hash_password(getpass("Teacher password: ")))'
   ```

   Add a teacher entry to `teachers.json` using the generated hash:

   ```json
   {
     "teachers": [
       {"username": "teacher1", "password_hash": "<generated hash>"}
     ]
   }
   ```

   `teachers.json` is local-only and excluded from Git. Passwords are stored as salted PBKDF2 hashes.

3. Run the application from the `src` directory:

   ```
   uvicorn app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                      | Sign in as a teacher and receive a bearer token                     |
| POST   | `/auth/logout`                                                     | Revoke the current teacher session                                  |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student (teacher login required)                         |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher login required)                    |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
Teacher sessions also expire after eight hours or when the server restarts.
