import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "activities.db"

DEFAULT_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


def get_connection():
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activities (
            name TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            schedule TEXT NOT NULL,
            max_participants INTEGER NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_name TEXT NOT NULL,
            email TEXT NOT NULL,
            UNIQUE(activity_name, email),
            FOREIGN KEY(activity_name) REFERENCES activities(name) ON DELETE CASCADE
        )
        """
    )
    connection.commit()
    seed_default_activities(connection)
    connection.close()


def seed_default_activities(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM activities")
    activity_count = cursor.fetchone()[0]
    if activity_count > 0:
        return

    for name, details in DEFAULT_ACTIVITIES.items():
        cursor.execute(
            "INSERT INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)",
            (name, details["description"], details["schedule"], details["max_participants"]),
        )
        for email in details["participants"]:
            cursor.execute(
                "INSERT OR IGNORE INTO participants (activity_name, email) VALUES (?, ?)",
                (name, email),
            )

    connection.commit()


def get_all_activities():
    connection = get_connection()
    cursor = connection.cursor()
    activities = {}
    for row in cursor.execute("SELECT name, description, schedule, max_participants FROM activities").fetchall():
        activities[row["name"]] = {
            "description": row["description"],
            "schedule": row["schedule"],
            "max_participants": row["max_participants"],
            "participants": [],
        }

    for row in cursor.execute("SELECT activity_name, email FROM participants").fetchall():
        activities.setdefault(row["activity_name"], {"participants": []})["participants"].append(row["email"])

    connection.close()
    return activities


def get_activity(activity_name):
    connection = get_connection()
    cursor = connection.cursor()
    activity_row = cursor.execute(
        "SELECT name, description, schedule, max_participants FROM activities WHERE name = ?",
        (activity_name,),
    ).fetchone()
    if activity_row is None:
        connection.close()
        return None

    participants = [
        row["email"]
        for row in cursor.execute(
            "SELECT email FROM participants WHERE activity_name = ? ORDER BY email",
            (activity_name,),
        ).fetchall()
    ]
    connection.close()

    return {
        "name": activity_row["name"],
        "description": activity_row["description"],
        "schedule": activity_row["schedule"],
        "max_participants": activity_row["max_participants"],
        "participants": participants,
    }


def add_participant(activity_name, email):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT max_participants FROM activities WHERE name = ?",
        (activity_name,),
    )
    activity = cursor.fetchone()
    if activity is None:
        connection.close()
        return False, "Activity not found"

    participant_count = cursor.execute(
        "SELECT COUNT(*) FROM participants WHERE activity_name = ?",
        (activity_name,),
    ).fetchone()[0]
    if participant_count >= activity["max_participants"]:
        connection.close()
        return False, "Activity is full"

    existing = cursor.execute(
        "SELECT 1 FROM participants WHERE activity_name = ? AND email = ?",
        (activity_name, email),
    ).fetchone()
    if existing is not None:
        connection.close()
        return False, "Student is already signed up"

    cursor.execute(
        "INSERT INTO participants (activity_name, email) VALUES (?, ?)",
        (activity_name, email),
    )
    connection.commit()
    connection.close()
    return True, None


def remove_participant(activity_name, email):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT 1 FROM participants WHERE activity_name = ? AND email = ?",
        (activity_name, email),
    )
    if cursor.fetchone() is None:
        connection.close()
        return False

    cursor.execute(
        "DELETE FROM participants WHERE activity_name = ? AND email = ?",
        (activity_name, email),
    )
    connection.commit()
    connection.close()
    return True
