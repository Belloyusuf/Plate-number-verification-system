# Plate Number Verification System (ALPR)

A Django-based Automatic License Plate Recognition (ALPR) web application built as a Final Year Project. The system allows authorised personnel to register vehicle owners, register vehicles, scan number plates via webcam or image upload, and instantly verify whether a scanned plate is registered in the database.

---

## Features

- **Live ALPR Console** — capture a frame from your webcam or upload an image; the system reads the plate number using OCR and returns the result
- **Plate Verification** — after reading a plate, the system checks the vehicle database and displays full owner and vehicle details if registered, or reports the plate as unregistered
- **Owner Management** — register, update, and view vehicle owners
- **Vehicle Management** — register, update, and view vehicles with full technical details
- **Approved Centres** — manage approved vehicle registration centres
- **Quick Search** — search the registry directly by plate number
- **Secure Login** — all pages require authentication

---

## How Plate Scanning Works

1. You open the ALPR Console and either start the webcam or upload an image
2. The system runs OCR (Tesseract) on the image to read the plate text
3. The extracted plate number is searched in the database
4. **If found** — owner name, vehicle type, model, colour, and registration number are displayed
5. **If not found** — the plate text that was read is still shown, along with a message that it is not registered in the database

---

## Prerequisites

Make sure the following are installed on your Windows machine before you begin:

| Tool | Download |
|---|---|
| Python 3.10 or higher | https://www.python.org/downloads/ |
| Git | https://git-scm.com/download/win |
| Tesseract OCR | https://github.com/UB-Mannheim/tesseract/wiki |

> **Important during Python install:** tick the checkbox **"Add Python to PATH"**

> **Important during Tesseract install:** note the installation path (default is `C:\Program Files\Tesseract-OCR\`). You will need it in Step 5.

---

## Setup Guide (Windows)

### Step 1 — Clone the repository

Open **Command Prompt** or **PowerShell** and run:

```cmd
git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
cd YOUR-REPO-NAME\software
```

Replace the URL with the actual GitHub repository link.

---

### Step 2 — Create a virtual environment

The `myenv` folder in the repo was built on Linux and will not work on Windows. Create a fresh one:

```cmd
python -m venv myenv
```

---

### Step 3 — Activate the virtual environment

```cmd
myenv\Scripts\activate
```

Your terminal prompt will change to show `(myenv)` when it is active. You must do this every time you open a new terminal window.

---

### Step 4 — Install all required packages

```cmd
pip install -r requirements.txt
```

---

### Step 5 — Configure the Tesseract path

Open `owners/alpr.py` in any text editor and find this line near the top:

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

If you installed Tesseract in a different folder, update this path to match your installation. Otherwise leave it as is.

---

### Step 6 — Run database migrations

```cmd
python manage.py makemigrations
python manage.py migrate
```

---

### Step 7 — Create an admin account

```cmd
python manage.py createsuperuser
```

You will be prompted to enter:

- **Username** — e.g. `admin`
- **Email** — press Enter to skip
- **Password** — type it twice (nothing shows on screen, that is normal)

---

### Step 8 — Run the application

```cmd
python manage.py runserver
```

Open your browser and go to:

```
http://127.0.0.1:8000
```

Log in with the username and password you created in Step 7.

---

## Every time you want to run the app

```cmd
cd path\to\YOUR-REPO-NAME\software
myenv\Scripts\activate
python manage.py runserver
```

Then visit `http://127.0.0.1:8000` in your browser.

---

## Optional — Better plate detection accuracy

Installing these two packages gives the system a full object detection pipeline (YOLO + EasyOCR) on top of Tesseract, which improves accuracy on real-world plate images:

```cmd
pip install easyocr ultralytics
```

> These are large downloads (1–2 GB) and work best with a dedicated GPU. Tesseract alone is sufficient for basic use.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognised | Re-install Python and tick **"Add Python to PATH"** |
| `myenv\Scripts\activate` fails | Run `Set-ExecutionPolicy RemoteSigned` in PowerShell as Administrator |
| `No module named 'django'` | Make sure `(myenv)` is showing in your terminal prompt |
| Tesseract errors / no plate read | Check the path in `owners/alpr.py` matches your Tesseract install location |
| Port already in use | Run `python manage.py runserver 8080` and visit `http://127.0.0.1:8080` |
| `pip install` fails | Run `python -m pip install --upgrade pip` first, then retry |

---

## Project Structure

```
software/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── platenumber/          # Django project settings and URL config
│   ├── settings.py
│   └── urls.py
└── owners/               # Main application
    ├── models.py          # Owner, CarRegisteration, Approved_Centres
    ├── views.py           # All views
    ├── urls.py            # URL patterns
    ├── forms.py           # Login and ALPR upload forms
    ├── alpr.py            # ALPR pipeline (OCR + database lookup)
    ├── admin.py           # Django admin registration
    ├── templates/         # HTML templates
    └── static/            # CSS, JS, images
```

---

## Tech Stack

- **Backend** — Django 6
- **Database** — SQLite
- **OCR** — Tesseract (via pytesseract), optional EasyOCR
- **Detection** — optional YOLOv8/9/10 via Ultralytics
- **Frontend** — Bootstrap 4, Font Awesome, custom CSS
