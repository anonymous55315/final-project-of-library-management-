"""Database and business logic for the Library Management System (no web code here)."""
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("DB_PATH", str(BASE_DIR / "library.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    isbn TEXT UNIQUE,
    category TEXT,
    year INTEGER,
    total INTEGER NOT NULL DEFAULT 1,
    available INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id),
    borrower TEXT NOT NULL,
    student_id TEXT,
    phone TEXT,
    issued_on TEXT NOT NULL,
    returned_on TEXT
);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with connect() as db:
        db.executescript(SCHEMA)
        # upgrade older databases that do not have the newer columns yet
        cols = [r["name"] for r in db.execute("PRAGMA table_info(issues)")]
        for col in ("student_id", "phone"):
            if col not in cols:
                db.execute(f"ALTER TABLE issues ADD COLUMN {col} TEXT")


def list_books(q=""):
    q = q.strip()
    with connect() as db:
        if q:
            like = f"%{q}%"
            rows = db.execute(
                "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? "
                "OR isbn LIKE ? OR category LIKE ? ORDER BY title",
                (like, like, like, like),
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM books ORDER BY title").fetchall()
    return [dict(r) for r in rows]


def list_issued():
    with connect() as db:
        rows = db.execute(
            "SELECT issues.*, books.title FROM issues JOIN books ON books.id = issues.book_id "
            "WHERE returned_on IS NULL ORDER BY issued_on DESC, issues.id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_stats():
    with connect() as db:
        row = db.execute(
            "SELECT COUNT(*) AS titles, COALESCE(SUM(total),0) AS copies, "
            "COALESCE(SUM(available),0) AS available FROM books"
        ).fetchone()
    return dict(row)


def get_issue(issue_id):
    """One issue record with book details, used for the printable slip."""
    with connect() as db:
        row = db.execute(
            "SELECT issues.*, books.title, books.author, books.isbn FROM issues "
            "JOIN books ON books.id = issues.book_id WHERE issues.id = ?",
            (issue_id,),
        ).fetchone()
    return dict(row) if row else None


def add_book(title, author, isbn, category, year, total):
    title, author = title.strip(), author.strip()
    if not title or not author:
        return "Title and author are required.", "err"
    try:
        copies = max(1, int(total.strip() or 1))
        yr = int(year.strip()) if year.strip() else None
    except ValueError:
        return "Year and copies must be numbers.", "err"
    try:
        with connect() as db:
            db.execute(
                "INSERT INTO books (title, author, isbn, category, year, total, available) "
                "VALUES (?,?,?,?,?,?,?)",
                (title, author, isbn.strip() or None, category.strip(), yr, copies, copies),
            )
    except sqlite3.IntegrityError:
        return "A book with that ISBN already exists.", "err"
    return "Book added.", "ok"


def issue_book(book_id, borrower, student_id, phone):
    """Returns (message, kind, issue_id or None)."""
    borrower = borrower.strip()
    student_id = student_id.strip().upper()
    phone = re.sub(r"[\s-]", "", phone)
    if not borrower:
        return "Enter the student's name.", "err", None
    if not re.fullmatch(r"[A-Z0-9/-]{3,20}", student_id):
        return "Student ID must be 3-20 letters/numbers (e.g. 21CS045).", "err", None
    if not re.fullmatch(r"(\+91)?\d{10}", phone):
        return "Enter a valid 10-digit phone number.", "err", None
    with connect() as db:
        book = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if not book or book["available"] < 1:
            return "No copies available.", "err", None
        db.execute("UPDATE books SET available = available - 1 WHERE id = ?", (book_id,))
        cur = db.execute(
            "INSERT INTO issues (book_id, borrower, student_id, phone, issued_on) VALUES (?,?,?,?,?)",
            (book_id, borrower, student_id, phone, date.today().isoformat()),
        )
        issue_id = cur.lastrowid
    return f"Issued to {borrower} ({student_id}).", "ok", issue_id


def return_book(issue_id):
    with connect() as db:
        row = db.execute(
            "SELECT * FROM issues WHERE id = ? AND returned_on IS NULL", (issue_id,)
        ).fetchone()
        if not row:
            return "This book is already returned.", "err"
        db.execute("UPDATE issues SET returned_on = ? WHERE id = ?",
                   (date.today().isoformat(), issue_id))
        db.execute("UPDATE books SET available = available + 1 WHERE id = ?", (row["book_id"],))
    return "Book returned.", "ok"


def delete_book(book_id):
    with connect() as db:
        out = db.execute(
            "SELECT COUNT(*) FROM issues WHERE book_id = ? AND returned_on IS NULL", (book_id,)
        ).fetchone()[0]
        if out:
            return "Can't delete: copies are still issued.", "err"
        db.execute("DELETE FROM issues WHERE book_id = ?", (book_id,))
        db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    return "Book deleted.", "ok"
