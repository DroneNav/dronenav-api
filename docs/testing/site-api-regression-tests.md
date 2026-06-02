
# Site API Regression Tests

## Prerequisites

Authority ID:

```text
019e886f-5110-7067-90f9-17e73143a30a
```

---

## Health Endpoint

```bash
curl https://api.dronenav.org/health
```

Expected:

```json
{"status":"ok"}
```

---

## Database Connectivity

```bash
curl https://api.dronenav.org/api/system/database
```

Expected:

```json
{
  "status":"connected"
}
```

---

## Create Site

```bash
curl -X POST https://api.dronenav.org/api/sites \
  -H "Content-Type: application/json" \
  -d '{
    "authority_id": "019e886f-5110-7067-90f9-17e73143a30a",
    "site_name": "Regression Test Site",
    "site_type": "school",
    "created_by": "dronenav",
    "minimum_altitude_ft": 0,
    "maximum_altitude_ft": 400,
    "geometry": {
      "type": "Polygon",
      "coordinates": [
        [
          [-84.2941, 34.0732],
          [-84.2938, 34.0732],
          [-84.2938, 34.0735],
          [-84.2941, 34.0735],
          [-84.2941, 34.0732]
        ]
      ]
    }
  }'
```

Expected:

```json
{
  "status":"created",
  "site_id":"..."
}
```

Save returned Site ID.

---

## Get Site Collection

```bash
curl https://api.dronenav.org/api/sites
```

Expected:

```json
{
  "sites":[ ... ]
}
```

---

## Get Single Site

```bash
curl https://api.dronenav.org/api/sites/{site_id}
```

Expected:

```json
{
  "site_id":"..."
}
```

---

## Update Site

Change:

```text
site_name
```

Expected:

```json
{
  "status":"updated"
}
```

---

## Delete Site

```bash
curl -X DELETE \
"https://api.dronenav.org/api/sites/{site_id}?deleted_by=dronenav"
```

Expected:

```json
{
  "status":"deleted"
}
```

---

## Verify Soft Delete

```bash
curl https://api.dronenav.org/api/sites
```

Deleted Site should not appear.

```bash
curl https://api.dronenav.org/api/sites/{site_id}
```

Expected:

```text
404
```

---

## Database Verification

```sql
SELECT
  site_id,
  site_name,
  operational_status,
  deleted_at,
  deleted_by
FROM sites;
```

Verify deleted Sites remain in the database.

