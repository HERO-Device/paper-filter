# Paper Filter - Collaborative Literature Review System

A collaborative web-based paper filtering system for the H.E.R.O. System literature review. Supports team-based paper review with consensus tracking, role-based access, and real-time progress monitoring.

## 🎯 Overview

This system enables a team of 8 reviewers + 1 supervisor to collaboratively filter through thousands of papers:
- **Groupmates**: Swipe through papers (Y/N) independently
- **Supervisor**: View only consensus papers (5+ keeps out of 8)
- **Admin**: Full access to all papers, votes, and analytics

## ✨ Features

- **Multi-User Authentication**: Secure signup with invite codes
- **Tinder-Style Swipe Interface**: Quick Y/N decisions with keyboard shortcuts
- **Consensus Tracking**: Papers with 5+ keeps automatically shown to supervisor
- **Real-Time Progress**: Live dashboard showing everyone's progress
- **Role-Based Access**: Different views for groupmates, supervisor, and admin
- **Export Capabilities**: CSV export of consensus papers and full results
- **AI-Powered Pre-Filtering**: Optional OpenAI integration to reduce paper count

## 📁 Project Structure
```
paper-filter/
├── preprocessing/              # Data preparation (run locally)
│   ├── data_processing.py      # Remove duplicates
│   ├── nlp_filter.py           # AI filtering with OpenAI
│   ├── csv_to_postgres.py      # Import to database
│   └── .env                    # OpenAI API key
│
├── server/                     # Flask application (deploy to server)
│   ├── app.py                  # Main application
│   ├── auth.py                 # Authentication logic
│   ├── config.py               # Configuration settings
│   ├── models.py               # Database queries
│   ├── .env                    # Database credentials
│   │
│   ├── routes/                 # API endpoints
│   │   ├── auth_routes.py      # Login/signup
│   │   ├── swipe_routes.py     # Swipe & progress
│   │   └── admin_routes.py     # Supervisor/admin
│   │
│   ├── templates/              # HTML pages
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── swipe.html          # Groupmate view
│   │   ├── progress.html       # Progress dashboard
│   │   ├── supervisor.html     # Consensus papers
│   │   └── admin.html          # Admin analytics
│   │
│   └── static/                 # JavaScript & CSS
│       ├── js/
│       │   ├── swipe.js
│       │   ├── progress.js
│       │   ├── supervisor.js
│       │   └── admin.js
│       └── css/
│           └── styles.css
│
├── data/                       # Data files (gitignored)
│   ├── raw/                    # Original Scopus exports
│   ├── processed/              # After preprocessing
│   └── exports/                # Final results
│
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 15+
- (Optional) OpenAI API key for NLP filtering

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL Database

**Option A: Docker (Recommended)**
```bash
docker run -d \
  --name paper_filter_db \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=paper-filter \
  -p 5432:5432 \
  postgres:15
```

**Option B: Local Installation**
- Install PostgreSQL from [postgresql.org](https://postgresql.org)
- Create database: `CREATE DATABASE paper_filter;`

### 3. Configure Environment Variables

**Create `server/.env`:**
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=paper-filter
DB_USER=postgres
DB_PASSWORD=your_password_here

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
```

**Create `preprocessing/.env`** (only if using NLP filtering):
```bash
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
BATCH_SIZE=50
```

### 4. Customize Invite Codes

Edit `server/config.py` and update the invite codes:
```python
INVITE_CODES = {
    'HERO-ALICE-2025': {'role': 'groupmate', 'suggested_name': 'Alice'},
    'HERO-BOB-2025': {'role': 'groupmate', 'suggested_name': 'Bob'},
    # ... add 6 more groupmates ...
    'HERO-SUPERVISOR-2025': {'role': 'supervisor', 'suggested_name': 'Dr. Smith'},
}
```

### 5. Prepare Your Data

**Step 1: Remove Duplicates**
```bash
cd preprocessing
python data_processing.py ../data/raw/scopus_export.csv ../data/processed/deduplicated.csv
```

**Step 2: (Optional) AI Filtering**
```bash
python nlp_filter.py ../data/processed/deduplicated.csv ../data/processed/
```
This reduces 15,000+ papers to ~2,000 high-quality papers using OpenAI.

**Step 3: Import to Database**
```bash
cd ../server
python -c "from config import config; import psycopg2; conn = psycopg2.connect(**config.DB_CONFIG); cursor = conn.cursor(); exec(open('setup_database.py').read())"
```

Or create a quick script to set up tables, then:
```bash
cd preprocessing
python csv_to_postgres.py ../data/processed/keep.csv
```

