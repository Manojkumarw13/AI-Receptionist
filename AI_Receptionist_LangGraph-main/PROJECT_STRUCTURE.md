# AI Receptionist - Project Structure

## 📁 Directory Organization

```
AI_Receptionist_LangGraph-main/
│
├── 📄 Main Application Files
│   ├── streamlit_app.py          # Main Streamlit application
│   ├── caller_agent.py            # LangGraph agent for AI conversations
│   ├── tools.py                   # Tool functions for agent
│   ├── ml_utils.py                # Machine learning utilities
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Environment variables (API keys)
│   ├── .gitignore                 # Git ignore rules
│   └── README.md                  # Project documentation
│
├── 📁 scripts/                    # Utility Scripts
│   ├── download_images.py         # Download healthcare images from Unsplash
│   ├── download_logos.py          # Download logo options from Flaticon
│   ├── remove_bg.py               # Remove background from images
│   └── check.py                   # Verification/check script
│
├── 📁 data/                       # Data Files
│   ├── appointments.json          # Appointment records
│   ├── doctors.json               # Doctor information
│   ├── user_data.json             # User accounts
│   ├── disease_specialties.json   # Disease to specialty mapping
│   ├── appointment_data.csv       # Appointment data (CSV format)
│   └── visitors.json              # Visitor check-in records
│
├── 📁 screenshots/                # Application Screenshots
│   ├── appointment_booked.png     # Appointment confirmation screenshot
│   ├── pic.png                    # General screenshot
│   └── pic_nobg.png               # Screenshot with removed background
│
├── 📁 static/                     # Static Assets
│   ├── styles.css                 # Custom CSS styling
│   │
│   └── 📁 images/
│       ├── 📁 current/            # Currently Used Images
│       │   ├── logo.png           # Active logo (transparent background)
│       │   └── medical_technology.jpg  # Active background image
│       │
│       ├── 📁 logos/              # Logo Options
│       │   ├── health_logo_1.png  # Lock/Security icon
│       │   ├── health_logo_2.png  # Prescription icon
│       │   ├── health_logo_3.png  # Medical monitor icon
│       │   ├── health_logo_4.png  # Heartbeat icon ⭐
│       │   ├── health_logo_5.png  # Doctor icon ⭐
│       │   └── logo_backup.png    # Original logo backup
│       │
│       ├── 📁 backgrounds/        # Background Image Options
│       │   ├── doctor_consultation.jpg
│       │   ├── healthcare_team.jpg
│       │   ├── hospital_interior.jpg
│       │   ├── medical_background.jpg
│       │   └── welcome_bg.png     # Original background
│       │
│       └── README.txt             # Image documentation
│
└── 📁 __pycache__/                # Python cache files (auto-generated)
```

## 🎯 Key Features

### Main Application (`streamlit_app.py`)
- **AI Assistant**: Chat with AI receptionist for appointments
- **Visitor Check-in**: Photo capture and registration
- **Manual Booking**: Step-by-step appointment scheduling with ML predictions
- **User Authentication**: Login/Register system

### Agent System (`caller_agent.py`)
- LangGraph-based conversational AI
- Tool calling for appointments, availability checks
- Groq API integration for LLM

### Tools (`tools.py`)
- Appointment booking
- Availability checking with ML
- QR code generation
- Visitor registration

### ML Utilities (`ml_utils.py`)
- Appointment time prediction
- Optimal scheduling recommendations

## 📦 File Paths in Code

All file references have been updated to use the organized structure:

```python
# Data files
USER_DATABASE_FILE = "data/user_data.json"
DOCTORS_DATABASE_FILE = "data/doctors.json"
APPOINTMENTS_DATABASE_FILE = "data/appointments.json"
DISEASE_SPECIALTIES_FILE = "data/disease_specialties.json"

# Images
LOGO_PATH = "static/images/current/logo.png"
BACKGROUND_PATH = "static/images/current/medical_technology.jpg"
```

## 🚀 Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run streamlit_app.py
```

## 🔧 Utility Scripts

### Download Images
```bash
python scripts/download_images.py
```
Downloads professional healthcare images from Unsplash.

### Download Logos
```bash
python scripts/download_logos.py
```
Downloads logo options from Flaticon.

### Remove Background
```bash
python scripts/remove_bg.py
```
Removes background from images using rembg library.

## 📝 Notes

- All images from Unsplash are free to use (Unsplash License)
- Logo icons from Flaticon require attribution
- Environment variables stored in `.env` file
- Data files use JSON format for easy editing

## 🎨 Customization

### Change Logo
Replace `static/images/current/logo.png` with your preferred logo from `static/images/logos/`

### Change Background
Replace `static/images/current/medical_technology.jpg` with any image from `static/images/backgrounds/`

### Update Styling
Edit `static/styles.css` for custom colors, fonts, and effects
