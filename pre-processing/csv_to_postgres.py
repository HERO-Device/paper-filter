import pandas as pd
import psycopg2
from psycopg2 import sql
import sys
import os
import bcrypt
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'paper_filter'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'your_password_here')
}

USERS = [
    {'username': 'callum', 'password': 'Pass', 'display_name': 'Callum', 'role': 'groupmate'},
    {'username': 'daniil', 'password': 'Pass', 'display_name': 'Daniil ', 'role': 'groupmate'},
    {'username': 'dylan', 'password': 'Pass', 'display_name': 'Dylan', 'role': 'groupmate'},
    {'username': 'ellen', 'password': 'Pass', 'display_name': 'Ellen', 'role': 'groupmate'},
    {'username': 'koko', 'password': 'Pass', 'display_name': 'Koko', 'role': 'groupmate'},
    {'username': 'manqi', 'password': 'Pass', 'display_name': 'Manqi', 'role': 'groupmate'},
    {'username': 'rohan', 'password': 'Pass', 'display_name': 'Rohan', 'role': 'groupmate'},
    {'username': 'ratul', 'password': 'Pass', 'display_name': 'Ratul', 'role': 'groupmate'},
    {'username': 'davide', 'password': 'Pass', 'display_name': 'Davide', 'role': 'supervisor'},
]


def create_database_schema(conn):
    """Create all necessary tables for the application"""

    cursor = conn.cursor()

    print("Creating database schema...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            display_name VARCHAR(100),
            role VARCHAR(20) NOT NULL CHECK (role IN ('groupmate', 'supervisor', 'admin')),
            invite_code VARCHAR(50) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Created 'users' table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT,
            year INTEGER,
            abstract TEXT,
            doi VARCHAR(255),
            source VARCHAR(100),
            nlp_confidence VARCHAR(20),
            nlp_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Created 'papers' table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS swipe_decisions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
            decision VARCHAR(10) NOT NULL CHECK (decision IN ('keep', 'reject')),
            decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, paper_id)
        );
    """)
    print("Created 'swipe_decisions' table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            current_paper_index INTEGER DEFAULT 0,
            total_kept INTEGER DEFAULT 0,
            total_rejected INTEGER DEFAULT 0,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Created 'user_progress' table")

    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_swipe_user ON swipe_decisions(user_id);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_swipe_paper ON swipe_decisions(paper_id);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_paper_title ON papers(title);
    """)
    print("Created indexes")

    conn.commit()
    print("Database schema created successfully\n")


def import_papers_from_csv(csv_path, conn):
    """
    Import papers from CSV to PostgreSQL

    Args:
        csv_path: Path to CSV file (should be keep.csv from NLP filtering)
        conn: PostgreSQL connection
    """

    print(f"Loading papers from {csv_path}...")
    df = pd.read_csv(csv_path)

    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'title' in col_lower:
            column_mapping['title'] = col
        elif 'author' in col_lower:
            column_mapping['authors'] = col
        elif 'year' in col_lower or 'date' in col_lower:
            column_mapping['year'] = col
        elif 'abstract' in col_lower:
            column_mapping['abstract'] = col
        elif 'doi' in col_lower:
            column_mapping['doi'] = col
        elif 'source' in col_lower or 'journal' in col_lower:
            column_mapping['source'] = col

    if 'nlp_confidence' in df.columns:
        column_mapping['nlp_confidence'] = 'nlp_confidence'

    if 'title' not in column_mapping:
        raise ValueError("Could not find title column in CSV")

    print(f"Found columns: {list(column_mapping.keys())}")
    print(f"Total papers to import: {len(df):,}\n")

    cursor = conn.cursor()
    imported = 0
    skipped = 0

    print("Importing papers...")
    for idx, row in df.iterrows():
        try:
            title = row[column_mapping['title']]

            # Skip if title is empty
            if pd.isna(title) or str(title).strip() == '':
                skipped += 1
                continue

            # Extract other fields (with defaults)
            authors = row.get(column_mapping.get('authors'), None)
            year = row.get(column_mapping.get('year'), None)
            abstract = row.get(column_mapping.get('abstract'), None)
            doi = row.get(column_mapping.get('doi'), None)
            source = row.get(column_mapping.get('source'), None)
            nlp_confidence = row.get(column_mapping.get('nlp_confidence'), None)

            if pd.notna(year):
                try:
                    year = int(float(year))
                except:
                    year = None

            cursor.execute("""
                           INSERT INTO papers (title, authors, year, abstract, doi, source, nlp_confidence)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                           """, (
                               str(title),
                               str(authors) if pd.notna(authors) else None,
                               year,
                               str(abstract) if pd.notna(abstract) else None,
                               str(doi) if pd.notna(doi) else None,
                               str(source) if pd.notna(source) else None,
                               str(nlp_confidence) if pd.notna(nlp_confidence) else None
                           ))

            imported += 1

            if imported % 100 == 0:
                conn.commit()
                print(f"Imported {imported:,}/{len(df):,} papers...")

        except Exception as e:
            print(f"Error importing row {idx}: {e}")
            skipped += 1

    conn.commit()

    print("\nPaper Import Complete")
    print(f"Successfully imported: {imported:,}")
    print(f"Skipped: {skipped:,}")


