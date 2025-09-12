"""Base repository class with common CRUD operations."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
import logging
from app.services.database import DatabaseManager, get_database_manager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T], ABC):
    """Base repository class with common database operations."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.db_manager: Optional[DatabaseManager] = None
    
    async def _get_db_manager(self) -> DatabaseManager:
        """Get database manager instance."""
        if not self.db_manager:
            self.db_manager = await get_database_manager()
        return self.db_manager
    
    @abstractmethod
    def _row_to_model(self, row: Dict[str, Any]) -> T:
        """Convert database row to model instance."""
        pass
    
    @abstractmethod
    def _model_to_dict(self, model: T) -> Dict[str, Any]:
        """Convert model instance to dictionary for database operations."""
        pass
    
    async def create(self, model: T) -> Optional[T]:
        """
        Create a new record in the database.
        
        Args:
            model: Model instance to create
            
        Returns:
            Created model instance with ID, or None if failed
        """
        try:
            db_manager = await self._get_db_manager()
            data = self._model_to_dict(model)
            
            # Remove None values and id if present
            data = {k: v for k, v in data.items() if v is not None and k != 'id'}
            
            if not data:
                logger.error("No data to insert")
                return None
            
            # Build INSERT query
            columns = list(data.keys())
            placeholders = [f"${i+1}" for i in range(len(columns))]
            values = list(data.values())
            
            query = f"""
                INSERT INTO {self.table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING *
            """
            
            result = await db_manager.execute_query(query, *values, fetch_one=True)
            
            if result:
                return self._row_to_model(result)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create record in {self.table_name}: {e}")
            return None
    
    async def get_by_id(self, record_id: str) -> Optional[T]:
        """
        Get a record by ID.
        
        Args:
            record_id: Record ID to fetch
            
        Returns:
            Model instance if found, None otherwise
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = f"SELECT * FROM {self.table_name} WHERE id = $1"
            result = await db_manager.execute_query(query, record_id, fetch_one=True)
            
            if result:
                return self._row_to_model(result)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get record by ID from {self.table_name}: {e}")
            return None
    
    async def get_all(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[T]:
        """
        Get all records with optional pagination and ordering.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Column to order by
            order_desc: Whether to order in descending order
            
        Returns:
            List of model instances
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = f"SELECT * FROM {self.table_name}"
            params = []
            
            if order_by:
                direction = "DESC" if order_desc else "ASC"
                query += f" ORDER BY {order_by} {direction}"
            
            if limit is not None:
                params.append(limit)
                query += f" LIMIT ${len(params)}"
            
            if offset is not None:
                params.append(offset)
                query += f" OFFSET ${len(params)}"
            
            results = await db_manager.execute_query(query, *params, fetch_all=True)
            
            return [self._row_to_model(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get all records from {self.table_name}: {e}")
            return []
    
    async def update(self, record_id: str, updates: Dict[str, Any]) -> Optional[T]:
        """
        Update a record by ID.
        
        Args:
            record_id: ID of record to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated model instance if successful, None otherwise
        """
        try:
            db_manager = await self._get_db_manager()
            
            # Remove None values and id
            updates = {k: v for k, v in updates.items() if v is not None and k != 'id'}
            
            if not updates:
                logger.warning("No updates provided")
                return await self.get_by_id(record_id)
            
            # Add updated_at timestamp if column exists
            updates['updated_at'] = datetime.utcnow()
            
            # Build UPDATE query
            set_clauses = [f"{col} = ${i+1}" for i, col in enumerate(updates.keys())]
            values = list(updates.values())
            values.append(record_id)  # Add ID for WHERE clause
            
            query = f"""
                UPDATE {self.table_name}
                SET {', '.join(set_clauses)}
                WHERE id = ${len(values)}
                RETURNING *
            """
            
            result = await db_manager.execute_query(query, *values, fetch_one=True)
            
            if result:
                return self._row_to_model(result)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to update record in {self.table_name}: {e}")
            return None
    
    async def delete(self, record_id: str) -> bool:
        """
        Delete a record by ID.
        
        Args:
            record_id: ID of record to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = f"DELETE FROM {self.table_name} WHERE id = $1"
            result = await db_manager.execute_query(query, record_id)
            
            # Check if any rows were affected
            return "DELETE 1" in str(result)
            
        except Exception as e:
            logger.error(f"Failed to delete record from {self.table_name}: {e}")
            return False
    
    async def exists(self, record_id: str) -> bool:
        """
        Check if a record exists by ID.
        
        Args:
            record_id: ID to check
            
        Returns:
            True if record exists, False otherwise
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = f"SELECT 1 FROM {self.table_name} WHERE id = $1"
            result = await db_manager.execute_query(query, record_id, fetch_one=True)
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to check existence in {self.table_name}: {e}")
            return False
    
    async def count(self, where_clause: Optional[str] = None, params: Optional[List] = None) -> int:
        """
        Count records with optional WHERE clause.
        
        Args:
            where_clause: Optional WHERE clause (without WHERE keyword)
            params: Parameters for the WHERE clause
            
        Returns:
            Number of matching records
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = f"SELECT COUNT(*) as count FROM {self.table_name}"
            query_params = []
            
            if where_clause:
                query += f" WHERE {where_clause}"
                if params:
                    query_params.extend(params)
            
            result = await db_manager.execute_query(query, *query_params, fetch_one=True)
            
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Failed to count records in {self.table_name}: {e}")
            return 0
    
    async def find_by_field(self, field_name: str, field_value: Any) -> List[T]:
        """
        Find records by a specific field value.
        
        Args:
            field_name: Name of the field to search
            field_value: Value to search for
            
        Returns:
            List of matching model instances
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = f"SELECT * FROM {self.table_name} WHERE {field_name} = $1"
            results = await db_manager.execute_query(query, field_value, fetch_all=True)
            
            return [self._row_to_model(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to find records by {field_name} in {self.table_name}: {e}")
            return []
    
    async def find_one_by_field(self, field_name: str, field_value: Any) -> Optional[T]:
        """
        Find a single record by a specific field value.
        
        Args:
            field_name: Name of the field to search
            field_value: Value to search for
            
        Returns:
            Model instance if found, None otherwise
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = f"SELECT * FROM {self.table_name} WHERE {field_name} = $1 LIMIT 1"
            result = await db_manager.execute_query(query, field_value, fetch_one=True)
            
            if result:
                return self._row_to_model(result)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find record by {field_name} in {self.table_name}: {e}")
            return None