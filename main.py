from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

class Attendee(BaseModel):
    first_name: str
    last_name: str
    preferred_name: str = None
    company: str
    title: str
    email: str

def get_db_connection():
    conn = sqlite3.connect('attendees.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.post("/register/")
async def register_attendee(attendee: Attendee):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO attendees (first_name, last_name, preferred_name, company, title, email) 
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (attendee.first_name, attendee.last_name, attendee.preferred_name, attendee.company, attendee.title, attendee.email))
    conn.commit()
    conn.close()
    return {"message": "Attendee registered successfully"}

@app.get("/export/")
async def export_checked_in():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendees WHERE checked_in = TRUE")
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.post("/clear/")
async def clear_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendees")
    conn.commit()
    conn.close()
    return {"message": "Database cleared successfully"}

@app.post("/check-in/{attendee_id}")
async def check_in_attendee(attendee_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE attendees SET checked_in = TRUE WHERE id = ?", (attendee_id,))
    conn.commit()
    cursor.execute("SELECT * FROM attendees WHERE id = ?", (attendee_id,))
    attendee = cursor.fetchone()
    conn.close()

    if attendee:
        print_label(attendee)
        return {"message": "Checked in and label printed"}
    else:
        raise HTTPException(status_code=404, detail="Attendee not found")

def print_label(attendee):
    name = attendee['preferred_name'] or attendee['first_name']
    label_content = f"""
    N: {name} {attendee['last_name']}
    C: {attendee['company']}
    """
    with open("label.txt", "w") as file:
        file.write(label_content)
    os.system(f"lp -d DYMO_LabelWriter label.txt")