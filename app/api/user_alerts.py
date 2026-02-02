"""
User Alert Configurations API
CRUD operations for user-defined alert triggers
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import structlog
import uuid

from app.services.supabase_client import get_supabase_client
from app.services.auth_service import get_current_user, UserSession

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/user/alerts", tags=["User Alert Configurations"])


# ============== Pydantic Models ==============

class DeliveryChannels(BaseModel):
    """Delivery channel configuration"""
    email: bool = True
    webhook: bool = False
    discord: bool = False
    slack: bool = False


class AlertConfigCreate(BaseModel):
    """Create alert configuration request"""
    name: str = Field(..., min_length=1, max_length=100, description="Alert name")
    trigger_source: str = Field(..., description="flare_intensity | kp_index | solar_wind")
    condition: str = Field(default="greater_than", description="greater_than | less_than | equals")
    threshold: float = Field(..., ge=0, description="Trigger threshold value")
    delivery_channels: DeliveryChannels = Field(default_factory=DeliveryChannels)
    webhook_url: Optional[str] = Field(None, description="Custom webhook URL")
    webhook_payload: Optional[dict] = Field(None, description="Custom webhook JSON payload")
    is_active: bool = True


class AlertConfigUpdate(BaseModel):
    """Update alert configuration request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    trigger_source: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = Field(None, ge=0)
    delivery_channels: Optional[DeliveryChannels] = None
    webhook_url: Optional[str] = None
    webhook_payload: Optional[dict] = None
    is_active: Optional[bool] = None


class AlertConfigResponse(BaseModel):
    """Alert configuration response"""
    id: str
    user_id: str
    name: str
    trigger_source: str
    condition: str
    threshold: float
    delivery_channels: DeliveryChannels
    webhook_url: Optional[str]
    webhook_payload: Optional[dict]
    is_active: bool
    triggered_count: int = 0
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AlertConfigListResponse(BaseModel):
    """List of alert configurations"""
    alerts: List[AlertConfigResponse]
    total: int


# ============== Repository ==============

