import os
import csv
from datetime import datetime, timedelta

from dotenv import load_dotenv
from supabase import create_client


# ============================================================
# SUPABASE SETUP
# ============================================================

load_dotenv()

url = os.environ["NEXT_PUBLIC_SUPABASE_URL"]
key = os.environ["NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"]

supabase = create_client(url, key)


# ============================================================
# GET GROUPS
# ============================================================

def get_groups():
    response = (
        supabase
        .table("groups")
        .select("*")
        .order("name")
        .execute()
    )

    return response.data


# ============================================================
# SELECT GROUP
# ============================================================

def select_group():
    groups = get_groups()

    if not groups:
        print("No groups found.")
        return None

    print("\nAvailable Groups")
    print("----------------")

    for i, group in enumerate(groups, start=1):
        print(
            f"{i}. {group['name']} "
            f"(TA: {group['ta_name']})"
        )

    while True:
        try:
            choice = int(input("\nSelect your group: "))

            if 1 <= choice <= len(groups):
                return groups[choice - 1]

            print("Invalid group number.")

        except ValueError:
            print("Please enter a number.")


# ============================================================
# GET STUDENTS IN GROUP
# ============================================================

def get_students(group_id):
    response = (
        supabase
        .table("students")
        .select("*")
        .eq("group_id", group_id)
        .order("name")
        .execute()
    )

    return response.data


# ============================================================
# GET DATE
# ============================================================

def get_date():
    while True:
        date_input = input(
            "\nEnter date (YYYY-MM-DD): "
        ).strip()

        try:
            datetime.strptime(date_input, "%Y-%m-%d")
            return date_input

        except ValueError:
            print("Invalid date. Please use YYYY-MM-DD.")


# ============================================================
# GET ABSENT STUDENTS
# ============================================================

def get_absent_students(students):
    print("\nRoster")
    print("------")

    for i, student in enumerate(students, start=1):
        print(f"{i:>2}. {student['name']}")

    print("\nEnter absent student numbers separated by spaces.")
    print("Press Enter if everyone is present.")

    while True:
        user_input = input("\nAbsent students: ").strip()

        if user_input == "":
            return set()

        try:
            absent_numbers = {
                int(number)
                for number in user_input.split()
            }

        except ValueError:
            print("Please enter only student numbers.")
            continue

        invalid = [
            number
            for number in absent_numbers
            if number < 1 or number > len(students)
        ]

        if invalid:
            print(f"Invalid student numbers: {invalid}")
            continue

        return absent_numbers


# ============================================================
# BUILD ATTENDANCE RECORDS
# ============================================================

def build_attendance(
    students,
    absent_numbers,
    attendance_date,
    ta_name
):
    records = []

    for i, student in enumerate(students, start=1):

        status = "present"

        if i in absent_numbers:
            status = "absent"

        record = {
            "attendance_date": attendance_date,
            "student_id": student["id"],
            "status": status,
            "recorded_by": ta_name
        }

        records.append(record)

    return records


# ============================================================
# DISPLAY SUMMARY
# ============================================================

def show_summary(
    students,
    absent_numbers,
    group,
    attendance_date
):
    print()
    print("=" * 45)
    print("ATTENDANCE SUMMARY")
    print("=" * 45)

    print(f"Group: {group['name']}")
    print(f"TA:    {group['ta_name']}")
    print(f"Date:  {attendance_date}")

    print("\nStudents")
    print("--------------------------------")

    for i, student in enumerate(students, start=1):

        if i in absent_numbers:
            status = "ABSENT"
        else:
            status = "PRESENT"

        print(f"{student['name']:<25} {status}")


# ============================================================
# SAVE TO SUPABASE
# ============================================================

def save_attendance(records):
    try:
        (
            supabase
            .table("attendance")
            .insert(records)
            .execute()
        )

        print("\nAttendance successfully saved.")

    except Exception as error:
        print("\nCould not save attendance.")
        print(error)


# ============================================================
# TAKE ATTENDANCE
# ============================================================

def take_attendance():
    group = select_group()

    if group is None:
        return

    students = get_students(group["id"])

    if not students:
        print(f"\nNo students found in {group['name']}.")
        return

    attendance_date = get_date()

    print()
    print("=" * 45)
    print(group["name"])
    print(f"TA: {group['ta_name']}")
    print(f"Date: {attendance_date}")
    print("=" * 45)

    absent_numbers = get_absent_students(students)

    show_summary(
        students,
        absent_numbers,
        group,
        attendance_date
    )

    confirm = input(
        "\nSave attendance? (y/n): "
    ).strip().lower()

    if confirm != "y":
        print("\nAttendance cancelled.")
        return

    records = build_attendance(
        students,
        absent_numbers,
        attendance_date,
        group["ta_name"]
    )

    save_attendance(records)


