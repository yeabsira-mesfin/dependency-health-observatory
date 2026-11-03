# Reproduction

```bash
npm ci --ignore-scripts
python -m unittest discover -s tests -v
python -m research.analyze                 # no network; bundled snapshot
python -m research.observatory --config reproduction-config.json
npm run build
npm run preview
```

Python 3.12+ standard library only. Node 22+. Collector writes `public/data/observatory.json`, a CSV alongside it, and a local SQLite database. SQLite rows include their generation timestamp. The raw response cache is `.cache/` and is ignored by Git; it preserves source URLs, original observation times and response hashes.

`--offline` requires an already populated cache. `--refresh` bypasses cached responses. `sample-config.json` is the original sample selection; `reproduction-config.json` pins downstream commit SHAs. Package metadata is necessarily live and can change; the committed snapshot is the exact dataset for reproducible descriptive analysis. Network outages, API limits and unknown advisory data are recorded in `errors`.

All dashboard data is loaded from the checked-in JSON. Publishing a refreshed JSON and rebuilding is required to change the deployed snapshot. See deployment instructions for Vercel; no Python runtime is required there.