class UserAlertConfigRepository:
    """Database operations for user alert configurations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.table = "user_alert_configs"
    
    async def create(self, user_id: str, config: AlertConfigCreate) -> dict:
        """Create a new alert configuration"""
        try:
            data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": config.name,
                "trigger_source": config.trigger_source,
                "condition": config.condition,
                "threshold": config.threshold,
                "delivery_channels": config.delivery_channels.model_dump(),
                "webhook_url": config.webhook_url,
                "webhook_payload": config.webhook_payload,
                "is_active": config.is_active,
                "triggered_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.client.table(self.table).insert(data).execute()
            
            if result.data:
                logger.info("alert_config_created", user_id=user_id, alert_id=data["id"])
                return result.data[0]
            
            raise HTTPException(status_code=500, detail="Failed to create alert configuration")
            
        except Exception as e:
            logger.error("alert_config_create_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_by_id(self, user_id: str, alert_id: str) -> Optional[dict]:
        """Get a specific alert configuration"""
        try:
            result = self.supabase.client.table(self.table)\
                .select("*")\
                .eq("id", alert_id)\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error("alert_config_get_failed", error=str(e))
            return None
    
    async def get_all(self, user_id: str) -> List[dict]:
        """Get all alert configurations for a user"""
        try:
            result = self.supabase.client.table(self.table)\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error("alert_configs_get_failed", error=str(e))
            return []
    
    async def update(self, user_id: str, alert_id: str, config: AlertConfigUpdate) -> Optional[dict]:
        """Update an alert configuration"""
        try:
            # Build update data (only non-None fields)
            update_data = {"updated_at": datetime.utcnow().isoformat()}
            
            if config.name is not None:
                update_data["name"] = config.name
            if config.trigger_source is not None:
                update_data["trigger_source"] = config.trigger_source
            if config.condition is not None:
                update_data["condition"] = config.condition
            if config.threshold is not None:
                update_data["threshold"] = config.threshold
            if config.delivery_channels is not None:
                update_data["delivery_channels"] = config.delivery_channels.model_dump()
            if config.webhook_url is not None:
                update_data["webhook_url"] = config.webhook_url
            if config.webhook_payload is not None:
                update_data["webhook_payload"] = config.webhook_payload
            if config.is_active is not None:
                update_data["is_active"] = config.is_active
            
            result = self.supabase.client.table(self.table)\
                .update(update_data)\
                .eq("id", alert_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if result.data:
                logger.info("alert_config_updated", user_id=user_id, alert_id=alert_id)
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("alert_config_update_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete(self, user_id: str, alert_id: str) -> bool:
        """Delete an alert configuration"""
        try:
            result = self.supabase.client.table(self.table)\
                .delete()\
                .eq("id", alert_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if result.data:
                logger.info("alert_config_deleted", user_id=user_id, alert_id=alert_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("alert_config_delete_failed", error=str(e))
            return False
    
    async def toggle_active(self, user_id: str, alert_id: str) -> Optional[dict]:
        """Toggle alert active status"""
        try:
            # Get current state
            current = await self.get_by_id(user_id, alert_id)
            if not current:
                return None
            
            new_state = not current.get("is_active", True)
            
            result = self.supabase.client.table(self.table)\
                .update({
                    "is_active": new_state,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", alert_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if result.data:
                logger.info("alert_config_toggled", alert_id=alert_id, is_active=new_state)
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("alert_config_toggle_failed", error=str(e))
            return None


# Singleton
_alert_repo: Optional[UserAlertConfigRepository] = None

def get_alert_repo() -> UserAlertConfigRepository:
    global _alert_repo
    if _alert_repo is None:
        _alert_repo = UserAlertConfigRepository()
    return _alert_repo


# ============== API Endpoints ==============

@router.get("", response_model=AlertConfigListResponse)
async def list_user_alerts(
    user: UserSession = Depends(get_current_user),
    repo: UserAlertConfigRepository = Depends(get_alert_repo)
):
    """
    Get all alert configurations for the current user.
    
    Returns a list of configured alert triggers with their delivery settings.
    """
    alerts = await repo.get_all(user.user_id)
    
    return AlertConfigListResponse(
        alerts=[AlertConfigResponse(**a) for a in alerts],
        total=len(alerts)
    )


@router.post("", response_model=AlertConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_user_alert(
    config: AlertConfigCreate,
    user: UserSession = Depends(get_current_user),
    repo: UserAlertConfigRepository = Depends(get_alert_repo)
):
    """
    Create a new alert configuration.
    
    **Trigger Sources**:
    - `flare_intensity`: Trigger when flare class exceeds threshold (1-10 scale)
    - `kp_index`: Trigger when Kp index exceeds threshold (0-9)
    - `solar_wind`: Trigger when solar wind speed exceeds threshold (km/s)
    
    **Delivery Channels**:
    - Email: Sends to user's registered email
    - Webhook: HTTP POST to custom URL
    - Discord: (Coming soon)
    - Slack: (Coming soon)
    """
    # Validate trigger source
    valid_sources = ["flare_intensity", "kp_index", "solar_wind"]
    if config.trigger_source not in valid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trigger_source. Must be one of: {valid_sources}"
        )
    
    # Validate condition
    valid_conditions = ["greater_than", "less_than", "equals"]
    if config.condition not in valid_conditions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid condition. Must be one of: {valid_conditions}"
        )
    
    alert = await repo.create(user.user_id, config)
    return AlertConfigResponse(**alert)


@router.get("/{alert_id}", response_model=AlertConfigResponse)
async def get_user_alert(
    alert_id: str,
    user: UserSession = Depends(get_current_user),
    repo: UserAlertConfigRepository = Depends(get_alert_repo)
):
    """Get a specific alert configuration by ID."""
    alert = await repo.get_by_id(user.user_id, alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert configuration not found")
    
    return AlertConfigResponse(**alert)


@router.patch("/{alert_id}", response_model=AlertConfigResponse)
async def update_user_alert(
    alert_id: str,
    config: AlertConfigUpdate,
    user: UserSession = Depends(get_current_user),
    repo: UserAlertConfigRepository = Depends(get_alert_repo)
):
    """Update an existing alert configuration."""
    # Validate if provided
    if config.trigger_source:
        valid_sources = ["flare_intensity", "kp_index", "solar_wind"]
        if config.trigger_source not in valid_sources:
            raise HTTPException(status_code=400, detail=f"Invalid trigger_source")
    
    if config.condition:
        valid_conditions = ["greater_than", "less_than", "equals"]
        if config.condition not in valid_conditions:
            raise HTTPException(status_code=400, detail=f"Invalid condition")
    
    alert = await repo.update(user.user_id, alert_id, config)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert configuration not found")
    
    return AlertConfigResponse(**alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_alert(
    alert_id: str,
    user: UserSession = Depends(get_current_user),
    repo: UserAlertConfigRepository = Depends(get_alert_repo)
):
    """Delete an alert configuration."""
    deleted = await repo.delete(user.user_id, alert_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert configuration not found")
    
    return None


@router.post("/{alert_id}/toggle", response_model=AlertConfigResponse)
async def toggle_user_alert(
    alert_id: str,
    user: UserSession = Depends(get_current_user),
    repo: UserAlertConfigRepository = Depends(get_alert_repo)
):
    """Toggle an alert configuration on/off."""
    alert = await repo.toggle_active(user.user_id, alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert configuration not found")
    
    return AlertConfigResponse(**alert)
