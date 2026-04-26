# Dashboards App

The `dashboards` app provides role-specific dashboards and transaction log views.

## Responsibilities

- Admin dashboard KPIs and trend analytics.
- Librarian dashboard operational metrics.
- Student dashboard personal borrowing summary.
- Filterable transaction logs.
- Admin user role update action.

## Key Views

- `AdminDashboardView`
- `LibrarianDashboardView`
- `StudentDashboardView`
- `TransactionLogsView`
- `UserRoleUpdateView`

## Caching

Dashboard KPI and analytics data is read through `caching.services.LibraryCacheService`.
