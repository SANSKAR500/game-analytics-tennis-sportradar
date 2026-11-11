"""Parameterized SQL used by the Streamlit application."""

HOME = """
SELECT (SELECT COUNT(*) FROM competitors) AS total_competitors,
       (SELECT COUNT(DISTINCT country) FROM competitors) AS countries_represented,
       (SELECT MAX(points) FROM competitor_rankings) AS highest_points
"""

COUNTRIES = """
SELECT c.country, COUNT(*) AS total_competitors,
       ROUND(AVG(cr.points), 2) AS avg_points
FROM competitors c
JOIN competitor_rankings cr ON cr.competitor_id = c.competitor_id
GROUP BY c.country
ORDER BY avg_points DESC
"""

SEARCH = """
SELECT c.name, c.country, cr.rank, cr.movement, cr.points,
       cr.competitions_played
FROM competitors c
JOIN competitor_rankings cr ON cr.competitor_id = c.competitor_id
WHERE c.name ILIKE %(pattern)s
ORDER BY cr.rank
LIMIT %(limit)s OFFSET %(offset)s
"""

FILTER = """
SELECT c.name, c.country, cr.rank, cr.movement, cr.points,
       cr.competitions_played
FROM competitors c
JOIN competitor_rankings cr ON cr.competitor_id = c.competitor_id
WHERE cr.rank BETWEEN %(min_rank)s AND %(max_rank)s
  AND (%(country)s = '' OR c.country = %(country)s)
  AND cr.points >= %(min_points)s
ORDER BY cr.rank
LIMIT %(limit)s OFFSET %(offset)s
"""

DETAIL = """
SELECT c.competitor_id, c.name, c.country, c.country_code,
       c.abbreviation, cr.rank, cr.movement, cr.points,
       cr.competitions_played
FROM competitors c
JOIN competitor_rankings cr ON cr.competitor_id = c.competitor_id
WHERE c.competitor_id = %(competitor_id)s
"""

TOP_POINTS = """
SELECT cr.rank, c.name, c.country, cr.points
FROM competitor_rankings cr
JOIN competitors c ON c.competitor_id = cr.competitor_id
ORDER BY cr.points DESC, cr.rank ASC
LIMIT 10
"""

MOVERS = """
SELECT c.name, c.country, cr.rank, cr.movement
FROM competitor_rankings cr
JOIN competitors c ON c.competitor_id = cr.competitor_id
ORDER BY ABS(cr.movement) DESC, cr.rank ASC
LIMIT 10
"""

COMPETITIONS = """
SELECT c.competition_id, c.competition_name, c.parent_id,
       c.type, c.gender, cat.category_name
FROM competitions c
LEFT JOIN categories cat ON cat.category_id = c.category_id
WHERE (%(type)s = '' OR c.type = %(type)s)
  AND (%(category)s = '' OR cat.category_name = %(category)s)
ORDER BY COALESCE(c.parent_id, c.competition_id), c.competition_name
LIMIT %(limit)s OFFSET %(offset)s
"""

VENUES = """
SELECT v.venue_id, v.venue_name, v.city_name, v.country_name,
       v.country_code, v.timezone, cx.complex_name
FROM venues v
LEFT JOIN complexes cx ON cx.complex_id = v.complex_id
WHERE (%(country)s = '' OR v.country_name = %(country)s)
  AND (%(complex)s = '' OR cx.complex_name = %(complex)s)
ORDER BY cx.complex_name, v.venue_name
LIMIT %(limit)s OFFSET %(offset)s
"""

