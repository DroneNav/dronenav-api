from sqlalchemy import text

from app.config.database import engine


FAA_MASTER_FILE = "database/data/DOF.DAT"
FAA_DAILY_CHANGE_FILE = "database/data/DOF_DAILY_CHANGE_UPDATE.DAT"
FAA_BATCH_SIZE = 1000


def dms_to_decimal(value):
    parts = value.strip().split()

    if len(parts) != 3:
        raise ValueError(f"Invalid FAA coordinate: {value!r}")

    degrees = int(parts[0])
    minutes = int(parts[1])
    seconds_direction = parts[2]

    direction = seconds_direction[-1]
    seconds = float(seconds_direction[:-1])

    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

    if direction in ("S", "W"):
        decimal = -decimal
    elif direction not in ("N", "E"):
        raise ValueError(f"Invalid FAA coordinate direction: {direction!r}")

    return decimal


def parse_master_record(line):
    oas_number = line[0:9].strip()
    verification_status = line[10:11].strip()
    latitude = dms_to_decimal(line[35:47])
    longitude = dms_to_decimal(line[48:61])
    obstacle_type = line[62:81].strip()
    quantity = int(line[81:82].strip())
    maximum_height_agl_ft = int(line[84:89].strip())
    elevation_amsl_ft = int(line[90:95].strip())

    return {
        "oas_number": oas_number,
        "verification_status": verification_status,
        "obstacle_type": obstacle_type,
        "quantity": quantity,
        "maximum_height_agl_ft": maximum_height_agl_ft,
        "elevation_amsl_ft": elevation_amsl_ft,
        "latitude": latitude,
        "longitude": longitude,
    }


def parse_daily_change_record(line):
    action = line[0:9].strip()
    oas_number = line[10:19].strip()
    verification_status = line[20:21].strip()
    latitude = dms_to_decimal(line[45:57])
    longitude = dms_to_decimal(line[58:71])
    obstacle_type = line[72:91].strip()
    quantity = int(line[91:92].strip())
    maximum_height_agl_ft = int(line[93:98].strip())
    elevation_amsl_ft = int(line[99:104].strip())

    return {
        "action": action,
        "oas_number": oas_number,
        "verification_status": verification_status,
        "obstacle_type": obstacle_type,
        "quantity": quantity,
        "maximum_height_agl_ft": maximum_height_agl_ft,
        "elevation_amsl_ft": elevation_amsl_ft,
        "latitude": latitude,
        "longitude": longitude,
    }


def load_master_records():
    with open(FAA_MASTER_FILE, "r", encoding="cp1252") as faa_file:
        for line_number, line in enumerate(faa_file, start=1):
            if line_number <= 4:
                continue

            if not line.strip():
                continue

            yield parse_master_record(line)


def load_daily_change_records():
    with open(FAA_DAILY_CHANGE_FILE, "r", encoding="cp1252") as faa_file:
        for line_number, line in enumerate(faa_file, start=1):
            if line_number <= 7:
                continue

            if not line.strip():
                continue

            yield parse_daily_change_record(line)


def validate_daily_change_records(records):
    old_oas_numbers = {
        record["oas_number"]
        for record in records
        if record["action"] == "OLD"
    }

    new_oas_numbers = {
        record["oas_number"]
        for record in records
        if record["action"] == "NEW"
    }

    if old_oas_numbers != new_oas_numbers:
        raise ValueError(
            "FAA Daily Change OLD/NEW records do not match."
        )


def synchronize_daily_change_file():
    records = list(load_daily_change_records())

    validate_daily_change_records(records)

    with engine.begin() as connection:
        for record in records:
            action = record["action"]

            if action in ("ADD", "NEW"):
                upsert_daily_change_record(connection, record)
            elif action in ("REMOVE", "DISMANTLE"):
                delete_daily_change_record(connection, record)
            elif action == "OLD":
                continue
            else:
                raise ValueError(
                    f"Unsupported FAA Daily Change action: {action!r}"
                )

    print(f"Applied {len(records)} FAA Daily Change records.")


def insert_master_records(connection, records):
    connection.execute(
        text("""
            INSERT INTO faa_obstacles (
                oas_number,
                verification_status,
                obstacle_type,
                quantity,
                maximum_height_agl_ft,
                elevation_amsl_ft,
                geometry
            )
            VALUES (
                :oas_number,
                :verification_status,
                :obstacle_type,
                :quantity,
                :maximum_height_agl_ft,
                :elevation_amsl_ft,
                ST_SetSRID(
                    ST_MakePoint(:longitude, :latitude),
                    4326
                )
            )
        """),
        records,
    )


def upsert_daily_change_record(connection, record):
    connection.execute(
        text("""
            INSERT INTO faa_obstacles (
                oas_number,
                verification_status,
                obstacle_type,
                quantity,
                maximum_height_agl_ft,
                elevation_amsl_ft,
                geometry
            )
            VALUES (
                :oas_number,
                :verification_status,
                :obstacle_type,
                :quantity,
                :maximum_height_agl_ft,
                :elevation_amsl_ft,
                ST_SetSRID(
                    ST_MakePoint(:longitude, :latitude),
                    4326
                )
            )
            ON CONFLICT (oas_number)
            DO UPDATE SET
                verification_status = EXCLUDED.verification_status,
                obstacle_type = EXCLUDED.obstacle_type,
                quantity = EXCLUDED.quantity,
                maximum_height_agl_ft = EXCLUDED.maximum_height_agl_ft,
                elevation_amsl_ft = EXCLUDED.elevation_amsl_ft,
                geometry = EXCLUDED.geometry
        """),
        record,
    )


def delete_daily_change_record(connection, record):
    connection.execute(
        text("""
            DELETE FROM faa_obstacles
            WHERE oas_number = :oas_number
        """),
        {
            "oas_number": record["oas_number"],
        },
    )


def update_master_quantities(connection, records):
    connection.execute(
        text("""
            UPDATE faa_obstacles
            SET quantity = :quantity
            WHERE oas_number = :oas_number
        """),
        records,
    )


def synchronize_master_quantities():
    batch = []
    updated_count = 0

    with engine.begin() as connection:
        for record in load_master_records():
            if record["quantity"] == 1:
                continue

            batch.append({
                "oas_number": record["oas_number"],
                "quantity": record["quantity"],
            })

            if len(batch) >= FAA_BATCH_SIZE:
                update_master_quantities(connection, batch)
                updated_count += len(batch)
                batch = []

        if batch:
            update_master_quantities(connection, batch)
            updated_count += len(batch)

    print(f"Updated {updated_count} FAA obstacle quantities.")


def load_master_file():
    batch = []
    loaded_count = 0

    with engine.begin() as connection:
        for record in load_master_records():
            batch.append(record)

            if len(batch) >= FAA_BATCH_SIZE:
                insert_master_records(connection, batch)
                loaded_count += len(batch)
                batch = []

                print(f"Loaded {loaded_count} FAA obstacle records.")

        if batch:
            insert_master_records(connection, batch)
            loaded_count += len(batch)

    print(f"Loaded {loaded_count} FAA obstacle records.")


if __name__ == "__main__":
    load_master_file()