def create_users(conn, users_list):
    """
    Create users in database with hashed passwords

    Args:
        conn: PostgreSQL connection
        users_list: List of dicts with keys: username, password, display_name, role
    """

    cursor = conn.cursor()

    print("Creating users...")
    created = 0
    skipped = 0

    for user in users_list:
        password_hash = bcrypt.hashpw(
            user['password'].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        try:
            cursor.execute("""
                           INSERT INTO users (username, password_hash, display_name, role)
                           VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING
                RETURNING id
                           """, (
                               user['username'],
                               password_hash,
                               user.get('display_name', user['username']),
                               user['role']
                           ))

            result = cursor.fetchone()

            if result:
                user_id = result[0]

                if user['role'] == 'groupmate':
                    cursor.execute("""
                                   INSERT INTO user_progress (user_id, current_paper_index, total_kept, total_rejected)
                                   VALUES (%s, 0, 0, 0) ON CONFLICT (user_id) DO NOTHING
                                   """, (user_id,))

                print(f"Created user: {user['username']} ({user['role']})")
                created += 1
            else:
                print(f"User already exists: {user['username']}")
                skipped += 1

        except Exception as e:
            print(f"Error creating user {user['username']}: {e}")
            skipped += 1

    conn.commit()

    print("\nUser Creation Complete")
    print(f"Created: {created}")
    print(f"Skipped (already exist): {skipped}")


def main():
    """Main function for command-line usage"""

    if len(sys.argv) < 2:
        print("Usage: python csv_to_postgres.py <keep.csv> [--create-users]")
        print("\nExample:")
        print("  python csv_to_postgres.py ../data/processed/keep.csv")
        print("  python csv_to_postgres.py ../data/processed/keep.csv --create-users")
        print("\nMake sure to set database credentials in .env file:")
        print("  DB_HOST=localhost")
        print("  DB_PORT=5432")
        print("  DB_NAME=paper_filter")
        print("  DB_USER=postgres")
        print("  DB_PASSWORD=your_password")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    create_users_flag = '--create-users' in sys.argv

    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    print("\nPostgreSQL Database Setup\n")

    print("Connecting to PostgreSQL...")
    print(f"  Host: {DB_CONFIG['host']}")
    print(f"  Database: {DB_CONFIG['database']}")
    print(f"  User: {DB_CONFIG['user']}")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected to database\n")

        create_database_schema(conn)

        import_papers_from_csv(csv_path, conn)

        if create_users_flag:
            create_users(conn, USERS)
            print("Users have temporary passwords!")
            print("They should change them after first login.\n")
        else:
            print("ℹ Users not created (use --create-users flag to create them)\n")

        conn.close()

        print("\nDatabase setup complete!\n")
        print("Next steps:")
        print("  1. Start your Flask server")
        print("  2. Users can sign up or log in")
        print("  3. Begin swiping through papers!")

    except psycopg2.OperationalError as e:
        print(f"\nDatabase connection error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is PostgreSQL running?")
        print("  2. Are your .env credentials correct?")
        print("  3. Does the database exist?")
        print("     CREATE DATABASE paper_filter;")
        sys.exit(1)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
