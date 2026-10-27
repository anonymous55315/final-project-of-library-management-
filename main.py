"""FastAPI web app for the Library Management System."""
from contextlib import asynccontextmanager
from datetime import date
from urllib.parse import quote

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import library as lib


@asynccontextmanager
async def lifespan(app: FastAPI):
    lib.init_db()
    yield


app = FastAPI(title="Library Management System", lifespan=lifespan)
templates = Jinja2Templates(directory=str(lib.BASE_DIR / "templates"))


def go(msg: str, kind: str, to: str = "/"):
    return RedirectResponse(f"{to}?msg={quote(msg)}&kind={kind}", status_code=303)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, q: str = "", msg: str = "", kind: str = "ok"):
    return templates.TemplateResponse(request, "index.html", {
        "books": lib.list_books(q),
        "issued": lib.list_issued(),
        "stats": lib.get_stats(),
        "q": q.strip(),
        "msg": msg,
        "kind": "err" if kind == "err" else "ok",
    })


@app.post("/add")
def add_book(title: str = Form(...), author: str = Form(...), isbn: str = Form(""),
             category: str = Form(""), year: str = Form(""), total: str = Form("1")):
    msg, kind = lib.add_book(title, author, isbn, category, year, total)
    return go(msg, kind)


@app.post("/issue/{book_id}")
def issue(book_id: int, borrower: str = Form(...), student_id: str = Form(...),
          phone: str = Form(...), print_slip: str = Form("", alias="print")):
    msg, kind, issue_id = lib.issue_book(book_id, borrower, student_id, phone)
    if issue_id and print_slip:
        return RedirectResponse(f"/print/{issue_id}?auto=1", status_code=303)
    return go(msg, kind)


@app.post("/return/{issue_id}")
def return_book(issue_id: int):
    msg, kind = lib.return_book(issue_id)
    return go(msg, kind)


@app.post("/delete/{book_id}")
def delete(book_id: int):
    msg, kind = lib.delete_book(book_id)
    return go(msg, kind)


@app.get("/print-issued", response_class=HTMLResponse)
def print_issued(request: Request, auto: int = 0):
    """Print a report of all books that are currently issued, with student details."""
    return templates.TemplateResponse(request, "issued_report.html", {
        "issued": lib.list_issued(), "auto": auto, "now_date": date.today().isoformat()
    })


@app.get("/print/{issue_id}", response_class=HTMLResponse)
def print_slip(request: Request, issue_id: int, auto: int = 0):
    issue_row = lib.get_issue(issue_id)
    if not issue_row:
        raise HTTPException(status_code=404, detail="Issue record not found")
    return templates.TemplateResponse(request, "slip.html", {"i": issue_row, "auto": auto})
