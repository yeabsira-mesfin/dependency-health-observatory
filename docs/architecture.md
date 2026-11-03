# Architecture

React + TypeScript + Vite render checked-in JSON research outputs. UI filtering and JSON/CSV exports work in the browser without credentials. A separate Python CLI performs collection or trusted evaluation, validates inputs, records provenance, and writes JSON/CSV outputs. The two public-data pipelines also store analysis rows in local SQLite databases. Raw API caches and SQLite files stay local; sanitized derived observations are committed.

A static Vercel deployment is intentionally separate from data collection. It needs no persistent server process or database. Build and tests do not refresh network data. Collection is explicit, bounded, and cacheable. Source URLs and observation timestamps travel with data; stale observations are not presented as live monitoring.

AgentBench retains the original React reviewer workbench and FastAPI routes. Its trusted Python fixture executor is a CLI only, with no API route exposing code execution. The dashboard displays exported evidence.
