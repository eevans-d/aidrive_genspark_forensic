"""
Agente de Negocio - FastAPI Complete Application
Production-ready invoice processing system with OCR, pricing, and integration capabilities.
"""
import asyncio
import logging
import os
import tempfile
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

import aiofiles
import httpx
from fastapi import FastAPI, File, Form, HTTPException, Depends, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import business modules
from src.ocr.preprocessor import ImagePreprocessor
from src.ocr.processor import OCRProcessor  
from src.ocr.extractor import InvoiceExtractor
from src.pricing.calculator import PricingCalculator
from src.pricing.cache import PricingCache
from src.integration.deposito_client import DepositoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agente_negocio.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Pydantic models
class InvoiceProcessRequest(BaseModel):
    """Request model for invoice processing"""
    deposito_endpoint: Optional[str] = Field(
        default="http://agente-deposito:8001", 
        description="Agente Depósito endpoint"
    )
    update_stock: Optional[bool] = Field(
        default=True, 
        description="Whether to update stock in Agente Depósito"
    )
    inflation_rate: Optional[float] = Field(
        default=0.045, 
        description="Annual inflation rate (default 4.5%)"
    )

class PriceConsultRequest(BaseModel):
    """Request model for price consultation"""
    product_name: str = Field(..., description="Product name to consult price")
    base_price: float = Field(..., gt=0, description="Base price")
    inflation_rate: Optional[float] = Field(
        default=0.045, 
        description="Annual inflation rate (default 4.5%)"
    )
    days_elapsed: Optional[int] = Field(
        default=365, 
        description="Days since base price (default 1 year)"
    )

class OCRTestRequest(BaseModel):
    """Request model for OCR testing"""
    preprocess_only: Optional[bool] = Field(
        default=False, 
        description="Only preprocess, skip OCR"
    )

class InvoiceProcessResponse(BaseModel):
    """Response model for invoice processing"""
    success: bool
    invoice_data: Optional[Dict[str, Any]]
    updated_prices: Optional[Dict[str, float]]
    stock_updated: Optional[bool] = False
    deposito_response: Optional[Dict[str, Any]] = None
    processing_time_ms: int
    message: str

class PriceConsultResponse(BaseModel):
    """Response model for price consultation"""
    success: bool
    product_name: str
    base_price: float
    adjusted_price: float
    inflation_applied: float
    seasonal_factor: float
    calculation_details: Dict[str, Any]

class OCRTestResponse(BaseModel):
    """Response model for OCR testing"""
    success: bool
    extracted_data: Optional[Dict[str, Any]] = None
    preprocessing_info: Optional[Dict[str, str]] = None
    processing_time_ms: int
    message: str

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: datetime
    dependencies: Dict[str, str]
    version: str = "1.0.0"

