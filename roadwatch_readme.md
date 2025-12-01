# RoadWatch Nigeria

AI-Powered Infrastructure Damage Reporting and Management System

## Project Overview

RoadWatch Nigeria is a web application enabling Nigerian citizens to report road damage through a mobile-friendly platform. The system uses machine learning to analyze images, detect damage types, estimate severity, and calculate repair costs. An administrative dashboard allows government officials to manage reports and optimize repair budgets.

## Live Application

- **Citizen Portal**: https://roadwatchnigeria.vercel.app/
- **Admin Dashboard**: https://roadwatchnigeria.vercel.app/admin
- **Admin Test Credentials**: 
  - Username: `roadwatch_admin`
  - Password: `mySecureInitialPassword123`

## Technology Stack

- **Backend**: Python 3.10, Flask, SQLAlchemy
- **Frontend**: HTML5, TailwindCSS, Vanilla JavaScript
- **Database**: PostgreSQL (Supabase)
- **ML/AI**: YOLOv8 (Roboflow API), OpenCV
- **Optimization**: PuLP (linear programming)
- **Authentication**: JWT
- **Deployment**: Render (backend), Vercel (frontend)

## Project Structure

```
roadwatch-nigeria/
├── api/
│   ├── integrated_backend.py          # Main Flask application
│   ├── database.py                    # Database models
│   ├── damagepipeline.py              # Roboflow AI pipeline
│   ├── enhanced_budget.py             # Budget optimization engine
│   ├── budget_api.py                  # Budget API endpoints
│   └── scripts/
├── frontend/
│   ├── citizen_portal.html            # Citizen reporting interface
│   ├── admin.html                     # Admin dashboard
│   └── config.js                      # API configuration
├── budget_optimization/
│   ├── enhanced_budget.py
│   ├── README.md
│   └── test_budget_integration.py
├── requirements.txt
└── README.md
```

## Local Setup

### Prerequisites

- Python 3.10+
- Git

### Backend Installation

1. **Clone repository**
   ```bash
   git clone https://github.com/tomunizua/road-infra-ng.git
   cd road-infra-ng
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Set environment variables** in `.env`
   ```
   SQLALCHEMY_DATABASE_URI=postgresql://user:password@host:port/database
   JWT_SECRET_KEY=your_secret_key
   FLASK_ENV=development
   ```

5. **Run backend**
   ```bash
   python api/integrated_backend.py
   ```
   Server runs on `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Start local server**
   ```bash
   python -m http.server 8000
   # or: npx http-server
   ```

3. **Access application**
   - Citizen Portal: `http://localhost:8000/citizen_portal.html`
   - Admin Dashboard: `http://localhost:8000/admin.html`
   - Use test credentials for admin login

## Key Features

- **AI Damage Detection**: Machine learning analyzes images to detect potholes and road cracks
- **Automatic Severity Scoring**: Reports receive severity scores (0-100) and repair cost estimates
- **GPS Location Mapping**: Automatically detects user location and maps to Lagos LGAs
- **Report Tracking**: Citizens receive unique tracking numbers to monitor status
- **Admin Dashboard**: Manage reports, filter by status/LGA, and view analytics
- **Budget Optimization**: Allocates repair budgets across reports using priority weighting
- **Real-time Status Updates**: Bulk scheduling and report status management

## Database Schema

Primary table: `reports`

| Field | Type | Description |
|-------|------|-----------|
| tracking_number | String | Unique report identifier |
| location | String | Road location |
| damage_type | String | Type of damage (pothole, crack, etc.) |
| severity_score | Integer | 0-100 severity scale |
| estimated_cost | Integer | Repair cost in Naira |
| status | String | submitted, under_review, scheduled, completed |
| gps_latitude | Float | GPS coordinate |
| gps_longitude | Float | GPS coordinate |
| lga | String | Local Government Area |
| created_at | DateTime | Submission timestamp |

## API Endpoints

### Report Submission
```
POST /api/submit-report
{
    "location": "Ikeja Road, Lagos",
    "lga": "Ikeja",
    "description": "Large pothole",
    "photo": "data:image/jpeg;base64,...",
    "gps_coordinates": {"lat": 6.5244, "lng": 3.3792}
}
```

### Track Report
```
GET /api/track/{tracking_number}
```

### Admin - List Reports
```
GET /api/admin/reports
Authorization: Bearer {token}
```

### Admin - Update Status
```
POST /api/admin/update-status
{
    "report_id": 1,
    "status": "scheduled"
}
```

### Budget Optimization
```
POST /api/budget/optimize
{
    "repairs": [...],
    "total_budget": 5000000,
    "strategy": "priority_weighted"
}
```

## Budget Optimization Strategies

1. **Priority-Weighted**: Balances severity, urgency, area, and depth
2. **Severity-First**: Prioritizes high-risk repairs
3. **Proportional**: Fair allocation based on estimated costs
4. **Hybrid**: Guarantees critical repairs, optimizes remainder

## AI Damage Detection

- **Model**: YOLOv8 via Roboflow
- **Input**: User-submitted images (max 10MB, PNG/JPG)
- **Output**: Damage type, location, confidence score
- **Processing**: OpenCV analyzes damage dimensions for severity estimation

## Deployment

### Backend (Render)
- Build Command: `pip install -r requirements.txt`
- Start Command: `bash start.sh`
- Environment: Set `ROBOFLOW_API_KEY`, `JWT_SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`

### Frontend (Vercel)
- Automatic deployment from GitHub
- Static file serving from `frontend/` directory
- Update API URL in `config.js` for production

## Testing

Run backend tests:
```bash
python -m unittest api/test_budget_pipeline.py
```

Run budget optimization tests:
```bash
cd budget_optimization
python test_budget_integration.py
```

Run integration tests:
```bash
python test_sync.py
```

## Troubleshooting

**Backend won't start**
- Check port 5000 not in use: `lsof -i :5000`
- Verify database connection: `SQLALCHEMY_DATABASE_URI` in .env
- Run `python api/scripts/debug.py` for diagnostics

**Reports not showing in admin**
- Verify database connection to Supabase
- Check admin authentication token valid
- Clear browser cache

**Images not uploading**
- Verify file size under 10MB
- Check file format (PNG/JPG)
- Ensure Roboflow API key is valid

**GPS not detecting location**
- Requires HTTPS or localhost
- Check browser geolocation permissions
- Verify GPS service enabled on device

## Configuration


### Database
Use Supabase PostgreSQL connection string:
```
SQLALCHEMY_DATABASE_URI=postgresql://user:password@host:port/database
```

## File Upload Security

- Max file size: 10MB
- Allowed formats: PNG, JPG, JPEG
- Files stored in `/tmp/uploads` with unique names
- Automatic format conversion to JPEG

## Known Limitations

- Currently covers Lagos State only
- Roboflow free tier has API rate limits
- Mobile camera tested on modern browsers
- GPS detection requires HTTPS or localhost

## Support

- Email: t.omunizua@alustudent.com
- GitHub: https://github.com/tomunizua/road-infra-ng
- Final report: https://docs.google.com/document/d/1Ikngcf0tBQV4sPO6RzzWXpw5DFOlAZNf/edit?usp=sharing&ouid=117352081927827611025&rtpof=true&sd=true

## License

ALU Software Engineering Capstone Project