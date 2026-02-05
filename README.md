# Legartis – Contract Clause Tracker (Case Study)

## Goal
Build a small system that:
- Stores uploaded contracts (text/markdown)
- Detects presence of clause types using patterns (keywords now; regex/AI later)
- Allows user confirmation/override (hybrid workflow)
- Shows an overview matrix (contracts × clause types)

This repository is implemented as a Docker Compose stack: Postgres + Flask API + SPA.

Run:
```
docker-compose up
```