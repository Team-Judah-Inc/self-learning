# Self-Learning Backend

Go backend service for the Finance MVP application.

This uses a **Monolithic Architecture** that runs both the **API Server** (Read Layer) and the **Background Sync Engine** (Write Layer) in a single binary.

## Project Structure

```text
backend/
├── cmd/
│   └── server/
│       └── main.go          # Entrypoint: Starts API + Fetcher/Normalizer Workers
├── internal/
│   ├── api/                 # HTTP Layer
│   │   ├── handlers/        # Controllers (GET /transactions, etc.)
│   │   ├── middleware/      # Auth & Logging
│   │   └── routes.go        # Router Setup
│   │
│   ├── worker/              # The Sync Engine (Background Jobs)
│   │   ├── fetcher.go       # Loop A: Pulls from Bank -> S3 -> Queue
│   │   └── normalizer.go    # Loop B: Reads Queue -> DB (Deduplication)
│   │
│   ├── models/              # Shared Data Structs (User, Account, Transaction)
│   ├── database/            # SQLite Connection & GORM AutoMigrate
│   └── config/              # Configuration management
│
├── pkg/
│   └── logger/              # Logging utilities
├── go.mod                   # Dependencies
├── go.sum                   # Checksums
└── .env.example             # Env var template
````

## Getting Started

### Prerequisites

* **Go 1.21** or higher
* **VS Code Extension:**
  [SQLite Viewer](https://marketplace.visualstudio.com/items?itemName=qwtel.sqlite-viewer)
  (Recommended for viewing `riseapp.db` locally)

### Installation

1. Clone the repository and navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

3. Install dependencies (including GORM & SQLite driver):

   ```bash
   go mod tidy
   ```

### Running the Server

**Development Mode**
Starts the API on port `8080` **and** the background workers (Fetcher/Normalizer):

```bash
go run cmd/server/main.go
```

To populate the database with a test account run:
```bash
go run cmd/seed/main.go
```

---

## Database Inspection (Local) 🗄️

This project uses an embedded **SQLite** database (`riseapp.db`).
It runs in **WAL Mode** (Write-Ahead Logging) for high concurrency.

### How to view data

1. Install the **SQLite Viewer** extension in VS Code.
2. In the file explorer, click on `riseapp.db`.
3. Browse the `users`, `accounts`, and `transactions` tables.
4. **Note:** You may see `riseapp.db-wal` or `riseapp.db-shm` files.
   Do **not** delete them — they are temporary consistency files managed by SQLite.

---

## Environment Variables

See `.env.example` for all available configuration options:

* `PORT` – Server port (default: `8080`)
* `ENVIRONMENT` – Environment mode (`development` / `production`)
* `ALLOWED_ORIGINS` – CORS allowed origins
* `DATABASE_URL` – Path to SQLite file (default: `riseapp.db`)
* `JWT_SECRET` – Secret key for JWT tokens
* `LOG_LEVEL` – Logging level (`debug` / `info` / `error`)

## Architecture Overview

1. **API Layer**

   * Serves JSON to the frontend
   * Fast, read-heavy queries

## License

MIT
