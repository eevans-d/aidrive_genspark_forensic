"""
TAXONOMÍAS POR INDUSTRIA - ANÁLISIS DE SENTIMIENTOS ESPECIALIZADO
Automotriz | Hotelero | Salud | Agro - Clasificación automática de problemas críticos
"""
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
from textblob import TextBlob
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

@dataclass
class IndustryTaxonomy:
    industry_name: str
    critical_issues: List[str]
    positive_indicators: List[str]
    negative_indicators: List[str]
    sentiment_weights: Dict[str, float]
    keyword_patterns: Dict[str, List[str]]
    severity_levels: Dict[str, int]
    action_triggers: Dict[str, str]

class IndustryTaxonomyAnalyzer:
    def __init__(self):
        self.taxonomies = self._initialize_taxonomies()
        self.nlp_model = self._load_nlp_model()
        self.sentiment_analyzer = self._initialize_sentiment_analyzer()
        self.logger = self._setup_logging()

        # Vectorizador para análisis semántico
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='spanish',
            ngram_range=(1, 3)
        )

        # Métricas por industria
        self.industry_metrics = {}

        self.logger.info("🏭 Sistema de Taxonomías por Industria inicializado")

    def _initialize_taxonomies(self) -> Dict[str, IndustryTaxonomy]:
        """Inicializar taxonomías especializadas por industria"""
        return {
            'automotriz': IndustryTaxonomy(
                industry_name='Automotriz',
                critical_issues=[
                    'tiempos de espera', 'tiempo de espera', 'demora en servicio',
                    'financiación', 'financiamiento', 'crédito automotriz',
                    'garantía', 'warranty', 'defectos de fábrica',
                    'repuestos', 'spare parts', 'disponibilidad piezas',
                    'servicio técnico', 'taller', 'reparación',
                    'entrega tardía', 'delivery delay', 'retraso entrega'
                ],
                positive_indicators=[
                    'excelente servicio', 'atención rápida', 'profesional',
                    'buena financiación', 'fácil financiamiento', 'sin demoras',
                    'calidad superior', 'confiable', 'recomendado',
                    'buen precio', 'oferta competitiva', 'valor agregado'
                ],
                negative_indicators=[
                    'pésimo servicio', 'muy lento', 'deficiente',
                    'caro', 'sobreprecio', 'estafa',
                    'no recomiendo', 'evitar', 'problema grave',
                    'sin solución', 'ignoran cliente', 'mala experiencia'
                ],
                sentiment_weights={
                    'tiempos_espera': 3.5,  # Muy crítico para automotriz
                    'financiacion': 3.0,
                    'calidad_servicio': 2.8,
                    'garantia': 2.5,
                    'precio': 2.0
                },
                keyword_patterns={
                    'servicio_lento': [
                        r'esper[aeé] más de \d+ (horas?|días?|semanas?)',
                        r'(demora|tardanza|lentitud) en (el )?servicio',
                        r'taller (lento|demorado|ineficiente)'
                    ],
                    'problemas_financiacion': [
                        r'(rechaz[ao]|deneg[ao]) (el )?crédito',
                        r'financiación (negada|rechazada|difícil)',
                        r'no (aprueban|otorgan) (el )?préstamo'
                    ],
                    'defectos_producto': [
                        r'(falla|avería|defecto) de fábrica',
                        r'problema (mecánico|eléctrico|estructural)',
                        r'(no funciona|se rompió|se averió)'
                    ]
                },
                severity_levels={
                    'tiempos_espera': 4,
                    'financiacion': 3,
                    'defectos_producto': 5,
                    'servicio_lento': 3,
                    'precio_alto': 2
                },
                action_triggers={
                    'tiempos_espera': 'ESCALATE_CUSTOMER_SERVICE',
                    'defectos_producto': 'QUALITY_CONTROL_ALERT',
                    'financiacion': 'REVIEW_CREDIT_PROCESS',
                    'servicio_lento': 'TRAINING_REQUIRED'
                }
            ),

            'hotelero': IndustryTaxonomy(
                industry_name='Hotelero',
                critical_issues=[
                    'temporada alta', 'high season', 'peak season',
                    'calidad servicio', 'service quality', 'atención cliente',
                    'limpieza', 'cleanliness', 'higiene',
                    'ruido', 'noise', 'sonido molesto',
                    'reserva', 'booking', 'disponibilidad',
                    'precio temporada', 'seasonal pricing', 'tarifa alta'
                ],
                positive_indicators=[
                    'excelente ubicación', 'vista hermosa', 'limpio',
                    'personal amable', 'servicio impecable', 'recomendado',
                    'buena relación precio-calidad', 'cómodo', 'tranquilo',
                    'desayuno incluido', 'amenidades completas'
                ],
                negative_indicators=[
                    'sucio', 'ruidoso', 'caro para lo que ofrece',
                    'personal grosero', 'mala ubicación', 'no recomiendo',
                    'habitación pequeña', 'sin mantenimiento', 'obsoleto'
                ],
                sentiment_weights={
                    'temporada_alta': 4.0,  # Crítico para hotelería
                    'calidad_servicio': 3.5,
                    'limpieza': 3.8,
                    'ubicacion': 2.5,
                    'precio': 2.8
                },
                keyword_patterns={
                    'problemas_temporada_alta': [
                        r'temporada alta (caro|costoso|sobreprecio)',
                        r'no hay (disponibilidad|habitaciones) en (diciembre|enero|julio|agosto)',
                        r'precios (excesivos|abusivos) en (verano|invierno|fiestas)'
                    ],
                    'problemas_limpieza': [
                        r'habitación (sucia|mugrienta|mal olor)',
                        r'baño (sucio|sin limpiar|asqueroso)',
                        r'sábanas (sucias|manchadas|sin cambiar)'
                    ],
                    'servicio_deficiente': [
                        r'personal (grosero|maleducado|antipático)',
                        r'recepción (lenta|ineficiente|desorganizada)',
                        r'servicio (pésimo|terrible|inexistente)'
                    ]
                },
                severity_levels={
                    'temporada_alta': 3,
                    'limpieza': 5,
                    'servicio_deficiente': 4,
                    'ruido': 3,
                    'precio_alto': 2
                },
                action_triggers={
                    'limpieza': 'IMMEDIATE_HOUSEKEEPING_REVIEW',
                    'servicio_deficiente': 'STAFF_TRAINING_REQUIRED',
                    'temporada_alta': 'PRICING_STRATEGY_REVIEW',
                    'ruido': 'MAINTENANCE_CHECK_REQUIRED'
                }
            ),

            'salud': IndustryTaxonomy(
                industry_name='Salud',
                critical_issues=[
                    'tiempos espera', 'tiempo de espera', 'demora atención',
                    'atención médica', 'medical care', 'calidad atención',
                    'diagnóstico', 'diagnosis', 'tratamiento',
                    'emergencia', 'urgencia', 'emergency',
                    'costo tratamiento', 'precio consulta', 'cobertura',
                    'disponibilidad médico', 'horario atención'
                ],
                positive_indicators=[
                    'atención rápida', 'médico competente', 'diagnóstico certero',
                    'tratamiento efectivo', 'personal amable', 'instalaciones modernas',
                    'buen seguimiento', 'sin demoras', 'profesional',
                    'cobertura completa', 'precio justo'
                ],
                negative_indicators=[
                    'espera excesiva', 'mal diagnóstico', 'tratamiento inadecuado',
                    'médico incompetente', 'instalaciones deficientes', 'caro',
                    'sin seguimiento', 'emergencia mal atendida', 'negligencia'
                ],
                sentiment_weights={
                    'tiempos_espera': 4.5,  # Extremadamente crítico en salud
                    'atencion_medica': 5.0,  # Máxima prioridad
                    'emergencia': 5.0,
                    'diagnostico': 4.8,
                    'costo': 2.5
                },
                keyword_patterns={
                    'espera_excesiva': [
                        r'esper[aeé] (más de )?\d+ horas en (emergencia|urgencia)',
                        r'turno (demorado|tardío) (más de )?\d+ (días|semanas)',
                        r'espera (interminable|excesiva|inadmisible)'
                    ],
                    'atencion_deficiente': [
                        r'médico (incompetente|negligente|desinteresado)',
                        r'diagnóstico (erróneo|equivocado|tardío)',
                        r'tratamiento (inadecuado|ineficaz|contraproducente)'
                    ],
                    'emergencia_mal_atendida': [
                        r'emergencia (ignorada|desatendida|mal manejada)',
                        r'urgencia (no atendida|demorada|rechazada)',
                        r'(negaron|rechazaron) atención de emergencia'
                    ]
                },
                severity_levels={
                    'tiempos_espera': 4,
                    'atencion_deficiente': 5,
                    'emergencia_mal_atendida': 5,
                    'diagnostico_erroneo': 5,
                    'costo_alto': 2
                },
                action_triggers={
                    'tiempos_espera': 'PROCESS_OPTIMIZATION_URGENT',
                    'atencion_deficiente': 'MEDICAL_REVIEW_REQUIRED',
                    'emergencia_mal_atendida': 'ESCALATE_TO_ADMINISTRATION',
                    'diagnostico_erroneo': 'QUALITY_ASSURANCE_ALERT'
                }
            ),

            'agro': IndustryTaxonomy(
                industry_name='Agro',
                critical_issues=[
                    'precios commodities', 'commodity prices', 'precio soja',
                    'calidad', 'quality', 'calidad producto',
                    'logística', 'logistics', 'transporte',
                    'clima', 'weather', 'condiciones climáticas',
                    'plagas', 'pests', 'enfermedades cultivo',
                    'financiamiento agrícola', 'crédito rural'
                ],
                positive_indicators=[
                    'excelente cosecha', 'buenos precios', 'calidad premium',
                    'logística eficiente', 'transporte rápido', 'financiamiento accesible',
                    'clima favorable', 'sin plagas', 'rentable',
                    'mercado estable', 'demanda alta'
                ],
                negative_indicators=[
                    'precios bajos', 'mala cosecha', 'calidad inferior',
                    'logística deficiente', 'pérdidas transporte', 'sin financiamiento',
                    'sequía', 'inundaciones', 'plagas severas',
                    'mercado volátil', 'demanda baja'
                ],
                sentiment_weights={
                    'precios_commodities': 4.2,  # Crítico para agricultura
                    'calidad': 3.8,
                    'clima': 4.0,
                    'logistica': 3.2,
                    'plagas': 3.5
                },
                keyword_patterns={
                    'precios_bajos': [
                        r'precio (soja|maíz|trigo) (bajo|cayó|descendió)',
                        r'commodity (barato|depreciado|en baja)',
                        r'mercado (deprimido|a la baja|sin demanda)'
                    ],
                    'problemas_calidad': [
                        r'calidad (inferior|mala|deficiente)',
                        r'producto (rechazado|no aceptado|descalificado)',
                        r'estándar (no cumplido|inadecuado|insuficiente)'
                    ],
                    'problemas_climaticos': [
                        r'(sequía|seca) (severa|prolongada|extrema)',
                        r'(inundación|exceso lluvia|anegamiento)',
                        r'clima (adverso|desfavorable|extremo)'
                    ]
                },
                severity_levels={
                    'precios_bajos': 4,
                    'problemas_calidad': 3,
                    'problemas_climaticos': 5,
                    'plagas': 4,
                    'logistica_deficiente': 3
                },
                action_triggers={
                    'precios_bajos': 'MARKET_ANALYSIS_REQUIRED',
                    'problemas_calidad': 'QUALITY_CONTROL_REVIEW',
                    'problemas_climaticos': 'RISK_MANAGEMENT_ALERT',
                    'plagas': 'AGRONOMIC_INTERVENTION_NEEDED'
                }
            )
        }

    def _load_nlp_model(self):
        """Cargar modelo de NLP especializado"""
        try:
            # En producción, usar modelo específico para español
            return spacy.load("es_core_news_sm")
        except:
            self.logger.warning("⚠️ Modelo spaCy no encontrado, usando análisis básico")
            return None

    def _initialize_sentiment_analyzer(self):
        """Inicializar analizador de sentimientos especializado"""
        try:
            # Usar modelo pre-entrenado para español
            return pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
        except:
            self.logger.warning("⚠️ Modelo transformers no disponible, usando TextBlob")
            return None

    def _setup_logging(self):
        """Configurar logging para taxonomías"""
        logger = logging.getLogger('IndustryTaxonomies')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def analyze_industry_sentiment(self, text: str, industry: str) -> Dict[str, Any]:
        """Análisis de sentimiento especializado por industria"""
        if industry not in self.taxonomies:
            raise ValueError(f"Industria '{industry}' no soportada")

        taxonomy = self.taxonomies[industry]

        analysis_result = {
            'industry': industry,
            'timestamp': datetime.now().isoformat(),
            'text_analyzed': text[:200] + "..." if len(text) > 200 else text,
            'critical_issues_detected': [],
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'severity_level': 0,
            'recommended_actions': [],
            'industry_specific_metrics': {}
        }

        try:
            # 1. Detección de problemas críticos específicos de la industria
            critical_issues = await self._detect_critical_issues(text, taxonomy)
            analysis_result['critical_issues_detected'] = critical_issues

            # 2. Análisis de sentimiento con pesos específicos de la industria
            sentiment_analysis = await self._weighted_sentiment_analysis(text, taxonomy)
            analysis_result.update(sentiment_analysis)

            # 3. Análisis semántico con patrones específicos
            semantic_analysis = await self._semantic_pattern_analysis(text, taxonomy)
            analysis_result['semantic_matches'] = semantic_analysis

            # 4. Calcular nivel de severidad
            severity = self._calculate_industry_severity(critical_issues, sentiment_analysis, taxonomy)
            analysis_result['severity_level'] = severity

            # 5. Generar recomendaciones de acción
            recommendations = self._generate_action_recommendations(
                critical_issues, severity, taxonomy
            )
            analysis_result['recommended_actions'] = recommendations

            # 6. Métricas específicas de la industria
            industry_metrics = await self._calculate_industry_metrics(
                text, critical_issues, taxonomy
            )
            analysis_result['industry_specific_metrics'] = industry_metrics

            self.logger.info(f"✅ Análisis completado para industria: {industry}")

            return analysis_result

        except Exception as e:
            self.logger.error(f"❌ Error en análisis de industria {industry}: {e}")
            analysis_result['error'] = str(e)
            return analysis_result

    async def _detect_critical_issues(self, text: str, taxonomy: IndustryTaxonomy) -> List[Dict]:
        """Detectar problemas críticos específicos de la industria"""
        detected_issues = []
        text_lower = text.lower()

        # Buscar problemas críticos usando palabras clave
        for issue in taxonomy.critical_issues:
            if issue.lower() in text_lower:
                # Extraer contexto alrededor del problema
                context = self._extract_context(text, issue)
                severity = taxonomy.severity_levels.get(
                    issue.replace(' ', '_').replace('ó', 'o'), 3
                )

                detected_issues.append({
                    'issue_type': issue,
                    'context': context,
                    'severity': severity,
                    'confidence': self._calculate_issue_confidence(text, issue),
                    'weight': taxonomy.sentiment_weights.get(
                        issue.replace(' ', '_').replace('ó', 'o'), 1.0
                    )
                })

        # Buscar patrones específicos usando regex
        for pattern_name, patterns in taxonomy.keyword_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    detected_issues.append({
                        'issue_type': pattern_name,
                        'context': match.group(),
                        'severity': taxonomy.severity_levels.get(pattern_name, 3),
                        'confidence': 0.9,  # Alta confianza para patrones regex
                        'weight': taxonomy.sentiment_weights.get(pattern_name, 1.0)
                    })

        return detected_issues

    def _extract_context(self, text: str, keyword: str, context_size: int = 100) -> str:
        """Extraer contexto alrededor de una palabra clave"""
        keyword_pos = text.lower().find(keyword.lower())
        if keyword_pos == -1:
            return ""

        start = max(0, keyword_pos - context_size)
        end = min(len(text), keyword_pos + len(keyword) + context_size)

        return text[start:end].strip()

    def _calculate_issue_confidence(self, text: str, issue: str) -> float:
        """Calcular confianza de detección de un problema"""
        # Factores que aumentan la confianza:
        # 1. Múltiples menciones del problema
        # 2. Palabras de refuerzo negativo cerca
        # 3. Contexto específico de la industria

        issue_mentions = text.lower().count(issue.lower())
        confidence = min(0.3 + (issue_mentions * 0.2), 0.9)

        # Buscar palabras de refuerzo negativo
        negative_reinforcers = [
            'muy', 'extremadamente', 'terriblemente', 'pésimo', 'grave',
            'serio', 'crítico', 'urgente', 'inaceptable'
        ]

        context = self._extract_context(text, issue)
        for reinforcer in negative_reinforcers:
            if reinforcer in context.lower():
                confidence += 0.1

        return min(confidence, 1.0)

    async def _weighted_sentiment_analysis(self, text: str, taxonomy: IndustryTaxonomy) -> Dict:
        """Análisis de sentimiento con pesos específicos de la industria"""
        # Análisis base con TextBlob
        blob = TextBlob(text)
        base_sentiment = blob.sentiment

        sentiment_result = {
            'base_polarity': base_sentiment.polarity,
            'base_subjectivity': base_sentiment.subjectivity,
            'weighted_sentiment': 0.0,
            'industry_adjusted_score': 0.0,
            'confidence': 0.0
        }

        # Si tenemos modelo transformers, usarlo también
        if self.sentiment_analyzer:
            try:
                transformer_result = self.sentiment_analyzer(text[:512])  # Límite de tokens
                sentiment_result['transformer_sentiment'] = transformer_result[0]
            except:
                self.logger.warning("⚠️ Error en análisis con transformers")

        # Ajustar sentimiento según indicadores específicos de la industria
        industry_adjustment = 0.0

        # Buscar indicadores positivos
        for positive in taxonomy.positive_indicators:
            if positive.lower() in text.lower():
                industry_adjustment += 0.2

        # Buscar indicadores negativos (más peso)
        for negative in taxonomy.negative_indicators:
            if negative.lower() in text.lower():
                industry_adjustment -= 0.3

        # Aplicar pesos de la industria
        weighted_sentiment = base_sentiment.polarity + industry_adjustment
        weighted_sentiment = max(-1.0, min(1.0, weighted_sentiment))  # Mantener en rango [-1, 1]

        sentiment_result['weighted_sentiment'] = weighted_sentiment
        sentiment_result['industry_adjustment'] = industry_adjustment
        sentiment_result['confidence'] = (base_sentiment.subjectivity + 0.5) / 1.5

        return sentiment_result

    async def _semantic_pattern_analysis(self, text: str, taxonomy: IndustryTaxonomy) -> List[Dict]:
        """Análisis semántico con patrones específicos de la industria"""
        semantic_matches = []

        # Si tenemos modelo NLP, usar análisis más avanzado
        if self.nlp_model:
            doc = self.nlp_model(text)

            # Extraer entidades relevantes
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'EVENT', 'MONEY']:
                    semantic_matches.append({
                        'entity': ent.text,
                        'label': ent.label_,
                        'confidence': 0.8,
                        'context_relevant': self._is_context_relevant(
                            ent.text, taxonomy
                        )
                    })

        # Análisis de co-ocurrencia de términos críticos
        critical_terms = taxonomy.critical_issues + taxonomy.negative_indicators
        for i, term1 in enumerate(critical_terms):
            for term2 in critical_terms[i+1:]:
                if (term1.lower() in text.lower() and 
                    term2.lower() in text.lower()):

                    # Calcular distancia entre términos
                    pos1 = text.lower().find(term1.lower())
                    pos2 = text.lower().find(term2.lower())
                    distance = abs(pos1 - pos2)

                    if distance < 200:  # Términos cercanos
                        semantic_matches.append({
                            'pattern': f"{term1} + {term2}",
                            'distance': distance,
                            'confidence': max(0.3, 1.0 - (distance / 200)),
                            'severity_multiplier': 1.5
                        })

        return semantic_matches

    def _is_context_relevant(self, entity: str, taxonomy: IndustryTaxonomy) -> bool:
        """Verificar si una entidad es relevante para la industria"""
        industry_terms = (
            taxonomy.critical_issues + 
            taxonomy.positive_indicators + 
            taxonomy.negative_indicators
        )

        for term in industry_terms:
            if (entity.lower() in term.lower() or 
                term.lower() in entity.lower()):
                return True

        return False

    def _calculate_industry_severity(self, critical_issues: List[Dict], 
                                   sentiment_analysis: Dict, 
                                   taxonomy: IndustryTaxonomy) -> int:
        """Calcular nivel de severidad específico de la industria"""
        base_severity = 0

        # Severidad basada en problemas críticos detectados
        for issue in critical_issues:
            base_severity += issue['severity'] * issue['weight']

        # Ajuste por sentimiento
        sentiment_score = sentiment_analysis['weighted_sentiment']
        if sentiment_score < -0.7:
            base_severity += 2
        elif sentiment_score < -0.3:
            base_severity += 1
        elif sentiment_score > 0.3:
            base_severity = max(0, base_severity - 1)

        # Normalizar a escala 1-5
        normalized_severity = min(5, max(1, int(base_severity / 2) + 1))

        return normalized_severity

    def _generate_action_recommendations(self, critical_issues: List[Dict], 
                                       severity: int, 
                                       taxonomy: IndustryTaxonomy) -> List[Dict]:
        """Generar recomendaciones de acción específicas"""
        recommendations = []

        # Recomendaciones basadas en problemas específicos detectados
        for issue in critical_issues:
            issue_key = issue['issue_type'].replace(' ', '_').replace('ó', 'o')
            if issue_key in taxonomy.action_triggers:
                recommendations.append({
                    'action': taxonomy.action_triggers[issue_key],
                    'priority': 'HIGH' if issue['severity'] >= 4 else 'MEDIUM',
                    'reason': f"Detected: {issue['issue_type']}",
                    'context': issue['context'][:100]
                })

        # Recomendaciones basadas en severidad general
        if severity >= 4:
            recommendations.append({
                'action': 'IMMEDIATE_ESCALATION',
                'priority': 'CRITICAL',
                'reason': f'High severity level: {severity}',
                'context': f'Industry: {taxonomy.industry_name}'
            })
        elif severity == 3:
            recommendations.append({
                'action': 'DETAILED_INVESTIGATION',
                'priority': 'HIGH',
                'reason': f'Moderate severity level: {severity}',
                'context': f'Industry: {taxonomy.industry_name}'
            })

        return recommendations

    async def _calculate_industry_metrics(self, text: str, critical_issues: List[Dict], 
                                        taxonomy: IndustryTaxonomy) -> Dict:
        """Calcular métricas específicas de la industria"""
        metrics = {
            'industry_name': taxonomy.industry_name,
            'total_critical_issues': len(critical_issues),
            'issue_breakdown': {},
            'sentiment_distribution': {},
            'risk_score': 0.0
        }

        # Desglose por tipo de problema
        for issue in critical_issues:
            issue_type = issue['issue_type']
            if issue_type not in metrics['issue_breakdown']:
                metrics['issue_breakdown'][issue_type] = 0
            metrics['issue_breakdown'][issue_type] += 1

        # Calcular score de riesgo específico de la industria
        risk_score = 0.0
        for issue in critical_issues:
            risk_score += issue['severity'] * issue['weight'] * issue['confidence']

        metrics['risk_score'] = min(10.0, risk_score / max(1, len(critical_issues)))

        # Métricas específicas por industria
        if taxonomy.industry_name == 'Automotriz':
            metrics['waiting_time_mentions'] = len([
                i for i in critical_issues 
                if 'tiempo' in i['issue_type'].lower()
            ])
            metrics['financing_issues'] = len([
                i for i in critical_issues 
                if 'financ' in i['issue_type'].lower()
            ])

        elif taxonomy.industry_name == 'Hotelero':
            metrics['seasonal_issues'] = len([
                i for i in critical_issues 
                if 'temporada' in i['issue_type'].lower()
            ])
            metrics['cleanliness_issues'] = len([
                i for i in critical_issues 
                if 'limpieza' in i['issue_type'].lower()
            ])

        elif taxonomy.industry_name == 'Salud':
            metrics['waiting_time_critical'] = len([
                i for i in critical_issues 
                if 'espera' in i['issue_type'].lower() and i['severity'] >= 4
            ])
            metrics['medical_care_issues'] = len([
                i for i in critical_issues 
                if 'atención' in i['issue_type'].lower()
            ])

        elif taxonomy.industry_name == 'Agro':
            metrics['price_related_issues'] = len([
                i for i in critical_issues 
                if 'precio' in i['issue_type'].lower()
            ])
            metrics['climate_issues'] = len([
                i for i in critical_issues 
                if 'clima' in i['issue_type'].lower()
            ])

        return metrics

    async def verify_taxonomy_example(self, industry: str, test_text: str) -> Dict[str, Any]:
        """Verificar taxonomía con ejemplo específico"""
        if industry not in self.taxonomies:
            return {'error': f'Industria {industry} no encontrada'}

        # Analizar el texto de ejemplo
        analysis = await self.analyze_industry_sentiment(test_text, industry)

        # Verificar que se detectaron los elementos esperados
        verification = {
            'industry': industry,
            'test_text': test_text,
            'analysis_result': analysis,
            'verification_passed': False,
            'expected_detections': [],
            'actual_detections': analysis['critical_issues_detected']
        }

        # Definir detecciones esperadas por industria
        expected_by_industry = {
            'automotriz': ['tiempos', 'espera', 'financiación'],
            'hotelero': ['temporada', 'servicio', 'calidad'],
            'salud': ['espera', 'atención', 'médica'],
            'agro': ['precio', 'calidad', 'commodities']
        }

        expected = expected_by_industry.get(industry, [])
        verification['expected_detections'] = expected

        # Verificar si se detectaron los elementos esperados
        detected_terms = [issue['issue_type'].lower() for issue in analysis['critical_issues_detected']]
        detections_found = sum(1 for exp in expected if any(exp in det for det in detected_terms))

        verification['verification_passed'] = detections_found >= len(expected) * 0.5
        verification['detection_rate'] = detections_found / len(expected) if expected else 1.0

        return verification

