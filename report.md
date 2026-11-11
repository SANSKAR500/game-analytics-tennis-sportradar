# Final Report — Game Analytics: Unlocking Tennis Data with SportRadar API

## 1. Project overview

This project builds an end-to-end tennis analytics workflow around the Sportradar Tennis API. Python is used for API collection and data-quality validation, SQL is used for relational storage and analysis, PostgreSQL is the primary database, and Streamlit provides an interactive exploration layer.

## 2. Workflow

1. Authenticate to Sportradar using an API key stored outside source code.
2. Request competition, complex/venue, and doubles competitor ranking feeds.
3. Flatten nested JSON into relational CSVs.
4. Validate schema, uniqueness, required fields, and foreign-key consistency.
5. Load the reference data into PostgreSQL.
6. Run the supplied SQL analysis queries.
7. Surface selected queries through Streamlit with parameterized SQL and pagination.

## 3. Schema and normalization

The schema separates reusable entities into six tables:

- `categories`: category reference data.
- `competitions`: competitions and their parent/sub-event relationships.
- `complexes`: tennis venue complexes.
- `venues`: physical venues belonging to complexes.
- `competitors`: competitor reference data.
- `competitor_rankings`: ranking facts associated with competitors.

This separates entity attributes from ranking measures and prevents repeating category, complex, venue, and competitor descriptions across ranking rows.

`parent_id` is intentionally not a self-referencing foreign key in the supplied schema because an API response can contain a child competition whose parent is not included in the same response. Enforcing the FK during bulk load would make otherwise valid API data fail to load.

## 4. API design

The collectors target Tennis API v3. The competition feed contains nested category information, so the collector creates the category reference table and the competition fact/reference rows separately. The complexes feed contains nested venues, so it is split into `complexes` and `venues`. The doubles rankings feed contains nested competitor objects, so it is split into `competitors` and `competitor_rankings`.

The HTTP client handles timeouts, HTTP errors, network failures, invalid JSON, and HTTP 429 rate limits with retry/backoff. Required identifiers are validated before rows are emitted.

## 5. Query insights

The supplied SQL supports several analytical questions:

- competition counts by category and type
- parent/sub-event hierarchy inspection
- venue counts by complex and country
- stable versus moving ranking positions
- total points by country
- competitor counts by country
- latest-snapshot maximum points
- country average points
- top 10 competitors by points
- largest ranking movements

These queries form the analytical contract between the relational database and the Streamlit dashboard.

## 6. Streamlit design

The dashboard is intentionally minimal. The overview provides three headline measures: total competitors, represented countries, and highest points. Competitor exploration supports name search and rank/country/points filtering. Country analysis provides a table and average-points chart. Leaderboards provide ranking and movement views. Competition and venue pages expose the reference-data hierarchy.

Pagination is used for potentially large result sets. Database filtering is parameterized rather than constructed with string concatenation.

## 7. Data-quality fixes

The supplied `CHANGES.md` documents corrections already incorporated into the reference data. These include corrected competition type values, classification of mixed-doubles events, the United Cup category correction, and the relabeling of the ranking query as a latest-snapshot query.

The project preserves those corrected CSV and SQL files instead of reintroducing the earlier values. A later review pass fixed the API client error handling, made the collectors fail on unexpected responses, made the database layer read-only, and corrected the Streamlit deployment settings (see CHANGES.md).

## 8. Limitations

### Competition level

The API exposes a competition `level` field, but the current relational schema does not store it. The Streamlit competition page therefore uses category as a stand-in. This is a presentation choice, not a claim that category and level are equivalent.

### Competitor participation

There is no competitor-to-competition bridge table in the supplied schema. Therefore, the project cannot reliably answer questions such as whether a particular competitor participated in a particular singles or doubles competition.

### Ranking history

The API ranking response provides year/week metadata, but the current `competitor_rankings` table does not persist it. The current database should therefore be treated as a snapshot. Historical trend analysis would require adding snapshot metadata and an appropriate key/partitioning strategy.

### Doubles scope

The ranking collector uses the doubles competitor rankings feed. It should not be used to claim ATP men's singles coverage. If singles analytics are required, a separate rankings collection and a clearly defined schema extension should be added.

## 9. Future improvements

- Persist ranking `year` and `week` in a snapshot table.
- Add a competition-participation bridge when the appropriate Sportradar feed is collected.
- Add singles rankings as a separate fact set.
- Store the competition `level` when the dashboard requires it as a true API-derived dimension.
- Add automated scheduled refreshes and data-quality checks.
- Add integration tests using mocked API responses.

## 10. Conclusion

The completed project demonstrates a reproducible API-to-database-to-dashboard workflow. Its strongest design choices are explicit data validation, normalized reference/fact tables, retry-safe API collection, parameterized database queries, and honest documentation of data limitations.
