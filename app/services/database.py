"""Database connection utilities and management."""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool, Connection
from app.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self._pool: Optional[Pool] = None
        self._connection_params = self._get_connection_params()
    
    def _get_connection_params(self) -> Dict[str, Any]:
        """Get database connection parameters from settings."""
        database_url = self.settings.database.database_url
        
        if not database_url:
            logger.warning("Database URL not provided")
            return {}
        
        # Parse database URL or use individual components
        if database_url.startswith('postgresql://'):
            return {"dsn": database_url}
        else:
            # Fallback to individual parameters if needed
            return {
                "host": "localhost",
                "port": 5432,
                "database": "solar_weather",
                "user": "postgres",
                "password": "password"
            }
    
    async def initialize_pool(self, min_size: int = 5, max_size: int = 20) -> None:
        """
        Initialize the database connection pool.
        
        Args:
            min_size: Minimum number of connections in the pool
            max_size: Maximum number of connections in the pool
        """
        if not self._connection_params:
            logger.warning("No database connection parameters available")
            return
        
        try:
            self._pool = await asyncpg.create_pool(
                min_size=min_size,
                max_size=max_size,
                command_timeout=60,
                **self._connection_params
            )
            logger.info(f"Database pool initialized with {min_size}-{max_size} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close_pool(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Get a database connection from the pool.
        
        Yields:
            Connection: Database connection
            
        Raises:
            RuntimeError: If pool is not initialized
            Exception: If connection cannot be acquired
        """
        if not self._pool:
            raise RuntimeError("Database pool not initialized")
        
        connection = None
        try:
            connection = await self._pool.acquire()
            yield connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                await self._pool.release(connection)
    
    async def execute_query(
        self, 
        query: str, 
        *args, 
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Any:
        """
        Execute a database query.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            fetch_one: Whether to fetch one result
            fetch_all: Whether to fetch all results
            
        Returns:
            Query result or None
        """
        async with self.get_connection() as conn:
            try:
                if fetch_one:
                    result = await conn.fetchrow(query, *args)
                    return dict(result) if result else None
                elif fetch_all:
                    results = await conn.fetch(query, *args)
                    return [dict(row) for row in results]
                else:
                    return await conn.execute(query, *args)
                    
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Args: {args}")
                raise
    
    async def execute_transaction(self, queries: List[tuple]) -> bool:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, args) tuples
            
        Returns:
            True if transaction succeeded, False otherwise
        """
        async with self.get_connection() as conn:
            async with conn.transaction():
                try:
                    for query, args in queries:
                        await conn.execute(query, *args)
                    return True
                    
                except Exception as e:
                    logger.error(f"Transaction failed: {e}")
                    return False
    
    async def run_migration(self, migration_file: str) -> bool:
        """
        Run a database migration from file.
        
        Args:
            migration_file: Path to migration SQL file
            
        Returns:
            True if migration succeeded, False otherwise
        """
        try:
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            async with self.get_connection() as conn:
                await conn.execute(migration_sql)
            
            logger.info(f"Migration {migration_file} executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration {migration_file} failed: {e}")
            return False
    
    async def check_connection(self) -> bool:
        """
        Check if database connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            return True
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get information about a database table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column information dictionaries
        """
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = $1
        ORDER BY ordinal_position
        """
        
        return await self.execute_query(query, table_name, fetch_all=True)
    
    async def get_table_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Number of rows in the table
        """
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = await self.execute_query(query, fetch_one=True)
        return result['count'] if result else 0


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.migrations_table = "schema_migrations"
    
    async def initialize_migrations_table(self) -> None:
        """Create the migrations tracking table if it doesn't exist."""
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.migrations_table} (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL UNIQUE,
            executed_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        
        await self.db_manager.execute_query(query)
        logger.info("Migrations table initialized")
    
    async def is_migration_applied(self, migration_name: str) -> bool:
        """
        Check if a migration has been applied.
        
        Args:
            migration_name: Name of the migration
            
        Returns:
            True if migration has been applied, False otherwise
        """
        query = f"SELECT 1 FROM {self.migrations_table} WHERE migration_name = $1"
        result = await self.db_manager.execute_query(query, migration_name, fetch_one=True)
        return result is not None
    
    async def record_migration(self, migration_name: str) -> None:
        """
        Record that a migration has been applied.
        
        Args:
            migration_name: Name of the migration
        """
        query = f"INSERT INTO {self.migrations_table} (migration_name) VALUES ($1)"
        await self.db_manager.execute_query(query, migration_name)
        logger.info(f"Migration {migration_name} recorded")
    
    async def run_migrations(self, migrations_dir: str = "database/migrations") -> bool:
        """
        Run all pending migrations.
        
        Args:
            migrations_dir: Directory containing migration files
            
        Returns:
            True if all migrations succeeded, False otherwise
        """
        import os
        import glob
        
        await self.initialize_migrations_table()
        
        # Get all migration files
        migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
        
        if not migration_files:
            logger.info("No migration files found")
            return True
        
        success_count = 0
        
        for migration_file in migration_files:
            migration_name = os.path.basename(migration_file)
            
            # Skip if already applied
            if await self.is_migration_applied(migration_name):
                logger.info(f"Migration {migration_name} already applied, skipping")
                continue
            
            # Run the migration
            if await self.db_manager.run_migration(migration_file):
                await self.record_migration(migration_name)
                success_count += 1
                logger.info(f"Migration {migration_name} completed successfully")
            else:
                logger.error(f"Migration {migration_name} failed")
                return False
        
        logger.info(f"Completed {success_count} migrations")
        return True
    
    async def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """
        Get list of applied migrations.
        
        Returns:
            List of migration records
        """
        query = f"SELECT * FROM {self.migrations_table} ORDER BY executed_at"
        return await self.db_manager.execute_query(query, fetch_all=True)


# Global database manager instance
db_manager = DatabaseManager()
migration_manager = MigrationManager(db_manager)


async def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager


async def get_migration_manager() -> MigrationManager:
    """Get the global migration manager instance."""
    return migration_manager


async def initialize_database() -> bool:
    """
    Initialize the database connection and run migrations.
    
    Returns:
        True if initialization succeeded, False otherwise
    """
    try:
        # Initialize connection pool
        await db_manager.initialize_pool()
        
        # Run migrations
        success = await migration_manager.run_migrations()
        
        if success:
            logger.info("Database initialization completed successfully")
        else:
            logger.error("Database initialization failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False


async def cleanup_database() -> None:
    """Clean up database connections."""
    await db_manager.close_pool()
    logger.info("Database cleanup completed")