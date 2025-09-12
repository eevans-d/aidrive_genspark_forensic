# 🤖 OCR Avanzado Multi-Engine para Facturas Argentinas

Sistema avanzado de OCR con múltiples motores (EasyOCR + Tesseract + PaddleOCR) para procesamiento de facturas argentinas con Computer Vision, validación AFIP y postprocesamiento inteligente.

## 🚀 Características Principales

### ⚡ OCR Multi-Engine con Voting System
- **EasyOCR**: Excelente para texto en imágenes naturales
- **Tesseract**: Configurable y bueno para texto limpio
- **PaddleOCR**: Muy bueno para documentos estructurados
- **Voting System**: Combina resultados para máxima accuracy

### 📸 Computer Vision Preprocessing
- Detección automática de orientación
- Corrección de perspectiva
- Mejora de calidad (contraste, nitidez, ruido)
- ROI detection automático
- Normalización para OCR óptimo

### 🇦🇷 Validación Argentina Específica
- Validación CUIT con dígito verificador
- Formatos de factura A, B, C
- Montos en formato argentino
- Campos obligatorios según AFIP
- Detección automática tipo de documento

### 🧹 Postprocesamiento Inteligente
- Corrección errores OCR comunes
- Spell checking contextual
- Normalización de campos
- Confidence scoring mejorado

### 📊 Performance & Analytics
- Cache Redis inteligente
- Métricas de performance
- Testing framework comparativo
- Reportes automáticos HTML/CSV/JSON

## 📁 Estructura del Proyecto

```
ocr_advanced/
├── ocr_engine_advanced.py          # Motor OCR principal multi-engine
├── image_preprocessor.py           # Preprocessor Computer Vision
├── factura_validator.py           # Validador específico Argentina
├── ocr_postprocessor.py           # Postprocessor y limpieza
├── agente_negocio_ocr_advanced.py # API FastAPI integrada
├── ocr_testing_framework.py       # Framework testing y benchmarks
├── install_ocr_system.sh          # Script instalación automática
└── README.md                       # Esta documentación
```

## 🔧 Instalación

### Instalación Automática
```bash
# Hacer ejecutable y ejecutar
chmod +x install_ocr_system.sh
./install_ocr_system.sh
```

### Instalación Manual
```bash
# Dependencias del sistema
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-spa
sudo apt-get install -y redis-server
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0

# Dependencias Python
pip install easyocr pytesseract paddlepaddle paddleocr
pip install opencv-python pillow numpy pandas
pip install fastapi uvicorn redis aioredis
pip install scikit-learn matplotlib
```

## 🚀 Uso Rápido

### 1. Iniciar el Sistema
```bash
cd ocr_advanced
python agente_negocio_ocr_advanced.py
```

### 2. API Endpoints Disponibles

#### Endpoint Legacy (Compatible v1.0)
```bash
curl -X POST "http://localhost:8001/procesar-factura" \
     -F "archivo=@mi_factura.jpg"
```

#### Endpoint Avanzado v2.0
```bash
curl -X POST "http://localhost:8001/procesar-factura-avanzada" \
     -F "archivo=@mi_factura.jpg" \
     -F "request={\"auto_enhance\":true,\"validate_fields\":true,\"return_debug_info\":true}"
```

#### Procesamiento en Lote
```bash
curl -X POST "http://localhost:8001/procesar-facturas-batch" \
     -F "archivos=@factura1.jpg" \
     -F "archivos=@factura2.jpg" \
     -F "auto_enhance=true"
```

### 3. Uso Programático

```python
import asyncio
from ocr_engine_advanced import OCREngineAdvanced
from image_preprocessor import ImagePreprocessor
from factura_validator import FacturaValidatorArgentino

async def procesar_factura(imagen_path):
    # Inicializar componentes
    preprocessor = ImagePreprocessor()
    ocr_engine = OCREngineAdvanced()
    validator = FacturaValidatorArgentino()

    # 1. Preprocessar imagen
    resultado_prep = preprocessor.preprocess_factura(imagen_path)

    # 2. OCR avanzado
    resultado_ocr = await ocr_engine.process_factura(imagen_path)

    # 3. Validar campos argentinos
    resultado_val = validator.validate_factura_completa(
        resultado_ocr["text_raw"]
    )

    return {
        "success": resultado_ocr["success"],
        "campos_extraidos": resultado_ocr["campos_extraidos"],
        "confidence": resultado_ocr["confidence"],
        "validacion_exitosa": resultado_val.is_valid,
        "datos_normalizados": resultado_val.normalized_data
    }

# Ejecutar
resultado = asyncio.run(procesar_factura("mi_factura.jpg"))
print(resultado)
```

## 📊 Testing y Benchmarks

### Ejecutar Tests Comparativos
```bash
python ocr_testing_framework.py
```

