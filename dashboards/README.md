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

## Recommendation Rendering (Student Dashboard)

Recommendation cards are rendered directly in the student dashboard template from context values set in `StudentDashboardView`.

| Recommendation Type | Endpoint | Payload | Template Context | Displayed Fields | Notes |
| --- | --- | --- | --- | --- | --- |
| Personality | `POST {RECOMMENDATION_SERVICE_URL}recommend/personality` | `{ "user_id": "<uuid>" }` | `personality_recommendations` | Title, author, cover image, recommendation reason | Rendered when present |
| Similarity | `POST {RECOMMENDATION_SERVICE_URL}recommend/similar` | `{ "book_id": "<uuid>", "limit": 5 }` | `similarity_recommendations` | Title, author, cover image | Heading tied to the user's most recent borrowed book |

If the [recommendation service](http://github.com/peterkahumu/library-recommendation-service) is unavailable or returns no results, the dashboard still loads and recommendation sections are omitted.


## Caching

Dashboard KPI and analytics data is read through `caching.services.LibraryCacheService`.
