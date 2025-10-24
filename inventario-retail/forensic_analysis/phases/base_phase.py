"""
Clase base abstracta para fases de análisis forense
Alineada 100% al repositorio real
"""
import sys
import os
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional

# ✅ Path-based import según convención del repositorio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

logger = logging.getLogger("forensic.base_phase")

class ForensicPhase(ABC):
    """
    Clase base abstracta para las 5 fases de análisis forense.
    
    Cada fase debe implementar:
    - validate_input(): Validar estructura de datos de entrada
    - execute(): Ejecutar lógica específica de la fase
    
    El método run() orquesta la ejecución con trazabilidad completa.
    """
    
    def __init__(self, phase_number: int, phase_name: str):
        """
        Args:
            phase_number: Número de fase (1-5)
            phase_name: Nombre descriptivo de la fase
        """
        self.phase_number = phase_number
        self.phase_name = phase_name
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.status: str = "pending"
    
    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Valida que el input tenga la estructura correcta para esta fase.
        
        Args:
            data: Diccionario con datos de entrada
            
        Returns:
            True si válido, False si inválido
            
        Raises:
            ValueError: Si faltan campos críticos
        """
        pass
    
    @abstractmethod
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la lógica principal de la fase.
        
        Args:
            data: Datos validados de entrada
            
        Returns:
            Diccionario con resultados de la fase
            
        Raises:
            Exception: Si la ejecución falla
        """
        pass
    
    def run(self, data: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """
        Ejecuta la fase completa con trazabilidad.
        
        Flujo:
        1. Registrar inicio
        2. Validar input
        3. Ejecutar lógica
        4. Agregar metadata estándar
        5. Registrar finalización
        
        Args:
            data: Datos de entrada
            execution_id: ID único de la ejecución (UUID)
            
        Returns:
            Diccionario con resultado + metadata
            
        Raises:
            ValueError: Si validación falla
            Exception: Si ejecución falla
        """
        self.start_time = datetime.utcnow()
        self.status = "running"
        
        logger.info(
            f"Phase {self.phase_number} starting: {self.phase_name} "
            f"execution_id={execution_id}"
        )
        
        try:
            # Validación de input
            if not self.validate_input(data):
                raise ValueError(f"Invalid input for Phase {self.phase_number}")
            
            # Ejecución de lógica
            result = self.execute(data)
            
            # Metadata estándar para trazabilidad
            result.update({
                "phase_number": self.phase_number,
                "phase_name": self.phase_name,
                "status": "success",
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "execution_id": execution_id
            })
            
            self.status = "success"
            self.end_time = datetime.utcnow()
            
            logger.info(
                f"Phase {self.phase_number} completed successfully: "
                f"execution_id={execution_id} "
                f"duration={(self.end_time - self.start_time).total_seconds():.2f}s"
            )
            
            return result
            
        except Exception as e:
            self.status = "failed"
            self.end_time = datetime.utcnow()
            
            logger.error(
                f"Phase {self.phase_number} failed: {e} "
                f"execution_id={execution_id}"
            )
            
            raise
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Retorna metadata de la fase.
        
        Returns:
            Diccionario con información de estado
        """
        return {
            "phase_number": self.phase_number,
            "phase_name": self.phase_name,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() 
                if self.start_time and self.end_time else None
        }
