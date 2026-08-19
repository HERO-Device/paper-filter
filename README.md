# paper-filter

Web-based collaborative paper filtering system, built to run the systematic literature
review behind the H.E.R.O project.

The review followed Joanna Briggs Institute scoping review methodology and was reported
under PRISMA-ScR. A Scopus search was run on 25 November 2025 against a search string
verified by Dr Damon Hoad. This tool handled the screening stage: every candidate paper
was reviewed independently by two reviewers at title/abstract and full-text stages, with
disagreements resolved by a moderator. The resulting review is Section 2 of the
[project report](https://github.com/HERO-Device/hero_system/blob/main/docs/ES410_HERO_Project_Report.pdf).

This is a research tool, not part of the H.E.R.O device. The device repositories are
[`hero_core`](https://github.com/HERO-Device/hero_core),
[`hero_system`](https://github.com/HERO-Device/hero_system) and
[`hero_portal`](https://github.com/HERO-Device/hero_portal).

---

## Features

- Swipe-based paper review interface
- Multi-role workflow: reviewers, moderator, systems reviewer, supervisor
- Real-time consensus tracking
- Progress dashboard
- Role-based access control via invite codes
- Optional LLM-assisted pre-filtering of abstracts

---

## Repository layout

```
paper-filter/
├── server/
│   ├── app.py              Flask application factory and entry point.
│   ├── auth.py             Login, signup, invite-code role assignment.
│   ├── config.py           Configuration and invite codes.
│   ├── models/             Data access, one module per entity.
│   ├── routes/             Blueprints, one per role.
│   ├── templates/          Jinja templates, one per role view.
│   ├── static/             CSS and per-role JavaScript.
│   └── migrations/         Incremental SQL applied after setup_database.sql.
├── pre-processing/
│   ├── data_processing.py  Scopus export cleaning and deduplication.
│   ├── nlp_filter.py       LLM-assisted abstract pre-filtering.
│   └── csv_to_postgres.py  Bulk import of processed papers.
├── data/
│   ├── raw/                Scopus exports as downloaded.
│   └── processed/          Deduplicated output.
├── setup_database.sql      Full schema.
├── Dockerfile
└── docker-compose.yml
```

---

## Quick start

### Prerequisites

- Python 3.11 or newer, or Docker and Docker Compose
- PostgreSQL 16

### Install

```bash
git clone https://github.com/HERO-Device/paper-filter.git
cd paper-filter

# Environment
cp server/.env.example server/.env
cp pre-processing/.env.example pre-processing/.env
# Edit both with your credentials

# Database
sudo -u postgres psql -c 'CREATE DATABASE "paper-filter";'
sudo -u postgres psql -d paper-filter -f setup_database.sql
sudo -u postgres psql -d paper-filter -f server/migrations/add_abstract_stage.sql
```

### Run with Docker

```bash
docker-compose up -d
```

### Run directly

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server/app.py
```

Available at <http://localhost:5000>.

### Import papers

```bash
python pre-processing/data_processing.py          # Clean and deduplicate a Scopus export
python pre-processing/nlp_filter.py               # Optional, needs OPENAI_API_KEY
python pre-processing/csv_to_postgres.py data/processed/deduplicated.csv
```

---

## Configuration

Both `.env` files are documented by their `.env.example` counterparts.

`server/.env`: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `SECRET_KEY`,
`FLASK_ENV`, `FLASK_DEBUG`, `SERVER_HOST`, `SERVER_PORT`.

`pre-processing/.env`: `OPENAI_API_KEY`, `OPENAI_MODEL`, `BATCH_SIZE`.

Invite codes are defined in `server/config.py` and map a new signup to a role.

---

## Workflow

1. **Reviewers**, two of them, screen every paper and may flag one for systems review.
2. **Moderator** resolves disputes where the two reviewers disagree.
3. **Systems reviewer** handles only the flagged papers.
4. **Supervisor** views consensus results and exports CSV.

See [WORKFLOW.md](WORKFLOW.md) for the full process and [SETUP.md](SETUP.md) for
deployment detail.

---

## Known issues for whoever picks this up

1. **Invite codes are published in this README and in `server/config.py`.** They are the
   only thing gating role assignment. Rotate them before any further deployment.
2. **`SECRET_KEY` defaults to `dev-secret-key-change-in-production`** in the example
   environment file. Flask sessions are not secure until it is changed.

3. **`pre-processing/csv_to_postgres.py` seeds five named accounts with the password
   `pass`.** `reviewer1` (Callum), `reviewer2` (Rohan), `moderator` (Daniil), `systems`
   and `supervisor` are all created with the same trivial password, bcrypt-hashed on
   insert but plaintext in source. If these accounts are still in use anywhere, rotate
   the passwords before handoff.

4. **The admin dashboard assumes an obsolete review model.** `server/static/js/admin.js`
   treats `keep_votes >= 5` as consensus and `total_votes >= 8` as fully reviewed, which
   dates from an earlier design with eight reviewers. The current workflow has two. The
   `/api/admin/all-papers` endpoint now returns real vote counts, but those two
   thresholds still need correcting to match the two-reviewer workflow.

## A note on `data/`

The 10 MB under `data/` is kept in version control on purpose. `data/raw/` holds the
Scopus export exactly as downloaded on 27 December 2025, and `data/processed/` holds the
deduplicated output. These are the provenance for a PRISMA-ScR review, so removing them
to save repository size would make the literature review unreproducible.

---

## Citation

Firat, R., Luo, M., Nixon-Antón, E., Puri, D., Scholes, C., Taylor-Takahashi, K.,
Vaish, R., and Zotkin, D. (2026). *H.E.R.O (Health and Emotion Remote Observation)*.
ES410 Group Project, School of Engineering, University of Warwick. Supervised by
Dr Davide Piaggio.

## License

MIT. See [LICENSE](LICENSE).
