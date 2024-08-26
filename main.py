from fastapi import FastAPI, Form, HTTPException
from PIL import Image, ImageDraw, ImageFont
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import os

app = FastAPI()

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
    logo = Image.open("logo.png")

    # Create a blank image with a white background
    label_width = 400
    label_height = 300
    label = Image.new('RGB', (label_width, label_height), 'white')

    # Paste the logo into the label
    logo = logo.resize((label_width, int(label_width / logo.width * logo.height)))  # Resize logo
    label.paste(logo, (0, 0))

    # Prepare to draw text
    draw = ImageDraw.Draw(label)
    font = ImageFont.load_default()

    # Position text below the logo
    text_y_position = logo.height + 10  # 10 pixels below the logo
    draw.text((10, text_y_position), text, fill="black", font=font)

    # Save the final label as an image
    label_path = "/tmp/label.png"
    label.save(label_path)

    # Print the label using CUPS
    os.system(f"lp -d DYMOLabelWriter -o fit-to-page {label_path}")

# Thank you page
@app.get("/thank-you", response_class=HTMLResponse)
async def thank_you():
    return "<html><body><h3>Thank you for registering! Your name badge is printing.</h3></body></html>"
