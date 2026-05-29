# ERD: Normalization & Query Optimization Heuristics

Design for data integrity and access patterns, not just storage format. Avoid basic SQL tutorials.

## Decision Tree: Resolving Polymorphism

When a record needs to relate to multiple different types of parents (e.g., a Comment on a Post vs a Comment on a Video):

- **Condition**: The number of parent types is small and fixed (e.g., exactly two).
  - **Action**: Use Exclusive Arcs (Multiple nullable Foreign Keys with a CHECK constraint ensuring exactly one is NOT NULL). This maintains database-level referential integrity.
- **Condition**: The number of parent types is large or highly dynamic.
  - **Action**: Use a Polymorphic Association (`commentable_type` + `commentable_id`). _Warning: You must explicitly note in the diagram that this sacrifices database-level referential integrity._
- **Condition**: Strict referential integrity is mandatory across all parent types.
  - **Action**: Use Supertype/Subtype (Table Inheritance). Create a base `Commentable` table that both `Post` and `Video` extend via a 1:1 foreign key relation.

### Pattern 1: Exclusive Arcs (Small Fixed Set of Parent Types)

**Scenario**: Comments can be on Posts OR Articles, never both.

```sql
CREATE TABLE comments (
  comment_id UUID PRIMARY KEY,
  post_id UUID NULLABLE,
  article_id UUID NULLABLE,
  content TEXT,
  created_at TIMESTAMP,
  -- Ensures exactly one parent is present
  CHECK (
    (post_id IS NOT NULL AND article_id IS NULL) OR
    (post_id IS NULL AND article_id IS NOT NULL)
  ),
  FOREIGN KEY (post_id) REFERENCES posts(post_id),
  FOREIGN KEY (article_id) REFERENCES articles(article_id)
);
```

**Diagram**:

```
posts |--<--| comments
articles |--<--| comments
```

**Pros**: Database-level integrity, direct referencing
**Cons**: Not scalable if new types added frequently

---

### Pattern 2: Polymorphic Association (Dynamic/Large Parent Type Set)

**Scenario**: Reactions can be on Posts, Comments, Videos, Articles (many types, growing).

```sql
CREATE TABLE reactions (
  reaction_id UUID PRIMARY KEY,
  reactable_type VARCHAR(50),  -- 'post', 'comment', 'video', etc.
  reactable_id UUID,
  reaction_type VARCHAR(20),   -- 'like', 'love', 'angry'
  user_id UUID,
  created_at TIMESTAMP
  -- No FK — application must enforce integrity
);
```

**Diagram**:

```
reactions
  - reaction_id PK
  - reactable_type (post|comment|video)
  - reactable_id UUID
  - reaction_type
  - user_id

⚠️ NOTE: Polymorphic association — no database-level FK integrity
Application must validate reactable_type + reactable_id pair
```

**Pros**: Scales to many types, no schema changes needed
**Cons**: No database-level integrity, risk of orphaned records

---

### Pattern 3: Supertype/Subtype (Strict Inheritance)

**Scenario**: Content hierarchy: Post, Video, Article all inherit shared properties.

```sql
CREATE TABLE content (
  content_id UUID PRIMARY KEY,
  content_type VARCHAR(50),  -- discriminator
  title VARCHAR(255),
  created_at TIMESTAMP
);

CREATE TABLE posts (
  post_id UUID PRIMARY KEY REFERENCES content(content_id),
  body TEXT
);

CREATE TABLE videos (
  video_id UUID PRIMARY KEY REFERENCES content(content_id),
  url VARCHAR(500),
  duration_seconds INT
);

CREATE TABLE articles (
  article_id UUID PRIMARY KEY REFERENCES content(content_id),
  body TEXT,
  publish_date DATE
);
```

**Diagram**:

```
content (base)
  - content_id PK
  - content_type (discriminator)
  - title
  - created_at
    |
    +-- posts (1:1)
    +-- videos (1:1)
    +-- articles (1:1)
```

**Pros**: Strict integrity, shared attributes in one table
**Cons**: Requires joins, more complex queries

## Heuristic: Handling Temporal Data (History)

- **Trap**: Mutating critical records (like Prices or Addresses) in place, losing historical context.
- **Expert Move**: When financial or auditing integrity is required, do NOT use simple update patterns.
  - Model a Slowly Changing Dimension (SCD Type 2) table (e.g., add `effective_date`, `expiration_date`, `is_current` columns).
  - OR, model an append-only Event Store if the architecture uses Event Sourcing.

## Heuristic: Denormalization for Read Performance

- **Trap**: Assuming 3rd Normal Form is always the answer for high-scale applications.
- **Expert Move**: If a query requires joining >5 heavily trafficked tables, model a denormalized projection table or materialized view.
- You MUST document the synchronization mechanism (e.g., "Updated via CDC" or "Async Worker") that keeps the denormalized view consistent with the normalized source of truth. Show this mechanism via notes in the ERD.
