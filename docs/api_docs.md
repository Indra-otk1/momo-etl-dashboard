# MoMo SMS Transactions API — Documentation

**Base URL:** `http://localhost:8080`  
**Authentication:** HTTP Basic Auth  
**Credentials:** `admin` / `momo2024`  
**Content-Type:** `application/json`

---

## Authentication

All endpoints require a valid `Authorization` header using HTTP Basic Auth.

**How to encode credentials:**
```
Base64("admin:momo2024") → "YWRtaW46bW9tbzIwMjQ="
```

**Header format:**
```
Authorization: Basic YWRtaW46bW9tbzIwMjQ=
```

**Error response (401):**
```json
{
  "error": "Unauthorized. Provide valid credentials."
}
```

---

## Endpoints

### 1. GET /transactions
Returns all transactions in the database.

**Request:**
```bash
curl -u admin:momo2024 http://localhost:8080/transactions
```

**Response (200):**
```json
{
  "count": 3,
  "transactions": [
    {
      "id": 1,
      "external_id": "TXN-00001",
      "category": "INCOMING_MONEY",
      "amount": 50000.0,
      "balance_after": 250000.0,
      "phone_number": "+250788100001",
      "transaction_date": "2024-01-15T08:23:00",
      "status": "SUCCESS",
      "raw_sms": "You have received 50,000 RWF from Alice Uwimana."
    }
  ]
}
```

---

### 2. GET /transactions/{id}
Returns a single transaction by ID.

**Request:**
```bash
curl -u admin:momo2024 http://localhost:8080/transactions/1
```

**Response (200):**
```json
{
  "id": 1,
  "external_id": "TXN-00001",
  "category": "INCOMING_MONEY",
  "amount": 50000.0,
  "balance_after": 250000.0,
  "phone_number": "+250788100001",
  "transaction_date": "2024-01-15T08:23:00",
  "status": "SUCCESS",
  "raw_sms": "You have received 50,000 RWF from Alice Uwimana."
}
```

**Response (404):**
```json
{
  "error": "Transaction not found."
}
```

---

### 3. POST /transactions
Creates a new transaction record.

**Request:**
```bash
curl -u admin:momo2024 \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{
           "category": "PAYMENT",
           "amount": 15000,
           "phone_number": "+250788100004",
           "transaction_date": "2024-01-20T10:00:00",
           "status": "SUCCESS",
           "balance_after": 198000
         }' \
     http://localhost:8080/transactions
```

**Required fields:** `category`, `amount`, `transaction_date`

**Response (201):**
```json
{
  "message": "Transaction created.",
  "transaction": {
    "id": 8,
    "external_id": "TXN-00008",
    "category": "PAYMENT",
    "amount": 15000.0,
    "balance_after": 198000,
    "phone_number": "+250788100004",
    "transaction_date": "2024-01-20T10:00:00",
    "status": "SUCCESS",
    "raw_sms": ""
  }
}
```

**Response (400 — missing fields):**
```json
{
  "error": "Missing required fields: ['transaction_date']"
}
```

---

### 4. PUT /transactions/{id}
Updates one or more fields of an existing transaction.

**Request:**
```bash
curl -u admin:momo2024 \
     -X PUT \
     -H "Content-Type: application/json" \
     -d '{"status": "FAILED"}' \
     http://localhost:8080/transactions/1
```

**Response (200):**
```json
{
  "message": "Transaction updated.",
  "transaction": {
    "id": 1,
    "external_id": "TXN-00001",
    "category": "INCOMING_MONEY",
    "amount": 50000.0,
    "status": "FAILED"
  }
}
```

**Response (404):**
```json
{
  "error": "Transaction not found."
}
```

---

### 5. DELETE /transactions/{id}
Deletes a transaction by ID.

**Request:**
```bash
curl -u admin:momo2024 \
     -X DELETE \
     http://localhost:8080/transactions/1
```

**Response (200):**
```json
{
  "message": "Transaction deleted.",
  "deleted": {
    "id": 1,
    "external_id": "TXN-00001",
    "category": "INCOMING_MONEY",
    "amount": 50000.0
  }
}
```

---

## Error Codes

| Code | Meaning |
|---|---|
| 200 | OK — request succeeded |
| 201 | Created — new record added |
| 400 | Bad Request — invalid or missing JSON fields |
| 401 | Unauthorized — missing or wrong credentials |
| 404 | Not Found — transaction ID or endpoint doesn't exist |

---

## Authentication Security Analysis

### Why Basic Auth is weak

Basic Auth encodes credentials in Base64 — this is **not encryption**. Anyone who intercepts the request can decode it instantly. Key weaknesses:

- Credentials are sent on **every single request**
- Base64 is trivially reversible — it offers zero security on its own
- Vulnerable to **man-in-the-middle attacks** without HTTPS
- No token expiry — stolen credentials work forever
- No way to revoke access for a single session

### Stronger alternatives

**JWT (JSON Web Tokens)**
- Server issues a signed token after login
- Client sends the token, not raw credentials
- Token expires automatically (e.g. after 1 hour)
- Can be revoked via a token blacklist
- Industry standard for REST APIs

**OAuth2**
- Delegates authentication to a trusted provider (Google, GitHub, etc.)
- No passwords stored on your server
- Supports scoped permissions (read-only vs full access)
- Best choice for APIs accessed by third-party apps

**Recommendation:** For this MoMo API, replace Basic Auth with **JWT** using the `PyJWT` library. Users log in once via `POST /auth/login` and receive a token they use for all subsequent requests.

---

## Running the API

```bash
# Install dependencies (none beyond stdlib — no pip needed)
python api/app.py

# Or with a custom XML path
python api/app.py data/raw/modified_sms_v2.xml
```

Server starts at `http://localhost:8080`.

---

## DSA: Search Efficiency

The API uses a **Python dictionary** (`id → transaction`) as its internal data store, giving O(1) average lookup time for `GET /transactions/{id}`.

| Method | Time Complexity | Notes |
|---|---|---|
| Linear Search | O(n) | Scans every record |
| Dictionary Lookup | O(1) | Direct hash map access |

See `dsa/search.py` for a full benchmark comparison.
