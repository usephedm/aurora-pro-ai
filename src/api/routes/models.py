"""
Aurora Pro AI - Model API Routes
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ...utils.model_loader import get_model_loader, ModelProvider
from ...core.logging import get_logger

router = APIRouter()
logger = get_logger("api.models")


class ModelLoad(BaseModel):
    """Schema for loading a model"""
    name: str
    provider: str = "ollama"
    config: Optional[Dict[str, Any]] = None


@router.get("/")
async def list_models() -> Dict[str, Any]:
    """List all loaded models"""
    try:
        model_loader = get_model_loader()
        models = model_loader.get_loaded_models()
        return {"models": models, "count": len(models)}
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/load", status_code=status.HTTP_201_CREATED)
async def load_model(model_data: ModelLoad) -> Dict[str, Any]:
    """Load a model into memory/cache"""
    try:
        model_loader = get_model_loader()
        provider = ModelProvider(model_data.provider)
        
        success = model_loader.load_model(
            model_data.name,
            provider,
            model_data.config
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to load model {model_data.name}"
            )
        
        return {
            "message": f"Model {model_data.name} loaded successfully",
            "name": model_data.name,
            "provider": model_data.provider
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{model_name}")
async def unload_model(model_name: str, provider: str = "ollama") -> Dict[str, str]:
    """Unload a model from memory/cache"""
    try:
        model_loader = get_model_loader()
        provider_enum = ModelProvider(provider)
        
        success = model_loader.unload_model(model_name, provider_enum)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_name} not found or failed to unload"
            )
        
        return {"message": f"Model {model_name} unloaded successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to unload model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{model_name}/status")
async def get_model_status(model_name: str, provider: str = "ollama") -> Dict[str, Any]:
    """Check if a model is loaded"""
    try:
        model_loader = get_model_loader()
        provider_enum = ModelProvider(provider)
        
        is_loaded = model_loader.is_model_loaded(model_name, provider_enum)
        
        return {
            "model": model_name,
            "provider": provider,
            "loaded": is_loaded
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
