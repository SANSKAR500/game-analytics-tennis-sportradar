-- MySQL 8: run from the project root, with local infile enabled:
--   mysql --local-infile=1 -u root -p < sql/load_mysql.sql
SET GLOBAL local_infile = 1;
SOURCE sql/tennis_queries_mysql.sql;
USE tennis_db;
LOAD DATA LOCAL INFILE 'data/categories.csv' INTO TABLE categories
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES
  (category_id, category_name);
LOAD DATA LOCAL INFILE 'data/competitions.csv' INTO TABLE competitions
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES
  (competition_id, competition_name, @parent_id, type, gender, category_id)
  SET parent_id = NULLIF(@parent_id, '');
LOAD DATA LOCAL INFILE 'data/complexes.csv' INTO TABLE complexes
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/venues.csv' INTO TABLE venues
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/competitors.csv' INTO TABLE competitors
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/competitor_rankings.csv' INTO TABLE competitor_rankings
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES
  (`rank`, movement, points, competitions_played, competitor_id);
