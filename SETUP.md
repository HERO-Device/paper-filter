# Setup Guide

## Server Deployment

### 1. Install Prerequisites
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y
```

### 2. Configure PostgreSQL
```bash
# Set PostgreSQL password
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'your_password';"

# Edit pg_hba.conf to allow Docker connections
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

Add these lines:
```
host    all             all             172.17.0.0/16           md5
host    all             all             172.19.0.0/16           md5
```
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/16/main/postgresql.conf
```

Change:
```
listen_addresses = '*'
port = 5433
```
```bash
# Restart PostgreSQL
sudo systemctl restart postgresql@16-main
```

### 3. Set Up Database
```bash
# Create database
sudo -u postgres psql -c 'CREATE DATABASE "paper-filter";'

# Run setup script
sudo -u postgres psql -d paper-filter -f setup_database.sql
```

### 4. Configure Application
```bash
# Copy environment template
cp server/.env.example server/.env

# Edit with your settings
nano server/.env
```

Update:
- `DB_HOST=172.17.0.1` (Docker bridge IP)
- `DB_PORT=5433`
- `DB_PASSWORD=your_password`
- `SECRET_KEY=generate_random_key`

### 5. Deploy with Docker
```bash
# Build image
docker-compose build

# Start container
docker-compose up -d

# Check logs
docker-compose logs -f app
```

### 6. Import Papers 
```bash
# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install pandas psycopg2-binary python-dotenv

# Update pre-processing/.env
nano pre-processing/.env
```

Set:
```
DB_HOST=localhost
DB_PORT=5433
DB_NAME=paper-filter
DB_USER=postgres
DB_PASSWORD=your_password
```
```bash
# Import papers
python pre-processing/csv_to_postgres.py data/processed/your_file.csv --create-users

deactivate
```

## Tailscale Setup (Remote Access)

### On Server
```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Connect to Tailscale
sudo tailscale up

# Get Tailscale IP
tailscale ip -4
```

### Share with Team

Option 1 - Share machine:
```bash
tailscale share home-server user@example.com
```

Option 2 - Tailscale Admin Console:
1. Go to https://login.tailscale.com/admin/machines
2. Find your server
3. Click "Share"
4. Add team email addresses

## Troubleshooting

### Can't connect to database from Docker

Check PostgreSQL is listening:
```bash
sudo ss -tlnp | grep 5433
```

Should show `0.0.0.0:5433`, not `127.0.0.1:5433`

### Docker can't reach host database

Test connection:
```bash
docker exec -it paper_filter_app psql -h 172.17.0.1 -p 5433 -U postgres -d paper-filter -c '\dt'
```

### Papers not loading

Check paper count:
```bash
sudo -u postgres psql -d paper-filter -p 5433 -c "SELECT COUNT(*) FROM papers;"
```

## Maintenance

### Update application
```bash
cd ~/projects/HERO/paper-filter
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

### Backup database
```bash
sudo -u postgres pg_dump -d paper-filter -p 5433 > backup_$(date +%Y%m%d).sql
```

### View logs
```bash
docker-compose logs -f app
```