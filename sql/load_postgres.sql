-- PostgreSQL: run from the project root (the folder that contains sql/ and data/):
--   createdb -U postgres tennis_db
--   psql -U postgres -d tennis_db -f sql/load_postgres.sql
\i sql/tennis_queries_postgres.sql
\copy categories FROM 'data/categories.csv' CSV HEADER
\copy competitions FROM 'data/competitions.csv' CSV HEADER
\copy complexes FROM 'data/complexes.csv' CSV HEADER
\copy venues FROM 'data/venues.csv' CSV HEADER
\copy competitors FROM 'data/competitors.csv' CSV HEADER
\copy competitor_rankings (rank, movement, points, competitions_played, competitor_id) FROM 'data/competitor_rankings.csv' CSV HEADER
