-- CORRECTED VERSION: type values fixed (tournament / doubles), United Cup category fixed,
-- query 5.6 relabelled as a snapshot (no week column in the data). See CHANGES.md.
-- =====================================================================
-- Game Analytics: Unlocking Tennis Data with SportRadar API
-- SQL script for MySQL 8+
-- Sections: 1) Schema  2) Indexes  3) Competitions queries
--           4) Venues/Complexes queries  5) Competitor rankings queries
-- =====================================================================

CREATE DATABASE IF NOT EXISTS tennis_db;
USE tennis_db;

-- =====================================================================
-- 1. SCHEMA
-- =====================================================================

-- Drop in reverse dependency order so the script can be re-run safely
DROP TABLE IF EXISTS competitor_rankings;
DROP TABLE IF EXISTS competitors;
DROP TABLE IF EXISTS venues;
DROP TABLE IF EXISTS complexes;
DROP TABLE IF EXISTS competitions;
DROP TABLE IF EXISTS categories;

-- ---------- Competitions module ----------
CREATE TABLE categories (
    category_id   VARCHAR(50)  PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

CREATE TABLE competitions (
    competition_id   VARCHAR(50)  PRIMARY KEY,
    competition_name VARCHAR(100) NOT NULL,
    parent_id        VARCHAR(50)  NULL,          -- NULL = top-level competition
    type             VARCHAR(20)  NOT NULL,      -- singles / doubles for events; tournament for parent events and team events
    gender           VARCHAR(10)  NOT NULL,      -- e.g. men / women / mixed
    category_id      VARCHAR(50),
    CONSTRAINT fk_competitions_category
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
);
-- NOTE: no FK on parent_id on purpose: the API can return a parent_id whose
-- parent row is not part of the response, which would break bulk inserts.

-- ---------- Complexes / venues module ----------
CREATE TABLE complexes (
    complex_id   VARCHAR(50)  PRIMARY KEY,
    complex_name VARCHAR(100) NOT NULL
);

CREATE TABLE venues (
    venue_id     VARCHAR(50)  PRIMARY KEY,
    venue_name   VARCHAR(100) NOT NULL,
    city_name    VARCHAR(100) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    country_code CHAR(3)      NOT NULL,
    timezone     VARCHAR(100) NOT NULL,
    complex_id   VARCHAR(50),
    CONSTRAINT fk_venues_complex
        FOREIGN KEY (complex_id) REFERENCES complexes (complex_id)
);

-- ---------- Doubles rankings module ----------
CREATE TABLE competitors (
    competitor_id VARCHAR(50)  PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    country       VARCHAR(100) NOT NULL,
    country_code  CHAR(3)      NOT NULL,
    abbreviation  VARCHAR(10)  NOT NULL
);

CREATE TABLE competitor_rankings (
    rank_id             INT AUTO_INCREMENT PRIMARY KEY,
    `rank`              INT NOT NULL,
    movement            INT NOT NULL,
    points              INT NOT NULL,
    competitions_played INT NOT NULL,
    competitor_id       VARCHAR(50),
    CONSTRAINT fk_rankings_competitor
        FOREIGN KEY (competitor_id) REFERENCES competitors (competitor_id)
);

-- =====================================================================
-- 2. INDEXES (foreign keys + columns used in WHERE / GROUP BY / ORDER BY)
-- =====================================================================
CREATE INDEX idx_competitions_category  ON competitions (category_id);
CREATE INDEX idx_competitions_parent    ON competitions (parent_id);
CREATE INDEX idx_competitions_type      ON competitions (type);
CREATE INDEX idx_venues_complex         ON venues (complex_id);
CREATE INDEX idx_venues_country         ON venues (country_name);
CREATE INDEX idx_rankings_competitor    ON competitor_rankings (competitor_id);
CREATE INDEX idx_rankings_rank          ON competitor_rankings (`rank`);
CREATE INDEX idx_rankings_points        ON competitor_rankings (points);
CREATE INDEX idx_competitors_country    ON competitors (country);

-- =====================================================================
-- 3. COMPETITIONS QUERIES
-- =====================================================================

-- 3.1 List all competitions along with their category name
SELECT c.competition_id,
       c.competition_name,
       c.type,
       c.gender,
       cat.category_name
FROM competitions c
LEFT JOIN categories cat ON cat.category_id = c.category_id
ORDER BY cat.category_name, c.competition_name;

-- 3.2 Count the number of competitions in each category
SELECT cat.category_id,
       cat.category_name,
       COUNT(c.competition_id) AS total_competitions
FROM categories cat
LEFT JOIN competitions c ON c.category_id = cat.category_id
GROUP BY cat.category_id, cat.category_name
ORDER BY total_competitions DESC;

-- 3.3 Find all competitions of type 'doubles' (includes mixed doubles events)
SELECT competition_id, competition_name, gender, category_id
FROM competitions
WHERE type = 'doubles'
ORDER BY competition_name;

-- 3.4 Get competitions that belong to a specific category (e.g., ITF Men)
SELECT c.competition_id, c.competition_name, c.type, c.gender
FROM competitions c
JOIN categories cat ON cat.category_id = c.category_id
WHERE cat.category_name = 'ITF Men'
ORDER BY c.competition_name;

-- 3.5 Identify parent competitions and their sub-competitions
SELECT p.competition_id   AS parent_id,
       p.competition_name AS parent_competition,
       s.competition_id   AS sub_competition_id,
       s.competition_name AS sub_competition
FROM competitions s
JOIN competitions p ON p.competition_id = s.parent_id
ORDER BY p.competition_name, s.competition_name;

-- 3.6 Analyze the distribution of competition types by category
SELECT cat.category_name,
       c.type,
       COUNT(*) AS total_competitions
FROM competitions c
JOIN categories cat ON cat.category_id = c.category_id
GROUP BY cat.category_name, c.type
ORDER BY cat.category_name, total_competitions DESC;

-- 3.7 List all competitions with no parent (top-level competitions)
SELECT competition_id, competition_name, type, gender, category_id
FROM competitions
WHERE parent_id IS NULL
ORDER BY competition_name;

-- =====================================================================
-- 4. COMPLEXES & VENUES QUERIES
-- =====================================================================

-- 4.1 List all venues along with their associated complex name
SELECT v.venue_id,
       v.venue_name,
       v.city_name,
       v.country_name,
       cx.complex_name
FROM venues v
LEFT JOIN complexes cx ON cx.complex_id = v.complex_id
ORDER BY cx.complex_name, v.venue_name;

-- 4.2 Count the number of venues in each complex
SELECT cx.complex_id,
       cx.complex_name,
       COUNT(v.venue_id) AS total_venues
FROM complexes cx
LEFT JOIN venues v ON v.complex_id = cx.complex_id
GROUP BY cx.complex_id, cx.complex_name
ORDER BY total_venues DESC;

-- 4.3 Get details of venues in a specific country (e.g., Chile)
SELECT venue_id, venue_name, city_name, country_name,
       country_code, timezone, complex_id
FROM venues
WHERE country_name = 'Chile'
ORDER BY city_name, venue_name;

-- 4.4 Identify all venues and their timezones
SELECT venue_name, city_name, country_name, timezone
FROM venues
ORDER BY timezone, venue_name;

-- 4.5 Find complexes that have more than one venue
SELECT cx.complex_id,
       cx.complex_name,
       COUNT(v.venue_id) AS total_venues
FROM complexes cx
JOIN venues v ON v.complex_id = cx.complex_id
GROUP BY cx.complex_id, cx.complex_name
HAVING COUNT(v.venue_id) > 1
ORDER BY total_venues DESC;

-- 4.6 List venues grouped by country
SELECT country_name,
       country_code,
       COUNT(*)                          AS total_venues,
       GROUP_CONCAT(venue_name ORDER BY venue_name SEPARATOR ', ')                  AS venues
FROM venues
GROUP BY country_name, country_code
ORDER BY total_venues DESC, country_name;

-- 4.7 Find all venues for a specific complex (e.g., Nacional)
SELECT v.venue_id, v.venue_name, v.city_name, v.country_name, v.timezone
FROM venues v
JOIN complexes cx ON cx.complex_id = v.complex_id
WHERE cx.complex_name = 'Nacional'
ORDER BY v.venue_name;

-- =====================================================================
-- 5. DOUBLES COMPETITOR RANKINGS QUERIES
-- =====================================================================

-- 5.1 Get all competitors with their rank and points
SELECT c.competitor_id,
       c.name,
       c.country,
       cr.`rank`,
       cr.points
FROM competitors c
JOIN competitor_rankings cr ON cr.competitor_id = c.competitor_id
ORDER BY cr.`rank`;

-- 5.2 Find competitors ranked in the top 5
SELECT c.name, c.country, cr.`rank`, cr.points
FROM competitor_rankings cr
JOIN competitors c ON c.competitor_id = cr.competitor_id
WHERE cr.`rank` <= 5
ORDER BY cr.`rank`;

-- 5.3 List competitors with no rank movement (stable rank)
SELECT c.name, c.country, cr.`rank`, cr.movement, cr.points
FROM competitor_rankings cr
JOIN competitors c ON c.competitor_id = cr.competitor_id
WHERE cr.movement = 0
ORDER BY cr.`rank`;

-- 5.4 Get the total points of competitors from a specific country (e.g., Croatia)
SELECT c.country,
       COUNT(*)         AS total_competitors,
       SUM(cr.points)   AS total_points
FROM competitors c
JOIN competitor_rankings cr ON cr.competitor_id = c.competitor_id
WHERE c.country = 'Croatia'
GROUP BY c.country;

-- 5.5 Count the number of competitors per country
SELECT country,
       COUNT(*) AS total_competitors
FROM competitors
GROUP BY country
ORDER BY total_competitors DESC, country;

-- 5.6 Find competitors with the highest points in the latest ranking snapshot
--     (the data has no week column; returns all competitors tied for the max)
SELECT c.name, c.country, cr.`rank`, cr.points
FROM competitor_rankings cr
JOIN competitors c ON c.competitor_id = cr.competitor_id
WHERE cr.points = (SELECT MAX(points) FROM competitor_rankings)
ORDER BY c.name;

-- =====================================================================
-- 6. EXTRA QUERIES FOR THE STREAMLIT DASHBOARD
-- =====================================================================

-- 6.1 Homepage summary: total competitors, countries, highest points
SELECT (SELECT COUNT(*)                FROM competitors)          AS total_competitors,
       (SELECT COUNT(DISTINCT country) FROM competitors)          AS countries_represented,
       (SELECT MAX(points)             FROM competitor_rankings)  AS highest_points;

-- 6.2 Country-wise analysis: competitor count and average points
SELECT c.country,
       COUNT(*)                  AS total_competitors,
       ROUND(AVG(cr.points), 2)  AS avg_points
FROM competitors c
JOIN competitor_rankings cr ON cr.competitor_id = c.competitor_id
GROUP BY c.country
ORDER BY avg_points DESC;

-- 6.3 Search competitor by name (replace the pattern as needed)
SELECT c.name, c.country, cr.`rank`, cr.movement, cr.points, cr.competitions_played
FROM competitors c
JOIN competitor_rankings cr ON cr.competitor_id = c.competitor_id
WHERE c.name LIKE '%Pavic%'
ORDER BY cr.`rank`;

-- 6.4 Filter by rank range, country and points threshold
SELECT c.name, c.country, cr.`rank`, cr.points
FROM competitors c
JOIN competitor_rankings cr ON cr.competitor_id = c.competitor_id
WHERE cr.`rank` BETWEEN 1 AND 50
  AND c.country = 'Croatia'
  AND cr.points >= 1000
ORDER BY cr.`rank`;

-- 6.5 Leaderboard: top 10 by points
SELECT cr.`rank`, c.name, c.country, cr.points
FROM competitor_rankings cr
JOIN competitors c ON c.competitor_id = cr.competitor_id
ORDER BY cr.points DESC
LIMIT 10;

-- 6.6 Biggest rank movers (up and down)
SELECT c.name, c.country, cr.`rank`, cr.movement
FROM competitor_rankings cr
JOIN competitors c ON c.competitor_id = cr.competitor_id
ORDER BY ABS(cr.movement) DESC
LIMIT 10;

-- 6.7 Countries with no ranked competitors (data-quality check)
SELECT c.country
FROM competitors c
LEFT JOIN competitor_rankings cr ON cr.competitor_id = c.competitor_id
GROUP BY c.country
HAVING COUNT(cr.rank_id) = 0;
