"""Alert endpoints for solar flare predictions."""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.models.core import (
    CurrentAlertResponse, 
    HistoricalAlertsResponse, 
    AlertResponse,
    SeverityLevel,
    ErrorResponse
)
from app.services.auth_service import get_auth_service, UserSession
from app.repositories.predictions import get_predictions_repository
from app.repositories.api_usage import get_api_usage_repository
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])
security = HTTPBearer()
auth_service = get_auth_service()
predictions_repo = get_predictions_repository()
api_usage_repo = get_api_usage_repository()
settings = get_settings()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserSession:
    """
    Dependency to get current authenticated user.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer token credentials
        
    Returns:
        UserSession for authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Try JWT token first
        user_session = await auth_service.validate_token(credentials.credentials)
        
        if not user_session:
            # Try API key authentication
            user_session = await auth_service.validate_api_key(credentials.credentials)
        
        if not user_session:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Log API usage
        await _log_api_usage(
            request=request,
            user_session=user_session,
            endpoint=str(request.url.path),
            method=request.method
        )
        
        return user_session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def check_rate_limits(user_session: UserSession, endpoint_type: str) -> None:
    """
    Check if user has exceeded rate limits for their subscription tier.
    
    Args:
        user_session: Current user session
        endpoint_type: Type of endpoint being accessed (alerts, history)
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    try:
        tier_config = settings.subscription_tiers.get(user_session.subscription_tier, {})
        rate_limits = tier_config.get("rate_limits", {})
        
        if endpoint_type not in rate_limits:
            return  # No rate limit configured
        
        limit = rate_limits[endpoint_type]
        
        # Check usage in the last hour
        usage_count = await api_usage_repo.get_usage_count(
            user_id=user_session.user_id,
            endpoint_pattern=f"%{endpoint_type}%",
            hours_back=1
        )
        
        if usage_count >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. {user_session.subscription_tier.title()} tier allows {limit} {endpoint_type} requests per hour.",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((datetime.utcnow() + timedelta(hours=1)).timestamp()))
                }
            )
        
        # Add rate limit headers
        remaining = limit - usage_count
        logger.info(f"Rate limit check passed: {usage_count}/{limit} for {user_session.subscription_tier} tier")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # Don't block request if rate limit check fails
        pass


async def _log_api_usage(
    request: Request,
    user_session: UserSession,
    endpoint: str,
    method: str,
    status_code: int = 200,
    response_time_ms: Optional[int] = None
) -> None:
    """Log API usage for analytics and rate limiting."""
    try:
        await api_usage_repo.create({
            "user_id": user_session.user_id,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "api_key_used": user_session.api_key is not None,
            "timestamp": datetime.utcnow()
        })
    except Exception as e:
        logger.warning(f"Failed to log API usage: {e}")


@router.get(
    "/current",
    response_model=CurrentAlertResponse,
    summary="Get Current Solar Flare Alert",
    description="Retrieve the current solar flare probability and alert status."
)
async def get_current_alert(
    request: Request,
    user_session: UserSession = Depends(get_current_user)
) -> CurrentAlertResponse:
    """
    Get the current solar flare alert status.
    
    Returns the most recent prediction with current probability,
    severity level, and alert status.
    
    **Authentication Required**: Bearer token (JWT or API key)
    
    **Rate Limits**:
    - Free tier: 10 requests/hour
    - Pro tier: 1000 requests/hour  
    - Enterprise tier: 10000 requests/hour
    """
    try:
        # Check rate limits
        await check_rate_limits(user_session, "alerts")
        
        # Get current prediction
        current_prediction = await predictions_repo.get_current_prediction()
        
        if not current_prediction:
            raise HTTPException(
                status_code=404,
                detail="No current prediction available"
            )
        
        # Calculate next update time (predictions run every 10 minutes)
        next_update = current_prediction.timestamp + timedelta(
            minutes=settings.model.prediction_interval_minutes
        )
        
        # Check if alert should be triggered based on user's thresholds
        user_thresholds = getattr(user_session, 'alert_thresholds', settings.default_alert_thresholds)
        alert_active = current_prediction.flare_probability >= user_thresholds.get('high', 0.8)
        
        return CurrentAlertResponse(
            current_probability=current_prediction.flare_probability,
            severity_level=current_prediction.severity_level,
            last_updated=current_prediction.timestamp,
            next_update=next_update,
            alert_active=alert_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current alert: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve current alert"
        )


