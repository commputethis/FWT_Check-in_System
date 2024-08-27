from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from PIL import Image, ImageDraw, ImageFont
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import csv
import os

app = FastAPI()

def get_db_connection():
    conn = sqlite3.connect('attendees.db')
    conn.row_factory = sqlite3.Row
    return conn

# Serve the HTML form
@app.get("/register", response_class=HTMLResponse)
async def get_registration_form():
    html_content = """
    <html>
        <body>
            <h2>Check-In Form</h2>
            <form action="/register" method="post">
                <label for="first_name">First Name:</label><br>
                <input type="text" id="first_name" name="first_name" required><br><br>
                <label for="last_name">Last Name:</label><br>
                <input type="text" id="last_name" name="last_name" required><br><br>
                <label for="preferred_name">Preferred Name:</label><br>
                <input type="text" id="preferred_name" name="preferred_name"><br><br>
                <label for="company">Company:</label><br>
                <input type="text" id="company" name="company" required><br><br>
                <label for="title">Title:</label><br>
                <input type="text" id="title" name="title"><br><br>
                <label for="email">Email:</label><br>
                <input type="email" id="email" name="email" required><br><br>
                <input type="submit" value="Check In">
            </form>
        </body>
    </html>
    """
    return html_content

# Process form submission and print label
@app.post("/register")
async def register_attendee(
    first_name: str = Form(...),
    last_name: str = Form(...),
    preferred_name: str = Form(None),
    company: str = Form(...),
    title: str = Form(...),
    email: str = Form(...)
):
    # Save the attendee in the database
    conn = sqlite3.connect('attendees.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO attendees (first_name, last_name, preferred_name, company, title, email, checked_in)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (first_name, last_name, preferred_name, company, title, email, True))
    attendee_id = cursor.lastrowid
    conn.commit()
    
    # Fetch the newly created attendee record
    cursor.execute("SELECT * FROM attendees WHERE id = ?", (attendee_id,))
    attendee = cursor.fetchone()
    conn.close()

    if attendee:
        # Print the label
        print_label(attendee)
        return RedirectResponse(url="/thank-you", status_code=303)
    else:
        raise HTTPException(status_code=404, detail="Attendee not found")

def print_label(attendee):
    # Prepare text
    name = attendee[3] if attendee[3] else attendee[1]  # preferred_name or first_name
    text = f"{name} {attendee[2]}\n{attendee[4]}"  # Last name and Company

    # Load logo image
    logo = Image.open("logo.png").convert("RGB")

    # Create a blank image with a white background
    label_width = 400
    label_height = 300
    label = Image.new('RGB', (label_width, label_height), 'white')

    # Resize and paste the logo into the label
    logo_width = label_width
    logo_height = int(label_width / logo.width * logo.height)
    logo = logo.resize((logo_width, logo_height), Image.ANTIALIAS)
    label.paste(logo, (0, 0))

    # Prepare to draw text
    draw = ImageDraw.Draw(label)
    font = ImageFont.load_default()

    # Position text below the logo
    text_y_position = logo_height + 10  # 10 pixels below the logo
    draw.text((10, text_y_position), text, fill="black", font=font)

    # Save the final label as an image
    label_path = "label.png"
    label.save(label_path)

    # Print the label using CUPS
    os.system(f"lp -d DYMO_LabelWriter -o fit-to-page {label_path}")

@app.post("/import/")
async def import_attendees(file: UploadFile = File(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    reader = csv.DictReader(file.file)
    for row in reader:
        cursor.execute('''INSERT INTO attendees (first_name, last_name, preferred_name, company, title, email) 
                        VALUES (?, ?, ?, ?, ?, ?)''',
                    (row['first_name'], row['last_name'], row['preferred_name'], row['company'], row['title'], row['email']))
    conn.commit()
    conn.close()
    return {"message": "Attendees imported successfully"}

# Thank you page
@app.get("/thank-you", response_class=HTMLResponse)
async def thank_you():
    return "<html><body><h3>Thank you for registering! Your name badge is printing.</h3></body></html>"
