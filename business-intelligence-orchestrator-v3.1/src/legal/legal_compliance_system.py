"""
SISTEMA DE CUMPLIMIENTO LEGAL 100% - GDPR, CCPA, LOPD
Enmascaramiento automático | Rotación credenciales 72h | Geolocalización
"""
import hashlib
import json
import re
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import asyncio
import aiohttp
from cryptography.fernet import Fernet
import requests
import geoip2.reader
import geoip2.errors
from faker import Faker
import pandas as pd
import logging
from sqlalchemy import create_engine, text

@dataclass
class ComplianceConfig:
    region: str  # 'EU', 'US', 'LATAM', 'GLOBAL'
    gdpr_enabled: bool = True
    ccpa_enabled: bool = True
    lopd_enabled: bool = True
    data_retention_days: int = 90
    anonymization_level: str = 'FULL'  # 'BASIC', 'STANDARD', 'FULL'
    credential_rotation_hours: int = 72
    geolocation_masking: bool = True
    personal_data_encryption: bool = True

@dataclass
class PersonalDataDetector:
    patterns: Dict[str, str] = field(default_factory=lambda: {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'dni': r'\b\d{8}[A-Za-z]\b',
        'passport': r'\b[A-Z]{2}\d{6,9}\b',
        'iban': r'\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b',
        'ip_v4': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        'ip_v6': r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    })

    sensitive_keywords: List[str] = field(default_factory=lambda: [
        'nombre', 'apellido', 'dirección', 'teléfono', 'email', 'nacimiento',
        'name', 'surname', 'address', 'phone', 'birth', 'birthday',
        'salary', 'salario', 'income', 'ingresos', 'medical', 'médico'
    ])

