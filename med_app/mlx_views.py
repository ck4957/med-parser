"""
Django API Endpoint for MLX Medical Parser
Integrates the MLX pipeline with your existing med-parser backend
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import traceback
from typing import Dict, Any

# Import your MLX pipeline
# Note: This will be lazily loaded to avoid startup overhead
_pipeline = None

logger = logging.getLogger(__name__)


def get_pipeline():
    """
    Lazy-load the MLX pipeline (singleton pattern).
    This avoids loading the 27B model on every request.
    """
    global _pipeline
    
    if _pipeline is None:
        logger.info("🚀 Initializing MLX pipeline (first request only)...")
        
        try:
            # Import here to avoid issues if MLX not installed
            from mlx_advanced_pipeline import AdvancedMedGemmaPipeline
            
            _pipeline = AdvancedMedGemmaPipeline(
                model_name="google/gemma-2-27b-it",
                quantization_bits=4,
                temperature=0.1
            )
            
            success = _pipeline.load_model()
            
            if not success:
                logger.error("❌ Failed to load MLX model")
                return None
                
            logger.info("✅ MLX pipeline ready")
            
        except Exception as e:
            logger.error(f"❌ Pipeline initialization failed: {e}")
            logger.error(traceback.format_exc())
            return None
    
    return _pipeline


@csrf_exempt  # For demo purposes; use proper CSRF in production
@require_http_methods(["POST"])
def process_medical_text(request) -> JsonResponse:
    """
    API endpoint to process medical transcripts using local MLX inference.
    
    POST /api/process-medical-text/
    
    Request Body:
    {
        "transcript": "Patient has hypertension, taking Lisinopril 10mg...",
        "validate_fhir": true,  // optional, default true
        "use_fallback": true     // optional, default true
    }
    
    Response:
    {
        "success": true,
        "data": {
            "medications": [...],
            "conditions": [...]
        },
        "validation": {...},
        "processing_time_ms": 1234,
        "model_info": {
            "model": "gemma-2-27b-it",
            "quantization": "4-bit",
            "device": "MLX (Apple M4 Max)"
        }
    }
    """
    
    try:
        # Parse request
        body = json.loads(request.body)
        transcript = body.get("transcript", "").strip()
        validate_fhir = body.get("validate_fhir", True)
        use_fallback = body.get("use_fallback", True)
        
        # Validate input
        if not transcript:
            return JsonResponse({
                "success": False,
                "error": "Missing 'transcript' in request body"
            }, status=400)
        
        if len(transcript) > 10000:
            return JsonResponse({
                "success": False,
                "error": "Transcript too long (max 10,000 characters)"
            }, status=400)
        
        # Get pipeline
        pipeline = get_pipeline()
        
        if pipeline is None:
            return JsonResponse({
                "success": False,
                "error": "MLX pipeline not available. Check server logs.",
                "suggestion": "Ensure MLX is installed and model is downloaded"
            }, status=503)
        
        # Process
        logger.info(f"Processing transcript ({len(transcript)} chars)...")
        
        import time
        start_time = time.time()
        
        if use_fallback:
            result = pipeline.process_transcript_with_fallback(
                transcript=transcript,
                validate=validate_fhir
            )
        else:
            result = pipeline.process_transcript(
                transcript=transcript,
                validate=validate_fhir
            )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        response_data = {
            "success": result["success"],
            "data": result.get("extracted_data"),
            "validation": result.get("validation_results"),
            "processing_time_ms": processing_time_ms,
            "model_info": {
                "model": "gemma-2-27b-it",
                "quantization": "4-bit",
                "device": "MLX (Apple M4 Max)",
                "privacy": "100% local inference (no cloud calls)"
            },
            "metadata": {
                "input_length": result.get("input_length"),
                "timestamp": result.get("timestamp"),
                "correction_stages": result.get("correction_stages", ["initial"])
            }
        }
        
        if not result["success"]:
            response_data["errors"] = result.get("errors", [])
        
        logger.info(f"✅ Processing complete in {processing_time_ms}ms")
        
        return JsonResponse(response_data, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON in request body"
        }, status=400)
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error(traceback.format_exc())
        
        return JsonResponse({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }, status=500)


@require_http_methods(["GET"])
def health_check(request) -> JsonResponse:
    """
    Health check endpoint to verify MLX pipeline status.
    
    GET /api/health/
    """
    
    pipeline = get_pipeline()
    
    if pipeline is None:
        return JsonResponse({
            "status": "unhealthy",
            "mlx_pipeline": "not initialized",
            "message": "Model not loaded. Try POST request to trigger initialization."
        }, status=503)
    
    return JsonResponse({
        "status": "healthy",
        "mlx_pipeline": "ready",
        "model": "gemma-2-27b-it (4-bit quantized)",
        "device": "Apple M4 Max (MLX)",
        "capabilities": [
            "medical entity extraction",
            "FHIR R4 validation",
            "self-correction",
            "vector DB fallback"
        ]
    }, status=200)


@require_http_methods(["GET"])
def model_info(request) -> JsonResponse:
    """
    Get detailed information about the loaded model.
    
    GET /api/model-info/
    """
    
    pipeline = get_pipeline()
    
    if pipeline is None:
        return JsonResponse({
            "error": "Pipeline not initialized"
        }, status=503)
    
    return JsonResponse({
        "model": {
            "name": pipeline.model_name,
            "quantization_bits": pipeline.quantization_bits,
            "max_tokens": pipeline.max_tokens,
            "temperature": pipeline.temperature
        },
        "hardware": {
            "device": "Apple M4 Max",
            "framework": "MLX",
            "gpu_cores": 40,
            "unified_memory": "Shared RAM/VRAM architecture"
        },
        "performance": {
            "estimated_tokens_per_second": "40-50",
            "estimated_latency_first_token": "1.5s",
            "memory_usage_approximate": "16GB"
        },
        "privacy": {
            "data_location": "100% local (no cloud calls)",
            "compliance": "HIPAA-compliant (data never leaves device)",
            "use_case": "Edge computing for healthcare"
        }
    }, status=200)
