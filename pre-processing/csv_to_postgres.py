"""
CSV to PostgreSQL Import Script
Imports papers from CSV and optionally creates users
"""

import pandas as pd
import psycopg2
import sys
import os
import bcrypt
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'paper-filter'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'your_password_here')
}

# Default users (optional - can be created via signup instead)
USERS = [
    {'username': 'reviewer1', 'password': 'pass', 'display_name': 'Callum', 'role': 'reviewer'},
    {'username': 'reviewer2', 'password': 'pass', 'display_name': 'Rohan', 'role': 'reviewer'},
    {'username': 'moderator', 'password': 'pass', 'display_name': 'Daniil', 'role': 'moderator'},
    {'username': 'systems', 'password': 'pass', 'display_name': 'Systems', 'role': 'systems'},
    {'username': 'supervisor', 'password': 'pass', 'display_name': 'Supervisor', 'role': 'supervisor'},
]


def import_papers_from_csv(csv_path, conn):
    """
    Import papers from CSV to PostgreSQL

    Args:
        csv_path: Path to CSV file
        conn: PostgreSQL connection
    """

    print(f"Loading papers from {csv_path}...")
    df = pd.read_csv(csv_path)

    print(f"Total papers to import: {len(df):,}\n")

    cursor = conn.cursor()
    imported = 0
    skipped = 0

    print("Importing papers...")
    for idx, row in df.iterrows():
        try:
            # Get title
            title = row.get('Title', '')

            # Skip if title is empty
            if pd.isna(title) or str(title).strip() == '':
                skipped += 1
                continue

            # Get other fields
            authors = row.get('Authors', None)
            year = row.get('Year', None)
            abstract = row.get('Abstract', None)
            doi = row.get('DOI', None)
            source = row.get('Source title', None)

            # Convert year to int if possible
            if pd.notna(year):
                try:
                    year = int(float(year))
                except (TypeError, ValueError):
                    year = None

            # Insert paper
            cursor.execute("""
                           INSERT INTO papers (title, authors, year, abstract, doi, source)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           """, (
                               str(title),
                               str(authors) if pd.notna(authors) else None,
                               year,
                               str(abstract) if pd.notna(abstract) else None,
                               str(doi) if pd.notna(doi) else None,
                               str(source) if pd.notna(source) else None
                           ))

            imported += 1

            # Commit every 100 papers
            if imported % 100 == 0:
                conn.commit()
                print(f"Imported {imported:,}/{len(df):,} papers...")

        except Exception as e:
            print(f"Error importing row {idx}: {e}")
            skipped += 1
            continue

    conn.commit()

    print("\nPaper Import Complete")
    print(f"  Successfully imported: {imported:,}")
    print(f"  Skipped (empty titles): {skipped:,}")


def create_users(conn, users_list):
    """
    Create users in database with hashed passwords

    Args:
        conn: PostgreSQL connection
        users_list: List of dicts with keys: username, password, display_name, role
    """

    cursor = conn.cursor()

    print("\nCreating users...")
    created = 0
    skipped = 0

    for user in users_list:
        # Hash password
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

                # Create progress for reviewers
                if user['role'] == 'reviewer':
                    cursor.execute("""
                                   INSERT INTO user_progress (user_id, current_paper_index, total_kept, total_rejected)
                                   VALUES (%s, 0, 0, 0) ON CONFLICT (user_id) DO NOTHING
                                   """, (user_id,))

                print(f" Created user: {user['username']} ({user['role']})")
                created += 1
            else:
                print(f"  - User already exists: {user['username']}")
                skipped += 1

        except Exception as e:
            print(f" Error creating user {user['username']}: {e}")
            skipped += 1

    conn.commit()

    print("\nUser Creation Complete")
    print(f"  Created: {created}")
    print(f"  Skipped (already exist): {skipped}")


def main():
    """Main function for command-line usage"""

    if len(sys.argv) < 2:
        print("Usage: python csv_to_postgres.py <papers.csv> [--create-users]")
        print("\nExample:")
        print("  python csv_to_postgres.py ../data/processed/deduplicated.csv")
        print("  python csv_to_postgres.py ../data/processed/deduplicated.csv --create-users")
        print("\nNote: Make sure database tables are already created!")
        print("      Run the SQL setup script first if needed.")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    create_users_flag = '--create-users' in sys.argv

    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("PostgreSQL Paper Import")
    print("=" * 60)

    print(f"\nDatabase: {DB_CONFIG['database']} @ {DB_CONFIG['host']}")
    print(f"CSV File: {csv_path}")

    try:
        # Connect to database
        print("\nConnecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Connected to database\n")

        # Import papers
        import_papers_from_csv(csv_path, conn)

        # Optionally create users
        if create_users_flag:
            create_users(conn, USERS)
        else:
            print("\nℹ Users not created (use --create-users flag to create them)")

        conn.close()

        print("\n" + "=" * 60)
        print("Import Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Start your Flask server: python server/app.py")
        print("  2. Sign up with invite codes or login with created users")
        print("  3. Begin reviewing papers!")

    except psycopg2.OperationalError as e:
        print(f"\nDatabase connection error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is PostgreSQL running?")
        print("  2. Are your credentials in .env correct?")
        print("  3. Does the database exist?")
        print("     Try: createdb paper-filter")
        sys.exit(1)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()