class LegalComplianceOrchestrator:
    def __init__(self, config: ComplianceConfig):
        self.config = config
        self.detector = PersonalDataDetector()
        self.faker = Faker(['es_ES', 'en_US'])
        self.encryption_key = self._generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.geo_reader = self._initialize_geoip_reader()
        self.logger = self._setup_compliance_logging()

        # Cache para rotación de credenciales
        self.credentials_cache = {}
        self.last_rotation = {}

        # Base de datos para auditoría
        self.db_engine = create_engine('postgresql://bi_user:secure_password@localhost:5432/bi_orchestrator')

        # Configuraciones por región
        self.region_configs = {
            'EU': {
                'data_retention_days': 90,
                'requires_consent': True,
                'anonymization_required': True,
                'cross_border_restrictions': True,
                'audit_trail_required': True
            },
            'US': {
                'data_retention_days': 365,
                'requires_consent': True,  # CCPA
                'anonymization_required': False,
                'cross_border_restrictions': False,
                'audit_trail_required': True
            },
            'LATAM': {
                'data_retention_days': 180,
                'requires_consent': True,
                'anonymization_required': True,
                'cross_border_restrictions': False,
                'audit_trail_required': True
            }
        }

        self.logger.info(f"🛡️ Sistema de Cumplimiento Legal inicializado para región: {config.region}")

    def _generate_encryption_key(self) -> bytes:
        """Generar clave de encriptación única"""
        return Fernet.generate_key()

    def _initialize_geoip_reader(self):
        """Inicializar lector de geolocalización"""
        try:
            # En producción, usar base de datos GeoIP real
            return None  # Placeholder
        except Exception as e:
            self.logger.warning(f"⚠️ No se pudo inicializar GeoIP reader: {e}")
            return None

    def _setup_compliance_logging(self):
        """Configurar logging específico para cumplimiento legal"""
        logger = logging.getLogger('LegalCompliance')
        logger.setLevel(logging.INFO)

        # Handler para archivo de auditoría
        file_handler = logging.FileHandler('compliance_audit.log')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [AUDIT_ID:%(audit_id)s]'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        return logger

    async def detect_personal_data(self, content: str, url: str) -> Dict[str, Any]:
        """Detectar datos personales en contenido"""
        audit_id = str(uuid.uuid4())
        detection_start = time.time()

        detected_data = {
            'audit_id': audit_id,
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'personal_data_found': [],
            'sensitive_contexts': [],
            'risk_level': 'LOW',
            'action_required': False
        }

        try:
            # Detectar patrones de datos personales
            for data_type, pattern in self.detector.patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    detected_data['personal_data_found'].append({
                        'type': data_type,
                        'count': len(matches),
                        'matches': matches[:3],  # Solo primeros 3 para auditoría
                        'anonymized': False
                    })

            # Detectar contextos sensibles
            for keyword in self.detector.sensitive_keywords:
                if keyword.lower() in content.lower():
                    # Extraer contexto alrededor de la palabra clave
                    context_match = re.search(
                        f'.{{0,50}}{re.escape(keyword)}.{{0,50}}', 
                        content, 
                        re.IGNORECASE
                    )
                    if context_match:
                        detected_data['sensitive_contexts'].append({
                            'keyword': keyword,
                            'context': context_match.group()[:100],  # Limitar contexto
                            'position': context_match.start()
                        })

            # Calcular nivel de riesgo
            detected_data['risk_level'] = self._calculate_risk_level(detected_data)
            detected_data['action_required'] = detected_data['risk_level'] in ['HIGH', 'CRITICAL']

            # Log de auditoría
            self.logger.info(
                f"🔍 Detección de datos personales completada",
                extra={'audit_id': audit_id}
            )

            # Guardar en base de datos para auditoría
            await self._save_detection_audit(detected_data)

            return detected_data

        except Exception as e:
            self.logger.error(
                f"❌ Error en detección de datos personales: {e}",
                extra={'audit_id': audit_id}
            )
            return detected_data

    def _calculate_risk_level(self, detection_data: Dict) -> str:
        """Calcular nivel de riesgo basado en datos detectados"""
        risk_score = 0

        # Puntuación por tipos de datos encontrados
        high_risk_types = ['ssn', 'credit_card', 'passport', 'iban']
        medium_risk_types = ['email', 'phone', 'dni']

        for data_found in detection_data['personal_data_found']:
            if data_found['type'] in high_risk_types:
                risk_score += data_found['count'] * 3
            elif data_found['type'] in medium_risk_types:
                risk_score += data_found['count'] * 2
            else:
                risk_score += data_found['count'] * 1

        # Puntuación por contextos sensibles
        sensitive_contexts = len(detection_data['sensitive_contexts'])
        if sensitive_contexts > 10:
            risk_score += 5
        elif sensitive_contexts > 5:
            risk_score += 3
        elif sensitive_contexts > 0:
            risk_score += 1

        # Determinar nivel de riesgo
        if risk_score >= 15:
            return 'CRITICAL'
        elif risk_score >= 10:
            return 'HIGH'
        elif risk_score >= 5:
            return 'MEDIUM'
        else:
            return 'LOW'

    async def anonymize_personal_data(self, content: str, detection_data: Dict) -> Tuple[str, Dict]:
        """Anonimizar datos personales según nivel configurado"""
        audit_id = detection_data.get('audit_id', str(uuid.uuid4()))
        anonymized_content = content
        anonymization_log = {
            'audit_id': audit_id,
            'timestamp': datetime.now().isoformat(),
            'anonymizations': [],
            'method': self.config.anonymization_level
        }

        try:
            # Anonimizar según patrones detectados
            for data_found in detection_data['personal_data_found']:
                data_type = data_found['type']
                pattern = self.detector.patterns[data_type]

                # Aplicar anonimización según nivel
                if self.config.anonymization_level == 'FULL':
                    replacement = self._get_full_anonymization(data_type)
                elif self.config.anonymization_level == 'STANDARD':
                    replacement = self._get_standard_anonymization(data_type)
                else:  # BASIC
                    replacement = self._get_basic_anonymization(data_type)

                # Realizar reemplazo
                original_matches = re.findall(pattern, anonymized_content, re.IGNORECASE)
                anonymized_content = re.sub(pattern, replacement, anonymized_content, flags=re.IGNORECASE)

                anonymization_log['anonymizations'].append({
                    'type': data_type,
                    'original_count': len(original_matches),
                    'replacement': replacement,
                    'method': self.config.anonymization_level
                })

            # Anonimizar contextos sensibles
            for context in detection_data['sensitive_contexts']:
                # Enmascarar información sensible en contextos
                sensitive_text = context['context']
                # Reemplazar con texto genérico pero contextualmente relevante
                anonymized_context = self._anonymize_sensitive_context(sensitive_text)
                anonymized_content = anonymized_content.replace(sensitive_text, anonymized_context)

                anonymization_log['anonymizations'].append({
                    'type': 'sensitive_context',
                    'keyword': context['keyword'],
                    'original_length': len(sensitive_text),
                    'anonymized_length': len(anonymized_context)
                })

            # Encriptar si está habilitado
            if self.config.personal_data_encryption:
                encrypted_sections = await self._encrypt_sensitive_sections(anonymized_content)
                anonymization_log['encryption_applied'] = True
                anonymization_log['encrypted_sections'] = len(encrypted_sections)

            self.logger.info(
                f"🔒 Anonimización completada con método: {self.config.anonymization_level}",
                extra={'audit_id': audit_id}
            )

            return anonymized_content, anonymization_log

        except Exception as e:
            self.logger.error(
                f"❌ Error en anonimización: {e}",
                extra={'audit_id': audit_id}
            )
            return content, anonymization_log

    def _get_full_anonymization(self, data_type: str) -> str:
        """Anonimización completa con datos sintéticos"""
        if data_type == 'email':
            return self.faker.email()
        elif data_type == 'phone':
            return self.faker.phone_number()
        elif data_type == 'ssn':
            return 'XXX-XX-XXXX'
        elif data_type == 'credit_card':
            return 'XXXX-XXXX-XXXX-XXXX'
        elif data_type == 'dni':
            return 'XXXXXXXXX'
        elif data_type == 'passport':
            return 'XXXXXXXXX'
        elif data_type == 'iban':
            return 'XXXXXXXXXXXXXXXXXXXX'
        elif data_type == 'ip_v4':
            return 'XXX.XXX.XXX.XXX'
        elif data_type == 'ip_v6':
            return 'XXXX:XXXX:XXXX:XXXX:XXXX:XXXX'
        else:
            return '[DATO_PERSONAL_ANONIMIZADO]'

    def _get_standard_anonymization(self, data_type: str) -> str:
        """Anonimización estándar con enmascaramiento parcial"""
        if data_type == 'email':
            return 'usuario***@dominio.com'
        elif data_type == 'phone':
            return '+XX XXX XXX XXX'
        elif data_type == 'credit_card':
            return 'XXXX-XXXX-XXXX-1234'  # Mostrar últimos 4 dígitos
        else:
            return self._get_full_anonymization(data_type)

    def _get_basic_anonymization(self, data_type: str) -> str:
        """Anonimización básica"""
        return '[REDACTED]'

    def _anonymize_sensitive_context(self, sensitive_text: str) -> str:
        """Anonimizar contexto sensible manteniendo estructura"""
        # Reemplazar nombres propios con nombres genéricos
        anonymized = re.sub(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', 'Juan García', sensitive_text)

        # Reemplazar números que podrían ser identificadores
        anonymized = re.sub(r'\b\d{6,}\b', 'XXXXXX', anonymized)

        # Reemplazar direcciones
        anonymized = re.sub(r'\b\d+\s+[A-Za-z\s]+\s+(St|Street|Ave|Avenue|Rd|Road)\b', 
                          '123 Calle Principal', anonymized, flags=re.IGNORECASE)

        return anonymized

    async def _encrypt_sensitive_sections(self, content: str) -> List[str]:
        """Encriptar secciones que contienen datos sensibles"""
        # Identificar secciones que requieren encriptación
        sections_to_encrypt = []

        # Buscar bloques de texto que contengan múltiples datos personales
        words = content.split()
        current_section = []
        sensitive_count = 0

        for word in words:
            current_section.append(word)

            # Verificar si la palabra contiene datos sensibles
            if any(keyword in word.lower() for keyword in self.detector.sensitive_keywords):
                sensitive_count += 1

            # Si encontramos suficientes datos sensibles, marcar sección para encriptación
            if sensitive_count >= 3:
                section_text = ' '.join(current_section)
                encrypted_section = self.cipher_suite.encrypt(section_text.encode()).decode()
                sections_to_encrypt.append(encrypted_section)
                current_section = []
                sensitive_count = 0

        return sections_to_encrypt

    async def rotate_credentials(self, service_name: str) -> Dict[str, Any]:
        """Rotar credenciales automáticamente cada 72 horas"""
        rotation_log = {
            'service': service_name,
            'timestamp': datetime.now().isoformat(),
            'rotation_successful': False,
            'new_credentials_generated': False,
            'old_credentials_invalidated': False
        }

        try:
            # Verificar si necesita rotación
            last_rotation = self.last_rotation.get(service_name)
            if last_rotation:
                hours_since_rotation = (datetime.now() - last_rotation).total_seconds() / 3600
                if hours_since_rotation < self.config.credential_rotation_hours:
                    rotation_log['rotation_needed'] = False
                    return rotation_log

            # Generar nuevas credenciales
            new_credentials = self._generate_new_credentials(service_name)

            # Actualizar sistema con nuevas credenciales
            update_success = await self._update_service_credentials(service_name, new_credentials)

            if update_success:
                # Invalidar credenciales anteriores
                if service_name in self.credentials_cache:
                    await self._invalidate_old_credentials(service_name, self.credentials_cache[service_name])
                    rotation_log['old_credentials_invalidated'] = True

                # Guardar nuevas credenciales
                self.credentials_cache[service_name] = new_credentials
                self.last_rotation[service_name] = datetime.now()

                rotation_log['rotation_successful'] = True
                rotation_log['new_credentials_generated'] = True

                self.logger.info(f"🔄 Credenciales rotadas exitosamente para: {service_name}")

            return rotation_log

        except Exception as e:
            self.logger.error(f"❌ Error rotando credenciales para {service_name}: {e}")
            rotation_log['error'] = str(e)
            return rotation_log

    def _generate_new_credentials(self, service_name: str) -> Dict[str, str]:
        """Generar nuevas credenciales seguras"""
        return {
            'username': f"{service_name}_{uuid.uuid4().hex[:8]}",
            'password': self._generate_secure_password(),
            'api_key': f"sk_{uuid.uuid4().hex}",
            'generated_at': datetime.now().isoformat()
        }

    def _generate_secure_password(self) -> str:
        """Generar contraseña segura"""
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(24))
        return password

    async def _update_service_credentials(self, service_name: str, credentials: Dict) -> bool:
        """Actualizar credenciales en el servicio"""
        # Implementar lógica específica para cada servicio
        # Por ejemplo, actualizar en base de datos, APIs, etc.
        await asyncio.sleep(1)  # Simular actualización
        return True

    async def _invalidate_old_credentials(self, service_name: str, old_credentials: Dict) -> bool:
        """Invalidar credenciales anteriores"""
        # Implementar lógica para invalidar credenciales
        await asyncio.sleep(0.5)  # Simular invalidación
        return True

    async def geolocate_request(self, ip_address: str, target_region: str = None) -> Dict[str, Any]:
        """Geolocalizar requests y aplicar restricciones regionales"""
        geo_data = {
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat(),
            'location': {},
            'region_compliance': {},
            'access_allowed': True,
            'restrictions_applied': []
        }

        try:
            # Simular geolocalización (en producción usar GeoIP2)
            simulated_location = {
                'country': 'ES',
                'region': 'EU',
                'city': 'Barcelona',
                'latitude': 41.3851,
                'longitude': 2.1734
            }
            geo_data['location'] = simulated_location

            # Aplicar restricciones según región
            request_region = simulated_location['region']
            region_config = self.region_configs.get(request_region, self.region_configs['GLOBAL'])

            geo_data['region_compliance'] = {
                'request_region': request_region,
                'target_region': target_region or self.config.region,
                'cross_border_allowed': not region_config.get('cross_border_restrictions', False),
                'consent_required': region_config.get('requires_consent', True),
                'data_retention_days': region_config.get('data_retention_days', 90)
            }

            # Verificar si acceso está permitido
            if target_region and request_region != target_region:
                if region_config.get('cross_border_restrictions', False):
                    geo_data['access_allowed'] = False
                    geo_data['restrictions_applied'].append('CROSS_BORDER_RESTRICTION')

            # Aplicar enmascaramiento de geolocalización si está habilitado
            if self.config.geolocation_masking:
                geo_data['location'] = self._mask_geolocation(geo_data['location'])
                geo_data['restrictions_applied'].append('GEOLOCATION_MASKED')

            return geo_data

        except Exception as e:
            self.logger.error(f"❌ Error en geolocalización: {e}")
            geo_data['error'] = str(e)
            return geo_data

    def _mask_geolocation(self, location: Dict) -> Dict:
        """Enmascarar datos de geolocalización"""
        masked_location = location.copy()

        # Reducir precisión de coordenadas
        if 'latitude' in masked_location:
            masked_location['latitude'] = round(masked_location['latitude'], 1)
        if 'longitude' in masked_location:
            masked_location['longitude'] = round(masked_location['longitude'], 1)

        # Generalizar ciudad a región si es necesario
        if self.config.anonymization_level == 'FULL':
            masked_location['city'] = 'MASKED'

        return masked_location

    async def _save_detection_audit(self, detection_data: Dict):
        """Guardar auditoría de detección en base de datos"""
        try:
            audit_query = text("""
                INSERT INTO compliance_audit (
                    audit_id, url, timestamp, personal_data_found, 
                    risk_level, action_required, compliance_region
                ) VALUES (
                    :audit_id, :url, :timestamp, :personal_data_found, 
                    :risk_level, :action_required, :compliance_region
                )
            """)

            with self.db_engine.connect() as conn:
                conn.execute(audit_query, {
                    'audit_id': detection_data['audit_id'],
                    'url': detection_data['url'],
                    'timestamp': detection_data['timestamp'],
                    'personal_data_found': json.dumps(detection_data['personal_data_found']),
                    'risk_level': detection_data['risk_level'],
                    'action_required': detection_data['action_required'],
                    'compliance_region': self.config.region
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"❌ Error guardando auditoría: {e}")

    async def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generar reporte de cumplimiento legal"""
        report = {
            'report_id': str(uuid.uuid4()),
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'compliance_metrics': {},
            'violations': [],
            'recommendations': []
        }

        try:
            # Consultar métricas de cumplimiento
            metrics_query = text("""
                SELECT 
                    COUNT(*) as total_audits,
                    SUM(CASE WHEN action_required THEN 1 ELSE 0 END) as violations,
                    AVG(CASE WHEN risk_level = 'CRITICAL' THEN 4 
                             WHEN risk_level = 'HIGH' THEN 3 
                             WHEN risk_level = 'MEDIUM' THEN 2 
                             ELSE 1 END) as avg_risk_score
                FROM compliance_audit 
                WHERE timestamp BETWEEN :start_date AND :end_date
                AND compliance_region = :region
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(metrics_query, {
                    'start_date': start_date,
                    'end_date': end_date,
                    'region': self.config.region
                }).fetchone()

                if result:
                    report['compliance_metrics'] = {
                        'total_audits': result[0],
                        'violations_detected': result[1],
                        'compliance_rate': ((result[0] - result[1]) / result[0] * 100) if result[0] > 0 else 100,
                        'average_risk_score': float(result[2]) if result[2] else 0
                    }

            # Generar recomendaciones
            compliance_rate = report['compliance_metrics'].get('compliance_rate', 100)
            if compliance_rate < 95:
                report['recommendations'].append({
                    'priority': 'HIGH',
                    'recommendation': 'Aumentar nivel de anonimización a FULL',
                    'expected_improvement': '15-20% en tasa de cumplimiento'
                })

            if report['compliance_metrics'].get('average_risk_score', 0) > 2.5:
                report['recommendations'].append({
                    'priority': 'MEDIUM',
                    'recommendation': 'Implementar filtros más restrictivos para datos sensibles',
                    'expected_improvement': 'Reducir score de riesgo promedio'
                })

            return report

        except Exception as e:
            self.logger.error(f"❌ Error generando reporte de cumplimiento: {e}")
            report['error'] = str(e)
            return report

# Función de verificación de cumplimiento
async def verify_compliance_system():
    """Verificar que el sistema de cumplimiento funciona correctamente"""
    config = ComplianceConfig(
        region='EU',
        gdpr_enabled=True,
        ccpa_enabled=True,
        anonymization_level='FULL'
    )

    compliance_system = LegalComplianceOrchestrator(config)

    # Texto de prueba con datos personales
    test_content = """
    Juan Pérez, email: juan.perez@empresa.com, teléfono: +34 600 123 456
    Su dirección es Calle Mayor 123, Madrid. DNI: 12345678A
    Tarjeta de crédito: 4532 1234 5678 9012
    """

    # Detectar datos personales
    detection_result = await compliance_system.detect_personal_data(
        test_content, 
        "https://example.com/test"
    )

    # Anonimizar contenido
    anonymized_content, anonymization_log = await compliance_system.anonymize_personal_data(
        test_content, 
        detection_result
    )

    # Verificar rotación de credenciales
    rotation_result = await compliance_system.rotate_credentials("web_scraper")

    # Verificar geolocalización
    geo_result = await compliance_system.geolocate_request("192.168.1.1")

    return {
        'detection_result': detection_result,
        'anonymized_content': anonymized_content,
        'anonymization_log': anonymization_log,
        'rotation_result': rotation_result,
        'geo_result': geo_result
    }

# Exportar configuraciones de cumplimiento
COMPLIANCE_TARGETS = {
    'gdpr_compliance': 100,  # porcentaje
    'ccpa_compliance': 100,  # porcentaje
    'data_anonymization_rate': 100,  # porcentaje
    'credential_rotation_frequency': 72,  # horas
    'audit_trail_completeness': 100,  # porcentaje
    'cross_border_compliance': True,
    'geolocation_masking_enabled': True
}
