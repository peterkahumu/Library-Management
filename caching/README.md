# Caching Module

This module centralizes cache key definitions and cache-backed data retrieval.

## Files

- `keys.py`: cache key constants and TTL values.
- `services.py`: `LibraryCacheService` get-or-set helpers and invalidation methods.
- `tests.py`: cache behavior and invalidation coverage.

## What Is Cached

- Homepage statistics
- Genre listings
- Dashboard KPIs and analytics
- Related books

## Invalidation

Invalidation is triggered from app signals and utility functions when key data changes.
