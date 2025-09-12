# Guía de Configuración AFIP - Sistema de Inventario Argentino

## Introducción

Esta guía te ayudará a configurar la integración con AFIP para facturación electrónica en el sistema de inventario. La integración permite generar y validar Códigos de Autorización Electrónica (CAE) de forma automática.

## Prerrequisitos

### 1. Requisitos AFIP
- Estar inscripto en AFIP como Responsable Inscripto
- Tener habilitado el servicio de Facturación Electrónica
- Contar con Clave Fiscal nivel 3 o superior
- Tener autorizado al menos un punto de venta para facturación electrónica

### 2. Requisitos Técnicos
- Python 3.8 o superior
- Acceso a internet para conectar con servicios AFIP
- Certificado digital de AFIP

## Paso 1: Generar Certificado Digital en AFIP

### 1.1 Acceder a AFIP
1. Ingresa a [AFIP](https://www.afip.gob.ar)
2. Selecciona "AFIP Web" → "Administrador de Relaciones de Clave Fiscal"
3. Ingresa con tu Clave Fiscal

### 1.2 Generar Certificado
1. Ve a "Certificados" → "Generar Certificado"
2. Completa los datos:
   - **Alias**: Nombre descriptivo (ej: "Sistema Inventario")
   - **CUIT**: Tu CUIT empresa
   - **Denominación**: Razón social de tu empresa
   - **Vigencia**: Selecciona el período de vigencia

3. Genera el archivo de solicitud (.csr)
4. Descarga el certificado generado (.crt)

### 1.3 Convertir Certificado a PEM
El sistema requiere certificados en formato PEM. Si tu certificado está en otro formato:

```bash
# Crear directorio para certificados
mkdir -p certificates

# Convertir certificado a PEM (si es necesario)
openssl x509 -in afip_cert.crt -out certificates/afip_cert.pem -outform PEM

# Convertir clave privada a PEM (si es necesario)
openssl rsa -in afip_key.key -out certificates/afip_key.pem -outform PEM
```

### 1.4 Configurar Permisos
```bash
# Configurar permisos restrictivos para los certificados
chmod 600 certificates/afip_cert.pem
chmod 600 certificates/afip_key.pem
chown $(whoami):$(whoami) certificates/afip_*.pem
```

## Paso 2: Configurar Servicios AFIP

### 2.1 Habilitar Web Services
1. En AFIP, ve a "Administrador de Relaciones de Clave Fiscal"
2. Selecciona "Nueva Relación"
3. Busca y selecciona:
   - **ws_sr_constancia_inscripcion**: Consulta de padrón
   - **wsfe**: Facturación electrónica
   - **wsfev1**: Facturación electrónica versión 1

### 2.2 Autorizar Puntos de Venta
1. Ve a "ABM Puntos de Venta"
2. Crea o verifica tus puntos de venta
3. Anota los números de punto de venta autorizados

## Paso 3: Configurar el Sistema

### 3.1 Editar Configuración
Edita el archivo `.env.integrations`:

```bash
# Datos de tu empresa
AFIP_CUIT=20-12345678-9
AFIP_RAZON_SOCIAL=TU EMPRESA SA

# Ambiente (testing para pruebas, production para producción)
AFIP_AMBIENTE=testing

# Rutas a los certificados
AFIP_CERTIFICADO_PATH=certificates/afip_cert.pem
AFIP_CLAVE_PRIVADA_PATH=certificates/afip_key.pem

# Puntos de venta autorizados (separados por coma)
AFIP_PUNTOS_VENTA=1,2,3
```

### 3.2 Verificar Configuración
```bash
# Ejecutar test de conexión AFIP
python -c "
from integrations.afip.wsfe_client import AFIPWSFEClient, AFIPCredentials
import asyncio

async def test_afip():
    credentials = AFIPCredentials(
        cuit='20-12345678-9',  # Tu CUIT
        certificado_path='certificates/afip_cert.pem',
        clave_privada_path='certificates/afip_key.pem',
        ambiente='testing'
    )

    client = AFIPWSFEClient(credentials)

    try:
        # Test de autenticación
        result = await client.verificar_autenticacion()
        print('✅ Conexión AFIP exitosa:', result)

        # Test de puntos de venta
        puntos = await client.obtener_puntos_venta()
        print('✅ Puntos de venta:', puntos)

    except Exception as e:
        print('❌ Error de conexión:', str(e))

asyncio.run(test_afip())
"
```

## Paso 4: Testing en Ambiente de Homologación

### 4.1 Configurar Testing
```bash
# En .env.integrations, asegurar:
AFIP_AMBIENTE=testing
TESTING_MODE=true
```

### 4.2 Generar Factura de Prueba
```python
from integrations.afip.wsfe_client import FacturaElectronica
from datetime import datetime

# Crear factura de prueba
factura = FacturaElectronica(
    tipo_cbte=1,           # Factura A
    punto_vta=1,           # Tu punto de venta
    cbte_desde=1,          # Número de factura
    cbte_hasta=1,
    concepto=1,            # Productos
    doc_tipo=80,           # CUIT
    doc_nro=20123456789,   # CUIT cliente (sin guiones)
    fecha_cbte=datetime.now().date(),
    imp_total=1210.00,     # Total con IVA
    mon_id="PES",          # Pesos argentinos
    mon_cotiz=1.0
)

# Generar CAE
resultado = await client.generar_cae(factura)
print("CAE generado:", resultado)
```

## Paso 5: Configuración para Producción

### 5.1 Actualizar Ambiente
```bash
# En .env.integrations cambiar:
AFIP_AMBIENTE=production
TESTING_MODE=false
```

### 5.2 Certificado de Producción
1. Genera un nuevo certificado en AFIP para **producción**
2. Reemplaza los archivos en `certificates/`
3. Verifica permisos y configuración

### 5.3 Testing Final
```bash
# Ejecutar suite de tests completa
python -m pytest tests/test_afip_integration.py -v
```

## Troubleshooting

### Error: "Certificado inválido"
- Verificar que el certificado esté en formato PEM
- Comprobar que no haya expirado
- Verificar permisos de archivos (600)

### Error: "CUIT no autorizado"
- Verificar que el CUIT esté correctamente configurado
- Comprobar que tengas servicios AFIP habilitados
- Verificar que el certificado corresponda al CUIT

### Error: "Punto de venta no autorizado"
- Verificar puntos de venta en AFIP
- Comprobar configuración en `.env.integrations`
- Asegurar que estén habilitados para facturación electrónica

### Error: "Servicio no disponible"
- Verificar estado de servicios AFIP
- Comprobar conectividad a internet
- Revisar logs del sistema

## Logs y Monitoreo

### 5.1 Configurar Logs
```bash
# Crear directorio de logs
mkdir -p logs

# Configurar rotación de logs en /etc/logrotate.d/afip-integration
echo "logs/afip_integration.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 644 www-data www-data
}" | sudo tee /etc/logrotate.d/afip-integration
```

### 5.2 Monitorear Integración
```python
# Script de monitoreo
from schedulers.compliance_scheduler import crear_compliance_scheduler

scheduler = crear_compliance_scheduler(cuit_empresa="20-12345678-9")
estado = scheduler.obtener_estado_tareas()

print("Estado tareas AFIP:")
for tarea in estado:
    print(f"- {tarea['descripcion']}: {'✅' if tarea['activa'] else '❌'}")
```

## Mantenimiento

### Renovación de Certificados
- Los certificados AFIP vencen periódicamente
- Configurar alertas 30 días antes del vencimiento
- Proceso de renovación similar al inicial

### Backup de Configuración
```bash
# Backup de certificados y configuración
tar -czf afip_backup_$(date +%Y%m%d).tar.gz certificates/ .env.integrations
```

### Monitoreo de Salud
- Implementar health checks automáticos
- Configurar alertas por email/Slack
- Monitorear logs de errores

## Contacto y Soporte

### AFIP
- **Mesa de Ayuda**: 0800-999-2347
- **Web**: https://www.afip.gob.ar
- **Documentación**: https://www.afip.gob.ar/ws/

### Sistema
- Revisar logs en `logs/afip_integration.log`
- Usar ambiente de testing para debugging
- Consultar documentación de la API AFIP

---

**⚠️ Importante**: Siempre probar en ambiente de homologación antes de producción. Mantener certificados seguros y actualizados.
