# Changes to the SQL and CSV data

## Data (csv/)
- competitions.csv
  - Tournament parents (rows with sub-events) and team events: type `mixed` -> `tournament`.
  - Australian Open Mixed Doubles (sr:competition:30) and Wimbledon Mixed Doubles (sr:competition:31): type `mixed` -> `doubles`, so `type = 'doubles'` finds them.
  - United Cup Mixed Team (sr:competition:33): category Grand Slam -> United Cup.
- categories.csv
  - Added `sr:category:united-cup,United Cup`. This ID is a placeholder. Replace it with the ID from the Sportradar API if you have one, and update competitions.csv to match.

## SQL (both dialects)
- Comment on `competitions.type` updated to list the new values.
- Query 3.3 comment notes that it includes mixed doubles.
- Query 5.6 relabelled as the latest snapshot. The data has no week column.

## Loading
- load_postgres.sql: blank parent_id loads as NULL automatically.
- load_mysql.sql: uses NULLIF(@parent_id, '') so blank parent_id loads as NULL.

## Not changed (still open)
- No competition level column.
- No competitor-to-competition link, so singles/doubles participation can't be answered.
- No week/year column in competitor_rankings.

## Code and app fixes (review pass)
- `scripts/api_client.py`: HTTP errors without a response compared a string to a number and would crash. Fixed.
- `scripts/collect_*.py`: now stop with a clear error if the expected root key is missing, instead of writing empty CSVs.
- `app/db.py`: queries run through a read-only cursor. Settings come from Streamlit secrets or environment variables. Decimal values become floats.
- `app/app.py`: results are cached for 10 minutes. `use_container_width` replaced with `width="stretch"` (the old argument is being removed from Streamlit).
- `requirements.txt`: Streamlit pinned to `>=1.67,<2`, the version the app was tested with.
- `sql/load_postgres.sql` and `sql/load_mysql.sql`: paths now resolve from the project root, as the README describes.
- README: added Streamlit Community Cloud deployment steps and a secrets example.
