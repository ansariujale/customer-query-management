# API Documentation

Base URL: `http://127.0.0.1:8000/api/`

All endpoints except register and login need this header:

```
Authorization: Token <your_token>
```

Interactive docs (Swagger): `http://127.0.0.1:8000/api/docs/`

---

## 1. Register

`POST /api/register/`

Request:
```json
{
    "username": "demo",
    "email": "demo@example.com",
    "password": "StrongPass@123",
    "confirm_password": "StrongPass@123"
}
```

Response `201`:
```json
{
    "message": "User registered successfully",
    "user": {"id": 1, "username": "demo", "email": "demo@example.com"},
    "token": "ef48c7250d7c6635d74231881c52c390c85bbac3"
}
```

Validation error `400`:
```json
{
    "confirm_password": ["Passwords do not match."]
}
```

## 2. Login

`POST /api/login/`

Request:
```json
{
    "username": "demo",
    "password": "StrongPass@123"
}
```

Response `200`:
```json
{
    "message": "Login successful",
    "token": "ef48c7250d7c6635d74231881c52c390c85bbac3",
    "user": {"id": 1, "username": "demo", "email": "demo@example.com"}
}
```

Wrong credentials `401`:
```json
{"error": "Invalid username or password"}
```

## 3. Logout

`POST /api/logout/`

Response `200`:
```json
{"message": "Logged out successfully"}
```

## 4. Create Query

`POST /api/queries/`

Request:
```json
{
    "customer_name": "Rahul Sharma",
    "email": "rahul@example.com",
    "subject": "Payment deducted twice",
    "description": "My payment has been deducted twice, but my subscription is still not activated."
}
```

`category`, `priority` and `status` are optional. Defaults are General, Medium and Pending.

Response `201`:
```json
{
    "id": 1,
    "customer_name": "Rahul Sharma",
    "email": "rahul@example.com",
    "subject": "Payment deducted twice",
    "description": "My payment has been deducted twice, but my subscription is still not activated.",
    "category": "General",
    "priority": "Medium",
    "status": "Pending",
    "suggested_response": "",
    "analysed_by": "",
    "analysed_at": null,
    "created_by": "demo",
    "created_at": "2026-11-19T05:25:27.073148Z",
    "updated_at": "2026-11-19T05:25:27.073186Z"
}
```

Validation error `400`:
```json
{
    "customer_name": ["Customer name must be at least 2 characters."],
    "email": ["Enter a valid email address."],
    "description": ["Description must be at least 10 characters."]
}
```

## 5. List Queries

`GET /api/queries/`

Optional query params:

| Param | Example | Notes |
|---|---|---|
| search | `?search=rahul` | matches customer name or email |
| category | `?category=Billing` | Technical, Billing, General, Account Related |
| priority | `?priority=High` | Low, Medium, High |
| status | `?status=Pending` | Pending, In Progress, Resolved |
| page | `?page=2` | 10 results per page |

Response `200`:
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "customer_name": "Rahul Sharma",
            "email": "rahul@example.com",
            "subject": "Payment deducted twice",
            "category": "Billing",
            "priority": "High",
            "status": "Pending",
            "...": "..."
        }
    ]
}
```

## 6. Query Details

`GET /api/queries/1/`

Response `200`: same object as in Create Query.

Not found or belongs to another user `404`:
```json
{"detail": "No CustomerQuery matches the given query."}
```

## 7. Update Query

`PUT /api/queries/1/` (send all fields) or `PATCH /api/queries/1/` (send only the fields you want to change)

Request:
```json
{
    "customer_name": "Rahul Sharma",
    "email": "rahul.new@example.com",
    "subject": "Payment deducted twice",
    "description": "Payment deducted twice, please check urgently.",
    "category": "Billing",
    "priority": "High",
    "status": "In Progress"
}
```

Response `200`: the updated query object.

## 8. Update Status

`PATCH /api/queries/1/status/`

Request:
```json
{"status": "Resolved"}
```

Response `200`: the updated query object.

Invalid status `400`:
```json
{"status": ["\"Closed\" is not a valid choice."]}
```

## 9. Delete Query

`DELETE /api/queries/1/`

Response `200`:
```json
{"message": "Query deleted successfully"}
```

## 10. AI Analysis

`POST /api/queries/1/analyze/`

No request body. It reads the subject and description of the saved query, sends it to Gemini and saves the result on the query.

Response `200`:
```json
{
    "message": "Query analysed successfully",
    "ai_used": "gemini",
    "analysis": {
        "category": "Billing",
        "priority": "High",
        "suggested_response": "We apologise for the inconvenience. Our team will verify the payment transaction and help activate your subscription."
    },
    "query": {
        "id": 1,
        "category": "Billing",
        "priority": "High",
        "suggested_response": "We apologise for the inconvenience. Our team will verify the payment transaction and help activate your subscription.",
        "analysed_by": "gemini",
        "analysed_at": "2026-11-19T05:25:28.124812Z",
        "...": "..."
    }
}
```

If Gemini is down or the key is missing, `ai_used` will be `"fallback"` and the result comes from keyword rules.

## 11. Dashboard

`GET /api/dashboard/`

Response `200`:
```json
{
    "total": 1,
    "pending": 1,
    "in_progress": 0,
    "resolved": 0,
    "high_priority": 1
}
```

## Common Errors

| Code | When |
|---|---|
| 400 | validation failed |
| 401 | token missing or wrong |
| 404 | query not found or not yours |
