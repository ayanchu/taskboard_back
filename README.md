# Taskboard Backend (Django + DRF)

A REST API backend for a Trello-style task/project management tool, built with
Django REST Framework and JWT auth. Designed to pair with a React + Redux frontend.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

The API will be available at `http://localhost:8000/`.

## Data model

- **Board** — a workspace. Has an `owner` and `members` (M2M).
- **List** — a column on a board (e.g. "To Do"). Has a `position` (float).
- **Card** — a task inside a list. Has a `position` (float), optional `assignee`, `due_date`.
- **Comment** — a comment on a card.

`position` is a **float**, not an integer, on purpose: when a card is dropped
between two existing cards, the frontend can just send the midpoint value
(e.g. between position 1 and 2 → send 1.5) without needing to re-save every
other card's position. Positions only need periodic re-normalization if they
get too granular after many reorders — not required for normal usage.

## Auth

JWT via `djangorestframework-simplejwt`.

| Endpoint | Method | Body | Notes |
|---|---|---|---|
| `/api/auth/register/` | POST | `username`, `email`, `password` | Public |
| `/api/auth/login/` | POST | `username`, `password` | Returns `access` + `refresh` tokens |
| `/api/auth/refresh/` | POST | `refresh` | Returns new `access` token |

Send the access token on every other request:
```
Authorization: Bearer <access_token>
```

## API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/boards/` | GET, POST | List boards you own/belong to; create a board |
| `/api/boards/{id}/` | GET, PATCH, DELETE | Full nested board (lists → cards → comments) in one response |
| `/api/lists/` | POST | Create a list on a board |
| `/api/lists/{id}/` | GET, PATCH, DELETE | |
| `/api/lists/{id}/reorder/` | PATCH | `{ "position": 2.5 }` — update a list's position |
| `/api/cards/` | POST | Create a card in a list |
| `/api/cards/{id}/` | GET, PATCH, DELETE | |
| `/api/cards/{id}/move/` | PATCH | `{ "list_id": 3, "position": 1.5 }` — the drag-and-drop endpoint: moves a card to a (possibly different) list at a new position |
| `/api/comments/` | POST | Create a comment on a card |
| `/api/comments/{id}/` | GET, DELETE | |

All list/card/comment endpoints are automatically scoped to boards the
authenticated user owns or is a member of — other users' boards return `404`,
not `403`, so board existence isn't leaked to non-members.

## Permissions

`boards/permissions.py` defines `IsBoardMember`, which walks up the FK chain
(`Comment → Card → List → Board`) to check membership, so the same permission
class works for every nested resource without duplicating access logic.

## Example flow (verified working)

```
POST /api/auth/register/   {username, email, password}      -> 201
POST /api/auth/login/      {username, password}              -> {access, refresh}
POST /api/boards/          {title}                           -> 201, board id
POST /api/lists/           {board, title, position}          -> 201, list id  (x2)
POST /api/cards/           {list, title, position}           -> 201, card id
GET  /api/boards/{id}/                                       -> full nested tree
PATCH /api/cards/{id}/move/  {list_id, position}             -> card relocated
```

This was tested end-to-end with DRF's `APIClient`, including confirming a
second user cannot see or modify another user's board.

## CORS

`django-cors-headers` is configured to allow `http://localhost:3000` (typical
Create React App / Vite dev server port). Adjust `CORS_ALLOWED_ORIGINS` in
`config/settings.py` for your frontend's actual origin, and for production.

## Notes for production

- Switch `DATABASES` to PostgreSQL.
- Move `SECRET_KEY` and `DEBUG` to environment variables.
- Set `ALLOWED_HOSTS` to your real domain (currently includes `testserver`
  for the test client and `localhost`/`127.0.0.1` for local dev).
