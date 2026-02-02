"""
NASA DONKI API Client
Fetches real solar data for predictions
"""

import httpx
import structlog
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from functools import wraps

logger = structlog.get_logger()


class NASADataClient:
    """
    Client for NASA DONKI API and NOAA Solar Weather APIs
    
    Endpoints:
    - Solar Flare (FLR)
    - Coronal Mass Ejection (CME)
    - Geomagnetic Storm (GST)
    - NOAA Solar Wind Data
    - NOAA Sunspot Data
    """
    
    DONKI_BASE_URL = "https://api.nasa.gov/DONKI"
    NOAA_BASE_URL = "https://services.swpc.noaa.gov"
    
    def __init__(self, api_key: Optional[str] = None, cache_service: Optional[Any] = None):
        self.api_key = api_key or "DEMO_KEY"
        self.cache = cache_service
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json"}
        )
        self._retry_count = 3
        self._retry_delay = 1.0
    
    async def _retry_request(self, request_func, *args, **kwargs):
        """Execute request with exponential backoff retry"""
        last_error = None
        
        for attempt in range(self._retry_count):
            try:
                return await request_func(*args, **kwargs)
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_error = e
                wait_time = self._retry_delay * (2 ** attempt)
                logger.warning(
                    "request_retry",
                    attempt=attempt + 1,
                    wait_seconds=wait_time,
                    error=str(e)
                )
                await asyncio.sleep(wait_time)
        
        logger.error("request_failed_all_retries", error=str(last_error))
        raise last_error
    
    async def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get value from cache if available"""
        if self.cache:
            try:
                return await self.cache.get(cache_key)
            except Exception as e:
                logger.warning("cache_get_failed", key=cache_key, error=str(e))
        return None
    
    async def _set_cached(self, cache_key: str, value: Any, ttl: int = 300):
        """Set value in cache"""
        if self.cache:
            try:
                await self.cache.set(cache_key, value, ttl=ttl)
            except Exception as e:
                logger.warning("cache_set_failed", key=cache_key, error=str(e))
    
    async def fetch_solar_flares(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch solar flare events from NASA DONKI API
        
        Args:
            start_date: Start of date range (default: 7 days ago)
            end_date: End of date range (default: now)
            
        Returns:
            List of solar flare events with classType, peakTime, sourceLocation
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        cache_key = f"nasa:flares:{start_date.date()}:{end_date.date()}"
        cached = await self._get_cached(cache_key)
        if cached:
            logger.debug("nasa_cache_hit", endpoint="flares")
            return cached
        
        params = {
            "api_key": self.api_key,
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d")
        }
        
        async def make_request():
            response = await self.client.get(
                f"{self.DONKI_BASE_URL}/FLR",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        try:
            data = await self._retry_request(make_request)
            
            # Normalize data
            flares = []
            for flare in (data or []):
                flares.append({
                    "flare_id": flare.get("flrID"),
                    "class_type": flare.get("classType", "C1.0"),
                    "peak_time": flare.get("peakTime"),
                    "begin_time": flare.get("beginTime"),
                    "end_time": flare.get("endTime"),
                    "source_location": flare.get("sourceLocation"),
                    "active_region": flare.get("activeRegionNum"),
                    "linked_events": flare.get("linkedEvents", [])
                })
            
            await self._set_cached(cache_key, flares, ttl=300)
            logger.info("nasa_flares_fetched", count=len(flares))
            return flares
            
        except Exception as e:
            logger.error("nasa_flares_fetch_failed", error=str(e))
            return []
    
    async def fetch_cme_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch Coronal Mass Ejection events from NASA DONKI API
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        cache_key = f"nasa:cme:{start_date.date()}:{end_date.date()}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        params = {
            "api_key": self.api_key,
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d")
        }
        
        async def make_request():
            response = await self.client.get(
                f"{self.DONKI_BASE_URL}/CME",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        try:
            data = await self._retry_request(make_request)
            
            cmes = []
            for cme in (data or []):
                cmes.append({
                    "cme_id": cme.get("activityID"),
                    "start_time": cme.get("startTime"),
                    "source_location": cme.get("sourceLocation"),
                    "speed": cme.get("cmeAnalyses", [{}])[0].get("speed"),
                    "half_angle": cme.get("cmeAnalyses", [{}])[0].get("halfAngle"),
                    "is_earth_directed": any(
                        "Earth" in str(a.get("enlilList", [])) 
                        for a in cme.get("cmeAnalyses", [])
                    )
                })
            
            await self._set_cached(cache_key, cmes, ttl=300)
            logger.info("nasa_cme_fetched", count=len(cmes))
            return cmes
            
        except Exception as e:
            logger.error("nasa_cme_fetch_failed", error=str(e))
            return []
    
    async def fetch_geomagnetic_storms(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Fetch Geomagnetic Storm events"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        cache_key = f"nasa:gst:{start_date.date()}:{end_date.date()}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        params = {
            "api_key": self.api_key,
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d")
        }
        
        async def make_request():
            response = await self.client.get(
                f"{self.DONKI_BASE_URL}/GST",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        try:
            data = await self._retry_request(make_request)
            
            storms = []
            for storm in (data or []):
                kp_values = storm.get("allKpIndex", [])
                max_kp = max([kp.get("kpIndex", 0) for kp in kp_values], default=0)
                
                storms.append({
                    "storm_id": storm.get("gstID"),
                    "start_time": storm.get("startTime"),
                    "kp_index": max_kp,
                    "linked_events": storm.get("linkedEvents", [])
                })
            
            await self._set_cached(cache_key, storms, ttl=600)
            logger.info("nasa_gst_fetched", count=len(storms))
            return storms
            
        except Exception as e:
            logger.error("nasa_gst_fetch_failed", error=str(e))
            return []
    
    async def fetch_current_solar_wind(self) -> Dict:
        """
        Get current solar wind speed and density from NOAA
        Updates every 1 minute
        """
        cache_key = "noaa:solar_wind:current"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        async def make_request():
            response = await self.client.get(
                f"{self.NOAA_BASE_URL}/products/summary/solar-wind-speed.json"
            )
            response.raise_for_status()
            return response.json()
        
        try:
            data = await self._retry_request(make_request)
            
            result = {
                "speed": float(data.get("WindSpeed", 400)),
                "timestamp": data.get("TimeStamp"),
                "source": "noaa-swpc"
            }
            
            # Also fetch density
            try:
                density_response = await self.client.get(
                    f"{self.NOAA_BASE_URL}/products/summary/solar-wind-mag-field.json"
                )
                density_data = density_response.json()
                result["bt"] = float(density_data.get("Bt", 5.0))
                result["bz"] = float(density_data.get("Bz", 0.0))
            except:
                result["bt"] = 5.0
                result["bz"] = 0.0
            
            await self._set_cached(cache_key, result, ttl=60)
            logger.info("solar_wind_fetched", speed=result["speed"])
            return result
            
        except Exception as e:
            logger.error("solar_wind_fetch_failed", error=str(e))
            return {
                "speed": 400.0,
                "bt": 5.0,
                "bz": 0.0,
                "source": "fallback"
            }
    
    async def fetch_sunspot_data(self) -> Dict:
        """
        Get current sunspot number and solar flux from NOAA
        """
        cache_key = "noaa:sunspots:current"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        async def make_request():
            response = await self.client.get(
                f"{self.NOAA_BASE_URL}/json/solar-cycle/observed-solar-cycle-indices.json"
            )
            response.raise_for_status()
            return response.json()
        
        try:
            data = await self._retry_request(make_request)
            
            # Get latest entry
            latest = data[-1] if data else {}
            
            result = {
                "sunspot_number": int(latest.get("ssn", 50)),
                "solar_flux": float(latest.get("f10.7", 150.0)),
                "observation_date": latest.get("time-tag"),
                "source": "noaa-swpc"
            }
            
            await self._set_cached(cache_key, result, ttl=3600)
            logger.info("sunspot_data_fetched", ssn=result["sunspot_number"])
            return result
            
        except Exception as e:
            logger.error("sunspot_fetch_failed", error=str(e))
            return {
                "sunspot_number": 50,
                "solar_flux": 150.0,
                "source": "fallback"
            }
    
    async def fetch_kp_index(self) -> Dict:
        """
        Get current Kp index (geomagnetic activity indicator)
        """
        cache_key = "noaa:kp:current"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        async def make_request():
            response = await self.client.get(
                f"{self.NOAA_BASE_URL}/products/noaa-planetary-k-index.json"
            )
            response.raise_for_status()
            return response.json()
        
        try:
            data = await self._retry_request(make_request)
            
            # Get latest Kp value (skip header row)
            latest = data[-1] if len(data) > 1 else ["", "", "2"]
            
            result = {
                "kp_index": float(latest[1]) if len(latest) > 1 else 2.0,
                "timestamp": latest[0] if latest else None,
                "source": "noaa-swpc"
            }
            
            await self._set_cached(cache_key, result, ttl=180)  # 3 min
            logger.info("kp_index_fetched", kp=result["kp_index"])
            return result
            
        except Exception as e:
            logger.error("kp_index_fetch_failed", error=str(e))
            return {
                "kp_index": 2.0,
                "source": "fallback"
            }
    
    async def get_comprehensive_solar_data(self) -> Dict:
        """
        Fetch all solar data concurrently for prediction input
        """
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        # Parallel fetch all data
        results = await asyncio.gather(
            self.fetch_current_solar_wind(),
            self.fetch_sunspot_data(),
            self.fetch_kp_index(),
            self.fetch_solar_flares(yesterday, now),
            return_exceptions=True
        )
        
        solar_wind = results[0] if not isinstance(results[0], Exception) else {"speed": 400, "bt": 5, "bz": 0}
        sunspots = results[1] if not isinstance(results[1], Exception) else {"sunspot_number": 50, "solar_flux": 150}
        kp_data = results[2] if not isinstance(results[2], Exception) else {"kp_index": 2}
        recent_flares = results[3] if not isinstance(results[3], Exception) else []
        
        return {
            "timestamp": now.isoformat(),
            "solar_wind_speed": solar_wind.get("speed", 400),
            "magnetic_field_bt": solar_wind.get("bt", 5),
            "magnetic_field_bz": solar_wind.get("bz", 0),
            "sunspot_number": sunspots.get("sunspot_number", 50),
            "solar_flux": sunspots.get("solar_flux", 150),
            "kp_index": kp_data.get("kp_index", 2),
            "recent_flares": [f.get("class_type", "C1.0") for f in recent_flares[-5:]],
            "recent_flare_count": len(recent_flares),
            "data_quality": "complete" if not any(isinstance(r, Exception) for r in results) else "partial"
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
        logger.info("nasa_client_closed")


# Singleton instance
_nasa_client: Optional[NASADataClient] = None


def get_nasa_client(api_key: Optional[str] = None, cache_service: Optional[Any] = None) -> NASADataClient:
    """Get or create NASA client singleton"""
    global _nasa_client
    if _nasa_client is None:
        _nasa_client = NASADataClient(api_key=api_key, cache_service=cache_service)
    return _nasa_client
