from sqlalchemy import text

from app.config.database import engine


def insert_residential_destination_record(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO residential_destinations (
                    site_id,
                    street_address,
                    normalized_address,
                    latitude,
                    longitude,
                    geocoded_latitude,
                    geocoded_longitude,
                    geocode_verified,
                    verified_by,
                    verified_at
                )
                VALUES (
                    :site_id,
                    :street_address,
                    :normalized_address,
                    :latitude,
                    :longitude,
                    :geocoded_latitude,
                    :geocoded_longitude,
                    :geocode_verified,
                    :verified_by,
                    :verified_at
                )
                RETURNING destination_id
            """),
            {
                "site_id": data["site_id"],
                "street_address": data["street_address"],
                "normalized_address": data["normalized_address"],
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "geocoded_latitude": data["geocoded_latitude"],
                "geocoded_longitude": data["geocoded_longitude"],
                "geocode_verified": False,
                "verified_by": None,
                "verified_at": None,
            }
        )

        return str(result.scalar())


def select_residential_destination_record(destination_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    destination_id,
                    site_id,
                    street_address,
                    normalized_address,
                    geocoded_latitude,
                    geocoded_longitude,
                    latitude,
                    longitude,
                    geocode_verified,
                    verified_by,
                    verified_at
                FROM residential_destinations
                WHERE destination_id = :destination_id
            """),
            {"destination_id": destination_id}
        )

        return result.mappings().first()


def select_residential_destination_records(site_id):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    destination_id,
                    site_id,
                    street_address,
                    normalized_address,
                    geocoded_latitude,
                    geocoded_longitude,
                    latitude,
                    longitude,
                    geocode_verified,
                    verified_by,
                    verified_at
                FROM residential_destinations
                WHERE site_id = :site_id
                ORDER BY normalized_address
            """),
            {"site_id": site_id}
        )

        return result.mappings().all()



def patch_residential_destination_record(destination_id, data):
    allowed_fields = [
        "street_address",
        "normalized_address",
        "geocoded_latitude",
        "geocoded_longitude",
        "latitude",
        "longitude",
    ]

    set_clauses = []
    params = {"destination_id": destination_id}

    for field in allowed_fields:
        if field in data:
            set_clauses.append(f"{field} = :{field}")
            params[field] = data[field]

    if not set_clauses:
        return None

    with engine.begin() as connection:
        result = connection.execute(
            text(f"""
                UPDATE residential_destinations
                SET
                    {", ".join(set_clauses)},
                    geocode_verified = FALSE,
                    verified_by = NULL,
                    verified_at = NULL
                WHERE destination_id = :destination_id
                RETURNING destination_id
            """),
            params
        )

        return result.mappings().first()


def verify_residential_destination_record(
    destination_id,
    latitude,
    longitude,
    verified_by,
):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE residential_destinations
                SET
                    latitude = :latitude,
                    longitude = :longitude,
                    geocode_verified = (
                        :latitude <> geocoded_latitude
                        AND :longitude <> geocoded_longitude
                    ),
                    verified_by = CASE
                        WHEN :latitude <> geocoded_latitude
                         AND :longitude <> geocoded_longitude
                        THEN :verified_by
                        ELSE NULL
                    END,
                    verified_at = CASE
                        WHEN :latitude <> geocoded_latitude
                         AND :longitude <> geocoded_longitude
                        THEN now()
                        ELSE NULL
                    END
                WHERE destination_id = :destination_id
                RETURNING
                    destination_id,
                    geocode_verified
            """),
            {
                "destination_id": destination_id,
                "latitude": latitude,
                "longitude": longitude,
                "verified_by": verified_by,
            }
        )

        return result.mappings().first()


def delete_residential_destination_record(destination_id):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                DELETE FROM residential_destinations
                WHERE destination_id = :destination_id
                RETURNING destination_id
            """),
            {"destination_id": destination_id}
        )

        return result.mappings().first()


