import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Student

bp = Blueprint("main", __name__)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not student_id or not full_name or not email or not password:
            flash("All fields are required.", "error")
        elif not EMAIL_PATTERN.fullmatch(email):
            flash("Enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
        elif Student.query.filter(
            (Student.student_id == student_id) | (Student.email == email)
        ).first():
            flash("An account with that student ID or email already exists.", "error")
        else:
            student = Student(
                student_id=student_id,
                full_name=full_name,
                email=email,
            )
            student.set_password(password)
            db.session.add(student)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash(
                    "An account with that student ID or email already exists.",
                    "error",
                )
            else:
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("main.login"))

        return render_template("register.html")

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "")
        student = Student.query.filter_by(student_id=student_id).first()
        if not student or not student.check_password(password):
            flash("Invalid student ID or password.", "error")
            return render_template("login.html")

        session["student_id"] = student.id
        return redirect(url_for("main.account"))

    return render_template("login.html")


@bp.route("/")
def account():
    student = db.session.get(Student, session.get("student_id"))
    if not student:
        session.pop("student_id", None)
        flash("Please log in to continue.", "error")
        return redirect(url_for("main.login"))
    return render_template("account.html", student=student)
