#!/usr/bin/env bash
set -euo pipefail

echo "Welcome, grader. This demo will start the full Pick-Up Hoops stack."
echo "The script will start the services, seed sample data, and then print the key URLs."
echo "Starting Docker Compose in detached mode..."

docker compose up --build -d

echo "Seeding sample data into the API database..."
docker compose exec api uv run python -m scripts.seed

echo "Open http://localhost:8000/docs for the API."
echo "Open http://localhost:8501 for the dashboard."
echo "Use admin / adminpassword to log in if you want to test protected delete flows."
echo "In the Games tab, use Export Games to CSV to download the upcoming schedule."
