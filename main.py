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
    text = f"{name} {attendee[2]}"  # Last name
    company = attendee[4]           # Company

    # Load logo image
    logo = Image.open("logo.png").convert("RGB")

    # Create a blank image with a white background
    label_width = 600
    label_height = 300
    label = Image.new('RGB', (label_width, label_height), 'white')

    # Resize and center the logo
    logo_width = int(label_width * 0.90)
    logo_height = int((logo_width / logo.width) * logo.height)
    logo = logo.resize((logo_width, logo_height), Image.ANTIALIAS)
    logo_x_position = (label_width - logo_width) // 2  # Center horizontally
    label.paste(logo, (logo_x_position, 0))

    # Prepare to draw text
    draw = ImageDraw.Draw(label)
    
    # Load a custom font and set font sizes
    font_large = ImageFont.truetype("arial.ttf", 72)  # Increase font size for name
    font_small = ImageFont.truetype("arial.ttf", 36)  # Slightly smaller font for company

    # Handle long names by splitting the text if necessary
    max_text_width = label_width - 20  # Maximum width for the text
    text_width, _ = draw.textsize(text, font=font_large)

    if text_width > max_text_width:
        # Split the name into first line and second line
        parts = text.split(" ")
        first_line = parts[0]
        second_line = " ".join(parts[1:])

        # Adjust font size if the name is still too long
        while draw.textsize(first_line, font=font_large)[0] > max_text_width:
            font_large = ImageFont.truetype("arial.ttf", font_large.size - 2)

        while draw.textsize(second_line, font=font_large)[0] > max_text_width:
            font_large = ImageFont.truetype("arial.ttf", font_large.size - 2)
    else:
        first_line = text
        second_line = ""

    # Calculate total height needed for text (including potential second line)
    first_line_width, first_line_height = draw.textsize(first_line, font=font_large)
    second_line_width, second_line_height = draw.textsize(second_line, font=font_large)
    company_width, company_height = draw.textsize(company, font=font_small)

    total_text_height = first_line_height + (second_line_height if second_line else 0) + company_height + 40  # 40 pixels for padding

    # If text height exceeds available space, reduce font sizes proportionally
    available_height = label_height - logo_height - 40  # 40 pixels padding
    if total_text_height > available_height:
        scale_factor = available_height / total_text_height
        font_large = ImageFont.truetype("arial.ttf", int(font_large.size * scale_factor))
        font_small = ImageFont.truetype("arial.ttf", int(font_small.size * scale_factor))

        # Recalculate text sizes with the new fonts
        first_line_width, first_line_height = draw.textsize(first_line, font=font_large)
        second_line_width, second_line_height = draw.textsize(second_line, font=font_large)
        company_width, company_height = draw.textsize(company, font=font_small)
    
    # Recalculate positions to center them
    first_line_x_position = (label_width - first_line_width) // 2
    second_line_x_position = (label_width - second_line_width) // 2
    company_x_position = (label_width - company_width) // 2
    
    text_y_position = logo_height + 10  # Adjust to 10 pixels below the logo
    second_line_y_position = text_y_position + first_line_height + 5  # 5 pixels below the first line
    company_y_position = (second_line_y_position if second_line else text_y_position) + first_line_height + 20  # 20 pixels below the name or second line

    # Draw text on the label
    draw.text((first_line_x_position, text_y_position), first_line, fill="black", font=font_large)
    if second_line:
        draw.text((second_line_x_position, second_line_y_position), second_line, fill="black", font=font_large)
    draw.text((company_x_position, company_y_position), company, fill="black", font=font_small)

    # Rotate the entire label 180 degrees
    label = label.rotate(180)

    # Save the final label as an image
    label_path = "label.png"
    label.save(label_path)

    # Print the label using CUPS
    os.system(f"lp -d DYMOLabelWriter -o fit-to-page {label_path}")

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
