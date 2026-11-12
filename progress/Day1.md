# E-Commerce Backend Engineering Lab

## Day 1 – Project Setup & Database Foundation

### 1. Project Overview

Building an e-commerce backend using a modular monolith architecture, with the long-term goal of evolving it into a microservices-based system.

### 2. Technologies Installed

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Psycopg2
- Pydantic
- Uvicorn
- pgAdmin

### 3. Project Structure

```text
distributed-ecommerce-system/
│
├── src/
│   ├── config/
│   │   └── db.py
│   │
│   ├── app/
│   │
│   └── models/
│       ├── user_model.py
│       ├── product_model.py
│       ├── inventory_model.py
│       ├── order_model.py
│       ├── order_item_model.py
│       ├── payment_model.py
│       ├── refresh_token_model.py
│       ├── idempotency_model.py
│       └── outbox_event_model.py
│
├── migrations/
│   └── versions/
│
├── alembic.ini
└── README.md
```

### 4. Database Setup

- Created PostgreSQL database: `ecommerce-db`
- Configured SQLAlchemy engine.
- Created database session using `SessionLocal`.
- Created SQLAlchemy declarative `Base`.
- Configured Alembic for database migrations.

### 5. Database Models Created

| Model | Purpose |
|---|---|
| User | Stores customer information |
| Product | Stores product details |
| Inventory | Tracks available stock |
| Order | Stores customer orders |
| OrderItem | Stores products within orders |
| Payment | Stores simulated payment records |
| RefreshToken | Manages refresh tokens |
| IdempotencyRecord | Helps prevent duplicate requests |
| OutboxEvent | Stores events for reliable publishing |

### 6. What I Learned

**SQLAlchemy**
- ORM concepts
- Database engine
- Database sessions
- Declarative Base
- Columns and data types
- Primary keys and foreign keys
- Unique constraints and nullable fields
- Server defaults

**Alembic**
- What database migrations are
- Why migrations are important
- Initializing Alembic
- Connecting Alembic to SQLAlchemy models
- Autogenerating migrations
- Applying migrations to PostgreSQL

### 7. Migration Workflow

Generate a migration:

```bash
alembic revision --autogenerate -m "migration message"
```

Apply migrations:

```bash
alembic upgrade head
```

### 8. Day 1 Progress

- [x] Python project initialized
- [x] Git repository initialized
- [x] Dependencies installed
- [x] PostgreSQL database created
- [x] SQLAlchemy configured
- [x] Alembic initialized and configured
- [x] User model created and migrated
- [x] Product model created and migrated
- [x] Inventory model created and migrated
- [x] Order model created and migrated
- [x] OrderItem model created and migrated
- [x] Payment model created and migrated
- [x] RefreshToken model created and migrated
- [x] IdempotencyRecord model created and migrated
- [x] OutboxEvent model created and migrated

---

**Day 1 Status: Database foundation established.**

Project: E-Commerce Backend Engineering Lab  
Architecture: Modular Monolith  
Database: PostgreSQL