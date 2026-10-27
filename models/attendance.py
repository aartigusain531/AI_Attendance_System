from datetime import datetime
from models.database import db, Student, Attendance


class AttendanceManager:

    @staticmethod
    def mark_attendance(
        student_identifier,
        identifier="name",
        verification_method="Face + Voice"
    ):

        if isinstance(student_identifier, Student):
            student = student_identifier
        elif identifier == "roll":
            student = Student.query.filter_by(roll_number=student_identifier).first()
        else:
            student = Student.query.filter_by(name=student_identifier).first()

        if student is None:
            return False, "Student not found."

        today = datetime.now().date()

        # Check if already marked today
        existing = Attendance.query.filter_by(
            student_id=student.id,
            date=today
        ).first()

        if existing:
            return False, "Attendance already marked today."

        attendance = Attendance(
            student_id=student.id,
            date=today,
            time=datetime.now().time(),
            status="Present",
            verification_method=verification_method
        )

        db.session.add(attendance)
        db.session.commit()

        return True, f"Attendance marked for {student.name}"

    @staticmethod
    def get_today_attendance():

        today = datetime.now().date()

        records = Attendance.query.filter_by(date=today).all()

        result = []

        for record in records:

            student = Student.query.get(record.student_id)

            result.append({
                "name": student.name,
                "roll": student.roll_number,
                "department": student.department,
                "time": str(record.time),
                "status": record.status
            })

        return result

    @staticmethod
    def total_students():
        return Student.query.count()

    @staticmethod
    def total_attendance():
        return Attendance.query.count()