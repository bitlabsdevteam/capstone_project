from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Basic health check response."""
    status: str
    timestamp: float
    version: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": 1699123456.789,
                "version": "1.0.0"
            }
        }


class DetailedHealthResponse(BaseModel):
    """Detailed health check response."""
    status: str
    timestamp: float
    version: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": 1699123456.789,
                "version": "1.0.0"
            }
        }