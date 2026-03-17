# ICAPCM - Project Management System

## 📌 Overview

ICAPCM is a Python-based desktop application designed for managing projects, users, and related workflows.
The application follows a modular structure with separate layers for authentication, database handling, utilities, and UI views.

---

## 🏗️ Project Structure

```
icapcm/
│
├── assets/          # Static resources (icons, images, etc.)
├── auth/            # Authentication and user management
├── database/        # Database models and operations
├── utils/           # Utility/helper functions
├── views/           # UI components/screens
│
├── main.py          # Application entry point
├── config.py        # Configuration settings
├── lang.py          # Language/localization support
│
├── ica_pms.db       # SQLite database
├── requirements.txt # Python dependencies
│
├── BUILD_DEMO.bat   # Build demo executable
├── BUILD_FULL.bat   # Build full executable
├── app.spec         # PyInstaller configuration
```

---

## ⚙️ Features

* User authentication system
* Modular architecture
* SQLite database integration
* Multi-language support
* Executable build support (via PyInstaller)

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/icassameer/icapcm.git
cd icapcm
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python main.py
```

---

## 🧱 Build Executable

To generate executable files:

### Demo version

```bash
BUILD_DEMO.bat
```

### Full version

```bash
BUILD_FULL.bat
```

---

## 🗄️ Database

* Uses SQLite (`ica_pms.db`)
* No external DB setup required

---

## 🛠️ Technologies Used

* Python
* SQLite
* PyInstaller

---

## 📌 Notes

* Ensure Python is installed before running
* Modify `config.py` for custom settings

---

## 👤 Author

Sameer Bagwan
GitHub: https://github.com/icassameer
