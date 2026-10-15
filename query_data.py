#!/usr/bin/env python3
"""Run starter SQL against the class-intake database.

Add more (title, sql) pairs to QUERIES, then:
    ./venv/bin/python query_data.py
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent

QUERIES: list[tuple[str, str]] = [
    (
        "How many students?",
        "SELECT count(*) AS n_students FROM students;",
    ),
    (
        "A few names and years",
        "SELECT name, school_year FROM students LIMIT 5;",
    ),
    (
        "Most common tools",
        """
        SELECT t.name, COUNT(*) AS n_students
        FROM student_tools st
        JOIN tools t ON st.tool_id = t.tool_id
        GROUP BY t.name
        ORDER BY n_students DESC;
        """,
    ),
    (
        "Most common availability slots",
        """
        SELECT a.name, COUNT(*) AS n_students
        FROM student_availability sa
        JOIN availability_slots a ON sa.slot_id = a.slot_id
        GROUP BY a.name
        ORDER BY n_students DESC;
        """,
    ),
    (
        "Average skill scores by school year",
        """
        SELECT
            school_year,
            ROUND(AVG(skill_programming), 2) AS programming,
            ROUND(AVG(skill_data_stats), 2) AS data_stats,
            ROUND(AVG(skill_frontend_design), 2) AS frontend,
            ROUND(AVG(skill_business_pitch), 2) AS pitch,
            COUNT(*) AS n
        FROM students
        GROUP BY school_year
        ORDER BY n DESC;
        """,
    ),
    (
        "Students missing working_style",
        """
        SELECT netid, name
        FROM students
        WHERE working_style IS NULL;
        """,
    ),
]


def print_rows(rows: list[dict]) -> None:
    if not rows:
        print("  (no rows)")
        return
    columns = list(rows[0].keys())
    widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            widths[col] = max(widths[col], len(str(row[col])))
    header = "  ".join(col.ljust(widths[col]) for col in columns)
    print(header)
    print("  ".join("-" * widths[col] for col in columns))
    for row in rows:
        print("  ".join(str(row[col]).ljust(widths[col]) for col in columns))


def main() -> None:
    load_dotenv(ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is not set in .env")

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for title, sql in QUERIES:
                print(f"\n=== {title} ===")
                cur.execute(sql)
                print_rows(cur.fetchall())
    finally:
        conn.close()


if __name__ == "__main__":
    main()
