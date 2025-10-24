"""
Orquestador de análisis forense con 5 fases
Ejecuta pipeline completo con trazabilidad
"""
import sys
import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from importlib import import_module

# ✅ Path-based import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Dynamic imports para manejar hyphen en 'inventario-retail'
_phase1_mod = import_module('inventario-retail.forensic_analysis.phases.phase_1_data_validation')
Phase1DataValidation = _phase1_mod.Phase1DataValidation

_phase2_mod = import_module('inventario-retail.forensic_analysis.phases.phase_2_consistency_check')
Phase2ConsistencyCheck = _phase2_mod.Phase2ConsistencyCheck

_phase3_mod = import_module('inventario-retail.forensic_analysis.phases.phase_3_pattern_analysis')
Phase3PatternAnalysis = _phase3_mod.Phase3PatternAnalysis

_phase4_mod = import_module('inventario-retail.forensic_analysis.phases.phase_4_performance_metrics')
Phase4PerformanceMetrics = _phase4_mod.Phase4PerformanceMetrics

_phase5_mod = import_module('inventario-retail.forensic_analysis.phases.phase_5_reporting')
Phase5Reporting = _phase5_mod.Phase5Reporting

logger = logging.getLogger("forensic.orchestrator")

class ForensicOrchestrator:
    """
    Orquestador principal del análisis forense.
    
    Responsabilidades:
    - Ejecutar las 5 fases secuencialmente
    - Propagar resultados entre fases
    - Gestionar errores y rollback
    - Generar reporte ejecutivo completo
    
    Fases Implementadas (v1.0 MVP):
    1. Data Validation - Validación de estructura y valores
    2. Consistency Check - Integridad referencial
    3. Pattern Analysis - Detección de anomalías y patrones
    4. Performance Metrics - Análisis de KPIs y bottlenecks
    5. Reporting - Consolidación y reportes ejecutivos
    """
    
    def __init__(self):
        """
        Inicializa orquestador con todas las 5 fases.
        
        v1.0: Phases 1-5 complete implementation
        """
        self.phases = [
            Phase1DataValidation(),
            Phase2ConsistencyCheck(),
            Phase3PatternAnalysis(),
            Phase4PerformanceMetrics(),
            Phase5Reporting()
        ]
        
        logger.info(f"ForensicOrchestrator initialized with {len(self.phases)} phase(s)")
    
    def run_analysis(
        self, 
        input_data: Dict[str, Any], 
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta pipeline completo de análisis forense.
        
        Args:
            input_data: Datos de entrada con inventory_data y transaction_data
            execution_id: ID único (UUID). Si None, se genera automáticamente
            
        Returns:
            Reporte completo con:
            - execution_id: UUID de la ejecución
            - start_time: Timestamp inicio
            - end_time: Timestamp finalización
            - total_duration_seconds: Duración total
            - phases: Lista de resultados de cada fase
            - overall_status: "success" | "failed"
            - summary: Resumen ejecutivo
            - failure_phase: (opcional) Número de fase que falló
            - failure_reason: (opcional) Razón del fallo
            
        Raises:
            No lanza excepciones. Errores capturados en el reporte.
        """
        execution_id = execution_id or str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(
            f"Starting forensic analysis: execution_id={execution_id} "
            f"phases_count={len(self.phases)}"
        )
        
        # Estructura base del reporte
        report = {
            "execution_id": execution_id,
            "start_time": start_time.isoformat(),
            "phases": [],
            "overall_status": "success"
        }
        
        # Ejecutar fases secuencialmente
        phase_data = input_data.copy()
        
        for phase in self.phases:
            try:
                logger.info(
                    f"Executing Phase {phase.phase_number}: {phase.phase_name} "
                    f"execution_id={execution_id}"
                )
                
                # Ejecutar fase
                result = phase.run(phase_data, execution_id)
                report["phases"].append(result)
                
                # Propagar resultado a siguiente fase
                phase_data["previous_phase_result"] = result
                
                logger.info(
                    f"Phase {phase.phase_number} completed: "
                    f"status={result.get('status')} "
                    f"execution_id={execution_id}"
                )
                
            except Exception as e:
                logger.error(
                    f"Phase {phase.phase_number} failed: {e} "
                    f"execution_id={execution_id}",
                    exc_info=True
                )
                
                # Marcar como fallido y detener pipeline
                report["overall_status"] = "failed"
                report["failure_phase"] = phase.phase_number
                report["failure_reason"] = str(e)
                
                # Agregar metadata de fase fallida
                report["phases"].append({
                    "phase_number": phase.phase_number,
                    "phase_name": phase.phase_name,
                    "status": "failed",
                    "error": str(e),
                    "execution_id": execution_id
                })
                
                break  # Detener ejecución de fases restantes
        
        # Finalizar reporte
        end_time = datetime.utcnow()
        report["end_time"] = end_time.isoformat()
        report["total_duration_seconds"] = round(
            (end_time - start_time).total_seconds(), 2
        )
        report["summary"] = self._generate_summary(report)
        
        logger.info(
            f"Analysis completed: execution_id={execution_id} "
            f"status={report['overall_status']} "
            f"duration={report['total_duration_seconds']}s"
        )
        
        return report
    
    def _generate_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera resumen ejecutivo del análisis.
        
        Args:
            report: Reporte completo
            
        Returns:
            Diccionario con métricas clave
        """
        total_phases = len(self.phases)
        completed_phases = len([
            p for p in report["phases"] 
            if p.get("status") == "success"
        ])
        
        success_rate = round(
            (completed_phases / total_phases * 100) if total_phases > 0 else 0, 
            2
        )
        
        summary = {
            "total_phases": total_phases,
            "completed_phases": completed_phases,
            "failed_phases": total_phases - completed_phases,
            "success_rate": success_rate,
            "execution_id": report["execution_id"],
            "overall_status": report["overall_status"]
        }
        
        # Agregar métricas específicas de Phase 1 si está disponible
        phase_1_result = next(
            (p for p in report["phases"] if p.get("phase_number") == 1), 
            None
        )
        
        if phase_1_result and phase_1_result.get("status") == "success":
            summary["data_quality_score"] = phase_1_result.get("data_quality_score", 0.0)
            summary["validation_warnings"] = len(phase_1_result.get("warnings", []))
            summary["validation_errors"] = len(phase_1_result.get("errors", []))
        
        return summary
    
    def get_phase_count(self) -> int:
        """Retorna número de fases configuradas"""
        return len(self.phases)
    
    def get_phases_info(self) -> List[Dict[str, Any]]:
        """
        Retorna información de todas las fases.
        
        Returns:
            Lista con metadata de cada fase
        """
        return [
            {
                "phase_number": phase.phase_number,
                "phase_name": phase.phase_name,
                "status": phase.status
            }
            for phase in self.phases
        ]
