[![Django CI](https://github.com/EdvardFarrow/transactional-wallet-service/actions/workflows/ci.yml/badge.svg)](https://github.com/EdvardFarrow/transactional-wallet-service/actions/workflows/ci.yml)

[![ru](https://img.shields.io/badge/lang-ru-grey.svg)](README_ru.md)


# Transactional Wallet Service

A microservice for processing internal transactions and bonus accruals.
It implements a fault-tolerant processing core with protection against **Race Conditions** (Double Spending) and asynchronous notifications.

---

## Key Features

### Reliability and Consistency
* **Protection against Race Conditions:** Implemented via pessimistic locking (`select_for_update`).
* **Protection against Deadlocks:** Resource locking always occurs in a strictly defined order (sorted by `wallet_id`).
* **Atomicity:** Debiting, crediting, and commission fees occur within a single transaction. Either everything succeeds, or nothing does.
* **Celery & Data Safety:** Utilizing `transaction.on_commit` guarantees that notification tasks are sent to the broker only after data is committed to the database.

### Functionality
* **Transaction API:** Transfers between users with balance validation.
* **Commission:** Automatic 10% deduction to the `admin` account if the transfer amount is > 1000.
* **Notifications:** Asynchronous status sending via Celery with a **Retry** mechanism (for network failures).

---

## Tech Stack

* **Core:** Python 3.12 + Django 5 + DRF
* **Database:** PostgreSQL 15 (required for `select_for_update` support and high concurrency).
* **Async:** Celery + Redis.
* **Infra:** Docker & Docker Compose.

---

## Quick Start

The project includes a `Makefile` for single-command management.

### 1. Project Launch
Build containers, apply migrations, and create test data (Alice, Bob, Admin):

```bash
make init
```
*This command starts web, db, redis, celery, applies migrations, and populates the database with initial data.*

### 2. Start Server (if not running)
```bash
make up
```

## Demonstration (Verification Script)

I have written a special script to demonstrate system operation and check for Race Conditions. You do not need to use Postman or curl manually.

Run the interactive demo:
```bash
make result
```
*(Or manually: docker compose exec web python result_example.py)*

Select from the menu:

*  Single Transfer: Check a standard transaction and commission accrual.

*  Race Condition Attack: Launch 30 simultaneous threads attempting to debit the balance into the negative.

Expected Result: The balance does not go negative, and transactions are processed sequentially.

## Project Structure

```plaintext
.
├── config/                # Django settings
├── core/                  # Main application
|   ├── admin.py           # Admin-dashboard
│   ├── models.py          # Wallet, Transaction models
│   ├── views.py           # Transaction logic and locks
│   ├── tasks.py           # Celery tasks 
│   └── tests.py           # Unit tests
├── result_example.py      # Race Condition demo script
├── setup_data.py          # Data initialization script
├── docker-compose.yml     # Infrastructure
└── Makefile               # Launch utilities
```

### Tests

Run Unit tests (checking API, commissions, and restrictions):
```bash
make test
```

