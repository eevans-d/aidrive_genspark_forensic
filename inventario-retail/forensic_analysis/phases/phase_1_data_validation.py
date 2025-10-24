"""
Fase 1: Validación exhaustiva de datos
Valida integridad y consistencia de inventario y transacciones
"""
import sys
import os
from typing import Dict, Any, List
import logging
from importlib import import_module

# ✅ Path-based import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

_base_mod = import_module('inventario-retail.forensic_analysis.phases.base_phase')
ForensicPhase = _base_mod.ForensicPhase

logger = logging.getLogger("forensic.phase1")

class Phase1DataValidation(ForensicPhase):
    """
    Fase 1: Validación de Datos
    
    Responsabilidades:
    - Validar estructura de datos de inventario
    - Verificar integridad de transacciones
    - Calcular data quality score
    - Generar warnings y errors categorizados
    
    Input esperado:
    {
        "inventory_data": dict,  # SKU -> {quantity, price, ...}
        "transaction_data": list  # [{sku, quantity, type, ...}]
    }
    
    Output:
    {
        "validation_checks": list,  # Checks realizados
        "warnings": list,           # Advertencias no críticas
        "errors": list,             # Errores críticos
        "data_quality_score": float # Score 0-100
    }
    """
    
    def __init__(self):
        super().__init__(1, "Data Validation")
        self.min_quality_score = 50.0  # Score mínimo aceptable
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Valida que existan campos requeridos.
        
        Args:
            data: Input data con inventory_data y transaction_data
            
        Returns:
            True si tiene estructura mínima
        """
        required = ["inventory_data", "transaction_data"]
        has_required = all(field in data for field in required)
        
        if not has_required:
            logger.warning(f"Missing required fields. Expected: {required}")
        
        return has_required
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta validaciones completas de datos.
        
        Args:
            data: Input data validado
            
        Returns:
            Resultado con checks, warnings, errors, score
        """
        result = {
            "validation_checks": [],
            "warnings": [],
            "errors": [],
            "data_quality_score": 0.0
        }
        
        # 1. Validar inventario
        inventory = data.get("inventory_data", {})
        self._validate_inventory(inventory, result)
        
        # 2. Validar transacciones
        transactions = data.get("transaction_data", [])
        self._validate_transactions(transactions, result)
        
        # 3. Validar consistencia cross-referencial
        self._validate_consistency(inventory, transactions, result)
        
        # 4. Calcular score final
        result["data_quality_score"] = self._calculate_quality_score(result)
        
        # 5. Log resultado
        logger.info(
            f"Phase 1 validation completed: "
            f"checks={len(result['validation_checks'])} "
            f"warnings={len(result['warnings'])} "
            f"errors={len(result['errors'])} "
            f"score={result['data_quality_score']:.2f}"
        )
        
        return result
    
    def _validate_inventory(self, inventory: Dict[str, Any], result: Dict[str, Any]):
        """Valida estructura y contenido del inventario"""
        
        # Check 1: Inventario no vacío
        if not inventory:
            result["errors"].append("Inventory data is empty")
            result["validation_checks"].append({
                "check": "inventory_not_empty",
                "status": "failed",
                "severity": "critical",
                "message": "No inventory data provided"
            })
            return
        
        result["validation_checks"].append({
            "check": "inventory_not_empty",
            "status": "passed",
            "severity": "info",
            "message": f"{len(inventory)} items found"
        })
        
        # Check 2: Estructura de items
        valid_items = 0
        invalid_items = []
        
        for sku, item in inventory.items():
            if self._validate_inventory_item(sku, item):
                valid_items += 1
            else:
                invalid_items.append(sku)
                result["warnings"].append(f"Invalid inventory item: {sku}")
        
        validation_rate = (valid_items / len(inventory) * 100) if len(inventory) > 0 else 0
        
        result["validation_checks"].append({
            "check": "inventory_structure",
            "status": "passed" if valid_items > 0 else "failed",
            "severity": "high" if validation_rate < 80 else "info",
            "details": {
                "total_items": len(inventory),
                "valid_items": valid_items,
                "invalid_items": len(invalid_items),
                "validation_rate": round(validation_rate, 2)
            }
        })
        
        # Check 3: Valores negativos
        negative_quantities = sum(
            1 for item in inventory.values()
            if isinstance(item.get("quantity"), (int, float)) and item["quantity"] < 0
        )
        
        if negative_quantities > 0:
            result["warnings"].append(
                f"{negative_quantities} items with negative quantity"
            )
            result["validation_checks"].append({
                "check": "inventory_no_negatives",
                "status": "warning",
                "severity": "medium",
                "details": {"negative_count": negative_quantities}
            })
    
    def _validate_transactions(self, transactions: List[Dict[str, Any]], result: Dict[str, Any]):
        """Valida estructura y contenido de transacciones"""
        
        # Check 1: Transacciones existen
        if not transactions:
            result["warnings"].append("No transaction data provided")
            result["validation_checks"].append({
                "check": "transactions_exist",
                "status": "warning",
                "severity": "low",
                "message": "Empty transaction list"
            })
            return
        
        result["validation_checks"].append({
            "check": "transactions_exist",
            "status": "passed",
            "severity": "info",
            "message": f"{len(transactions)} transactions found"
        })
        
        # Check 2: Estructura de transacciones
        valid_tx = 0
        invalid_tx_indices = []
        
        for idx, tx in enumerate(transactions):
            if self._validate_transaction(tx):
                valid_tx += 1
            else:
                invalid_tx_indices.append(idx)
                result["warnings"].append(f"Invalid transaction at index {idx}")
        
        tx_validation_rate = (valid_tx / len(transactions) * 100) if len(transactions) > 0 else 0
        
        result["validation_checks"].append({
            "check": "transactions_valid",
            "status": "passed" if valid_tx > 0 else "failed",
            "severity": "high" if tx_validation_rate < 80 else "info",
            "details": {
                "total_transactions": len(transactions),
                "valid_transactions": valid_tx,
                "invalid_transactions": len(invalid_tx_indices),
                "validation_rate": round(tx_validation_rate, 2)
            }
        })
    
    def _validate_consistency(self, inventory: Dict[str, Any], transactions: List[Dict[str, Any]], result: Dict[str, Any]):
        """Valida consistencia entre inventario y transacciones"""
        
        if not inventory or not transactions:
            return
        
        # Check: SKUs en transacciones existen en inventario
        inventory_skus = set(inventory.keys())
        tx_skus = set(tx.get("sku") for tx in transactions if "sku" in tx)
        
        missing_skus = tx_skus - inventory_skus
        
        if missing_skus:
            result["warnings"].append(
                f"{len(missing_skus)} SKUs in transactions not found in inventory"
            )
            result["validation_checks"].append({
                "check": "sku_consistency",
                "status": "warning",
                "severity": "medium",
                "details": {
                    "missing_skus_count": len(missing_skus),
                    "sample_missing": list(missing_skus)[:5]
                }
            })
        else:
            result["validation_checks"].append({
                "check": "sku_consistency",
                "status": "passed",
                "severity": "info",
                "message": "All transaction SKUs found in inventory"
            })
    
    def _validate_inventory_item(self, sku: str, item: Dict[str, Any]) -> bool:
        """
        Valida un item individual de inventario.
        
        Requerimientos:
        - Campo "quantity" presente y numérico
        - Campo "price" presente y > 0
        """
        required_fields = ["quantity", "price"]
        
        # Verificar campos requeridos
        if not all(field in item for field in required_fields):
            return False
        
        # Validar tipos y rangos
        try:
            quantity = float(item["quantity"])
            price = float(item["price"])
            
            # Price debe ser positivo
            if price <= 0:
                return False
            
            # Quantity puede ser 0 o positivo (negativo genera warning pero no invalida)
            return True
            
        except (ValueError, TypeError):
            return False
    
    def _validate_transaction(self, tx: Dict[str, Any]) -> bool:
        """
        Valida una transacción individual.
        
        Requerimientos:
        - Campos: sku, quantity, type
        """
        required_fields = ["sku", "quantity", "type"]
        return all(field in tx for field in required_fields)
    
    def _calculate_quality_score(self, result: Dict[str, Any]) -> float:
        """
        Calcula score de calidad basado en checks.
        
        Lógica:
        - Passed checks: +1 punto
        - Warning checks: +0.5 puntos
        - Failed checks: +0 puntos
        
        Score = (puntos / total_checks) * 100
        """
        total_checks = len(result["validation_checks"])
        
        if total_checks == 0:
            return 0.0
        
        points = 0.0
        
        for check in result["validation_checks"]:
            status = check.get("status", "failed")
            if status == "passed":
                points += 1.0
            elif status == "warning":
                points += 0.5
            # failed = 0 points
        
        score = (points / total_checks) * 100
        
        return round(score, 2)
