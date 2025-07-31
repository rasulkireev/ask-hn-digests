<!-- Types of changes -->
**Added** for new features.
**Changed** for changes in existing functionality.
**Deprecated** for soon-to-be removed features.
**Removed** for now removed features.
**Fixed** for any bug fixes.
**Security** in case of vulnerabilities.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2025-07-31
- You can now like and bookmark posts to read later.
- I now also generate a one tweet version of the summary


## [0.0.1] - 2025-07-27

- Use the new HN DB to get ids, instead of local duckdb
- Automated a bunch of tasks
  - getting latest HN discussions
  - generated summaries for most engaging conversations
  - scheduling the newsletter
- Add healthcheck pinging to all scheduled tasks
- Added croniter support for automated tasks
