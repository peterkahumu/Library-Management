# Book Circulation App

The `book_circulation` app contains borrowing and return workflows.

## Responsibilities

- Track borrowing lifecycle with `Transaction` model.
- Separate physical and digital borrowing behavior.
- Expose student and librarian workflow views.
- Trigger notification emails through `communications.email.LibraryEmailService`.

## Transaction Statuses

- `PENDING`
- `ISSUED`
- `DOWNLOADED`
- `RETURN_REQUESTED`
- `RETURNED`

## Main Flows

- Student requests borrow (`BorrowBookView`).
- Librarian approves/rejects (`ApproveBorrowView`, `RejectBorrowView`).
- Student requests return (`RequestReturnView`).
- Librarian approves/rejects return (`ApproveReturnView`, `RejectReturnView`).

## Data Integrity

- Status transitions are validated.
- Stock updates are handled atomically.
- Constraints ensure returned transactions have a `returned_date`.
