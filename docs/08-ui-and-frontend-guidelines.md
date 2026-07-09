# 08. UI and Frontend Guidelines

## Design Principles

TODO: This project currently appears to be backend/API-centered. If frontend is added, define concrete UI principles here.

General principles:

- Make primary actions clear.
- Show loading, error, and empty states.
- Do not hide server errors behind generic success messages.
- Avoid UI-only permission enforcement.

## Layout Rules

TODO: Define if a frontend application is added.

## Component Rules

- Buttons should show loading state when submitting.
- Destructive actions require clear confirmation.
- Reusable UI components should not contain domain business rules.

## Form Rules

- Required fields must be visible.
- Client validation is helpful but server validation is mandatory.
- Field errors and global errors should be visually distinct.

## Table Rules

- Tables should define empty state.
- Sorting and pagination rules should be explicit.
- Numeric values should be aligned consistently.

## Loading / Error / Empty States

- Loading state should prevent duplicate submission.
- Error state should show a recoverable message where possible.
- Empty state should explain what is missing and what the user can do next.

## State Management

TODO: Choose state management only if frontend exists.

## Accessibility

- Interactive controls should be keyboard accessible.
- Form inputs should have labels.
- Error messages should be associated with the relevant field.

## Open Questions

- Open Question: Will this project include frontend UI?
- Open Question: If frontend exists, what framework will be used?

