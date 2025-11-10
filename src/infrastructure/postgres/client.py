from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from logging import Logger, getLogger
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.configurations import Settings


class PostgresClient:
    def __init__(
        self, settings: Settings, echo: bool = False, pool_size: int = 5, max_overflow: int = 10
    ) -> None:
        self.logger: Logger = getLogger(__name__)
        self._settings = settings
        self._echo = echo
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self.engine: AsyncEngine | None = None
        self.session: async_sessionmaker[AsyncSession] | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the database engine and session factory."""
        if self._initialized:
            return

        self.logger.info("Initializing PostgreSQL client...")

        self.engine = create_async_engine(
            url=self._settings.database_url,
            echo=self._echo,
            pool_size=self._pool_size,
            max_overflow=self._max_overflow,
            pool_pre_ping=True,
        )

        self.session = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

        # Test connection
        await self.health_check()
        self._initialized = True
        self.logger.info("PostgreSQL client initialized successfully")

    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            if not self.engine:
                return False

            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with automatic cleanup."""
        if not self.session:
            raise RuntimeError("Database client not initialized. Call initialize() first.")

        async with self.session() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


    async def connect(self):
        """Legacy method for compatibility."""
        if not self.engine:
            raise RuntimeError("Database client not initialized. Call initialize() first.")
        async with self.engine.connect() as conn:
            yield conn

    async def execute(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        """Execute SQL query with parameters."""
        try:
            if not self.engine:
                raise RuntimeError("Database client not initialized. Call initialize() first.")

            async with self.engine.begin() as conn:
                res = await conn.execute(text(sql), params or {})
                return res

        except SQLAlchemyError as e:
            self.logger.error(f"{sql} execute failed {e}")
            raise e

    async def dispose(self) -> None:
        """Clean up database connections."""
        if self.engine:
            await self.engine.dispose()
            self.logger.info("PostgreSQL client connections disposed")
            self._initialized = False
