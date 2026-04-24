
PRAGMA foreign_keys = OFF;

CREATE TABLE IF NOT EXISTS patents (
    patent_id    TEXT    PRIMARY KEY,
    title        TEXT    NOT NULL,
    abstract     TEXT,
    filing_date  TEXT,
    year         INTEGER
);

CREATE TABLE IF NOT EXISTS inventors (
    inventor_id  TEXT    PRIMARY KEY,
    name         TEXT    NOT NULL,
    country      TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    company_id   TEXT    PRIMARY KEY,
    name         TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS relationships (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id    TEXT,
    inventor_id  TEXT,
    company_id   TEXT
);

CREATE INDEX IF NOT EXISTS idx_rel_patent   ON relationships(patent_id);
CREATE INDEX IF NOT EXISTS idx_rel_inventor ON relationships(inventor_id);
CREATE INDEX IF NOT EXISTS idx_rel_company  ON relationships(company_id);
CREATE INDEX IF NOT EXISTS idx_pat_year     ON patents(year);
