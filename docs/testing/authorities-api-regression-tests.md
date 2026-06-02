```text


curl https://api.dronenav.org/api/authorities



curl https://api.dronenav.org/api/authorities/019e886f-5110-7067-90f9-17e73143a30a



curl -X POST https://api.dronenav.org/api/authorities \
  -H "Content-Type: application/json" \
  -d '{
    "authority_name": "Georgia Test Authority",
    "authority_code": "GTA",
    "authority_type": "state_government",
    "created_by": "dronenav"
  }'


((api.dronenav.org:3.11)) [dronenavcp@raptor testing]$ curl https://api.dronenav.org/api/authorities{"authorities":[{"approved_at":null,"approved_by":null,"authority_code":"GTA","authority_id":"019e89a1-9b8a-7b73-8824-0d5d2a68bd94",
"authority_name":"Georgia Test Authority","authority_type":"state_government","contact_email":null,"contact_name":null,"contact_phon
e":null,"created_at":"2026-06-02T13:38:50.249593-05:00","created_by":"dronenav","operational_status":"active"},{"approved_at":null,"
approved_by":null,"authority_code":"NFCAA","authority_id":"019e886f-5110-7067-90f9-17e73143a30a","authority_name":"North Fulton Coun
ty Civil Aviation Authority","authority_type":"local_government","contact_email":null,"contact_name":null,"contact_phone":null,"crea
ted_at":"2026-06-02T08:04:17.166366-05:00","created_by":"dronenav","operational_status":"active"}]}

```
