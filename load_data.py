#!/usr/bin/env python3
"""Create the class-intake schema and load class_dataset.csv into Postgres."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schema.sql"
CSV_CANDIDATES = (
    ROOT / "data" / "class_dataset.csv",
    ROOT / "class_dataset.csv",
)
TABLES = (
    "students",
    "tools",
    "student_tools",
    "availability_slots",
    "student_availability",
)


def csv_path() -> Path:
    for path in CSV_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("Could not find class_dataset.csv in data/ or the project root")


def normalize_netid(raw: str) -> str:
    netid = raw.strip().lower()
    suffix = "@nyu.edu"
    if netid.endswith(suffix):
        netid = netid[: -len(suffix)]
    return netid


def missing_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text or text.upper() == "#NAME?":
        return None
    return text


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def sql_statements(sql: str) -> list[str]:
    kept: list[str] = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        kept.append(line)
    body = "\n".join(kept)
    return [stmt.strip() for stmt in body.split(";") if stmt.strip()]


def get_or_create_lookup(cur, table: str, name: str) -> int:
    id_col = "tool_id" if table == "tools" else "slot_id"
    cur.execute(
        f"INSERT INTO {table} (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        (name,),
    )
    cur.execute(f"SELECT {id_col} FROM {table} WHERE name = %s", (name,))
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Failed to resolve {table} name {name!r}")
    return row[0]


def main() -> None:
    load_dotenv(ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is not set in .env")

    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    source = csv_path()

    conn = psycopg2.connect(database_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DROP TABLE IF EXISTS
                        student_availability,
                        student_tools,
                        availability_slots,
                        tools,
                        students
                    CASCADE
                    """
                )
                for statement in sql_statements(schema):
                    cur.execute(statement)

                with source.open(newline="", encoding="utf-8") as handle:
                    for row in csv.DictReader(handle):
                        netid = normalize_netid(row["netid"])
                        cur.execute(
                            """
                            INSERT INTO students (
                                netid, name, school_year, intro_programming,
                                skill_programming, skill_data_stats,
                                skill_frontend_design, skill_business_pitch,
                                working_style, interests, semester_goal, submitted_at
                            )
                            VALUES (
                                %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s, %s
                            )
                            """,
                            (
                                netid,
                                row["name"].strip(),
                                row["school_year"].strip(),
                                row["intro_programming"].strip(),
                                int(row["skill_programming"]),
                                int(row["skill_data_stats"]),
                                int(row["skill_frontend_design"]),
                                int(row["skill_business_pitch"]),
                                missing_to_none(row["working_style"]),
                                missing_to_none(row["interests"]),
                                missing_to_none(row["semester_goal"]),
                                row["submitted_at"].strip(),
                            ),
                        )

                        for tool_name in split_semicolon(row["tools"]):
                            tool_id = get_or_create_lookup(cur, "tools", tool_name)
                            cur.execute(
                                """
                                INSERT INTO student_tools (netid, tool_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                                """,
                                (netid, tool_id),
                            )

                        for slot_name in split_semicolon(row["availability"]):
                            slot_id = get_or_create_lookup(
                                cur, "availability_slots", slot_name
                            )
                            cur.execute(
                                """
                                INSERT INTO student_availability (netid, slot_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                                """,
                                (netid, slot_id),
                            )

                print("Row counts:")
                for table in TABLES:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    print(f"  {table}: {cur.fetchone()[0]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