# ============================================================
# GET WEEK RANGE
# ============================================================

def get_week_range():
    while True:
        start_input = input(
            "\nEnter week start date (YYYY-MM-DD): "
        ).strip()

        try:
            start_date = datetime.strptime(
                start_input,
                "%Y-%m-%d"
            ).date()

            end_date = start_date + timedelta(days=6)

            return (
                start_date.isoformat(),
                end_date.isoformat()
            )

        except ValueError:
            print("Invalid date. Please use YYYY-MM-DD.")


# ============================================================
# GET STUDENT AND GROUP LOOKUPS
# ============================================================

def get_export_lookups():

    students_response = (
        supabase
        .table("students")
        .select("*")
        .execute()
    )

    groups_response = (
        supabase
        .table("groups")
        .select("*")
        .execute()
    )

    students = students_response.data
    groups = groups_response.data

    student_lookup = {
        student["id"]: student
        for student in students
    }

    group_lookup = {
        group["id"]: group
        for group in groups
    }

    return student_lookup, group_lookup


# ============================================================
# WRITE ATTENDANCE TO CSV
# ============================================================

def write_csv(
    attendance_records,
    filename
):
    if not attendance_records:
        print("\nNo attendance records found.")
        return

    student_lookup, group_lookup = get_export_lookups()

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Date",
            "Group",
            "TA",
            "Student Number",
            "Student Name",
            "Status"
        ])

        for record in attendance_records:

            student = student_lookup.get(
                record["student_id"]
            )

            if student is None:
                continue

            group = group_lookup.get(
                student["group_id"]
            )

            if group is None:
                continue

            writer.writerow([
                record["attendance_date"],
                group["name"],
                record["recorded_by"],
                student["student_number"],
                student["name"],
                record["status"]
            ])

    print("\nAttendance exported successfully.")
    print(f"File: {filename}")


# ============================================================
# EXPORT WEEKLY ATTENDANCE
# ============================================================

def export_weekly_attendance():

    print()
    print("=" * 45)
    print("EXPORT WEEKLY ATTENDANCE")
    print("=" * 45)

    start_date, end_date = get_week_range()

    print(
        f"\nExporting attendance from "
        f"{start_date} through {end_date}..."
    )

    response = (
        supabase
        .table("attendance")
        .select("*")
        .gte("attendance_date", start_date)
        .lte("attendance_date", end_date)
        .order("attendance_date")
        .execute()
    )

    records = response.data

    filename = (
        f"attendance_{start_date}_to_{end_date}.csv"
    )

    write_csv(
        records,
        filename
    )


# ============================================================
# EXPORT ENTIRE SEMESTER
# ============================================================

def export_all_attendance():

    print()
    print("=" * 45)
    print("EXPORT ALL ATTENDANCE")
    print("=" * 45)

    response = (
        supabase
        .table("attendance")
        .select("*")
        .order("attendance_date")
        .execute()
    )

    records = response.data

    filename = "attendance_full_semester.csv"

    write_csv(
        records,
        filename
    )


# ============================================================
# EXPORT MENU
# ============================================================

def export_menu():

    while True:

        print()
        print("==============================")
        print("       EXPORT ATTENDANCE")
        print("==============================")

        print()
        print("1. Export one week")
        print("2. Export entire semester")
        print("3. Back")

        choice = input(
            "\nSelect an option: "
        ).strip()

        if choice == "1":
            export_weekly_attendance()

        elif choice == "2":
            export_all_attendance()

        elif choice == "3":
            return

        else:
            print("\nInvalid option.")


# ============================================================
# MAIN MENU
# ============================================================

def main():

    while True:

        print()
        print("==============================")
        print("        ATTENDANCE CLI")
        print("==============================")

        print()
        print("1. Take attendance")
        print("2. Export attendance")
        print("3. Exit")

        choice = input(
            "\nSelect an option: "
        ).strip()

        if choice == "1":
            take_attendance()

        elif choice == "2":
            export_menu()

        elif choice == "3":
            print("\nGoodbye.")
            break

        else:
            print("\nInvalid option.")


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()
