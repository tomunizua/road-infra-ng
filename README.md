# 🛣️ RoadWatch Nigeria

**AI-Powered Infrastructure Damage Reporting and Management System**

RoadWatch is a web application designed to empower Nigerian citizens to report road damage, which is then analyzed by an AI model, prioritized, and managed by an administrative backend. This project is intended to be a capstone for the ALU Software Engineering program.

---

## 📜 Description

In many urban and rural areas, damaged road infrastructure like potholes poses significant risks to drivers and pedestrians. The process of reporting these issues is often slow and inefficient. RoadWatch tackles this problem by providing a simple, accessible platform for citizens to report damage using just a photo.

Our system uses a machine learning model to automatically detect the presence of damage, estimate its severity, and calculate a preliminary repair cost. This data is fed into a secure admin dashboard where officials can view all submitted reports, manage their status, and use a budget optimization tool to schedule repairs in the most impactful way possible.

## ✨ Key Features

- **AI-Powered Damage Detection**: A Convolutional Neural Network (CNN) built with Keras/TensorFlow analyzes user-submitted images to detect potholes.
- **Automatic Severity & Cost Estimation**: Reports are automatically assigned a severity score (1-10) and an estimated repair cost based on the AI's confidence.
- **Citizen Reporting Portal**: A user-friendly, mobile-responsive portal for submitting reports with an image, location, and description.
- **Unique Report Tracking**: Citizens receive a unique tracking number to monitor the status of their submitted report.
- **Secure Admin Dashboard**: A password-protected dashboard for administrators to view, manage, and act on all submitted reports.
- **Manual Report Management**: Admins can manually schedule repairs, assign contractors, or reject invalid reports with a reason.
- **Budget Optimization**: An optimization tool using Linear Programming (PuLP) to help admins schedule the most critical repairs within a given budget.

## 🔧 Tech Stack

| Category      | Technology                                                                                             |
|---------------|--------------------------------------------------------------------------------------------------------|
| **Backend**   | Python, Flask, SQLAlchemy, Keras/TensorFlow, PuLP                                                      |
| **Frontend**  | HTML, TailwindCSS, Vanilla JavaScript                                                                  |
| **Database**  | SQLite (for development)                                                                               |
| **Security**  | Basic HTTP Authentication for admin routes                                                             |

---

## 🚀 Setup and Installation

Follow these steps to set up the development environment and run the project locally.

### Prerequisites
- Python 3.8+
- `pip` (Python package installer)

### 1. Clone the Repository

```bash
# Replace with your actual GitHub repository link
git clone https://github.com/tomunizua/road-infra-ng.git
cd road-infra-ng
```

### 2. Set Up Backend

First, create and activate a virtual environment. This isolates the project's dependencies.

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

Next, install the required Python packages from the `requirements.txt` file.

```bash
pip install -r ../requirements.txt
```

### 3. Run the Application

With the virtual environment still active, start the Flask backend server.

```bash
python app.py
```

The server will start on `http://localhost:5000`. You should see log messages indicating that the model has loaded and the database is initialized.

### 4. Access the Portals

- **Citizen Portal**: Open your web browser and navigate to the `citizen_portal.html` file located in the `frontend` directory, or access it via `http://localhost:5000/citizen_portal.html`.
- **Admin Dashboard**: To access the secure admin dashboard, navigate to:
  - **URL**: `http://localhost:5000/admin`
  - **Username**: `admin`
  - **Password**: `secret`

---

## 🎨 Designs

### System Architecture

The application follows a simple client-server architecture.

```
[Citizen's Browser] ----> [Flask Backend (API)] <----> [SQLite DB]
       |                        |
       |                        |-----> [Keras Model]
       |
[Admin's Browser] ------> [Flask Backend (API)]
```

### App Interfaces

**Citizen Reporting Portal**
![Citizen Portal Screenshot1](https://github.com/tomunizua/road-infra-ng.git/raw/main/docs/images/citizen_portal1.png)
![Citizen Portal Screenshot2](https://github.com/tomunizua/road-infra-ng.git/raw/main/docs/images/citizen_portal2.png)

**Admin Dashboard**
!Admin Dashboard Screenshot(https://github.com/tomunizua/road-infra-ng.git/raw/main/docs/images/admin_dash.png)

---

## ☁️ Deployment Plan

While the project currently runs in a development environment, a production deployment would involve the following steps:

1.  **Backend**:
    -   Containerize the Flask application using **Docker**.
    -   Use a production-grade WSGI server like **Gunicorn** to run the app.
    -   Place the Gunicorn server behind a reverse proxy like **Nginx** for SSL termination, caching, and load balancing.
    -   Host the container on a cloud service like **Heroku**, **AWS Elastic Beanstalk**, or **DigitalOcean App Platform**.

2.  **Database**:
    -   Migrate from SQLite to a more robust, production-ready database like **PostgreSQL** or **MySQL**.

3.  **Static Files & Model**:
    -   Store the ML model (`.h5` file) and user-uploaded images in a cloud storage solution like **AWS S3** or **Google Cloud Storage**.
    -   Serve the frontend static files (HTML, CSS, JS) directly from Nginx or a Content Delivery Network (CDN) for better performance.

4.  **Security & Configuration**:
    -   Manage all sensitive information (database URI, secret keys, admin credentials) using **environment variables** instead of hardcoding them.
    -   Implement a more robust authentication system (e.g., JWT or session-based logins with hashed passwords) for the admin dashboard.

---

## 🎥 Video Demo

*(link to video demonstration)*

Watch a video demonstration of RoadWatch Nigeria here

