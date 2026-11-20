from sqlalchemy import text

from app.config.database import engine


def insert_residential_destination_record(data):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO residential_destinations (
                    site_id,
                    street_address,
                    latitude,
                    longitude,
                    ground_elevation_ft
                )
                VALUES (
                    :site_id,
                    :street_address,
                    :latitude,
                    :longitude,
                    :ground_elevation_ft
                )
                RETURNING destination_id
            """),
            {
                "site_id": data["site_id"],
                "street_address": data["street_address"],
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "ground_elevation_ft": data.get(
                    "ground_elevation_ft"
                ),
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
                    latitude,
                    longitude,
                    ground_elevation_ft
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
                    latitude,
                    longitude,
                    ground_elevation_ft
                FROM residential_destinations
                WHERE site_id = :site_id
                ORDER BY street_address
            """),
            {"site_id": site_id}
        )

        return result.mappings().all()



def patch_residential_destination_record(destination_id, data):
    allowed_fields = [
        "street_address",
        "latitude",
        "longitude",
        "ground_elevation_ft",
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
                    {", ".join(set_clauses)}
                WHERE destination_id = :destination_id
                RETURNING destination_id
            """),
            params
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


