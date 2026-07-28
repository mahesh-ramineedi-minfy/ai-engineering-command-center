"""
One-off admin script: seed a demo manager account so the login feature has
something to log in with out of the box.

Usage:
    python scripts/seed_manager.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sqlalchemy import select  # noqa: E402

from app.core.database import async_session_factory, init_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.user import User  # noqa: E402

# Hardcoded demo credentials — this is a buildathon/demo project, not production.
DEMO_EMAIL = "manager@example.com"
DEMO_PASSWORD = "ManagerDemo123!"


async def main() -> None:
    await init_db()
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        if result.scalar_one_or_none() is not None:
            print(f"User {DEMO_EMAIL} already exists — skipping.")
            return

        db.add(User(email=DEMO_EMAIL, hashed_password=hash_password(DEMO_PASSWORD), role="manager"))
        await db.commit()
        print(f"Seeded manager account: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
