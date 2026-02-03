# Circle TODOs (Flask)

A small, clean Flask TODO app with circular task badges, three priority levels, and JSON persistence.

## Run

```bash
pip install -r requirements.txt
flask --app app run --debug
```

Open the local URL printed by Flask (usually `http://127.0.0.1:5000`).

## Notes

- Tasks persist in `data/tasks.json` (auto-created on first run).
- Due time accepts `HH:MM` or a datetime-local string.
- Sorting is by due time ascending, then priority.
