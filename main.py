import os
from datetime import datetime

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
        print(
            f"{i:>2}. {student['name']}"
        )

    print("\nEnter absent student numbers separated by spaces.")
    print("Press Enter if everyone is present.")

    while True:
        user_input = input("\nAbsent students: ").strip()

        # Blank means everyone is present
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
            print(
                f"Invalid student numbers: {invalid}"
            )
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

        # Everyone is PRESENT by default
        status = "present"

        # Only change specified students
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

    print("\n")
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

        print(
            f"{student['name']:<25} {status}"
        )


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

    # Select TA/group
    group = select_group()

    if group is None:
        return

    # Get students belonging to group
    students = get_students(group["id"])

    if not students:
        print(
            f"\nNo students found in {group['name']}."
        )
        return

    # Enter date
    attendance_date = get_date()

    print()
    print("=" * 45)
    print(group["name"])
    print(f"TA: {group['ta_name']}")
    print(f"Date: {attendance_date}")
    print("=" * 45)

    # Enter only absent students
    absent_numbers = get_absent_students(students)

    # Show what will be saved
    show_summary(
        students,
        absent_numbers,
        group,
        attendance_date
    )

    # Confirmation
    confirm = input(
        "\nSave attendance? (y/n): "
    ).strip().lower()

    if confirm != "y":
        print("\nAttendance cancelled.")
        return

    # Build database records
    records = build_attendance(
        students,
        absent_numbers,
        attendance_date,
        group["ta_name"]
    )

    # Save all records
    save_attendance(records)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("==============================")
    print("        ATTENDANCE CLI")
    print("==============================")

    take_attendance()


if __name__ == "__main__":
    main()
