-- queries.sql
-- All 7 analytical queries for the patent pipeline

-- Q1: Top Inventors
SELECT i.name, i.country, COUNT(DISTINCT r.patent_id) AS patent_count
FROM inventors i
JOIN relationships r ON r.inventor_id = i.inventor_id
GROUP BY i.inventor_id
ORDER BY patent_count DESC LIMIT 20;

-- Q2: Top Companies
SELECT c.name, COUNT(DISTINCT r.patent_id) AS patent_count
FROM companies c
JOIN relationships r ON r.company_id = c.company_id
GROUP BY c.company_id
ORDER BY patent_count DESC LIMIT 20;

-- Q3: Countries
SELECT i.country, COUNT(DISTINCT r.patent_id) AS patent_count,
       ROUND(100.0 * COUNT(DISTINCT r.patent_id) / (SELECT COUNT(*) FROM patents), 2) AS share_pct
FROM inventors i
JOIN relationships r ON r.inventor_id = i.inventor_id
WHERE i.country NOT IN ('UNKNOWN', '')
GROUP BY i.country ORDER BY patent_count DESC LIMIT 20;

-- Q4: Trends Over Time
SELECT year, COUNT(*) AS patent_count
FROM patents WHERE year IS NOT NULL
GROUP BY year ORDER BY year;

-- Q5: JOIN Query
SELECT p.patent_id, p.title, p.year,
       i.name AS inventor_name, i.country, c.name AS company_name
FROM patents p
LEFT JOIN relationships r ON r.patent_id   = p.patent_id
LEFT JOIN inventors     i ON i.inventor_id = r.inventor_id
LEFT JOIN companies     c ON c.company_id  = r.company_id
ORDER BY p.year DESC LIMIT 100;

-- Q6: CTE Query
WITH company_yearly AS (
    SELECT c.company_id, c.name AS company_name, p.year,
           COUNT(DISTINCT r.patent_id) AS yearly_count
    FROM companies c
    JOIN relationships r ON r.company_id = c.company_id
    JOIN patents       p ON p.patent_id  = r.patent_id
    WHERE p.year IS NOT NULL
    GROUP BY c.company_id, c.name, p.year
),
company_totals AS (
    SELECT company_name,
           SUM(yearly_count) AS total_patents,
           COUNT(DISTINCT year) AS active_years,
           ROUND(AVG(yearly_count), 1) AS avg_per_year
    FROM company_yearly GROUP BY company_id, company_name
)
SELECT ROW_NUMBER() OVER (ORDER BY total_patents DESC) AS rank,
       company_name, total_patents, active_years, avg_per_year
FROM company_totals ORDER BY total_patents DESC LIMIT 10;

-- Q7: Ranking with Window Functions
WITH inv AS (
    SELECT i.name AS inventor_name, i.country,
           COUNT(DISTINCT r.patent_id) AS patent_count
    FROM inventors i
    JOIN relationships r ON r.inventor_id = i.inventor_id
    GROUP BY i.inventor_id
)
SELECT RANK()   OVER (ORDER BY patent_count DESC) AS overall_rank,
       RANK()   OVER (PARTITION BY country ORDER BY patent_count DESC) AS country_rank,
       inventor_name, country, patent_count,
       NTILE(4) OVER (ORDER BY patent_count DESC) AS quartile
FROM inv ORDER BY overall_rank LIMIT 30;