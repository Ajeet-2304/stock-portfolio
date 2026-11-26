# Stock Portfolio & Order Ledger

Django REST Framework + PostgreSQL implementation scaffold for the supplied take-home assignment.

## Run
```bash
cp .env.example .env
docker compose up --build
```
API runs at http://localhost:8000. Create an admin with:
```bash
docker compose exec web python manage.py createsuperuser
```

## Important first-run note
This repository intentionally does not include generated migrations. Generate and commit them:
```bash
docker compose exec web python manage.py makemigrations accounts market_data portfolios trading
docker compose exec web python manage.py migrate
```
For a fresh custom-user project, generate the accounts migration first and ensure it is applied before dependent app migrations.

## Authentication
- POST `/api/auth/register/`
- POST `/api/token/` (username/password; returns access + refresh)
- POST `/api/token/refresh/`
- GET/PATCH `/api/auth/profile/`
- POST `/api/auth/logout/` with refresh token

Send `Authorization: Bearer <access>` for protected endpoints.

## APIs
### Market data (admin writes; authenticated/public reads)
- `/api/market/exchanges/`
- `/api/market/instruments/`
- `/api/market/prices/`
- `/api/market/corporate-actions/`
- `/api/market/holidays/`

### Portfolio
- `/api/portfolios/`
- `/api/portfolios/{id}/balance/`
- `/api/portfolios/{id}/deposit/` body `{"amount":"10000.00"}`
- `/api/portfolios/{id}/withdraw/` body `{"amount":"1000.00"}`

### Trading
- POST/GET `/api/orders/`
- POST `/api/orders/{id}/executions/`
- POST `/api/orders/{id}/cancel/`

Order create example:
```json
{"portfolio":1,"instrument":1,"side":"BUY","order_type":"LIMIT","quantity":"10","limit_price":"100.00"}
```
Execution example:
```json
{"external_execution_id":"EX-001","quantity":"5","price":"99.50"}
```

### Reporting
- `/api/portfolios/{id}/holdings/`
- `/api/portfolios/{id}/value/?as_of=2025-03-14`
- `/api/portfolios/{id}/realized-pnl/?start_date=2025-01-01&end_date=2025-12-31`
- `/api/exchanges/{id}/top-movers/?start_date=2025-01-01&end_date=2025-01-31`
- `/api/instruments/{id}/moving-average/`

### Management commands
```bash
python manage.py load_prices prices.csv
python manage.py apply_corporate_actions
```


## Design decisions
- Custom user extends Django `AbstractUser`; JWT is used for API authentication.
- Cash ledger is the cash source of truth. Entries should be append-only; corrections should use reversing entries.
- Every BUY fill creates a tax lot; every SELL fill consumes open lots FIFO and records `LotConsumption`.
- `select_for_update` locks the portfolio before financial operations; PostgreSQL is required for meaningful row-locking behavior.
- Execution external ID is unique at database level for idempotency.
- Current holdings are derived from remaining tax lots rather than a second editable position balance.
- Instruments, portfolios, executions, lots and ledger rows use `PROTECT` to preserve financial history.

## Indexes
- DailyPrice `(instrument, trading_date)` supports per-instrument price history and latest-price queries.
- DailyPrice `(trading_date, instrument)` supports exchange/date reporting.
- Order `(portfolio, status)` supports pending reservation lookup.
- Execution `(order, executed_at)` supports order fill history.
- TaxLot `(portfolio, instrument, acquired_at, id)` supports FIFO lot selection.
- CashLedgerEntry `(portfolio, created_at)` supports portfolio ledger queries.


## What i would do differently with more time

- **Database partitioning**: Implement time-based partitioning (monthly/yearly) and composite indexes on (instrument_id, timestamp) to efficiently query 10 years of data across 5,000 instruments.

- **Data archiving**: Separate data into hot, warm, and cold storage. Keep recent data in the primary database and move older historical data to compressed, cost-effective object storage (Parquet).

- **Read replicas**: Introduce read replicas to distribute reporting and historical query workloads while keeping the primary database focused on ingestion and writes.

- **Caching**: Use Redis to cache frequently accessed instrument prices, historical queries, metadata, and precomputed aggregates.

- **Asynchronous processing**: Introduce Kafka or background workers for ingestion, data validation, aggregation, and archival to handle increasing data volumes reliably.

- **Monitoring and reliability**: Implement monitoring for query latency, database load, replication lag, storage growth, and ingestion failures, alongside automated backups and recovery.

- **What I would do differently with more time**: Conduct proper capacity planning, perform large-scale load testing, improve observability, introduce a dedicated analytical database if needed, and automate data lifecycle management and infrastructure deployment.

- **Price Prediction:** Use ML models (LSTM, XGBoost) to analyze historical data and forecast potential price movements.

- **Trend Detection:** Apply machine learning to identify market trends, patterns, and momentum across 5,000 instruments.

- **Anomaly Detection:** Use Isolation Forest or autoencoders to detect unusual price movements, volume spikes, and suspicious trading patterns.

- **Sentiment Analysis:** Use NLP on financial news, announcements, and social media to understand market sentiment.

- **Smart Recommendations:** Build recommendation models to identify instruments matching user-defined risk profiles and investment preferences.

- **Automated Insights:** Use LLMs to generate natural-language summaries of market movements, technical indicators, and portfolio performance.

- Risk Management: Use ML models to estimate volatility, identify potential risks, detect unusual portfolio exposure, and support risk-based alerts.
