# MoMo SMS Analytics Dashboard

**Team Name:** Idk yet

| Member | Role |
|---|---|
| fnyisenge | Group Lead |
| alvinmutangana | Backend / ETL |
| Indra_otk1 | Frontend / Database |

## Description
A data pipeline and analytics dashboard for processing MTN MoMo SMS notifications. XML data is parsed, cleaned, categorized, and stored in a relational database, then visualized through a static frontend dashboard.

## Architecture Diagram
![Architecture](docs/architecture_diagram.png)
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

## Quick Start
```bash
pip install -r requirements.txt
bash scripts/run_etl.sh
bash scripts/serve_frontend.sh  # open http://localhost:8000
```

## Scrum Board
https://trello.com/b/JMdXRS08



> All schema design, ERD decisions, and business logic were produced by the team.
