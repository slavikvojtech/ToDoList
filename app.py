from __future__ import annotations

import json
import os
from datetime import datetime, date
from uuid import uuid4

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def ensure_storage() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_tasks() -> list[dict]:
    ensure_storage()
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_tasks(tasks: list[dict]) -> None:
    ensure_storage()
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)


def parse_due_time(value: str) -> datetime:
    """
    Accepts "HH:MM" or "HH:MM-HH:MM" (range) and returns a datetime for sorting.
    Falls back to a far-future datetime if parsing fails.
    """
    if not value:
        return datetime.max

    value = value.strip()
    if "-" in value:
        value = value.split("-", 1)[0].strip()
    try:
        parsed_time = datetime.strptime(value, "%H:%M").time()
        return datetime.combine(date.today(), parsed_time)
    except ValueError:
        return datetime.max


def normalize_time_text(value: str) -> str:
    if not value:
        return value

    value = value.strip()
    if "-" in value:
        start_raw, end_raw = value.split("-", 1)
        start = normalize_time_text(start_raw.strip())
        end = normalize_time_text(end_raw.strip())
        return f"{start}-{end}" if start and end else value

    if ":" in value:
        return value

    if value.isdigit():
        if len(value) <= 2:
            return f"{int(value):02d}:00"
        if len(value) == 3:
            hours = int(value[0])
            minutes = int(value[1:])
            return f"{hours:02d}:{minutes:02d}"
        if len(value) == 4:
            hours = int(value[:2])
            minutes = int(value[2:])
            return f"{hours:02d}:{minutes:02d}"

    return value


def circle_size(title: str, priority: str) -> int:
    base_map = {"low": 120, "medium": 140, "high": 160}
    base = base_map.get(priority, 120)
    extra = max(0, len(title) - 20) * 2
    return base + extra


@app.route("/")
def index():
    tasks = load_tasks()
    has_done = any(task.get("done") for task in tasks)
    tasks_sorted = sorted(
        tasks,
        key=lambda t: (
            parse_due_time(t.get("due_time", "")),
            PRIORITY_ORDER.get(t.get("priority", "low"), 3),
        ),
    )
    return render_template(
        "index.html",
        tasks=tasks_sorted,
        circle_size=circle_size,
        has_done=has_done,
    )


@app.post("/add")
def add_task():
    title = request.form.get("title", "").strip()
    due_time = normalize_time_text(request.form.get("due_time", "").strip())
    priority = request.form.get("priority", "low").strip().lower()

    if not title or not due_time:
        return redirect(url_for("index"))

    if priority not in ("low", "medium", "high"):
        priority = "low"

    task = {
        "id": str(uuid4()),
        "title": title,
        "due_time": due_time,
        "priority": priority,
        "done": False,
        "created_at": datetime.utcnow().isoformat(),
    }

    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)

    return redirect(url_for("index"))


@app.post("/toggle/<task_id>")
def toggle_task(task_id: str):
    tasks = load_tasks()
    for task in tasks:
        if task.get("id") == task_id:
            task["done"] = not task.get("done", False)
            break
    save_tasks(tasks)
    return redirect(url_for("index"))


@app.post("/priority/<task_id>")
def update_priority(task_id: str):
    new_priority = request.form.get("priority", "").strip().lower()
    if new_priority not in ("low", "medium", "high"):
        return redirect(url_for("index"))

    tasks = load_tasks()
    for task in tasks:
        if task.get("id") == task_id:
            task["priority"] = new_priority
            break
    save_tasks(tasks)
    return redirect(url_for("index"))


@app.post("/delete_done")
def delete_done():
    tasks = load_tasks()
    tasks = [t for t in tasks if not t.get("done")]
    save_tasks(tasks)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
