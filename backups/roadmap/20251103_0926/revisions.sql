\pset pager off
\encoding UTF8
\copy (SELECT * FROM nav.roadmap_revisions ORDER BY created_at) TO STDOUT WITH CSV HEADER
