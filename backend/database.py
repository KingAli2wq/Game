import aiosqlite
import json
import os
import random
from uuid import uuid4
from backend.models import GameState

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "saves.db")


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS saves (
                game_id TEXT PRIMARY KEY,
                era_id TEXT,
                player_nation TEXT,
                year INTEGER,
                turn INTEGER,
                state_json TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Persistent issue pool — shared across all game sessions.
        # AI-generated and fallback issues are saved here so they can be
        # reused instead of re-generating every turn.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS issue_pool (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                issue_type TEXT DEFAULT 'political',
                urgency TEXT DEFAULT 'normal',
                options_json TEXT,
                use_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def get_pool_issue(issue_type: str = None) -> dict | None:
    """Return a random low-use issue from the pool, optionally filtered by type."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if issue_type:
            async with db.execute(
                "SELECT * FROM issue_pool WHERE issue_type = ? AND use_count < 5 ORDER BY use_count ASC, RANDOM() LIMIT 5",
                (issue_type,)
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            async with db.execute(
                "SELECT * FROM issue_pool WHERE use_count < 5 ORDER BY use_count ASC, RANDOM() LIMIT 5"
            ) as cursor:
                rows = await cursor.fetchall()
        if not rows:
            return None
        row = dict(random.choice(rows))
        row["options"] = json.loads(row.pop("options_json") or "[]")
        return row


async def add_pool_issue(issue_data: dict) -> None:
    """Save a new issue to the pool (skips duplicates by title)."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Avoid exact-title duplicates
        async with db.execute("SELECT id FROM issue_pool WHERE title = ?", (issue_data.get("title", ""),)) as cur:
            if await cur.fetchone():
                return
        await db.execute(
            "INSERT INTO issue_pool (id, title, description, issue_type, urgency, options_json) VALUES (?,?,?,?,?,?)",
            (
                str(uuid4())[:8],
                issue_data.get("title", ""),
                issue_data.get("description", ""),
                issue_data.get("issue_type", "political"),
                issue_data.get("urgency", "normal"),
                json.dumps(issue_data.get("options", [])),
            )
        )
        await db.commit()


async def mark_pool_issue_used(issue_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE issue_pool SET use_count = use_count + 1 WHERE id = ?", (issue_id,))
        await db.commit()


async def count_pool_issues(issue_type: str = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        if issue_type:
            async with db.execute(
                "SELECT COUNT(*) FROM issue_pool WHERE issue_type = ? AND use_count < 5", (issue_type,)
            ) as cur:
                row = await cur.fetchone()
        else:
            async with db.execute("SELECT COUNT(*) FROM issue_pool WHERE use_count < 5") as cur:
                row = await cur.fetchone()
        return row[0] if row else 0


async def seed_pool_if_empty(fallback_issues: list[dict]) -> None:
    """Populate the pool with fallback issues on first startup (no-op if already seeded)."""
    count = await count_pool_issues()
    if count == 0:
        for issue in fallback_issues:
            await add_pool_issue(issue)


async def save_game(state: GameState):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO saves (game_id, era_id, player_nation, year, turn, state_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            state.game_id,
            state.era_id,
            state.player_nation_id,
            state.year,
            state.turn,
            state.model_dump_json()
        ))
        await db.commit()


async def load_game(game_id: str) -> GameState | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT state_json FROM saves WHERE game_id = ?", (game_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return GameState.model_validate_json(row[0])
    return None


async def list_saves() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT game_id, era_id, player_nation, year, turn, updated_at FROM saves ORDER BY updated_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {"game_id": r[0], "era_id": r[1], "player_nation": r[2], "year": r[3], "turn": r[4], "updated_at": r[5]}
                for r in rows
            ]


async def delete_save(game_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM saves WHERE game_id = ?", (game_id,))
        await db.commit()
