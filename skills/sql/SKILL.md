---
name: sql
description: "SQL query patterns, anti-patterns, and index guidelines. Use when writing, reviewing, or refactoring SQL queries."
metadata:
  category: languages
---

# SQL

Apply these patterns when writing, reviewing, or refactoring SQL queries.

## Detection Patterns

```bash
rg "SELECT \*" --glob "*.sql"  # select specific columns
rg "LIKE '%" --glob "*.sql"  # leading wildcard kills indexes
rg "ORDER BY.*RAND" --glob "*.sql"  # full table scan
```

## Query Patterns

```sql
-- Select specific columns
SELECT * FROM users WHERE active = true;  -- →
SELECT id, name, email FROM users WHERE active = true;

-- EXISTS over COUNT for existence
SELECT COUNT(*) FROM orders WHERE user_id = 1;  -- scans all →
SELECT EXISTS(SELECT 1 FROM orders WHERE user_id = 1);  -- stops at first

-- COALESCE for defaults
CASE WHEN name IS NULL THEN 'Unknown' ELSE name END  -- →
COALESCE(name, 'Unknown')

-- JOIN over correlated subquery
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders);  -- →
SELECT DISTINCT u.* FROM users u JOIN orders o ON u.id = o.user_id;

-- UNION ALL when duplicates ok (faster, no sort)
SELECT name FROM customers UNION SELECT name FROM suppliers;  -- dedupes →
SELECT name FROM customers UNION ALL SELECT name FROM suppliers;

-- Avoid functions on indexed columns
WHERE UPPER(email) = 'X@Y.COM'  -- can't use index →
WHERE email = 'x@y.com'  -- uses index (store normalized)

-- Limit results when possible
SELECT * FROM logs ORDER BY created_at DESC;  -- full scan →
SELECT * FROM logs ORDER BY created_at DESC LIMIT 100;
```

## Index Guidelines

```sql
-- Index foreign keys (most ORMs don't auto-create)
CREATE INDEX idx_orders_user ON orders(user_id);

-- Composite index column order matters
-- Index on (a, b) supports: WHERE a=1, WHERE a=1 AND b=2
-- Does NOT support: WHERE b=2 alone

-- Covering index includes all needed columns
-- Query reads from index only, never touches table
```
