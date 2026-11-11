# Game Analytics: Unlocking Tennis Data with SportRadar API

A student data analytics project using the Sportradar Tennis API, PostgreSQL, SQL, Python, and Streamlit.

## Project objectives

- Collect competition, complex/venue, and doubles ranking data from Sportradar.
- Flatten nested JSON into normalized CSV datasets.
- Load the datasets into PostgreSQL (with MySQL 8 scripts also supplied).
- Explore rankings, countries, competitions, complexes, and venues through SQL and Streamlit.
- Demonstrate API error handling, data validation, relational design, and dashboard development.

## Architecture

```text
Sportradar API
      |
      v
Python collectors
      |
      v
CSV reference datasets
      |
      v
PostgreSQL / MySQL
      |
      v
Parameterized SQL
      |
      v
Streamlit dashboard
```

## Repository structure

```text
scripts/    API client, collectors, validation
sql/        PostgreSQL/MySQL schema + queries + loaders
data/       CSV reference data
app/        Streamlit app + database/query modules
tests/      automated validation test
report.md   final project report
```

## 1. Environment setup

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` from `.env.example` and add your own Sportradar API key and PostgreSQL credentials.

**Never commit `.env` or an API key. If an API key has accidentally been exposed, rotate it in the Sportradar console.**

## 2. Sportradar API

The collectors target Tennis API v3:

- `GET /tennis/{access_level}/v3/{language}/competitions.json`
- `GET /tennis/{access_level}/v3/{language}/complexes.json`
- `GET /tennis/{access_level}/v3/{language}/double_competitors_rankings.json`

The API uses the `x-api-key` header. The official documentation describes the common v3 URL shape and the endpoint response fields.

Run collectors from the project root:

```bash
python scripts/collect_competitions.py
python scripts/collect_complexes.py
python scripts/collect_rankings.py
```

Dry-run mode prints counts without overwriting CSVs:

```bash
python scripts/collect_competitions.py --dry-run
python scripts/collect_complexes.py --dry-run
python scripts/collect_rankings.py --dry-run
```

## 3. Validate CSV data

```bash
python scripts/validate_data.py
pytest -q
```

Validation checks column order, required values, duplicate primary keys, and these foreign-key relationships:

- competition → category
- venue → complex
- ranking → competitor

## 4. PostgreSQL

Create a database, then load the schema and CSVs:

```bash
createdb -U postgres tennis_db
psql -U postgres -d tennis_db -f sql/load_postgres.sql
```

The PostgreSQL loader uses the supplied schema and `COPY` commands. Blank `parent_id` values are loaded as SQL `NULL` by PostgreSQL CSV parsing.

## 5. MySQL 8 (optional)

Enable local infile if required and run:

```bash
mysql --local-infile=1 -u root -p < sql/load_mysql.sql
```

The MySQL loader explicitly converts blank `parent_id` values to `NULL` with `NULLIF`.

## 6. Run Streamlit locally

The app reads database settings from `.env` (or from Streamlit secrets when deployed).

```bash
streamlit run app/app.py
```

## 6a. Deploy to Streamlit Community Cloud

Streamlit Community Cloud cannot reach a database on your own computer, so the PostgreSQL database must be hosted online (for example, a free Neon or Supabase Postgres project).

1. Load the schema and CSVs into the hosted database (`sql/load_postgres.sql` uses `psql`; point it at the hosted host, or run `psql` with the connection string the host provides).
2. Push the repository to GitHub. Do not push `.env`.
3. In Streamlit Community Cloud, create a new app from the repository, with main file path `app/app.py`.
4. In the app's **Settings → Secrets**, paste the contents of `.streamlit/secrets.toml.example` with your real values.

The app reads the secrets first and falls back to environment variables, so the same code runs locally and on the cloud.


```bash
streamlit run app/app.py
```

The dashboard contains:

- Overview KPIs
- competitor search
- rank/country/points filters
- competitor details
- country analysis and chart
- top-points leaderboard
- biggest rank movers
- competition hierarchy and filters
- venue/complex/country browsing

Queries use PostgreSQL parameters rather than string concatenation. Large tables are paginated with `LIMIT`/`OFFSET`.

## Demo walkthrough

1. Open **Overview** and confirm the competitor/country/points KPIs.
2. Use **Competitors → Search** to search a player/team name.
3. Use **Competitors → Filter** to combine rank, country, and points constraints.
4. Open **Countries** to compare competitor counts and average points.
5. Open **Leaderboards** for the top 10 and biggest movers.
6. Open **Competitions** to inspect parent/sub-event relationships.
7. Open **Venues** to filter venues by country and complex.

### Screenshots

Add screenshots here after running the app:

```text
![Overview](docs/screenshots/overview.png)
![Competitors](docs/screenshots/competitors.png)
![Country analysis](docs/screenshots/countries.png)
![Competitions](docs/screenshots/competitions.png)
```

## Data limitations

- The database schema has no `level` column. The dashboard therefore uses **category as the level stand-in**, and the report documents this limitation.
- The current schema has no competitor-to-competition relationship, so it cannot determine whether a competitor participated in singles versus doubles competitions from the competition tables.
- The rankings API supplies ranking year/week metadata, but the current `competitor_rankings` schema does not persist those fields. Queries therefore describe the **latest loaded snapshot**, not a historical weekly series.
- This implementation collects **doubles competitor rankings**. It should not be presented as an ATP singles ranking dataset.

## Security

- API credentials are loaded from environment variables.
- `.env` is excluded by `.gitignore`.
- Database credentials are not stored in source code.
- SQL filters use bound parameters.

## Sources

Sportradar Tennis API documentation:
- https://developer.sportradar.com/tennis/reference/competitions
- https://developer.sportradar.com/tennis/reference/complexes
- https://developer.sportradar.com/tennis/reference/doubles-competitor-rankings
- https://developer.sportradar.com/tennis/docs/tennis-ig-api-basics