### 6. Import Your Papers
```bash
cd server
python import_papers.py ../data/processed/keep.csv
```

### 7. Run the Application
```bash
python app.py
```

Visit: **http://localhost:5000**

## 👥 User Workflow

### For Groupmates (8 People)

1. **Sign Up**: Visit `/signup` and use your invite code
2. **Create Account**: Choose username & password
3. **Login**: Access your swipe interface
4. **Swipe Papers**: Press `Y` (keep) or `N` (reject)
5. **Track Progress**: See your stats in real-time

**Keyboard Shortcuts:**
- `Y` = Keep paper
- `N` = Reject paper

### For Supervisor (1 Person)

1. **Sign Up**: Use supervisor invite code
2. **View Consensus**: See only papers with 5+ keeps (>50% agreement)
3. **Export Results**: Download consensus papers as CSV
4. **Monitor Progress**: Check team progress dashboard

### For Admin (You)

1. **Access Admin Panel**: Full analytics dashboard
2. **View All Papers**: See all papers with vote counts
3. **Filter & Export**: Export all data or consensus only
4. **Monitor Team**: Real-time progress tracking

## 📊 Consensus Logic

- Each paper receives 0-8 "keep" votes from groupmates
- Papers with **≥5 keeps** (>50%) appear in supervisor view
- Papers with <5 keeps are filtered out
- Admin sees all papers regardless of votes

## 🔧 Advanced Features

### NLP Pre-Filtering

Customize your filtering criteria in `preprocessing/nlp_filter.py`:
```python
INCLUSION_CRITERIA = """
Include papers that:
- Focus on neurodegenerative diseases
- Involve EEG or eye tracking
- Discuss wearable monitoring
"""

EXCLUSION_CRITERIA = """
Exclude papers that:
- Are review papers
- Focus only on animal studies
- Don't involve monitoring technology
"""
```

### Export Options

**Supervisor Export:**
- Only consensus papers (5+ keeps)
- Includes vote counts

**Admin Export:**
- All papers with vote statistics
- Individual user decisions
- Customizable filters

## 🐛 Troubleshooting

### "Database does not exist"
```bash
# Check database name matches .env
psql -U postgres -l
# Create if needed
createdb paper-filter
```

### "Connection refused on port 5432"
```bash
# Check PostgreSQL is running
docker ps  # if using Docker
# or
pg_isready
```

### "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### "Invite code invalid"
- Check `server/config.py` for available codes
- Ensure code hasn't been used already
- Codes are case-sensitive

### Import issues with route files
- Make sure you're running from the `server/` directory
- Imports use absolute paths, not relative

## 📈 Workflow Example

### Complete Literature Review Process

**Week 1: Data Preparation (You)**
```bash
# 1. Remove duplicates (15,913 → 15,500 papers)
python preprocessing/data_processing.py data/raw/scopus.csv

# 2. AI filtering (15,500 → 2,000 papers)
python preprocessing/nlp_filter.py data/processed/deduplicated.csv

# 3. Import to database
python preprocessing/csv_to_postgres.py data/processed/keep.csv
```

**Week 2: Team Review (8 Groupmates)**
- Each person reviews all 2,000 papers independently
- ~250 papers per day per person
- Takes 1-2 weeks depending on pace

**Week 3: Supervisor Review**
- Reviews consensus papers (~500-800 papers)
- Makes final inclusion decisions
- Exports final paper list

**Final Output:**
- Started: 15,913 papers
- After AI: 2,000 papers
- After consensus: ~500-800 papers
- Final review: ~200-400 papers for full text screening

## 🔐 Security Notes

- **Change SECRET_KEY in production**: Use a random 32-character string
- **Use strong passwords**: Enforce 8+ characters, mixed case, numbers
- **HTTPS recommended**: Use nginx reverse proxy with SSL certificate
- **Backup database regularly**: `pg_dump paper-filter > backup.sql`
- **Keep .env files secret**: Never commit to git

## 📝 Tips & Best Practices

1. **Start with AI filtering**: Reduces workload significantly
2. **Test with 10 papers first**: Import a small sample to test workflow
3. **Communicate with team**: Use the progress dashboard to coordinate
4. **Review in short sessions**: 50-100 papers at a time to avoid fatigue
5. **Export frequently**: Download consensus papers at regular intervals
6. **Monitor progress**: Check dashboard daily to ensure everyone is contributing

## 🤝 Contributing

This is a custom tool for the H.E.R.O. System project. For questions or issues, contact the project coordinator.

## 📜 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built for the H.E.R.O. System literature review at the University of Warwick.