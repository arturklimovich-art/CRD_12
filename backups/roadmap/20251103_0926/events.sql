\pset pager off
\encoding UTF8
\copy (SELECT * FROM core.events ORDER BY id) TO STDOUT WITH CSV HEADER
