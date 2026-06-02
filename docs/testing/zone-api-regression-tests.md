
# Zone API Regression Tests

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

## Create Zone 

```bash
curl -X POST https://api.dronenav.org/api/zones \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": "019e8a1d-b1a9-7c1f-87b0-3fd426c2f7bc",
    "zone_name": "Regression Test Zone",
    "zone_type": "restricted",
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
  "zone_id":"..."
}
```

Save returned Zone ID.

---

## Get Zone Collection

```bash
curl https://api.dronenav.org/api/zones
```

Expected:

```json
{
  "zones":[ ... ]
}
```

---

## Get Single zone

```bash
curl https://api.dronenav.org/api/zones/{zone_id}
```

Expected:

```json
{
  "zone_id":"..."
}
```

---

## Update zone

Change:

```text
zone_name
```

Expected:

```json
{
  "status":"updated"
}
```

---

## Delete zone

```bash
curl -X DELETE \
"https://api.dronenav.org/api/zones/{zone_id}?deleted_by=dronenav"
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
curl https://api.dronenav.org/api/zones
```

Deleted Site should not appear.

```bash
curl https://api.dronenav.org/api/zones/{zone_id}
```

Expected:

```text
404
```

---

## Database Verification

```sql
SELECT
  zone_id,
  zone_name,
  operational_status,
  deleted_at,
  deleted_by
FROM zones;
```

Verify deleted zones remain in the database.

