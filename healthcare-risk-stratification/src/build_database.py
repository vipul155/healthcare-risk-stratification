#!/usr/bin/env python3
"""Load the TuteDude course CSVs into a local SQLite database.

The source patients.csv contains a Name column. This loader intentionally ignores
that column and never writes it to the database.
"""
from __future__ import annotations

import csv
import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Callable, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATABASE = PROJECT_ROOT / "data" / "processed" / "healthcare.db"
SCHEMA_FILE = PROJECT_ROOT / "sql" / "00_create_tables.sql"

# Source headers map to clean database column names. Name is intentionally absent.
TABLES: dict[str, dict[str, tuple[str, Callable[[str], Any]]]] = {
    "patients": {
        "patient_id": ("PatientID", int),
        "age": ("Age", int),
        "gender": ("Gender", str),
        "diagnosis_id": ("DiagnosisID", int),
        "admission_date": ("AdmissionDate", str),
        "discharge_date": ("DischargeDate", str),
        "outcome_id": ("OutcomeID", int),
        "treatment_cost": ("TreatmentCost", float),
    },
    "diagnoses": {
        "diagnosis_id": ("DiagnosisID", int),
        "diagnosis_name": ("DiagnosisName", str),
    },
    "labs": {
        "lab_id": ("LabID", int),
        "patient_id": ("PatientID", int),
        "test_name": ("TestName", str),
        "result": ("Result", float),
        "normal_range": ("NormalRange", str),
    },
    "outcomes": {
        "outcome_id": ("OutcomeID", int),
        "outcome_name": ("OutcomeName", str),
    },
}


def convert_value(value: str | None, converter: Callable[[str], Any], file_name: str, row_number: int, header: str) -> Any:
    cleaned = (value or "").strip()
    if not cleaned:
        return None
    try:
        return converter(cleaned)
    except ValueError as exc:
        raise ValueError(
            f"{file_name}, row {row_number}: expected {header} to be "
            f"{converter.__name__}, got {cleaned!r}"
        ) from exc


def read_records(table: str, raw_dir: Path) -> list[tuple[Any, ...]]:
    file_name = f"{table}.csv"
    file_path = raw_dir / file_name
    if not file_path.exists():
        raise FileNotFoundError(f"Missing {file_path}. Put the course CSVs in data/raw/.")

    field_map = TABLES[table]
    records: list[tuple[Any, ...]] = []
    with file_path.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError(f"{file_name} is empty or has no header row.")

        actual_headers = {header.strip().casefold(): header for header in reader.fieldnames if header}
        required_headers = [source_header for source_header, _ in field_map.values()]
        missing = [header for header in required_headers if header.casefold() not in actual_headers]
        if missing:
            raise ValueError(f"{file_name} is missing required columns: {', '.join(missing)}")

        for row_number, row in enumerate(reader, start=2):
            values = []
            for source_header, converter in field_map.values():
                actual_header = actual_headers[source_header.casefold()]
                values.append(convert_value(row.get(actual_header), converter, file_name, row_number, source_header))
            records.append(tuple(values))
    return records


def insert_records(connection: sqlite3.Connection, table: str, records: list[tuple[Any, ...]]) -> None:
    columns = list(TABLES[table])
    column_sql = ", ".join(columns)
    placeholders = ", ".join("?" for _ in columns)
    connection.executemany(
        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})",
        records,
    )


def count_rows(connection: sqlite3.Connection, table: str) -> int:
    return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def print_quality_summary(connection: sqlite3.Connection) -> None:
    checks = [
        ("duplicate patient IDs", "SELECT COUNT(*) FROM (SELECT patient_id FROM patients GROUP BY patient_id HAVING COUNT(*) > 1)"),
        ("duplicate lab IDs", "SELECT COUNT(*) FROM (SELECT lab_id FROM labs GROUP BY lab_id HAVING COUNT(*) > 1)"),
        ("patients without a matching diagnosis", "SELECT COUNT(*) FROM patients p LEFT JOIN diagnoses d ON d.diagnosis_id = p.diagnosis_id WHERE p.diagnosis_id IS NULL OR d.diagnosis_id IS NULL"),
        ("patients without a matching outcome", "SELECT COUNT(*) FROM patients p LEFT JOIN outcomes o ON o.outcome_id = p.outcome_id WHERE p.outcome_id IS NULL OR o.outcome_id IS NULL"),
        ("labs without a matching patient", "SELECT COUNT(*) FROM labs l LEFT JOIN patients p ON p.patient_id = l.patient_id WHERE l.patient_id IS NULL OR p.patient_id IS NULL"),
        ("rows missing a patient age", "SELECT COUNT(*) FROM patients WHERE age IS NULL"),
        ("rows missing admission or discharge dates", "SELECT COUNT(*) FROM patients WHERE admission_date IS NULL OR discharge_date IS NULL"),
    ]
    print("\nBasic quality summary (counts only; no patient details):")
    for label, query in checks:
        value = connection.execute(query).fetchone()[0]
        print(f"- {label}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Load the course CSVs into a local SQLite database.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=RAW_DIR,
        help="Folder containing patients.csv, diagnoses.csv, labs.csv, and outcomes.csv.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DATABASE,
        help="Path for the generated SQLite database.",
    )
    args = parser.parse_args()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_FILE.read_text(encoding="utf-8")

    try:
        records_by_table = {table: read_records(table, args.input_dir) for table in TABLES}
        with sqlite3.connect(args.database) as connection:
            connection.executescript(schema)
            # The database is generated from the CSVs, so a rerun rebuilds its contents.
            for table in TABLES:
                connection.execute(f"DELETE FROM {table}")
            for table, records in records_by_table.items():
                insert_records(connection, table, records)

            print(f"Loaded database: {args.database}")
            for table in TABLES:
                print(f"- {table}: {count_rows(connection, table)} rows")
            print_quality_summary(connection)
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"Import stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
