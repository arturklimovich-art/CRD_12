\pset pager off
\encoding UTF8
\copy (SELECT * FROM nav.roadmap_items ORDER BY order_index, created_at) TO STDOUT WITH CSV HEADER