# Ejemplos de verificación por industria
INDUSTRY_TEST_EXAMPLES = {
    'automotriz': """
    Los tiempos de espera en el taller son demasiado largos, llevo 3 semanas esperando 
    que arreglen mi auto. Además, me rechazaron la financiación sin explicación clara. 
    El servicio técnico es muy deficiente y no dan soluciones concretas.
    """,

    'hotelero': """
    El hotel en temporada alta es carísimo para lo que ofrece. La habitación estaba sucia, 
    el personal de recepción fue grosero y había mucho ruido toda la noche. 
    La calidad del servicio no justifica el precio que cobran en verano.
    """,

    'salud': """
    Esperé más de 6 horas en emergencia para que me atendieran. El médico parecía 
    desinteresado y el diagnóstico fue superficial. La atención médica en este 
    hospital deja mucho que desear, especialmente en situaciones de urgencia.
    """,

    'agro': """
    Los precios de la soja están por el piso este año, la calidad del producto 
    no está siendo bien reconocida en el mercado. Los commodities agrícolas 
    enfrentan una crisis debido al clima adverso y la logística deficiente.
    """
}

# Función de verificación completa
async def verify_all_taxonomies():
    """Verificar todas las taxonomías con ejemplos"""
    analyzer = IndustryTaxonomyAnalyzer()
    results = {}

    for industry, test_text in INDUSTRY_TEST_EXAMPLES.items():
        print(f"\n🔍 Verificando taxonomía para: {industry.upper()}")
        result = await analyzer.verify_taxonomy_example(industry, test_text)
        results[industry] = result

        print(f"✅ Detecciones encontradas: {len(result['actual_detections'])}")
        print(f"📊 Tasa de detección: {result['detection_rate']:.1%}")
        print(f"🎯 Verificación pasó: {'SÍ' if result['verification_passed'] else 'NO'}")

    return results