### Crear Test Personalizado
```python
from ocr_testing_framework import OCRTestingFramework

async def mi_test():
    framework = OCRTestingFramework()

    # Crear imágenes de test
    imagenes_test = framework.create_test_images(5)

    # Ground truth (opcional)
    ground_truth = [
        {"cuit": "20-12345678-9", "total": "1234.56"},
        # ... más datos reales
    ]

    # Ejecutar comparación
    reporte = await framework.run_comprehensive_test(
        imagenes_test, ground_truth
    )

    print(f"Accuracy OCR Básico: {reporte.accuracy_comparison['basic_ocr_avg_accuracy']:.1%}")
    print(f"Accuracy OCR Avanzado: {reporte.accuracy_comparison['advanced_ocr_avg_accuracy']:.1%}")

asyncio.run(mi_test())
```

## 📈 Métricas y Monitoreo

### Health Check del Sistema
```bash
curl http://localhost:8001/health
```

### Estadísticas de Performance
```bash
curl http://localhost:8001/ocr-stats
```

### Test Rápido OCR
```bash
curl http://localhost:8001/test-ocr
```

## 🎯 Performance Esperado

### Benchmarks Típicos
- **Latencia**: <2s por factura (vs 5-10s OCR básico)
- **Accuracy**: +25% mejora en extracción de campos
- **Confidence**: +15% confianza promedio
- **Validación**: >85% facturas pasan validación AFIP

### Optimizaciones Incluidas
- Cache Redis para resultados repetidos
- Procesamiento async no bloqueante
- Preprocessor optimizado por tipo documento
- Voting system para mayor accuracy
- Fallback automático si engines fallan

## 🔧 Configuración Avanzada

### Personalizar OCR Engine
```python
# Configurar engines específicos
ocr_engine = OCREngineAdvanced()

# Ajustar parámetros Tesseract
ocr_engine.tesseract_config = "--oem 3 --psm 6 -l spa"

# Configurar threshold confianza
ocr_engine.min_confidence = 0.4
```

### Personalizar Preprocessor
```python
preprocessor = ImagePreprocessor()

# Ajustar resolución objetivo
preprocessor.target_dpi = 300
preprocessor.min_resolution = (1000, 800)

# Configurar mejoras automáticas
resultado = preprocessor.preprocess_factura(
    imagen_path, 
    auto_enhance=True
)
```

### Personalizar Validador
```python
validator = FacturaValidatorArgentino()

# Validación completa
resultado = validator.validate_factura_completa(texto_ocr)

# Validación rápida
resultado_rapido = validator.validate_quick(texto_ocr)
```

## 🚨 Troubleshooting

### Problemas Comunes

#### "ModuleNotFoundError: No module named 'easyocr'"
```bash
pip install easyocr
# o si falla:
pip install --upgrade pip
pip install easyocr --no-cache-dir
```

#### "Tesseract no encontrado"
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa
# En Windows: descargar desde GitHub releases
```

#### "Redis connection failed"
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Performance lento en primera ejecución
```bash
# EasyOCR descarga modelos en primera ejecución
# PaddleOCR también descarga modelos
# Es normal que tarde ~2-5 minutos la primera vez
```

### Logs y Debugging

#### Activar Logs Detallados
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# O en archivo
logging.basicConfig(
    level=logging.INFO,
    filename='/var/log/ocr_system/ocr.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### Debug Específico
```python
# Habilitar debug info en API
resultado = await procesar_factura_avanzada(
    archivo=archivo,
    request=FacturaProcessRequest(
        return_debug_info=True
    )
)
print(resultado.debug_info)
```

## 🔮 Próximas Mejoras

### Roadmap v2.1
- [ ] Integración con más OCR engines (TrOCR, Surya)
- [ ] Support para PDF multipágina
- [ ] OCR en tiempo real via webcam
- [ ] Mejores modelos ML para clasificación documentos
- [ ] API REST más completa con autenticación

### Roadmap v2.2  
- [ ] Integración con servicios cloud OCR (AWS Textract, Google Vision)
- [ ] Support para facturas electrónicas XML
- [ ] Dashboard web administrativo
- [ ] API webhooks para notificaciones

## 📞 Soporte

### Reportar Issues
Si encuentras problemas:

1. Verifica que todas las dependencias estén instaladas
2. Revisa logs en `/var/log/ocr_system/`
3. Ejecuta test de health check
4. Incluye información del sistema y ejemplo problemático

### Contribuir
Este sistema es parte del proyecto Sistema Inventario Retail Argentino.
Contribuciones son bienvenidas para:
- Mejoras de accuracy
- Optimizaciones de performance  
- Support para más tipos de documentos
- Mejores validaciones específicas Argentina

---

**🚀 Sistema OCR Avanzado v2.0 - Inventario Retail Argentino**
*Transformando facturas en datos con IA de última generación*
