import re
from datetime import datetime, timedelta

from models.database import Attendance, Student

_NON_NAME_TOKENS = {
    "all", "absent", "attendance", "class", "count", "grade", "history",
    "is", "list", "many", "present", "registered", "roll", "show",
    "student", "students", "status", "today", "total", "who", "yesterday",
}


def answer_attendance_question(question, grade):
    students = Student.query.filter_by(year=grade).order_by(Student.roll_number).all()
    today = datetime.utcnow().date()
    date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", question)
    name_search_question = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "", question)
    question_tokens = re.findall(r"[a-z0-9]+", name_search_question.casefold())
    if date_match:
        try:
            target_date = datetime.strptime(date_match.group(), "%Y-%m-%d").date()
        except ValueError as error:
            raise ValueError("Please use a valid date in YYYY-MM-DD format.") from error
    elif re.search(r"\byesterday\b", question, re.IGNORECASE):
        target_date = today - timedelta(days=1)
    else:
        target_date = today

    student_ids = [student.id for student in students]
    date_attendance = {}
    if student_ids:
        date_attendance = {
            record.student_id: record
            for record in Attendance.query.filter(
                Attendance.student_id.in_(student_ids),
                Attendance.date == target_date
            ).all()
        }

    def attendance_status(student):
        record = date_attendance.get(student.id)
        if not record:
            return "Absent", None
        return record.status or "Present", record.time

    def attendance_line(student):
        status, marked_time = attendance_status(student)
        suffix = f" at {marked_time}" if marked_time else ""
        return f"{student.name} ({student.roll_number}) — {status}{suffix}"

    full_name_matches = []
    for student in students:
        name_tokens = re.findall(r"[a-z0-9]+", student.name.casefold())
        if name_tokens and any(
            question_tokens[index:index + len(name_tokens)] == name_tokens
            for index in range(len(question_tokens) - len(name_tokens) + 1)
        ):
            full_name_matches.append(student)
    if full_name_matches:
        longest_name = max(len(re.findall(r"[a-z0-9]+", item.name.casefold())) for item in full_name_matches)
        matched_students = [
            item for item in full_name_matches
            if len(re.findall(r"[a-z0-9]+", item.name.casefold())) == longest_name
        ]
    else:
        matched_students = [
            student for student in students
            if any(
                len(token) >= 3 and token not in _NON_NAME_TOKENS and token in question_tokens
                for token in re.findall(r"[a-z0-9]+", student.name.casefold())
            )
            or re.search(
                rf"(?<![a-z0-9_-]){re.escape(student.roll_number.casefold())}(?![a-z0-9_-])",
                name_search_question.casefold()
            )
        ]

    if len(matched_students) > 1:
        names = ", ".join(f"{student.name} ({student.roll_number})" for student in matched_students[:10])
        message = f"I found more than one matching student in grade {grade}: {names}. Please include a roll number."
    elif len(matched_students) == 1:
        student = matched_students[0]
        history_requested = any(
            term in question.casefold()
            for term in ("history", "records", "how many times", "attendance count")
        )
        if history_requested:
            records = Attendance.query.filter_by(student_id=student.id).order_by(
                Attendance.date.desc(), Attendance.time.desc()
            ).all()
            history = [
                f"{record.date}: {record.status or 'Present'}"
                + (f" at {record.time}" if record.time else "")
                for record in records[:20]
            ]
            message = (
                f"{student.name} ({student.roll_number}) has {len(records)} attendance record(s)."
                + ("\n" + "\n".join(history) if history else "\nNo attendance records found.")
                + ("\nShowing the latest 20 records." if len(records) > 20 else "")
            )
        else:
            status, marked_time = attendance_status(student)
            time_message = f" Attendance was marked at {marked_time}." if marked_time else ""
            message = (
                f"{student.name} ({student.roll_number}) is {status} on {target_date}."
                f" Department: {student.department}; grade: {student.year or 'not set'}."
                f"{time_message}"
            )
    elif not students:
        message = f"There are no students registered in grade {grade}."
    elif any(term in question.casefold() for term in ("total attendance", "attendance records", "attendance count")):
        total_records = Attendance.query.filter(Attendance.student_id.in_(student_ids)).count()
        message = f"Grade {grade} has {len(students)} student(s) and {total_records} attendance record(s) in total."
    elif any(term in question.casefold() for term in ("how many", "total", "count")) and any(
        term in question.casefold() for term in ("student", "learner", "registered")
    ):
        message = f"There are {len(students)} students registered in grade {grade}."
    elif "absent" in question.casefold() or "present" in question.casefold():
        wanted_status = "Absent" if "absent" in question.casefold() else "Present"
        matching = [
            student for student in students
            if attendance_status(student)[0].casefold() == wanted_status.casefold()
        ]
        if matching:
            message = f"{wanted_status} on {target_date} ({len(matching)}):\n" + "\n".join(
                attendance_line(student) for student in matching[:50]
            )
            if len(matching) > 50:
                message += f"\n…and {len(matching) - 50} more."
        else:
            message = f"No students are marked {wanted_status.lower()} on {target_date}."
    elif any(term in question.casefold() for term in ("all students", "list students", "student list", "show students")):
        message = f"Students in grade {grade} and their attendance on {target_date} ({len(students)}):\n" + "\n".join(
            attendance_line(student) for student in students[:50]
        )
        if len(students) > 50:
            message += f"\n…and {len(students) - 50} more."
    else:
        message = (
            f"I can answer questions about grade {grade} using the current project records. "
            "Try “Is Piyush present today?”, “Who is absent?”, “How many students are registered?”, "
            "“List students”, or ask for a student's attendance history. "
            "For another date, include it as YYYY-MM-DD."
        )

    return message