@router.get(
    "/history",
    response_model=HistoricalAlertsResponse,
    summary="Get Historical Solar Flare Alerts",
    description="Retrieve historical solar flare predictions with filtering and pagination."
)
async def get_alert_history(
    request: Request,
    user_session: UserSession = Depends(get_current_user),
    hours_back: int = Query(24, ge=1, le=168, description="Hours of history to retrieve (max 7 days)"),
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity level"),
    min_probability: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum probability threshold"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(50, ge=1, le=100, description="Number of results per page")
) -> HistoricalAlertsResponse:
    """
    Get historical solar flare alert data with filtering and pagination.
    
    **Parameters**:
    - `hours_back`: Number of hours to look back (1-168, default: 24)
    - `severity`: Filter by severity level (low/medium/high)
    - `min_probability`: Filter by minimum probability (0.0-1.0)
    - `page`: Page number for pagination (default: 1)
    - `page_size`: Results per page (1-100, default: 50)
    
    **Authentication Required**: Bearer token (JWT or API key)
    
    **Rate Limits**:
    - Free tier: 5 requests/hour
    - Pro tier: 500 requests/hour
    - Enterprise tier: 5000 requests/hour
    """
    try:
        # Check rate limits
        await check_rate_limits(user_session, "history")
        
        # Validate enterprise features
        if hours_back > 24 and user_session.subscription_tier == "free":
            raise HTTPException(
                status_code=403,
                detail="Historical data beyond 24 hours requires Pro or Enterprise subscription"
            )
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Get predictions with filters
        if severity:
            predictions = await predictions_repo.get_predictions_by_severity(
                severity=severity,
                hours_back=hours_back
            )
        elif min_probability is not None:
            predictions = await predictions_repo.get_predictions_above_threshold(
                probability_threshold=min_probability,
                hours_back=hours_back
            )
        else:
            predictions = await predictions_repo.get_predictions_by_time_range(
                start_time=start_time,
                end_time=end_time
            )
        
        # Apply pagination
        total_count = len(predictions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_predictions = predictions[start_idx:end_idx]
        
        # Convert to AlertResponse format
        alerts = []
        for prediction in paginated_predictions:
            # Check if alert was triggered based on default thresholds
            alert_triggered = prediction.flare_probability >= settings.default_alert_thresholds.get('high', 0.8)
            
            # Generate alert message
            message = f"{prediction.severity_level.title()} severity solar flare prediction: {prediction.flare_probability:.1%} probability"
            
            alerts.append(AlertResponse(
                id=prediction.id or f"pred_{int(prediction.timestamp.timestamp())}",
                timestamp=prediction.timestamp,
                flare_probability=prediction.flare_probability,
                severity_level=prediction.severity_level,
                alert_triggered=alert_triggered,
                message=message
            ))
        
        has_more = end_idx < total_count
        
        return HistoricalAlertsResponse(
            alerts=alerts,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve alert history"
        )


@router.get(
    "/statistics",
    summary="Get Alert Statistics",
    description="Get statistical summary of recent solar flare predictions."
)
async def get_alert_statistics(
    request: Request,
    user_session: UserSession = Depends(get_current_user),
    hours_back: int = Query(24, ge=1, le=168, description="Hours to analyze (max 7 days)")
):
    """
    Get statistical summary of solar flare predictions.
    
    **Enterprise Feature**: Detailed statistics require Enterprise subscription.
    
    **Authentication Required**: Bearer token (JWT or API key)
    """
    try:
        # Check rate limits
        await check_rate_limits(user_session, "alerts")
        
        # Basic statistics for all tiers
        stats = await predictions_repo.get_prediction_statistics(hours_back=hours_back)
        
        # Enterprise users get additional detailed statistics
        if user_session.subscription_tier == "enterprise":
            hourly_counts = await predictions_repo.get_hourly_prediction_counts(hours_back=hours_back)
            stats["hourly_breakdown"] = hourly_counts
        
        return {
            "statistics": stats,
            "time_period_hours": hours_back,
            "subscription_tier": user_session.subscription_tier
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve alert statistics"
        )