"""Repository for user subscriptions data access."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from app.repositories.base import BaseRepository
from app.models.core import UserSubscription, SubscriptionTier

logger = logging.getLogger(__name__)


class SubscriptionsRepository(BaseRepository[UserSubscription]):
    """Repository for managing user subscriptions."""
    
    def __init__(self):
        super().__init__("user_subscriptions")
    
    def _row_to_model(self, row: Dict[str, Any]) -> UserSubscription:
        """Convert database row to UserSubscription model."""
        return UserSubscription(
            id=row.get('id'),
            user_id=row['user_id'],
            tier=SubscriptionTier(row.get('tier', 'free')),
            razorpay_subscription_id=row.get('razorpay_subscription_id'),
            razorpay_customer_id=row.get('razorpay_customer_id'),
            api_key_hash=row.get('api_key_hash'),
            webhook_url=row.get('webhook_url'),
            alert_thresholds=row.get('alert_thresholds', {}),
            is_active=row.get('is_active', True),
            subscription_start_date=row.get('subscription_start_date'),
            subscription_end_date=row.get('subscription_end_date'),
            last_login=row.get('last_login'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )
    
    def _model_to_dict(self, model: UserSubscription) -> Dict[str, Any]:
        """Convert UserSubscription model to dictionary."""
        return {
            'id': model.id,
            'user_id': model.user_id,
            'tier': model.tier.value,
            'razorpay_subscription_id': model.razorpay_subscription_id,
            'razorpay_customer_id': model.razorpay_customer_id,
            'api_key_hash': model.api_key_hash,
            'webhook_url': model.webhook_url,
            'alert_thresholds': model.alert_thresholds,
            'is_active': model.is_active,
            'subscription_start_date': model.subscription_start_date,
            'subscription_end_date': model.subscription_end_date,
            'last_login': model.last_login,
            'created_at': model.created_at,
            'updated_at': model.updated_at
        }
    
    async def get_by_user_id(self, user_id: str) -> Optional[UserSubscription]:
        """
        Get subscription by user ID.
        
        Args:
            user_id: User ID to look up
            
        Returns:
            UserSubscription if found, None otherwise
        """
        return await self.find_one_by_field('user_id', user_id)
    
    async def get_by_api_key_hash(self, api_key_hash: str) -> Optional[UserSubscription]:
        """
        Get subscription by API key hash.
        
        Args:
            api_key_hash: Hashed API key to look up
            
        Returns:
            UserSubscription if found, None otherwise
        """
        return await self.find_one_by_field('api_key_hash', api_key_hash)
    
    async def get_by_razorpay_subscription_id(self, subscription_id: str) -> Optional[UserSubscription]:
        """
        Get subscription by Razorpay subscription ID.
        
        Args:
            subscription_id: Razorpay subscription ID
            
        Returns:
            UserSubscription if found, None otherwise
        """
        return await self.find_one_by_field('razorpay_subscription_id', subscription_id)
    
    async def get_active_subscriptions(self, tier: Optional[SubscriptionTier] = None) -> List[UserSubscription]:
        """
        Get all active subscriptions, optionally filtered by tier.
        
        Args:
            tier: Optional tier to filter by
            
        Returns:
            List of active UserSubscription instances
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = "SELECT * FROM user_subscriptions WHERE is_active = true"
            params = []
            
            if tier:
                query += " AND tier = $1"
                params.append(tier.value)
            
            query += " ORDER BY created_at DESC"
            
            results = await db_manager.execute_query(query, *params, fetch_all=True)
            
            return [self._row_to_model(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get active subscriptions: {e}")
            return []
    
    async def get_subscriptions_by_tier(self, tier: SubscriptionTier) -> List[UserSubscription]:
        """
        Get all subscriptions for a specific tier.
        
        Args:
            tier: Subscription tier to filter by
            
        Returns:
            List of UserSubscription instances for the tier
        """
        return await self.find_by_field('tier', tier.value)
    
    async def get_expired_subscriptions(self) -> List[UserSubscription]:
        """
        Get subscriptions that have expired.
        
        Returns:
            List of expired UserSubscription instances
        """
        try:
            db_manager = await self._get_db_manager()
            
            current_time = datetime.utcnow()
            
            query = """
                SELECT * FROM user_subscriptions 
                WHERE subscription_end_date IS NOT NULL 
                AND subscription_end_date < $1
                AND is_active = true
                ORDER BY subscription_end_date DESC
            """
            
            results = await db_manager.execute_query(query, current_time, fetch_all=True)
            
            return [self._row_to_model(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get expired subscriptions: {e}")
            return []
    
    async def get_subscriptions_expiring_soon(self, days_ahead: int = 7) -> List[UserSubscription]:
        """
        Get subscriptions expiring within the specified number of days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of UserSubscription instances expiring soon
        """
        try:
            db_manager = await self._get_db_manager()
            
            current_time = datetime.utcnow()
            expiry_cutoff = current_time + timedelta(days=days_ahead)
            
            query = """
                SELECT * FROM user_subscriptions 
                WHERE subscription_end_date IS NOT NULL 
                AND subscription_end_date BETWEEN $1 AND $2
                AND is_active = true
                ORDER BY subscription_end_date ASC
            """
            
            results = await db_manager.execute_query(query, current_time, expiry_cutoff, fetch_all=True)
            
            return [self._row_to_model(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get subscriptions expiring soon: {e}")
            return []
    
    async def update_subscription_tier(
        self, 
        user_id: str, 
        new_tier: SubscriptionTier,
        razorpay_subscription_id: Optional[str] = None
    ) -> Optional[UserSubscription]:
        """
        Update user's subscription tier.
        
        Args:
            user_id: User ID to update
            new_tier: New subscription tier
            razorpay_subscription_id: Optional Razorpay subscription ID
            
        Returns:
            Updated UserSubscription if successful, None otherwise
        """
        try:
            subscription = await self.get_by_user_id(user_id)
            if not subscription:
                logger.error(f"Subscription not found for user {user_id}")
                return None
            
            updates = {
                'tier': new_tier.value,
                'subscription_start_date': datetime.utcnow()
            }
            
            if razorpay_subscription_id:
                updates['razorpay_subscription_id'] = razorpay_subscription_id
            
            # Set end date for paid tiers (30 days from now)
            if new_tier != SubscriptionTier.FREE:
                updates['subscription_end_date'] = datetime.utcnow() + timedelta(days=30)
            else:
                updates['subscription_end_date'] = None
            
            return await self.update(subscription.id, updates)
            
        except Exception as e:
            logger.error(f"Failed to update subscription tier: {e}")
            return None
    
    async def deactivate_subscription(self, user_id: str) -> bool:
        """
        Deactivate a user's subscription.
        
        Args:
            user_id: User ID to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = await self.get_by_user_id(user_id)
            if not subscription:
                return False
            
            updates = {
                'is_active': False,
                'tier': SubscriptionTier.FREE.value,
                'subscription_end_date': datetime.utcnow()
            }
            
            updated_subscription = await self.update(subscription.id, updates)
            return updated_subscription is not None
            
        except Exception as e:
            logger.error(f"Failed to deactivate subscription: {e}")
            return False
    
    async def update_api_key_hash(self, user_id: str, api_key_hash: str) -> bool:
        """
        Update user's API key hash.
        
        Args:
            user_id: User ID to update
            api_key_hash: New API key hash
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = await self.get_by_user_id(user_id)
            if not subscription:
                return False
            
            updated_subscription = await self.update(subscription.id, {'api_key_hash': api_key_hash})
            return updated_subscription is not None
            
        except Exception as e:
            logger.error(f"Failed to update API key hash: {e}")
            return False
    
    async def update_webhook_url(self, user_id: str, webhook_url: Optional[str]) -> bool:
        """
        Update user's webhook URL.
        
        Args:
            user_id: User ID to update
            webhook_url: New webhook URL (None to remove)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = await self.get_by_user_id(user_id)
            if not subscription:
                return False
            
            updated_subscription = await self.update(subscription.id, {'webhook_url': webhook_url})
            return updated_subscription is not None
            
        except Exception as e:
            logger.error(f"Failed to update webhook URL: {e}")
            return False
    
    async def update_alert_thresholds(self, user_id: str, thresholds: Dict[str, float]) -> bool:
        """
        Update user's alert thresholds.
        
        Args:
            user_id: User ID to update
            thresholds: New alert thresholds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = await self.get_by_user_id(user_id)
            if not subscription:
                return False
            
            updated_subscription = await self.update(subscription.id, {'alert_thresholds': thresholds})
            return updated_subscription is not None
            
        except Exception as e:
            logger.error(f"Failed to update alert thresholds: {e}")
            return False
    
    async def update_last_login(self, user_id: str) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User ID to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = await self.get_by_user_id(user_id)
            if not subscription:
                return False
            
            updated_subscription = await self.update(subscription.id, {'last_login': datetime.utcnow()})
            return updated_subscription is not None
            
        except Exception as e:
            logger.error(f"Failed to update last login: {e}")
            return False
    
    async def get_users_with_webhooks(self) -> List[Dict[str, Any]]:
        """
        Get all users who have webhook URLs configured.
        
        Returns:
            List of user subscription data with webhook URLs
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = """
                SELECT user_id, tier, webhook_url, alert_thresholds
                FROM user_subscriptions 
                WHERE webhook_url IS NOT NULL 
                AND webhook_url != ''
                AND is_active = true
                ORDER BY tier DESC, created_at ASC
            """
            
            results = await db_manager.execute_query(query, fetch_all=True)
            
            return [dict(row) for row in results] if results else []
            
        except Exception as e:
            logger.error(f"Failed to get users with webhooks: {e}")
            return []
    
    async def get_subscription_statistics(self) -> Dict[str, Any]:
        """
        Get subscription statistics.
        
        Returns:
            Dictionary with subscription statistics
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = """
                SELECT 
                    COUNT(*) as total_subscriptions,
                    COUNT(CASE WHEN is_active = true THEN 1 END) as active_subscriptions,
                    COUNT(CASE WHEN tier = 'free' THEN 1 END) as free_tier_count,
                    COUNT(CASE WHEN tier = 'pro' THEN 1 END) as pro_tier_count,
                    COUNT(CASE WHEN tier = 'enterprise' THEN 1 END) as enterprise_tier_count,
                    COUNT(CASE WHEN api_key_hash IS NOT NULL THEN 1 END) as users_with_api_keys,
                    COUNT(CASE WHEN webhook_url IS NOT NULL THEN 1 END) as users_with_webhooks
                FROM user_subscriptions
            """
            
            result = await db_manager.execute_query(query, fetch_one=True)
            
            if result:
                return {
                    'total_subscriptions': result['total_subscriptions'],
                    'active_subscriptions': result['active_subscriptions'],
                    'free_tier_count': result['free_tier_count'],
                    'pro_tier_count': result['pro_tier_count'],
                    'enterprise_tier_count': result['enterprise_tier_count'],
                    'users_with_api_keys': result['users_with_api_keys'],
                    'users_with_webhooks': result['users_with_webhooks']
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get subscription statistics: {e}")
            return {}


# Global repository instance
subscriptions_repository = SubscriptionsRepository()


def get_subscriptions_repository() -> SubscriptionsRepository:
    """Get the global subscriptions repository instance."""
    return subscriptions_repository