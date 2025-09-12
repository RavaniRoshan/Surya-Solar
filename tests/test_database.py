"""Integration tests for database operations."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncpg
from app.services.database import DatabaseManager, MigrationManager


class TestDatabaseManager:
    """Test cases for DatabaseManager."""
    
    @pytest.fixture
    def db_manager(self):
        """Create DatabaseManager instance for testing."""
        with patch('app.services.database.get_settings') as mock_settings:
            mock_settings.return_value.database.database_url = "postgresql://test:test@localhost:5432/test"
            return DatabaseManager()
    
    @pytest.mark.asyncio
    async def test_get_connection_params(self, db_manager):
        """Test database connection parameter parsing."""
        params = db_manager._get_connection_params()
        
        assert "dsn" in params
        assert params["dsn"] == "postgresql://test:test@localhost:5432/test"
    
    @pytest.mark.asyncio
    async def test_get_connection_params_empty_url(self):
        """Test connection params with empty database URL."""
        with patch('app.services.database.get_settings') as mock_settings:
            mock_settings.return_value.database.database_url = ""
            db_manager = DatabaseManager()
            
            params = db_manager._get_connection_params()
            assert params == {}
    
    @pytest.mark.asyncio
    async def test_initialize_pool_success(self, db_manager):
        """Test successful pool initialization."""
        mock_pool = Mock()
        
        with patch('asyncpg.create_pool', return_value=mock_pool) as mock_create_pool:
            await db_manager.initialize_pool(min_size=2, max_size=10)
            
            mock_create_pool.assert_called_once()
            assert db_manager._pool == mock_pool
    
    @pytest.mark.asyncio
    async def test_initialize_pool_no_params(self):
        """Test pool initialization with no connection parameters."""
        with patch('app.services.database.get_settings') as mock_settings:
            mock_settings.return_value.database.database_url = ""
            db_manager = DatabaseManager()
            
            # Should not raise exception
            await db_manager.initialize_pool()
            assert db_manager._pool is None
    
    @pytest.mark.asyncio
    async def test_close_pool(self, db_manager):
        """Test pool closure."""
        mock_pool = AsyncMock()
        db_manager._pool = mock_pool
        
        await db_manager.close_pool()
        
        mock_pool.close.assert_called_once()
        assert db_manager._pool is None
    
    @pytest.mark.asyncio
    async def test_get_connection_no_pool(self, db_manager):
        """Test getting connection without initialized pool."""
        with pytest.raises(RuntimeError, match="Database pool not initialized"):
            async with db_manager.get_connection():
                pass
    
    @pytest.mark.asyncio
    async def test_get_connection_success(self, db_manager):
        """Test successful connection acquisition."""
        mock_pool = AsyncMock()
        mock_connection = Mock()
        mock_pool.acquire.return_value = mock_connection
        db_manager._pool = mock_pool
        
        async with db_manager.get_connection() as conn:
            assert conn == mock_connection
        
        mock_pool.acquire.assert_called_once()
        mock_pool.release.assert_called_once_with(mock_connection)
    
    @pytest.mark.asyncio
    async def test_execute_query_fetch_one(self, db_manager):
        """Test query execution with fetch_one."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_row = {"id": 1, "name": "test"}
        
        mock_pool.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = mock_row
        db_manager._pool = mock_pool
        
        result = await db_manager.execute_query(
            "SELECT * FROM test WHERE id = $1", 
            1, 
            fetch_one=True
        )
        
        assert result == mock_row
        mock_connection.fetchrow.assert_called_once_with("SELECT * FROM test WHERE id = $1", 1)
    
    @pytest.mark.asyncio
    async def test_execute_query_fetch_all(self, db_manager):
        """Test query execution with fetch_all."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_rows = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
        
        mock_pool.acquire.return_value = mock_connection
        mock_connection.fetch.return_value = mock_rows
        db_manager._pool = mock_pool
        
        result = await db_manager.execute_query(
            "SELECT * FROM test", 
            fetch_all=True
        )
        
        assert result == mock_rows
        mock_connection.fetch.assert_called_once_with("SELECT * FROM test")
    
    @pytest.mark.asyncio
    async def test_execute_query_execute_only(self, db_manager):
        """Test query execution without fetching."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.execute.return_value = "INSERT 0 1"
        
        mock_pool.acquire.return_value = mock_connection
        db_manager._pool = mock_pool
        
        result = await db_manager.execute_query("INSERT INTO test (name) VALUES ($1)", "test")
        
        assert result == "INSERT 0 1"
        mock_connection.execute.assert_called_once_with("INSERT INTO test (name) VALUES ($1)", "test")
    
    @pytest.mark.asyncio
    async def test_execute_transaction_success(self, db_manager):
        """Test successful transaction execution."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_transaction = AsyncMock()
        
        mock_pool.acquire.return_value = mock_connection
        mock_connection.transaction.return_value = mock_transaction
        db_manager._pool = mock_pool
        
        queries = [
            ("INSERT INTO test (name) VALUES ($1)", ("test1",)),
            ("INSERT INTO test (name) VALUES ($1)", ("test2",))
        ]
        
        result = await db_manager.execute_transaction(queries)
        
        assert result is True
        assert mock_connection.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_transaction_failure(self, db_manager):
        """Test transaction execution with failure."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_transaction = AsyncMock()
        
        mock_pool.acquire.return_value = mock_connection
        mock_connection.transaction.return_value = mock_transaction
        mock_connection.execute.side_effect = Exception("Database error")
        db_manager._pool = mock_pool
        
        queries = [("INSERT INTO test (name) VALUES ($1)", ("test1",))]
        
        result = await db_manager.execute_transaction(queries)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_run_migration_success(self, db_manager):
        """Test successful migration execution."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        
        mock_pool.acquire.return_value = mock_connection
        db_manager._pool = mock_pool
        
        migration_content = "CREATE TABLE test (id SERIAL PRIMARY KEY);"
        
        with patch('builtins.open', mock_open(read_data=migration_content)):
            result = await db_manager.run_migration("test_migration.sql")
        
        assert result is True
        mock_connection.execute.assert_called_once_with(migration_content)
    
    @pytest.mark.asyncio
    async def test_run_migration_file_error(self, db_manager):
        """Test migration execution with file error."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = await db_manager.run_migration("nonexistent.sql")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_connection_healthy(self, db_manager):
        """Test healthy connection check."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.fetchval.return_value = 1
        
        mock_pool.acquire.return_value = mock_connection
        db_manager._pool = mock_pool
        
        result = await db_manager.check_connection()
        
        assert result is True
        mock_connection.fetchval.assert_called_once_with("SELECT 1")
    
    @pytest.mark.asyncio
    async def test_check_connection_unhealthy(self, db_manager):
        """Test unhealthy connection check."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.fetchval.side_effect = Exception("Connection failed")
        
        mock_pool.acquire.return_value = mock_connection
        db_manager._pool = mock_pool
        
        result = await db_manager.check_connection()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_table_info(self, db_manager):
        """Test getting table information."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_columns = [
            {"column_name": "id", "data_type": "integer", "is_nullable": "NO", "column_default": "nextval('test_id_seq'::regclass)"},
            {"column_name": "name", "data_type": "text", "is_nullable": "YES", "column_default": None}
        ]
        
        mock_pool.acquire.return_value = mock_connection
        mock_connection.fetch.return_value = mock_columns
        db_manager._pool = mock_pool
        
        result = await db_manager.get_table_info("test")
        
        assert result == mock_columns
        mock_connection.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_table_count(self, db_manager):
        """Test getting table row count."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.fetchrow.return_value = {"count": 42}
        
        mock_pool.acquire.return_value = mock_connection
        db_manager._pool = mock_pool
        
        result = await db_manager.get_table_count("test")
        
        assert result == 42
        mock_connection.fetchrow.assert_called_once_with("SELECT COUNT(*) FROM test")


