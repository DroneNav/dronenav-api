# FAA TFR Applicability API

The DroneNav FAA TFR Applicability API provides a single interface for determining which current FAA Temporary Flight Restrictions (TFRs) apply to a geographic location or operating geometry.

The caller supplies GeoJSON geometry. DroneNav identifies relevant current FAA TFRs, evaluates their geometry and effective schedules, and returns the applicable restrictions in a normalized machine-readable form together with the FAA's human-readable TFR notice.

The caller does not need to retrieve or interpret FAA WFS, AIXM, or TFR web-text data directly.

## Endpoint

```http
POST /api/tfrs/applicability
Content-Type: application/json
```

## Request

The request body contains a GeoJSON `geometry` object.

### Point Example

To determine which TFRs currently apply at a specific geographic coordinate:

```json
{
  "geometry": {
    "type": "Point",
    "coordinates": [
      -90.45083333,
      46.5025
    ]
  }
}
```

GeoJSON coordinates use the standard order:

```text
[longitude, latitude]
```

## Response

The API returns:

```json
{
  "tfrs": []
}
```

The `tfrs` array contains every current FAA TFR determined to be applicable to the submitted geometry.

If no current TFR applies, the array is empty:

```json
{
  "tfrs": []
}
```

An empty result means that the service did not identify a currently applicable FAA TFR for the submitted geometry. It does **not** mean that the location is free from every possible aviation restriction, NOTAM, or regulatory requirement.

## Applicable TFR Example

A successful match has the following general structure:

```json
{
  "tfrs": [
    {
      "notam_id": "6/9847",
      "restriction_type": "91.137(a)(1)",
      "issued_at": "2026-09-01T16:11:22Z",
      "begins_at": "2026-09-01T16:02:00+00:00",
      "ends_at": "2026-09-08T22:00:00+00:00",
      "begin_time_reference": "UTC",
      "end_time_reference": "UTC",

      "airspace_usages": [
        {
          "airspace_id": "Airspace001",

          "geometry_components": [
            {
              "operation": "BASE",
              "geometry": {
                "type": "circle",
                "center": [
                  -90.45083333,
                  46.5025
                ],
                "radius": {
                  "value": 2.0,
                  "unit": "NM"
                }
              }
            }
          ],

          "layers": [
            {
              "altitude_interpretation": "ABOVE_LOWER",

              "lower_altitude": {
                "value": "0",
                "unit": "FT",
                "raw_reference": "OTHER",
                "resolved_reference": "SURFACE"
              },

              "upper_altitude": {
                "value": "2000",
                "unit": "FT",
                "raw_reference": "OTHER",
                "resolved_reference": "AGL"
              },

              "normalized_schedules": [
                {
                  "type": "EXPLICIT_INTERVAL",
                  "start_date": "01-09",
                  "start_time": "16:02",
                  "end_date": "08-09",
                  "end_time": "22:00",
                  "day": null
                }
              ],

              "schedules": [
                {
                  "start_date": "01-09",
                  "start_time": "16:02",
                  "end_date": "08-09",
                  "end_time": "22:00",
                  "day": null,
                  "time_reference": "UTC"
                }
              ]
            }
          ]
        }
      ],

      "faa_text": "<Table> ... FAA human-readable TFR content ... </Table>"
    }
  ]
}
```

The exact number of airspace usages, geometry components, altitude layers, and schedules depends on the FAA TFR.

## NOTAM Identification

`notam_id` is the FAA NOTAM identifier associated with the TFR.

Example:

```json
"notam_id": "6/9847"
```

Applications should preserve this identifier when displaying, logging, or otherwise referencing the restriction.

## Restriction Type

`restriction_type` identifies the regulatory basis or type of restriction reported for the TFR.

Example:

```json
"restriction_type": "91.137(a)(1)"
```

Applications should not attempt to infer the restriction type from the geometry or altitude information.

## Effective Period

The overall TFR validity period is provided by:

```json
{
  "begins_at": "2026-09-01T16:02:00+00:00",
  "ends_at": "2026-09-08T22:00:00+00:00",
  "begin_time_reference": "UTC",
  "end_time_reference": "UTC"
}
```

These values describe the overall validity of the TFR.

Individual airspace layers may contain additional schedule information that determines when a particular portion of the restriction is effective.

## Airspace Usages

`airspace_usages` contains the normalized airspace definitions associated with the TFR.

A TFR may contain one or more airspace usages.

Each usage may contain:

* one or more geometry components;
* one or more altitude layers;
* one or more effective schedules.

