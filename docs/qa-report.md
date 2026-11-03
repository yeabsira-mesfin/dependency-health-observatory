# QA report

Verified locally on 2026-11-03, Python 3.12.14 and Node 24.22.1.

- 15 deterministic unit/transport tests passed. Includes unknown-vs-negative evidence, provenance/metrics edge cases, CSV injection escaping, rate-limit handling, host validation, cache provenance and pagination truncation.
- Public-data collection completed with zero reported source errors for the bundled sample.
- Offline analysis runs against the committed snapshot without credentials.
- TypeScript and Vite production build checked before publication.
- No raw API cache, credentials, personal emails or SQLite database is included in the published tree. Source URLs and response hashes accompany derived observations.
- Remote CI and Vercel deployment status are separate from these local checks. No Vercel deployment is claimed.

See methodology and limitations for research interpretation. A passing software test suite does not validate causal inference or make the sample representative.