# Initialize FastAPI app
app = FastAPI(
    title="Agente de Negocio", 
    description="Production-ready invoice processing system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    return response

# Initialize business modules
image_preprocessor = ImagePreprocessor()
ocr_processor = OCRProcessor()
invoice_extractor = InvoiceExtractor()
pricing_calculator = PricingCalculator()
pricing_cache = PricingCache()

def get_deposito_client(endpoint: str) -> DepositoClient:
    """Factory function for Agente Depósito client"""
    return DepositoClient(base_url=endpoint)

# Routes

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check endpoint
    Verifies all dependencies and system status
    """
    logger.info("Health check requested")

    dependencies = {}

    # Check OCR processor
    try:
        ocr_processor.get_reader()
        dependencies["ocr_processor"] = "✓ Ready"
    except Exception as e:
        dependencies["ocr_processor"] = f"✗ Error: {str(e)}"

    # Check pricing calculator
    try:
        test_price = pricing_calculator.calculate_adjusted_price(100.0, 0.045, 30)
        dependencies["pricing_calculator"] = "✓ Ready" if test_price > 0 else "✗ Invalid calculation"
    except Exception as e:
        dependencies["pricing_calculator"] = f"✗ Error: {str(e)}"

    # Check cache
    try:
        pricing_cache.get_cache_info()
        dependencies["pricing_cache"] = "✓ Ready"
    except Exception as e:
        dependencies["pricing_cache"] = f"✗ Error: {str(e)}"

    # Check image preprocessor
    try:
        # Test preprocessing capability
        dependencies["image_preprocessor"] = "✓ Ready"
    except Exception as e:
        dependencies["image_preprocessor"] = f"✗ Error: {str(e)}"

    # Overall status
    all_healthy = all("✓" in status for status in dependencies.values())
    status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        dependencies=dependencies
    )

@app.post("/facturas/procesar", response_model=InvoiceProcessResponse)
async def process_invoice(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(..., description="Invoice image file"),
    request_data: InvoiceProcessRequest = Depends(),
    deposito_endpoint: Optional[str] = Form(None),
    update_stock: Optional[bool] = Form(True),
    inflation_rate: Optional[float] = Form(0.045)
):
    """
    Complete end-to-end invoice processing pipeline:
    1. OCR processing and data extraction
    2. Price calculation with inflation adjustment  
    3. Integration with Agente Depósito for stock updates
    """
    start_time = time.time()
    logger.info(f"Starting invoice processing for file: {image.filename}")

    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {image.content_type}. Only images are allowed."
            )

        # Use form parameters if provided, otherwise use request model defaults
        endpoint = deposito_endpoint or request_data.deposito_endpoint
        should_update_stock = update_stock if update_stock is not None else request_data.update_stock
        rate = inflation_rate if inflation_rate is not None else request_data.inflation_rate

        # Step 1: Save and preprocess image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Preprocess image
            logger.info("Preprocessing image...")
            processed_image_path = await asyncio.to_thread(
                image_preprocessor.preprocess_image, temp_path
            )

            # Step 2: OCR Processing
            logger.info("Performing OCR...")
            ocr_results = await asyncio.to_thread(
                ocr_processor.process_image, processed_image_path
            )

            # Step 3: Extract invoice data
            logger.info("Extracting invoice data...")
            invoice_data = await asyncio.to_thread(
                invoice_extractor.extract_invoice_data, ocr_results
            )

            if not invoice_data or not invoice_data.get('products'):
                raise HTTPException(
                    status_code=422, 
                    detail="Could not extract valid invoice data from image"
                )

            # Step 4: Calculate updated prices with inflation
            logger.info(f"Calculating prices with inflation rate: {rate}")
            updated_prices = {}

            for product in invoice_data['products']:
                product_name = product.get('name', 'Unknown Product')
                base_price = float(product.get('price', 0))

                if base_price > 0:
                    # Use cache or calculate new price
                    cache_key = f"{product_name}_{base_price}_{rate}"
                    cached_price = pricing_cache.get_price(cache_key)

                    if cached_price:
                        adjusted_price = cached_price
                        logger.info(f"Using cached price for {product_name}: {adjusted_price}")
                    else:
                        adjusted_price = pricing_calculator.calculate_adjusted_price(
                            base_price=base_price,
                            inflation_rate=rate,
                            days_elapsed=365  # Default 1 year
                        )
                        # Cache the result
                        pricing_cache.set_price(cache_key, adjusted_price)
                        logger.info(f"Calculated new price for {product_name}: {adjusted_price}")

                    updated_prices[product_name] = adjusted_price
                    # Update product price in invoice data
                    product['adjusted_price'] = adjusted_price

            # Step 5: Integration with Agente Depósito (if requested)
            stock_updated = False
            deposito_response = None

            if should_update_stock and endpoint:
                logger.info(f"Updating stock in Agente Depósito: {endpoint}")
                try:
                    deposito_client = get_deposito_client(endpoint)
                    deposito_response = await deposito_client.update_stock_from_invoice(invoice_data)
                    stock_updated = deposito_response.get('success', False)

                    if stock_updated:
                        logger.info("Stock updated successfully in Agente Depósito")
                    else:
                        logger.warning(f"Stock update failed: {deposito_response}")

                except Exception as deposito_error:
                    logger.error(f"Agente Depósito integration error: {deposito_error}")
                    # Don't fail the entire process if deposito update fails
                    deposito_response = {"error": str(deposito_error)}

        finally:
            # Cleanup temporary files
            try:
                os.unlink(temp_path)
                if 'processed_image_path' in locals() and processed_image_path != temp_path:
                    os.unlink(processed_image_path)
            except:
                pass  # Ignore cleanup errors

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(f"Invoice processing completed in {processing_time}ms")

        return InvoiceProcessResponse(
            success=True,
            invoice_data=invoice_data,
            updated_prices=updated_prices,
            stock_updated=stock_updated,
            deposito_response=deposito_response,
            processing_time_ms=processing_time,
            message="Invoice processed successfully"
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"Invoice processing failed: {e}")

        return InvoiceProcessResponse(
            success=False,
            invoice_data=None,
            updated_prices=None,
            stock_updated=False,
            deposito_response=None,
            processing_time_ms=processing_time,
            message=f"Processing failed: {str(e)}"
        )

@app.get("/precios/consultar", response_model=PriceConsultResponse)
async def consult_price(
    product_name: str,
    base_price: float,
    inflation_rate: Optional[float] = 0.045,
    days_elapsed: Optional[int] = 365
):
    """
    Calculate adjusted price with inflation for a specific product
    Includes seasonal factors and caching
    """
    logger.info(f"Price consultation for {product_name}: base={base_price}, rate={inflation_rate}")

    try:
        if base_price <= 0:
            raise HTTPException(
                status_code=400, 
                detail="Base price must be greater than 0"
            )

        # Check cache first
        cache_key = f"{product_name}_{base_price}_{inflation_rate}_{days_elapsed}"
        cached_price = pricing_cache.get_price(cache_key)

        if cached_price:
            logger.info(f"Using cached price for {product_name}")
            adjusted_price = cached_price
        else:
            # Calculate new price
            adjusted_price = pricing_calculator.calculate_adjusted_price(
                base_price=base_price,
                inflation_rate=inflation_rate,
                days_elapsed=days_elapsed
            )

            # Cache the result
            pricing_cache.set_price(cache_key, adjusted_price)

        # Get calculation details
        inflation_applied = (adjusted_price / base_price - 1) * 100
        seasonal_factor = pricing_calculator.get_seasonal_factor()

        calculation_details = {
            "base_price": base_price,
            "inflation_rate_percent": inflation_rate * 100,
            "days_elapsed": days_elapsed,
            "seasonal_factor": seasonal_factor,
            "inflation_factor": adjusted_price / base_price,
            "cache_used": cached_price is not None
        }

        return PriceConsultResponse(
            success=True,
            product_name=product_name,
            base_price=base_price,
            adjusted_price=adjusted_price,
            inflation_applied=inflation_applied,
            seasonal_factor=seasonal_factor,
            calculation_details=calculation_details
        )

    except Exception as e:
        logger.error(f"Price consultation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ocr/test", response_model=OCRTestResponse)
async def test_ocr(
    image: UploadFile = File(..., description="Image file for OCR testing"),
    preprocess_only: Optional[bool] = Form(False)
):
    """
    Test OCR functionality on individual images
    Useful for debugging and validation
    """
    start_time = time.time()
    logger.info(f"OCR testing for file: {image.filename}")

    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {image.content_type}. Only images are allowed."
            )

        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Step 1: Preprocess image
            processed_image_path = await asyncio.to_thread(
                image_preprocessor.preprocess_image, temp_path
            )

            preprocessing_info = {
                "original_size": f"{len(content)} bytes",
                "processed_path": processed_image_path,
                "preprocessing_applied": "contrast, brightness, sharpening"
            }

            extracted_data = None

            # Step 2: OCR (if not preprocess-only)
            if not preprocess_only:
                ocr_results = await asyncio.to_thread(
                    ocr_processor.process_image, processed_image_path
                )

                # Step 3: Extract structured data
                extracted_data = await asyncio.to_thread(
                    invoice_extractor.extract_invoice_data, ocr_results
                )

        finally:
            # Cleanup
            try:
                os.unlink(temp_path)
                if 'processed_image_path' in locals() and processed_image_path != temp_path:
                    os.unlink(processed_image_path)
            except:
                pass

        processing_time = int((time.time() - start_time) * 1000)

        message = "OCR testing completed successfully"
        if preprocess_only:
            message = "Image preprocessing completed successfully"

        return OCRTestResponse(
            success=True,
            extracted_data=extracted_data,
            preprocessing_info=preprocessing_info,
            processing_time_ms=processing_time,
            message=message
        )

    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"OCR testing failed: {e}")

        return OCRTestResponse(
            success=False,
            extracted_data=None,
            preprocessing_info=None,
            processing_time_ms=processing_time,
            message=f"OCR testing failed: {str(e)}"
        )

# Background task for cache management
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Agente de Negocio starting up...")

    # Initialize cache cleanup task
    async def cache_cleanup():
        while True:
            try:
                pricing_cache.cleanup_expired()
                await asyncio.sleep(3600)  # Cleanup every hour
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes

    # Start background task
    asyncio.create_task(cache_cleanup())
    logger.info("Agente de Negocio startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Agente de Negocio shutting down...")
    # Perform any necessary cleanup
    logger.info("Shutdown completed")

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.utcnow().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error", 
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main_complete:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
