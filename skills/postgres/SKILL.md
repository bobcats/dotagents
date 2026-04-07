---
name: postgres
description: "PostgreSQL-specific patterns, index strategies, and safe DDL. Use when working with PostgreSQL databases — writing queries, migrations, or optimizing."
metadata:
  category: languages
---

# PostgreSQL

Apply these patterns when working with PostgreSQL. Load the `sql` skill alongside this one for general SQL patterns.

## Detection Patterns

```bash
# Query anti-patterns
rg "SELECT \*" --glob "*.sql"
rg "LIKE '%|ILIKE '%" --glob "*.sql"  # leading wildcard kills indexes
rg "WHERE.*UPPER\(|WHERE.*LOWER\(" --glob "*.sql"  # function on indexed column
rg "ORDER BY.*RANDOM\(\)" --glob "*.sql"  # full table scan
```

## Index Patterns

```sql
-- Column order matters in composite indexes
-- Query must include leftmost column(s)
CREATE INDEX idx_orders ON orders(user_id, status);
-- Works: WHERE user_id = 1
-- Works: WHERE user_id = 1 AND status = 'active'
-- Fails: WHERE status = 'active' (can't use index)

-- Partial index for common filter
CREATE INDEX idx_users_active ON users(email) WHERE deleted_at IS NULL;

-- Expression index for function calls
CREATE INDEX idx_users_email ON users(LOWER(email));
-- Now: WHERE LOWER(email) = 'x' uses index

-- GIN for JSONB containment queries
CREATE INDEX idx_data ON events USING GIN (data);
-- Supports: WHERE data @> '{"type": "click"}'
```

## Query Patterns

```sql
-- EXISTS over COUNT for existence check
SELECT COUNT(*) FROM orders WHERE user_id = 1;  -- scans all
SELECT EXISTS(SELECT 1 FROM orders WHERE user_id = 1);  -- stops at first

-- ANY over multiple ORs
WHERE id = 1 OR id = 2 OR id = 3  -- →
WHERE id = ANY(ARRAY[1, 2, 3])

-- COALESCE for defaults
CASE WHEN name IS NULL THEN 'Unknown' ELSE name END  -- →
COALESCE(name, 'Unknown')

-- Verify index usage
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'x@y.com';
-- Index Scan = good, Seq Scan on large table = missing index
```

## Safe DDL

```sql
-- Add index without blocking writes
CREATE INDEX CONCURRENTLY idx_orders_user ON orders(user_id);

-- Add foreign key without blocking
ALTER TABLE orders ADD CONSTRAINT fk_user
  FOREIGN KEY (user_id) REFERENCES users(id) NOT VALID;
-- Then separately:
ALTER TABLE orders VALIDATE CONSTRAINT fk_user;

-- Add NOT NULL without blocking
ALTER TABLE users ADD CONSTRAINT chk_email
  CHECK (email IS NOT NULL) NOT VALID;
ALTER TABLE users VALIDATE CONSTRAINT chk_email;
ALTER TABLE users ALTER COLUMN email SET NOT NULL;
ALTER TABLE users DROP CONSTRAINT chk_email;
```
