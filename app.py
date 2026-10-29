#!/usr/bin/env python3
"""Tiny Flask app: list student names from Postgres."""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from flask import Flask, jsonify

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

app = Flask(__name__, static_folder="static", static_url_path="")


def student_names():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM students ORDER BY name")
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/names")
def api_names():
    return jsonify(student_names())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(host="0.0.0.0", port=port)
