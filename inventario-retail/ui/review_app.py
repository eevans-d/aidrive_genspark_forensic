"""
Streamlit UI - Manual Invoice Review
===================================

Aplicación Streamlit para revisión manual de facturas AFIP argentinas.
Integra con el sistema de inventario para procesamiento OCR y validación.

Características:
- Upload de imágenes de facturas AFIP
- Procesamiento OCR con EasyOCR
- Validación de CUIT y datos fiscales
- Revisión manual de campos extraídos
- Integración con agente_negocio para almacenamiento
- Contexto argentino (pesos, AFIP, impuestos)

Autor: Sistema Multi-Agente Inventario
Versión: Post-MVP con UI
"""

import os
import sys
import io
import json
import logging
import requests
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(
    page_title="📋 Revisión Manual - Facturas AFIP",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================
# CONFIGURACIÓN Y UTILS
# ========================

# URLs de servicios (configurables)
AGENTE_NEGOCIO_URL = os.getenv("AGENTE_NEGOCIO_URL", "http://localhost:8002")
AGENTE_DEPOSITO_URL = os.getenv("AGENTE_DEPOSITO_URL", "http://localhost:8001") 
ML_PREDICTOR_URL = os.getenv("ML_PREDICTOR_URL", "http://localhost:8003")

# Formatos argentinos
CURRENCY_FORMAT = "ARS ${:,.2f}"
DATE_FORMAT = "%d/%m/%Y"

# Categorías de productos argentinos
CATEGORIAS_PRODUCTOS = [
    "lacteos", "bebidas", "panaderia", "carnes", "vegetales",
    "limpieza", "personal", "hogar", "electrodomesticos", "otros"
]

# Tipos de IVA argentinos
TIPOS_IVA = {
    "21": 0.21,
    "10.5": 0.105,
    "27": 0.27,
    "0": 0.0,
    "exento": 0.0
}

def format_currency(amount: float) -> str:
    """Formatear moneda argentina"""
    return CURRENCY_FORMAT.format(amount)

def validate_cuit(cuit_str: str) -> bool:
    """Validar CUIT argentino"""
    if not cuit_str or len(cuit_str) != 11:
        return False

    try:
        # Algoritmo de validación de CUIT
        cuit = [int(d) for d in cuit_str]
        multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

        sum_check = sum(c * m for c, m in zip(cuit[:10], multipliers))
        remainder = sum_check % 11

        if remainder < 2:
            expected_digit = remainder
        else:
            expected_digit = 11 - remainder

        return cuit[10] == expected_digit

    except (ValueError, IndexError):
        return False

def call_service_api(url: str, method: str = "GET", data: dict = None, files: dict = None) -> dict:
    """Llamar APIs de los servicios del sistema"""
    try:
        if method.upper() == "POST":
            if files:
                response = requests.post(url, data=data, files=files, timeout=30)
            else:
                response = requests.post(url, json=data, timeout=30)
        else:
            response = requests.get(url, params=data, timeout=30)

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error llamando API {url}: {str(e)}")
        return {"error": str(e)}

# ========================
# ESTADO DE SESIÓN
# ========================

def init_session_state():
    """Inicializar estado de la sesión"""
    if 'uploaded_invoices' not in st.session_state:
        st.session_state.uploaded_invoices = []

    if 'current_invoice' not in st.session_state:
        st.session_state.current_invoice = None

    if 'ocr_results' not in st.session_state:
        st.session_state.ocr_results = {}

    if 'processing_queue' not in st.session_state:
        st.session_state.processing_queue = []

    if 'validation_errors' not in st.session_state:
        st.session_state.validation_errors = []

# ========================
# COMPONENTES UI
# ========================

def render_sidebar():
    """Renderizar sidebar con navegación y estado"""
    with st.sidebar:
        st.title("🏪 Sistema Inventario")
        st.markdown("### 📋 Revisión Manual AFIP")

        # Estado del sistema
        st.markdown("#### 🔄 Estado Servicios")

        # Verificar servicios
        services_status = check_services_health()

        for service, status in services_status.items():
            if status['healthy']:
                st.success(f"✅ {service}")
            else:
                st.error(f"❌ {service}")

        st.markdown("---")

        # Estadísticas de sesión
        st.markdown("#### 📊 Estadísticas Sesión")
        st.metric("Facturas Subidas", len(st.session_state.uploaded_invoices))
        st.metric("En Cola", len(st.session_state.processing_queue))
        st.metric("Errores Validación", len(st.session_state.validation_errors))

        st.markdown("---")

        # Configuración
        st.markdown("#### ⚙️ Configuración")

        auto_validate = st.checkbox("Auto-validar CUIT", value=True)
        auto_calculate_iva = st.checkbox("Auto-calcular IVA", value=True)
        strict_mode = st.checkbox("Modo Estricto", value=False, 
                                help="Requerir validación manual de todos los campos")

        # Guardar configuración en session state
        st.session_state.config = {
            'auto_validate': auto_validate,
            'auto_calculate_iva': auto_calculate_iva,
            'strict_mode': strict_mode
        }

def check_services_health() -> Dict[str, Dict]:
    """Verificar estado de salud de los servicios"""
    services = {
        "Agente Negocio": f"{AGENTE_NEGOCIO_URL}/health",
        "Agente Depósito": f"{AGENTE_DEPOSITO_URL}/health", 
        "ML Predictor": f"{ML_PREDICTOR_URL}/health"
    }

    status_results = {}

    for service_name, health_url in services.items():
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                status_results[service_name] = {
                    'healthy': True,
                    'details': response.json()
                }
            else:
                status_results[service_name] = {
                    'healthy': False,
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            status_results[service_name] = {
                'healthy': False,
                'error': str(e)
            }

    return status_results

def render_file_uploader():
    """Renderizar uploader de archivos"""
    st.markdown("### 📤 Subir Facturas AFIP")

    uploaded_files = st.file_uploader(
        "Seleccionar imágenes de facturas",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        accept_multiple_files=True,
        help="Formatos soportados: PNG, JPG, JPEG, PDF"
    )

    if uploaded_files:
        col1, col2 = st.columns([3, 1])

        with col1:
            st.info(f"📁 {len(uploaded_files)} archivo(s) seleccionado(s)")

        with col2:
            if st.button("🔄 Procesar Todas", type="primary"):
                process_uploaded_files(uploaded_files)

        # Mostrar preview de archivos
        if len(uploaded_files) <= 5:  # Limitar preview
            for uploaded_file in uploaded_files:
                with st.expander(f"👁️ Preview: {uploaded_file.name}"):
                    if uploaded_file.type.startswith('image'):
                        image = Image.open(uploaded_file)
                        st.image(image, width=300)
                    else:
                        st.write(f"📄 Archivo PDF: {uploaded_file.name}")

def process_uploaded_files(uploaded_files):
    """Procesar archivos subidos con OCR"""
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Procesando {uploaded_file.name}...")
        progress_bar.progress((i + 1) / len(uploaded_files))

        try:
            # Enviar a agente_negocio para OCR
            files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

            ocr_result = call_service_api(
                f"{AGENTE_NEGOCIO_URL}/ocr/process",
                method="POST",
                files=files
            )

            if 'error' not in ocr_result:
                # Guardar resultado
                invoice_data = {
                    'filename': uploaded_file.name,
                    'upload_time': datetime.now(),
                    'ocr_result': ocr_result,
                    'status': 'pending_review',
                    'file_size': len(uploaded_file.getvalue())
                }

                st.session_state.uploaded_invoices.append(invoice_data)
                st.session_state.ocr_results[uploaded_file.name] = ocr_result

            else:
                st.error(f"Error procesando {uploaded_file.name}: {ocr_result['error']}")

        except Exception as e:
            st.error(f"Error procesando {uploaded_file.name}: {str(e)}")

    status_text.text("✅ Procesamiento completado")
    st.success(f"🎉 {len(uploaded_files)} facturas procesadas exitosamente")
    st.experimental_rerun()

def render_invoice_list():
    """Renderizar lista de facturas procesadas"""
    if not st.session_state.uploaded_invoices:
        st.info("📭 No hay facturas cargadas. Sube algunas imágenes para comenzar.")
        return

    st.markdown("### 📋 Facturas Procesadas")

    # Filtros
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Filtrar por estado:",
            ["Todas", "pending_review", "validated", "error"],
            key="status_filter"
        )

    with col2:
        date_filter = st.date_input(
            "Desde fecha:",
            value=date.today(),
            key="date_filter"
        )

    with col3:
        limit_results = st.number_input(
            "Límite resultados:",
            min_value=5,
            max_value=100,
            value=20,
            key="limit_results"
        )

    # Filtrar facturas
    filtered_invoices = st.session_state.uploaded_invoices.copy()

    if status_filter != "Todas":
        filtered_invoices = [inv for inv in filtered_invoices if inv['status'] == status_filter]

    # Mostrar tabla de facturas
    if filtered_invoices:
        invoice_data = []
        for i, invoice in enumerate(filtered_invoices[-limit_results:]):
            ocr_data = invoice['ocr_result']

            invoice_data.append({
                'ID': i,
                'Archivo': invoice['filename'],
                'Estado': invoice['status'],
                'Proveedor': ocr_data.get('proveedor', {}).get('razon_social', 'N/A'),
                'CUIT': ocr_data.get('proveedor', {}).get('cuit', 'N/A'),
                'Total': format_currency(ocr_data.get('totales', {}).get('total', 0)),
                'Productos': len(ocr_data.get('productos', [])),
                'Fecha': invoice['upload_time'].strftime(DATE_FORMAT)
            })

        df = pd.DataFrame(invoice_data)

        # Tabla interactiva
        selected_rows = st.dataframe(
            df,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        # Mostrar factura seleccionada
        if selected_rows and len(selected_rows.selection.rows) > 0:
            selected_idx = selected_rows.selection.rows[0]
            selected_invoice = filtered_invoices[selected_idx]
            st.session_state.current_invoice = selected_invoice

            # Renderizar editor de factura
            render_invoice_editor()

def render_invoice_editor():
    """Renderizar editor de factura seleccionada"""
    if not st.session_state.current_invoice:
        return

    invoice = st.session_state.current_invoice
    ocr_data = invoice['ocr_result']

    st.markdown("---")
    st.markdown(f"### ✏️ Editando: {invoice['filename']}")

    # Pestañas para diferentes secciones
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Datos Generales", "🏢 Proveedor", "📦 Productos", "💰 Totales"])

    with tab1:
        render_general_data_editor(ocr_data)

    with tab2:
        render_supplier_editor(ocr_data)

    with tab3:
        render_products_editor(ocr_data)

    with tab4:
        render_totals_editor(ocr_data)

    # Botones de acción
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("💾 Guardar Cambios", type="primary"):
            save_invoice_changes(invoice, ocr_data)

    with col2:
        if st.button("✅ Validar y Enviar"):
            validate_and_submit_invoice(invoice, ocr_data)

    with col3:
        if st.button("🔄 Re-procesar OCR"):
            reprocess_invoice_ocr(invoice)

    with col4:
        if st.button("🗑️ Eliminar", type="secondary"):
            delete_invoice(invoice)

def render_general_data_editor(ocr_data: dict):
    """Editor de datos generales de la factura"""
    st.markdown("#### 📄 Información General")

    col1, col2 = st.columns(2)

    with col1:
        # Número de factura
        numero_factura = st.text_input(
            "Número de Factura:",
            value=ocr_data.get('numero_factura', ''),
            key="edit_numero_factura"
        )

        # Fecha de factura
        fecha_str = ocr_data.get('fecha_factura', '')
        try:
            fecha_factura = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        except:
            fecha_factura = date.today()

        fecha_factura = st.date_input(
            "Fecha de Factura:",
            value=fecha_factura,
            key="edit_fecha_factura"
        )

        # Tipo de factura
        tipo_factura = st.selectbox(
            "Tipo de Factura:",
            ["A", "B", "C", "E", "M"],
            index=0 if not ocr_data.get('tipo_factura') else ["A", "B", "C", "E", "M"].index(ocr_data.get('tipo_factura', 'B')),
            key="edit_tipo_factura"
        )

    with col2:
        # Punto de venta
        punto_venta = st.text_input(
            "Punto de Venta:",
            value=ocr_data.get('punto_venta', ''),
            key="edit_punto_venta"
        )

        # CAE
        cae = st.text_input(
            "CAE (Código de Autorización):",
            value=ocr_data.get('cae', ''),
            help="Código de Autorización Electrónica de AFIP",
            key="edit_cae"
        )

        # Fecha de vencimiento CAE
        vto_cae_str = ocr_data.get('fecha_vto_cae', '')
        try:
            vto_cae = datetime.strptime(vto_cae_str, '%Y-%m-%d').date() if vto_cae_str else None
        except:
            vto_cae = None

        vto_cae = st.date_input(
            "Vencimiento CAE:",
            value=vto_cae,
            key="edit_vto_cae"
        )

    # Actualizar OCR data
    ocr_data.update({
        'numero_factura': numero_factura,
        'fecha_factura': fecha_factura.isoformat(),
        'tipo_factura': tipo_factura,
        'punto_venta': punto_venta,
        'cae': cae,
        'fecha_vto_cae': vto_cae.isoformat() if vto_cae else ''
    })

def render_supplier_editor(ocr_data: dict):
    """Editor de datos del proveedor"""
    st.markdown("#### 🏢 Datos del Proveedor")

    proveedor = ocr_data.get('proveedor', {})

    col1, col2 = st.columns(2)

    with col1:
        razon_social = st.text_input(
            "Razón Social:",
            value=proveedor.get('razon_social', ''),
            key="edit_razon_social"
        )

        cuit = st.text_input(
            "CUIT:",
            value=proveedor.get('cuit', ''),
            key="edit_cuit"
        )

        # Validar CUIT automáticamente
        if cuit and st.session_state.config.get('auto_validate', True):
            if validate_cuit(cuit):
                st.success("✅ CUIT válido")
            else:
                st.error("❌ CUIT inválido")

        direccion = st.text_area(
            "Dirección:",
            value=proveedor.get('direccion', ''),
            key="edit_direccion"
        )

    with col2:
        condicion_iva = st.selectbox(
            "Condición IVA:",
            ["Responsable Inscripto", "Monotributista", "Exento", "Consumidor Final"],
            index=0,
            key="edit_condicion_iva"
        )

        telefono = st.text_input(
            "Teléfono:",
            value=proveedor.get('telefono', ''),
            key="edit_telefono"
        )

        email = st.text_input(
            "Email:",
            value=proveedor.get('email', ''),
            key="edit_email"
        )

    # Actualizar datos del proveedor
    ocr_data['proveedor'] = {
        'razon_social': razon_social,
        'cuit': cuit,
        'direccion': direccion,
        'condicion_iva': condicion_iva,
        'telefono': telefono,
        'email': email
    }

def render_products_editor(ocr_data: dict):
    """Editor de productos de la factura"""
    st.markdown("#### 📦 Productos")

    productos = ocr_data.get('productos', [])

    if not productos:
        st.info("No se detectaron productos. Agregar manualmente:")
        if st.button("➕ Agregar Producto"):
            productos.append({
                'descripcion': '',
                'cantidad': 1,
                'precio_unitario': 0.0,
                'subtotal': 0.0,
                'categoria': 'otros',
                'codigo_producto': '',
                'alicuota_iva': '21'
            })
            ocr_data['productos'] = productos

    # Editor de productos existentes
    for i, producto in enumerate(productos):
        with st.expander(f"📦 Producto {i+1}: {producto.get('descripcion', 'Sin descripción')[:30]}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                descripcion = st.text_input(
                    "Descripción:",
                    value=producto.get('descripcion', ''),
                    key=f"prod_desc_{i}"
                )

                codigo = st.text_input(
                    "Código:",
                    value=producto.get('codigo_producto', ''),
                    key=f"prod_codigo_{i}"
                )

                categoria = st.selectbox(
                    "Categoría:",
                    CATEGORIAS_PRODUCTOS,
                    index=CATEGORIAS_PRODUCTOS.index(producto.get('categoria', 'otros')),
                    key=f"prod_categoria_{i}"
                )

            with col2:
                cantidad = st.number_input(
                    "Cantidad:",
                    min_value=0.01,
                    value=float(producto.get('cantidad', 1)),
                    step=0.01,
                    key=f"prod_cantidad_{i}"
                )

                precio_unitario = st.number_input(
                    "Precio Unitario:",
                    min_value=0.0,
                    value=float(producto.get('precio_unitario', 0)),
                    step=0.01,
                    key=f"prod_precio_{i}"
                )

                alicuota_iva = st.selectbox(
                    "Alícuota IVA:",
                    list(TIPOS_IVA.keys()),
                    index=list(TIPOS_IVA.keys()).index(str(producto.get('alicuota_iva', '21'))),
                    key=f"prod_iva_{i}"
                )

            with col3:
                # Cálculo automático de subtotal
                subtotal = cantidad * precio_unitario
                st.metric("Subtotal:", format_currency(subtotal))

                # IVA
                iva_rate = TIPOS_IVA[alicuota_iva]
                iva_amount = subtotal * iva_rate
                st.metric("IVA:", format_currency(iva_amount))

                # Total con IVA
                total_con_iva = subtotal + iva_amount
                st.metric("Total c/IVA:", format_currency(total_con_iva))

                # Botón eliminar producto
                if st.button("🗑️", key=f"del_prod_{i}", help="Eliminar producto"):
                    productos.pop(i)
                    st.experimental_rerun()

            # Actualizar producto
            productos[i] = {
                'descripcion': descripcion,
                'codigo_producto': codigo,
                'categoria': categoria,
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'alicuota_iva': alicuota_iva,
                'subtotal': subtotal,
                'iva': iva_amount,
                'total': total_con_iva
            }

    # Botón agregar nuevo producto
    if st.button("➕ Agregar Otro Producto"):
        productos.append({
            'descripcion': '',
            'cantidad': 1,
            'precio_unitario': 0.0,
            'subtotal': 0.0,
            'categoria': 'otros',
            'codigo_producto': '',
            'alicuota_iva': '21'
        })
        st.experimental_rerun()

    ocr_data['productos'] = productos

def render_totals_editor(ocr_data: dict):
    """Editor de totales de la factura"""
    st.markdown("#### 💰 Totales")

    productos = ocr_data.get('productos', [])

    # Calcular totales automáticamente
    subtotal_calc = sum(p.get('subtotal', 0) for p in productos)
    iva_calc = sum(p.get('iva', 0) for p in productos)
    total_calc = subtotal_calc + iva_calc

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 🧮 Totales Calculados")
        st.metric("Subtotal:", format_currency(subtotal_calc))
        st.metric("IVA Total:", format_currency(iva_calc))
        st.metric("Total General:", format_currency(total_calc))

        # Botón para usar totales calculados
        if st.button("📊 Usar Totales Calculados"):
            ocr_data['totales'] = {
                'subtotal': subtotal_calc,
                'iva_total': iva_calc,
                'total': total_calc
            }
            st.success("✅ Totales actualizados")

    with col2:
        st.markdown("##### ✏️ Edición Manual")

        totales = ocr_data.get('totales', {})

        subtotal_manual = st.number_input(
            "Subtotal:",
            min_value=0.0,
            value=float(totales.get('subtotal', subtotal_calc)),
            step=0.01,
            key="edit_subtotal"
        )

        iva_manual = st.number_input(
            "IVA Total:",
            min_value=0.0,
            value=float(totales.get('iva_total', iva_calc)),
            step=0.01,
            key="edit_iva_total"
        )

        total_manual = st.number_input(
            "Total:",
            min_value=0.0,
            value=float(totales.get('total', total_calc)),
            step=0.01,
            key="edit_total"
        )

        # Verificar discrepancias
        diff_total = abs(total_manual - total_calc)
        if diff_total > 0.01:
            st.warning(f"⚠️ Diferencia con total calculado: {format_currency(diff_total)}")

        # Actualizar totales
        ocr_data['totales'] = {
            'subtotal': subtotal_manual,
            'iva_total': iva_manual,
            'total': total_manual
        }

def save_invoice_changes(invoice: dict, ocr_data: dict):
    """Guardar cambios en factura"""
    try:
        # Actualizar timestamp
        invoice['last_modified'] = datetime.now()
        invoice['ocr_result'] = ocr_data

        st.success("💾 Cambios guardados exitosamente")

        # Log de cambios
        logger.info(f"Factura {invoice['filename']} modificada manualmente")

    except Exception as e:
        st.error(f"❌ Error guardando cambios: {str(e)}")

def validate_and_submit_invoice(invoice: dict, ocr_data: dict):
    """Validar y enviar factura al sistema"""
    validation_errors = []

    # Validaciones básicas
    if not ocr_data.get('numero_factura'):
        validation_errors.append("Número de factura requerido")

    if not ocr_data.get('proveedor', {}).get('cuit'):
        validation_errors.append("CUIT del proveedor requerido")

    cuit = ocr_data.get('proveedor', {}).get('cuit', '')
    if cuit and not validate_cuit(cuit):
        validation_errors.append("CUIT inválido")

    if not ocr_data.get('productos'):
        validation_errors.append("Al menos un producto requerido")

    # Validar totales
    productos = ocr_data.get('productos', [])
    if productos:
        total_calc = sum(p.get('total', 0) for p in productos)
        total_declared = ocr_data.get('totales', {}).get('total', 0)

        if abs(total_calc - total_declared) > 0.01:
            validation_errors.append(f"Discrepancia en totales: calculado {format_currency(total_calc)}, declarado {format_currency(total_declared)}")

    if validation_errors:
        st.error("❌ Errores de validación:")
        for error in validation_errors:
            st.error(f"  • {error}")
        return

    # Enviar al agente_negocio
    try:
        with st.spinner("📤 Enviando factura al sistema..."):

            # Formatear datos para el sistema
            invoice_payload = {
                'factura_data': ocr_data,
                'source': 'manual_review',
                'reviewer': 'streamlit_ui',
                'validated': True
            }

            result = call_service_api(
                f"{AGENTE_NEGOCIO_URL}/invoices/submit",
                method="POST",
                data=invoice_payload
            )

            if 'error' not in result:
                # Actualizar estado
                invoice['status'] = 'validated'
                invoice['submitted_at'] = datetime.now()

                st.success("✅ Factura enviada exitosamente al sistema")
                st.balloons()

                # Mostrar ID de transacción si está disponible
                if 'transaction_id' in result:
                    st.info(f"🆔 ID de transacción: {result['transaction_id']}")

                # Opcional: mostrar predicción de demanda
                show_demand_prediction_for_products(productos)

            else:
                st.error(f"❌ Error enviando factura: {result['error']}")

    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")

def show_demand_prediction_for_products(productos: List[dict]):
    """Mostrar predicción de demanda para productos de la factura"""
    if not productos:
        return

    st.markdown("#### 🔮 Predicción de Demanda")

    try:
        # Obtener predicción para productos más importantes
        for producto in productos[:3]:  # Limitar a 3 productos
            descripcion = producto.get('descripcion', 'Producto')
            categoria = producto.get('categoria', 'otros')

            # Simular llamada a ML predictor (requeriría mapeo producto_id)
            # En implementación real, mapearía descripción/código a producto_id

            with st.expander(f"📈 Predicción: {descripcion[:30]}"):
                # Datos simulados para demo
                prediction_data = {
                    'demanda_predicha_7d': np.random.randint(10, 100),
                    'confianza': np.random.uniform(0.7, 0.95),
                    'tendencia': np.random.choice(['creciente', 'estable', 'decreciente'])
                }

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Demanda 7 días", prediction_data['demanda_predicha_7d'])

                with col2:
                    st.metric("Confianza", f"{prediction_data['confianza']:.1%}")

                with col3:
                    trend_color = {"creciente": "🟢", "estable": "🟡", "decreciente": "🔴"}
                    st.metric("Tendencia", f"{trend_color[prediction_data['tendencia']]} {prediction_data['tendencia']}")

    except Exception as e:
        st.warning(f"⚠️ No se pudo obtener predicción de demanda: {str(e)}")

def reprocess_invoice_ocr(invoice: dict):
    """Re-procesar factura con OCR"""
    try:
        with st.spinner("🔄 Re-procesando con OCR..."):
            # En implementación real, reenviaría imagen original
            st.info("🔄 Funcionalidad de re-procesamiento pendiente de implementación")

    except Exception as e:
        st.error(f"❌ Error re-procesando: {str(e)}")

def delete_invoice(invoice: dict):
    """Eliminar factura de la sesión"""
    try:
        # Remover de session state
        if invoice in st.session_state.uploaded_invoices:
            st.session_state.uploaded_invoices.remove(invoice)

        # Limpiar factura actual
        if st.session_state.current_invoice == invoice:
            st.session_state.current_invoice = None

        st.success("🗑️ Factura eliminada")
        st.experimental_rerun()

    except Exception as e:
        st.error(f"❌ Error eliminando factura: {str(e)}")

def render_analytics_dashboard():
    """Renderizar dashboard de analytics"""
    st.markdown("### 📊 Analytics y Estadísticas")

    if not st.session_state.uploaded_invoices:
        st.info("📊 No hay datos para mostrar analytics")
        return

    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)

    total_invoices = len(st.session_state.uploaded_invoices)
    validated_invoices = len([inv for inv in st.session_state.uploaded_invoices if inv['status'] == 'validated'])
    pending_invoices = len([inv for inv in st.session_state.uploaded_invoices if inv['status'] == 'pending_review'])

    with col1:
        st.metric("Total Facturas", total_invoices)

    with col2:
        st.metric("Validadas", validated_invoices)

    with col3:
        st.metric("Pendientes", pending_invoices)

    with col4:
        validation_rate = (validated_invoices / total_invoices * 100) if total_invoices > 0 else 0
        st.metric("Tasa Validación", f"{validation_rate:.1f}%")

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        # Gráfico de estados
        status_counts = {}
        for invoice in st.session_state.uploaded_invoices:
            status = invoice['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        if status_counts:
            fig_status = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="Distribución por Estado"
            )
            st.plotly_chart(fig_status, use_container_width=True)

    with col2:
        # Gráfico temporal
        upload_dates = [inv['upload_time'].date() for inv in st.session_state.uploaded_invoices]

        if upload_dates:
            date_counts = {}
            for date in upload_dates:
                date_counts[date] = date_counts.get(date, 0) + 1

            fig_timeline = px.bar(
                x=list(date_counts.keys()),
                y=list(date_counts.values()),
                title="Facturas por Fecha"
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

# ========================
# APLICACIÓN PRINCIPAL
# ========================

def main():
    """Función principal de la aplicación"""

    # Inicializar estado
    init_session_state()

    # Renderizar sidebar
    render_sidebar()

    # Título principal
    st.title("📋 Sistema de Revisión Manual - Facturas AFIP")
    st.markdown("#### 🇦🇷 Procesamiento OCR y Validación para Retail Argentino")

    # Pestañas principales
    tab1, tab2, tab3 = st.tabs(["📤 Subir y Procesar", "📋 Revisar Facturas", "📊 Analytics"])

    with tab1:
        render_file_uploader()

    with tab2:
        render_invoice_list()

    with tab3:
        render_analytics_dashboard()

    # Footer
    st.markdown("---")
    st.markdown(
        "🏪 **Sistema Multi-Agente Inventario Argentina** | "
        "🤖 Powered by FastAPI + Streamlit | "
        "🔮 ML Demand Prediction"
    )

if __name__ == "__main__":
    main()