class TestMigrationManager:
    """Test cases for MigrationManager."""
    
    @pytest.fixture
    def migration_manager(self):
        """Create MigrationManager instance for testing."""
        mock_db_manager = Mock()
        return MigrationManager(mock_db_manager)
    
    @pytest.mark.asyncio
    async def test_initialize_migrations_table(self, migration_manager):
        """Test migrations table initialization."""
        migration_manager.db_manager.execute_query = AsyncMock()
        
        await migration_manager.initialize_migrations_table()
        
        migration_manager.db_manager.execute_query.assert_called_once()
        call_args = migration_manager.db_manager.execute_query.call_args[0]
        assert "CREATE TABLE IF NOT EXISTS schema_migrations" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_is_migration_applied_true(self, migration_manager):
        """Test checking if migration is applied (true case)."""
        migration_manager.db_manager.execute_query = AsyncMock(return_value={"migration_name": "001_test.sql"})
        
        result = await migration_manager.is_migration_applied("001_test.sql")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_is_migration_applied_false(self, migration_manager):
        """Test checking if migration is applied (false case)."""
        migration_manager.db_manager.execute_query = AsyncMock(return_value=None)
        
        result = await migration_manager.is_migration_applied("001_test.sql")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_record_migration(self, migration_manager):
        """Test recording a migration."""
        migration_manager.db_manager.execute_query = AsyncMock()
        
        await migration_manager.record_migration("001_test.sql")
        
        migration_manager.db_manager.execute_query.assert_called_once()
        call_args = migration_manager.db_manager.execute_query.call_args[0]
        assert "INSERT INTO schema_migrations" in call_args[0]
        assert call_args[1] == "001_test.sql"
    
    @pytest.mark.asyncio
    async def test_run_migrations_no_files(self, migration_manager):
        """Test running migrations with no files."""
        migration_manager.initialize_migrations_table = AsyncMock()
        
        with patch('glob.glob', return_value=[]):
            result = await migration_manager.run_migrations("test_dir")
        
        assert result is True
        migration_manager.initialize_migrations_table.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_migrations_success(self, migration_manager):
        """Test successful migration execution."""
        migration_manager.initialize_migrations_table = AsyncMock()
        migration_manager.is_migration_applied = AsyncMock(return_value=False)
        migration_manager.record_migration = AsyncMock()
        migration_manager.db_manager.run_migration = AsyncMock(return_value=True)
        
        with patch('glob.glob', return_value=["001_test.sql", "002_test.sql"]):
            result = await migration_manager.run_migrations("test_dir")
        
        assert result is True
        assert migration_manager.db_manager.run_migration.call_count == 2
        assert migration_manager.record_migration.call_count == 2
    
    @pytest.mark.asyncio
    async def test_run_migrations_skip_applied(self, migration_manager):
        """Test running migrations with some already applied."""
        migration_manager.initialize_migrations_table = AsyncMock()
        migration_manager.is_migration_applied = AsyncMock(side_effect=[True, False])
        migration_manager.record_migration = AsyncMock()
        migration_manager.db_manager.run_migration = AsyncMock(return_value=True)
        
        with patch('glob.glob', return_value=["001_test.sql", "002_test.sql"]):
            result = await migration_manager.run_migrations("test_dir")
        
        assert result is True
        assert migration_manager.db_manager.run_migration.call_count == 1
        assert migration_manager.record_migration.call_count == 1
    
    @pytest.mark.asyncio
    async def test_run_migrations_failure(self, migration_manager):
        """Test migration execution with failure."""
        migration_manager.initialize_migrations_table = AsyncMock()
        migration_manager.is_migration_applied = AsyncMock(return_value=False)
        migration_manager.db_manager.run_migration = AsyncMock(return_value=False)
        
        with patch('glob.glob', return_value=["001_test.sql"]):
            result = await migration_manager.run_migrations("test_dir")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_applied_migrations(self, migration_manager):
        """Test getting applied migrations."""
        mock_migrations = [
            {"id": 1, "migration_name": "001_test.sql", "executed_at": "2024-01-01T00:00:00Z"},
            {"id": 2, "migration_name": "002_test.sql", "executed_at": "2024-01-01T01:00:00Z"}
        ]
        migration_manager.db_manager.execute_query = AsyncMock(return_value=mock_migrations)
        
        result = await migration_manager.get_applied_migrations()
        
        assert result == mock_migrations
        migration_manager.db_manager.execute_query.assert_called_once()


def mock_open(read_data=""):
    """Mock open function for file operations."""
    from unittest.mock import mock_open as _mock_open
    return _mock_open(read_data=read_data)