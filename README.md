# Paper Filter - Literature Review Tool

Web-based collaborative paper filtering system designed for the HERO project systematic literature review.

## Features

- Swipe-based paper review interface (Paper Tinder)
- Multi-role workflow (Reviewers, Moderator, Systems, Supervisor)
- Real-time consensus tracking
- Progress dashboard
- Role-based access control

## Quick Start

### Prerequisites
- Docker & Docker Compose
- PostgreSQL 16
- Tailscale (for remote access)

### Installation
```bash
# Clone repository
git clone https://github.com/HERO-Device/paper-filter.git
cd paper-filter

# Set up environment
cp server/.env.example server/.env
# Edit server/.env with your database credentials

# Set up database
sudo -u postgres psql -c 'CREATE DATABASE "paper-filter";'
sudo -u postgres psql -d paper-filter -f setup_database.sql

# Import papers (optional)
python pre-processing/csv_to_postgres.py data/processed/your_file.csv

# Run with Docker
docker-compose up -d
```

### Access

- Local: `http://localhost:5000`
- Tailscale: `http://server_ip:5000`

## Invite Codes

Configure in `server/config.py`:
- `HERO-REVIEWER1-2025` - Reviewer role
- `HERO-REVIEWER2-2025` - Reviewer role
- `HERO-MODERATOR-2025` - Moderator role
- `HERO-SYSTEMS-2025` - Systems reviewer role
- `HERO-SUPERVISOR-2025` - Supervisor (view-only)
- `HERO-ADMIN-2025` - Admin access

## Workflow

1. **Reviewers** (2) - Review all papers, can flag for systems review
2. **Moderator** - Resolves disputes (1 yes, 1 no)
3. **Systems** - Reviews flagged papers only
4. **Supervisor** - Views consensus results, exports CSV

See [WORKFLOW.md](WORKFLOW.md) for details.

## Documentation

- [Setup Guide](SETUP.md) - Deployment and configuration
- [Workflow Guide](WORKFLOW.md) - Review process details

## License

MIT