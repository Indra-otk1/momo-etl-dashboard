# MoMo SMS Analytics Dashboard

**Team Name:** Idk yet

| Member | Role |
|---|---|
| fnyisenge | Group Lead |
| alvinmutangana | Backend / ETL |
| Indra_otk1 | Frontend / Database |

## Description
A data pipeline, REST API, and analytics dashboard for processing MTN MoMo SMS notifications. XML data is parsed, cleaned, and stored in a relational database, exposed through a secured REST API, and visualized through a static frontend.

## Project Structure
├── api/          # REST API (http.server + Basic Auth)
├── dsa/          # Linear search vs dictionary lookup comparison
├── etl/          # XML parsing and data pipeline
├── database/     # SQL setup scripts
├── docs/         # API documentation and ERD
├── screenshots/  # curl/Postman test screenshots
└── data/raw/     # Source XML file
## Quick Start
```bash
pip install -r requirements.txt
bash scripts/run_etl.sh
python api/app.py data/raw/modified_sms_v2.xml  # API at http://localhost:8080
bash scripts/serve_frontend.sh                  # Dashboard at http://localhost:8000
```
## Architecture Diagram
![Architecture](<img width="1021" height="391" alt="Momo" src="https://github.com/user-attachments/assets/17b930e1-2569-487e-b36a-e9129af50c41" />
)
> Full diagram: https://drive.google.com/file/d/1J1C03lxPXahCgGqCN71RVSY6Zuyh8oDE/view?usp=sharing

## Database Design
ERD: [`docs/erd_diagram.png`](docs/erd_drawing.md)
SQL Script: [`database/database_setup.sql`](database/database_setup.sql)
JSON Schemas: [`examples/json_schemas.json`](examples/json_schemas.json)

| Table | Description |
|---|---|
| `transaction_categories` | Lookup table for transaction types |
| `transactions` | One row per parsed SMS transaction |
| `users` | Individuals and businesses in transactions |
| `transaction_participants` | Junction table (M:N) with SENDER/RECEIVER role |
| `system_logs` | ETL pipeline processing and error logs |
## API Endpoints
Auth: Basic Auth — `admin` / `momo2024` | Docs: [`docs/api_docs.md`](docs/api_docs.md)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/transactions` | List all transactions |
| GET | `/transactions/{id}` | Get one transaction |
| POST | `/transactions` | Add a transaction |
| PUT | `/transactions/{id}` | Update a transaction |
| DELETE | `/transactions/{id}` | Delete a transaction |

## Database
ERD: [`docs/erd_drawing.md`](docs/erd_drawing.md) · SQL: [`database/database_setup.sql`](database/database_setup.sql)

| Table | Description |
|---|---|
| `transaction_categories` | Lookup table for transaction types |
| `transactions` | One row per parsed SMS |
| `users` | Individuals and businesses |
| `transaction_participants` | M:N junction table with SENDER/RECEIVER role |
| `system_logs` | ETL processing and error logs |

## Scrum Board
https://trello.com/b/JMdXRS08

Team Participation sheet: https://docs.google.com/spreadsheets/d/1m4t3oPV9ZABsXWPF-fuJEvMnu-5w2bsB9TePtScwV4g/edit?gid=0#gid=0