Clients should not assume that a TFR contains only one circle, polygon, altitude range, or schedule.

## Geometry

TFR geometry is represented by `geometry_components`.

Example circle:

```json
{
  "operation": "BASE",
  "geometry": {
    "type": "circle",
    "center": [
      -90.45083333,
      46.5025
    ],
    "radius": {
      "value": 2.0,
      "unit": "NM"
    }
  }
}
```

DroneNav normalizes FAA airspace geometry so callers do not need to interpret the original FAA AIXM geometry representation.

Geometry components may use operations including:

```text
BASE
SUBTR
```

`BASE` establishes restricted geometry.

`SUBTR` removes geometry from the applicable area.

Clients reconstructing the complete restriction geometry should preserve these operations rather than treating every component as an independent restricted area.

## Altitude

Altitude restrictions are represented within an airspace layer.

Example:

```json
{
  "lower_altitude": {
    "value": "0",
    "unit": "FT",
    "resolved_reference": "SURFACE"
  },
  "upper_altitude": {
    "value": "2000",
    "unit": "FT",
    "resolved_reference": "AGL"
  }
}
```

Altitude references may vary between TFRs.

Examples include:

```text
SURFACE
AGL
MSL
FL
```

Callers should therefore use both the altitude value and its resolved reference rather than assuming all FAA TFR altitudes use the same vertical reference.

## Schedules

TFRs may be continuously effective for their entire validity period or may contain more specific operating schedules.

DroneNav returns normalized schedule information in `normalized_schedules`.

Schedule types may include:

```text
EXPLICIT_INTERVAL
RECURRING
OPEN_START
OPEN_END
TFR_VALIDITY
```

The original normalized FAA schedule representation is also available through `schedules`.

Where a time reference is supplied, callers should preserve it when interpreting or displaying schedule information.

FAA TFR schedules are commonly expressed in UTC.

## FAA Human-Readable Text

Each applicable TFR includes:

```json
"faa_text": "..."
```

`faa_text` contains the human-readable HTML supplied by the FAA for the TFR.

It can contain information such as:

* NOTAM number;
* issue date;
* location;
* beginning and ending dates;
* reason for the NOTAM;
* restriction type;
* affected areas;
* altitude information;
* operating restrictions and requirements;
* FAA or controlling-facility contact information;
* regulatory authority;
* other explanatory information supplied by the FAA.

This field complements the normalized machine-readable fields.

Applications can use the normalized fields for automated processing while making `faa_text` available when a human needs to review the FAA's own presentation of the restriction.

### Rendering `faa_text`

`faa_text` is externally supplied HTML.

Web applications should treat it as external content and apply appropriate HTML sanitization before inserting it into a browser DOM.

The FAA HTML may also contain relative links or image references. Clients should not assume that those relative resources will resolve correctly from the client's own application origin.

## What the API Determines

The endpoint answers:

> **Which current FAA Temporary Flight Restrictions apply to this submitted geometry?**

DroneNav performs the underlying FAA data retrieval and interpretation necessary to answer that question.

Conceptually:

```text
Submitted GeoJSON
        |
        v
Current FAA TFR inventory
        |
        v
Spatial candidate selection
        |
        v
FAA TFR detail
        |
        v
Geometry interpretation
        |
        v
Altitude and schedule normalization
        |
        v
Current applicability evaluation
        |
        v
Applicable TFRs
        |
        +-- machine-readable normalized data
        |
        +-- FAA human-readable text
```

The implementation details and FAA source formats are intentionally hidden from API consumers.

## Important Scope

This API is specifically an **FAA Temporary Flight Restriction applicability service**.

An empty `tfrs` array means no currently applicable TFR was identified for the submitted geometry.

It does not constitute a determination that:

* the airspace is generally unrestricted;
* flight is authorized;
* no other NOTAM applies;
* no controlled-airspace authorization is required;
* no local, state, federal, or other operational restriction applies;
* the proposed operation complies with all applicable aviation regulations.

Applications should treat TFR applicability as one component of their broader flight-planning or operational decision process.

## Typical Integration

A client application generally needs only one request:

```text
Operating geometry
       |
       v
POST /api/tfrs/applicability
       |
       v
tfrs[]
       |
       +-- empty
       |     No applicable TFR identified
       |
       +-- one or more entries
             |
             +-- normalized data for software
             |
             +-- faa_text for human review
```

This allows an application to integrate current FAA TFR awareness without implementing its own FAA TFR discovery, AIXM parsing, geometry processing, altitude interpretation, schedule normalization, or human-readable TFR retrieval.

