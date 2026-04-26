# Pages App

The `pages` app provides entrypoint pages and role-aware redirect behavior.

## Current Scope

- Home page view (`HomeView`).

## Behavior

- Authenticated users are redirected to their role dashboard:
  - admin -> `admin_dashboard`
  - librarian -> `librarian_dashboard`
  - student -> `student_dashboard`
- Anonymous users receive the public home page with featured books and cached stats.
