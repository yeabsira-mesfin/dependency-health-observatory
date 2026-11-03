# Methodology

The original contribution is a small, reproducible observation pipeline plus a React evidence explorer, not a new abandonment predictor.

## Sampling and measurement

The fixed six-package convenience sample covers a popular package, an explicitly deprecated package, a stable package with infrequent releases, and three downstream dependencies present in webpack's two pinned manifests. It is selected to demonstrate different measurement paths, not estimate ecosystem prevalence.

Use full npm package metadata. Latest release age refers to the version named by the `latest` dist-tag, not necessarily the most recently published prerelease. Cadence is the median gap between all timestamped published versions; prereleases are included and near-simultaneous releases can create small gaps. The indicator thresholds (365/730 days) are arbitrary descriptive thresholds, not validated abandonment rules. Maintainer count does not measure active maintenance.

Deprecation comes only from the latest version's explicit notice. Archival and push timestamps come from the package's linked GitHub repository and may refer to a monorepo. Download totals carry exact measurement-period dates and are not user counts. OSV is queried for the latest exact npm version; zero returned records is not a security guarantee. This does not resolve semver ranges or transitive dependencies. A failed or truncated query is unknown, not zero.

Before/after manifests are read at exact commit SHAs. Compare direct declared dependency ranges across all dependency sections. A changed range is not a resolved-version update, proof of replacement, or causal response to deprecation. Missing files remain unknown. Retained dependencies are right-censored with respect to removal at the end of the observed pair. No historical deprecation onset is available, so this sample does not estimate response delays. The tested upper-bound helper requires an explicitly supplied signal date and is not used to invent one.

`research.analyze` describes counts by maintenance signal, advisory availability, and downstream outcome. Small convenience groups cannot support inferential or causal claims.

## Public API sources

- [npm package metadata](https://github.com/npm/registry/blob/main/docs/responses/package-metadata.md)
- [npm downloads](https://github.com/npm/registry/blob/main/docs/download-counts.md)
- [GitHub REST API](https://docs.github.com/en/rest)
- [OSV API](https://google.github.io/osv.dev/api/)

The collector is sequential (concurrency one), caps requests and response sizes, retries transient errors at most twice, respects short Retry-After values and stops on longer rate limits. The client follows same-host HTTPS redirects only and has no authentication-token support, preventing private-source collection in this demo. A local cache preserves original observation timestamps.

## Academic context

- Courtney Miller, Mahmoud Jahanshahi, Audris Mockus, Bogdan Vasilescu, Christian Kästner. *Understanding the Response to Open-Source Dependency Abandonment in the npm Ecosystem*. ICSE 2025. [Author manuscript](https://courtney-e-miller.github.io/papers/QuantifyingOSSDependencyAbandonmentResponse.pdf).
- Courtney Miller, Hao He, Weigen Chen, Elizabeth Lin, Chenyang Yang, Bogdan Vasilescu, Christian Kästner. *Designing Abandabot: When Does Open Source Dependency Abandonment Matter?* ICSE 2026. [Author manuscript](https://courtney-e-miller.github.io/papers/designingAbandabot.pdf).

The first study motivates separating explicit end-of-life notices from inactivity and observing downstream responses. The second motivates contextual interpretation of dependency impact. This code uses no copied dataset, classifier, or implementation; it is an independent, small descriptive instrument, not a replication of their published results.
