"""Supabase client configuration and initialization."""

from supabase import create_client, Client
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Singleton Supabase client wrapper."""
    
    _instance = None
    _client: Client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Supabase client with configuration."""
        settings = get_settings()
        
        # Skip initialization if no URL provided (for testing)
        if not settings.database.supabase_url:
            logger.warning("Supabase URL not provided, skipping client initialization")
            return
        
        try:
            self._client = create_client(
                supabase_url=settings.database.supabase_url,
                supabase_key=settings.database.supabase_key
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    @property
    def client(self) -> Client:
        """Get the Supabase client instance."""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    def get_service_client(self) -> Client:
        """Get Supabase client with service key for admin operations."""
        settings = get_settings()
        
        # Skip initialization if no URL provided (for testing)
        if not settings.database.supabase_url:
            logger.warning("Supabase URL not provided, returning None")
            return None
        
        try:
            return create_client(
                supabase_url=settings.database.supabase_url,
                supabase_key=settings.database.supabase_service_key
            )
        except Exception as e:
            logger.error(f"Failed to create service client: {e}")
            raise


# Global client instance
supabase_client = SupabaseClient()


def get_supabase_client() -> Client:
    """Get the global Supabase client instance."""
    return supabase_client.client


def get_supabase_service_client() -> Client:
    """Get Supabase client with service key for admin operations."""
    return supabase_client.get_service_client()