"""
Aurora Pro AI - Model Loader Utilities
"""
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from ..core.config import get_settings
from ..core.logging import get_logger
from ..cache.redis_cache import get_cache

logger = get_logger("model_loader")
settings = get_settings()


class ModelProvider(str, Enum):
    """Supported model providers"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    VLLM = "vllm"


class ModelLoader:
    """Utility for loading and managing AI models"""
    
    def __init__(self):
        self.cache = get_cache()
        self.loaded_models: Dict[str, Any] = {}
        logger.info("Model loader initialized")
    
    def load_model(
        self,
        model_name: str,
        provider: ModelProvider = ModelProvider.OLLAMA,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Load a model into memory/cache
        
        Args:
            model_name: Name of the model to load
            provider: Model provider (ollama, openai, etc.)
            config: Additional configuration for the model
        
        Returns:
            bool: True if model loaded successfully
        """
        try:
            cache_key = f"model:{provider}:{model_name}"
            
            # Check if already loaded
            if cache_key in self.loaded_models:
                logger.info("Model already loaded", extra={"model": model_name})
                return True
            
            # Check cache
            cached_model = self.cache.get(cache_key)
            if cached_model:
                self.loaded_models[cache_key] = cached_model
                logger.info("Model loaded from cache", extra={"model": model_name})
                return True
            
            # Load based on provider
            model_info = {
                "name": model_name,
                "provider": provider,
                "config": config or {},
                "loaded_at": datetime.utcnow().isoformat()
            }
            
            if provider == ModelProvider.OLLAMA:
                model_info["base_url"] = settings.ollama_base_url
            elif provider == ModelProvider.OPENAI:
                model_info["api_key_set"] = bool(settings.openai_api_key)
            
            # Cache the model info
            self.cache.set(cache_key, model_info, ttl=86400)  # 24 hours
            self.loaded_models[cache_key] = model_info
            
            logger.info(
                "Model loaded successfully",
                extra={"model": model_name, "provider": provider}
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to load model: {e}",
                extra={"model": model_name, "provider": provider}
            )
            return False
    
    def unload_model(self, model_name: str, provider: ModelProvider = ModelProvider.OLLAMA) -> bool:
        """Unload a model from memory/cache"""
        try:
            cache_key = f"model:{provider}:{model_name}"
            
            if cache_key in self.loaded_models:
                del self.loaded_models[cache_key]
            
            self.cache.delete(cache_key)
            
            logger.info(
                "Model unloaded",
                extra={"model": model_name, "provider": provider}
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to unload model: {e}",
                extra={"model": model_name, "provider": provider}
            )
            return False
    
    def get_loaded_models(self) -> Dict[str, Any]:
        """Get list of currently loaded models"""
        return self.loaded_models.copy()
    
    def is_model_loaded(self, model_name: str, provider: ModelProvider = ModelProvider.OLLAMA) -> bool:
        """Check if a model is loaded"""
        cache_key = f"model:{provider}:{model_name}"
        return cache_key in self.loaded_models


# Global model loader instance
_model_loader: Optional[ModelLoader] = None


def get_model_loader() -> ModelLoader:
    """Get global model loader instance"""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader
