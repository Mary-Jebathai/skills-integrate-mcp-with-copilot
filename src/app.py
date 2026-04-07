"""
High School Management System API

A FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path

from .db import (
    add_participant,
    get_activity,
    get_all_activities,
    initialize_database,
    remove_participant,
)

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount(
    "/static",
    StaticFiles(directory=current_dir / "static"),
    name="static",
)


@app.on_event("startup")
def on_startup():
    initialize_database()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return get_all_activities()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    success, error = add_participant(activity_name, email)
    if not success:
        if error == "Activity not found":
            raise HTTPException(status_code=404, detail=error)
        raise HTTPException(status_code=400, detail=error)

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    activity = get_activity(activity_name)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity",
        )

    if not remove_participant(activity_name, email):
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity",
        )

    return {"message": f"Unregistered {email} from {activity_name}"}
