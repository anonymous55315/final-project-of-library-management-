# Library Management System — Improved Version

A student-friendly library management web app built with **Python, FastAPI, SQLite, and Jinja2**.

## Features
- Add books and search by title, author, ISBN, or category.
- Track total and available copies.
- Issue books with student name, student ID/roll number, and phone number.
- Return issued books and update availability.
- Print an individual book issue receipt.
- **Print a complete currently-issued-books report** with issue ID, book title, student name, student ID, phone number, and issue date.
- Dashboard statistics and responsive layout.
- API documentation at `/docs`.

## Run on Windows
Open a terminal in this folder and run:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000 in your browser. Click **Print issued books list** to open the printable report; use the browser print dialog to print or choose **Save as PDF**.

## Important database note
The ZIP intentionally does not include `library.db`, to avoid distributing any existing student contact details. On first run, the app creates a fresh database. To keep your existing library records, back up your original `library.db` and copy it into this folder before running the app.

## Deployment note
For a hosted deployment, use persistent storage or PostgreSQL. A temporary filesystem may lose SQLite data after restart. Student names and phone numbers are personal data, so do not publish a real student database in a public GitHub repository.

## Demo checklist for college
1. Add a sample book.
2. Search for the book.
3. Issue it to a **dummy/demo student**.
4. Show the dashboard count and available-copy count changing.
5. Open the issued-books report and print/save it as PDF.
6. Return the book and show availability increase again.
7. Explain the stack: FastAPI handles routes, SQLite stores records, and Jinja2 renders HTML templates.
