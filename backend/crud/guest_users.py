"""Users for visitors who try Word Wiz without an account (routers/guest.py).

The try page keeps a random id in the browser and sends it with each reading.
The first accepted reading from an id adds a `users` row with is_guest set and
no email or password, so the row can never sign in. Later readings from the
same browser reuse it, so one visitor counts once however much they read.

Signing up from that browser (email or Google) passes the id along, and
upgrade_guest_user turns the guest row into the new account instead of adding
a second row for the same person.
"""

import uuid

from models import User, UserSettings
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

GUEST_USERNAME_PREFIX = "guest-"


def parse_guest_id(raw: str | None) -> str | None:
    """The canonical form of a browser's guest id, or None if it isn't a UUID."""
    if not raw:
        return None
    try:
        return str(uuid.UUID(raw.strip()))
    except (ValueError, AttributeError):
        return None


def _find(db: Session, guest_id: str) -> User | None:
    return (
        db.query(User)
        .filter(User.username == GUEST_USERNAME_PREFIX + guest_id, User.is_guest.is_(True))
        .first()
    )


def record_guest_user(db: Session, raw_guest_id: str | None) -> User | None:
    """Get or add the guest row for this browser. None if the id isn't valid."""
    guest_id = parse_guest_id(raw_guest_id)
    if guest_id is None:
        return None
    user = _find(db, guest_id)
    if user is not None:
        return user
    user = User(username=GUEST_USERNAME_PREFIX + guest_id, is_guest=True)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two readings from one browser raced and the other added the row.
        db.rollback()
        return _find(db, guest_id)
    db.refresh(user)
    return user


def upgrade_guest_user(
    db: Session,
    raw_guest_id: str | None,
    *,
    username: str,
    email: str,
    full_name: str | None,
    hashed_password: str | None,
) -> User | None:
    """Turn this browser's guest row into a real account.

    Returns None when there is no guest row for the id, and the caller creates
    the account as usual.
    """
    guest_id = parse_guest_id(raw_guest_id)
    user = _find(db, guest_id) if guest_id else None
    if user is None:
        return None
    user.username = username
    user.email = email
    user.full_name = full_name
    user.hashed_password = hashed_password
    user.is_guest = False
    # Guest rows skip settings because they never sign in; accounts need them.
    if user.settings is None:
        db.add(UserSettings(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user
