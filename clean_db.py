import asyncio
from app.database.session import async_engine
from sqlalchemy import text

async def c():
    async with async_engine.connect() as conn:
        await conn.execute(text("DELETE FROM users WHERE email = 'testuser@example.com'"))
        await conn.commit()
        print("DB cleaned")

asyncio.run(c())
