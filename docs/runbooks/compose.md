# Compose Runbook

## Launch the Stack

Start the full EX3 stack with Docker Compose from the project root:

```bash
docker compose up --build
```

This builds the images, starts the API, UI, Redis, and worker services, and keeps the stack running in the foreground. Use this command for the full end-to-end demo.

If you want the dashboard to open with sample content, seed the API database after the stack is up:

```bash
docker compose exec api uv run python -m scripts.seed
```

For a faster demo flow, the project also includes [scripts/demo.sh](../../scripts/demo.sh), which starts the stack in detached mode, seeds data, and prints the URLs to open.

## Run the Automated Tests

Run the project test suite with:

```bash
uv run python -m pytest tests/
```

This executes the API and worker tests against the local project environment.

## Thoughtful Enhancement: CSV Export

The Streamlit dashboard includes a **CSV Export** button on the **Games** tab labeled **Export Games to CSV**. It exports the upcoming games table to a file named `games_schedule.csv`.

To test the feature:

1. Start the stack with `docker compose up --build`.
2. Open the Streamlit UI in your browser.
3. Go to the **Games** tab.
4. Confirm that the upcoming games table is visible.
5. Click **Export Games to CSV**.
6. Verify that the browser downloads `games_schedule.csv` and that the file contains the current upcoming games rows.

If no upcoming open games are available, the button will not appear because the export is generated from the rendered games table.

## Verify Health

After launching the stack, a quick local check is:

```bash
docker compose ps
docker compose exec redis redis-cli ping
```

You should see the API and UI running, Redis should return `PONG`, and the worker should complete with exit code 0.
