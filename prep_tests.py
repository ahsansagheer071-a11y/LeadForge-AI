import asyncio
from app.database.session import async_engine
from sqlalchemy import text

async def c():
    async with async_engine.connect() as conn:
        await conn.execute(text("DELETE FROM users WHERE email IN ('testuser@example.com', 't@t.com')"))
        await conn.commit()
        print("cleaned test users from DB")

asyncio.run(c())
