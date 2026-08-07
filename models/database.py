from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()


# ==========================
# Student Table
# ==========================
class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    roll_number = db.Column(db.String(50), unique=True, nullable=False)

    department = db.Column(db.String(100), nullable=False)

    year = db.Column(db.String(20))

    phone = db.Column(db.String(20))

    email = db.Column(db.String(100))

    face_folder = db.Column(db.String(255))

    voice_file = db.Column(db.String(255))

    registered_on = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    attendances = db.relationship(
        "Attendance",
        backref="student",
        lazy=True
    )

    def __repr__(self):
        return f"<Student {self.name}>"

# ==========================
# Attendance Table
# ==========================
class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    date = db.Column(
        db.Date,
        default=datetime.utcnow().date
    )

    time = db.Column(
        db.Time,
        default=datetime.utcnow().time
    )

    status = db.Column(
        db.String(20),
        default="Present"
    )

    verification_method = db.Column(
        db.String(50),
        default="Face + Voice"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Attendance {self.student_id}>"

# ==========================
# Admin Table
# ==========================
class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Admin {self.username}>"

# ==========================
# Initialize Database
# ==========================
def init_database(app):
    db.init_app(app)

    with app.app_context():
        db.create_all()