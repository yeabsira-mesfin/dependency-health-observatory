# Dependency Health Observatory

**Which observable dependency signals are useful for identifying downstream maintenance or security risks?**

A React + TypeScript dashboard backed by a credential-free Python research pipeline. It records actual npm/GitHub/OSV observations and compares declared dependencies across pinned downstream manifests. This reuses the existing `React` repository and preserves its history. Intended name: `dependency-health-observatory`.

## Working capabilities

- npm version history, latest release age, cadence, deprecation notices, maintainers count and dependency ranges.
- GitHub archival and push timestamps, date-bounded download counts and OSV latest-version advisory counts.
- Distinct interpretable maintenance signals; **inactivity is not declared abandonment**.
- Pinned before/after manifest analysis: updated, removed, retained, added, unknown; unavailable files never imply removal.
- Bounded requests, retries, caching, pagination support, provenance hashes, JSON/CSV/SQLite outputs.
- React filters, charts, source links and exports; Vercel-ready static deployment with no credentials.

## Run and verify

```bash
# Node 22+, Python 3.12+ (no Python packages required)
npm ci --ignore-scripts
npm run dev
python -m research.observatory
python -m research.analyze
python -m unittest discover -s tests -v
npm run build
```

The dashboard ships with real observations of six packages: React, request, is-number, schema-utils, terser-webpack-plugin and acorn. It also records three declared range updates in webpack between v4.47.0 and v5.99.9, pinned to commit SHAs. This does not establish why those updates happened. `public/data/observatory.json` includes observation times, API sources, response hashes and collection gaps.

Use `--refresh` for fresh requests and `--offline` to reuse a populated local cache. `python -m research.analyze` reproduces descriptive tables from the committed snapshot without network access. Live metadata changes naturally over time.

See [methods](docs/methodology.md), [reproduction](docs/reproduction.md), [limitations](docs/limitations.md), [architecture](docs/architecture.md), [QA](docs/qa-report.md), and [Vercel deployment](docs/deployment.md). MIT-licensed code. Public-source derived observations retain their source attribution; this license does not relicense upstream API content.

Related: [AgentBench Research Edition](https://github.com/yeabsira-mesfin/JavaScript) · [Post-Merge Maintenance Study](https://github.com/yeabsira-mesfin/React-).

## Academic context

- Courtney Miller, Mahmoud Jahanshahi, Audris Mockus, Bogdan Vasilescu, Christian Kästner. *Understanding the Response to Open-Source Dependency Abandonment in the npm Ecosystem*. ICSE 2025. [Author manuscript](https://courtney-e-miller.github.io/papers/QuantifyingOSSDependencyAbandonmentResponse.pdf).
- Courtney Miller, Hao He, Weigen Chen, Elizabeth Lin, Chenyang Yang, Bogdan Vasilescu, Christian Kästner. *Designing Abandabot: When Does Open Source Dependency Abandonment Matter?* ICSE 2026. [Author manuscript](https://courtney-e-miller.github.io/papers/designingAbandabot.pdf).

The first study motivates separating explicit end-of-life notices from inactivity and observing downstream responses. The second motivates contextual interpretation of dependency impact. This code uses no copied dataset, classifier, or implementation; it is an independent, small descriptive instrument, not a replication of their published results.
