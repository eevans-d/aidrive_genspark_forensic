#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para Phase 2: Consistency Check

Cubre:
- Validación de referencias de proveedores
- Detección de transacciones orfandas
- Validación de correlación de movimientos
- Rangos de valores permitidos
- Detección de duplicados
"""

import sys
import os
import pytest
from typing import Dict, Any

# Path-based imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from importlib import import_module

# Usar dynamic import para manejar el hyphen
phase2_module = import_module('inventario-retail.forensic_analysis.phases.phase_2_consistency_check')
Phase2ConsistencyCheck = phase2_module.Phase2ConsistencyCheck


class TestPhase2ConsistencyCheck:
    """Test suite para Phase 2"""
    
    @pytest.fixture
    def phase2(self):
        """Fixture: instancia de Phase 2"""
        return Phase2ConsistencyCheck()
    
    def test_phase2_initialization(self, phase2):
        """Test: Phase 2 se inicializa correctamente"""
        assert phase2 is not None
        assert phase2.phase_number == 2
        assert phase2.phase_name == "Cross-Referential Consistency Check"
        assert phase2.checks_performed == []
        assert phase2.inconsistencies_found == []
        assert phase2.warnings == []
    
    def test_phase2_validate_input_succeeds(self, phase2):
        """Test: validate_input retorna True"""
        assert phase2.validate_input() is True
    
    def test_phase2_execute_returns_dict(self, phase2):
        """Test: execute() retorna estructura correcta"""
        result = phase2.execute()
        
        assert isinstance(result, dict)
        assert "phase" in result
        assert "timestamp" in result
        assert "checks" in result
        assert "inconsistencies" in result
        assert "warnings" in result
        assert "summary" in result
    
    def test_phase2_execute_creates_all_checks(self, phase2):
        """Test: execute() crea 5 checks"""
        result = phase2.execute()
        
        assert len(result["checks"]) == 5
        check_names = [c["name"] for c in result["checks"]]
        
        assert "Provider References Integrity" in check_names
        assert "Orphaned Transactions" in check_names
        assert "Stock Movement Correlation" in check_names
        assert "Value Range Validation" in check_names
        assert "Duplicate Records Detection" in check_names
    
    def test_phase2_execute_summary_structure(self, phase2):
        """Test: summary tiene estructura correcta"""
        result = phase2.execute()
        summary = result["summary"]
        
        assert "total_checks" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "inconsistencies_count" in summary
        assert "warnings_count" in summary
        assert "integrity_score" in summary
        
        # En v1.0 mock, todo pasa
        assert summary["total_checks"] == 5
        assert summary["passed"] == 5
        assert summary["failed"] == 0
        assert summary["integrity_score"] == 100.0
    
    def test_phase2_check_provider_references(self, phase2):
        """Test: check_provider_references se ejecuta"""
        result = phase2.execute()
        
        provider_check = next(
            (c for c in result["checks"] if c["name"] == "Provider References Integrity"),
            None
        )
        
        assert provider_check is not None
        assert provider_check["status"] == "PASSED"
        assert "details" in provider_check
    
    def test_phase2_check_orphaned_transactions(self, phase2):
        """Test: check_orphaned_transactions se ejecuta"""
        result = phase2.execute()
        
        orphaned_check = next(
            (c for c in result["checks"] if c["name"] == "Orphaned Transactions"),
            None
        )
        
        assert orphaned_check is not None
        assert orphaned_check["status"] == "PASSED"
        assert "details" in orphaned_check
    
    def test_phase2_check_stock_correlation(self, phase2):
        """Test: check_stock_movement_correlation se ejecuta"""
        result = phase2.execute()
        
        stock_check = next(
            (c for c in result["checks"] if c["name"] == "Stock Movement Correlation"),
            None
        )
        
        assert stock_check is not None
        assert stock_check["status"] == "PASSED"
        assert "details" in stock_check
    
    def test_phase2_check_value_ranges(self, phase2):
        """Test: check_value_ranges se ejecuta"""
        result = phase2.execute()
        
        value_check = next(
            (c for c in result["checks"] if c["name"] == "Value Range Validation"),
            None
        )
        
        assert value_check is not None
        assert value_check["status"] == "PASSED"
        assert "details" in value_check
    
    def test_phase2_check_duplicates(self, phase2):
        """Test: check_duplicates se ejecuta"""
        result = phase2.execute()
        
        dup_check = next(
            (c for c in result["checks"] if c["name"] == "Duplicate Records Detection"),
            None
        )
        
        assert dup_check is not None
        assert dup_check["status"] == "PASSED"
        assert "details" in dup_check
    
    def test_phase2_no_inconsistencies_in_mock_data(self, phase2):
        """Test: data mock v1.0 no tiene inconsistencies"""
        result = phase2.execute()
        
        # En v1.0 mock, no hay inconsistencias
        assert len(result["inconsistencies"]) == 0
    
    def test_phase2_no_warnings_in_mock_data(self, phase2):
        """Test: data mock v1.0 no tiene warnings"""
        result = phase2.execute()
        
        # En v1.0 mock, no hay warnings
        assert len(result["warnings"]) == 0
    
    def test_phase2_integrity_score_is_float(self, phase2):
        """Test: integrity_score es float"""
        result = phase2.execute()
        
        score = result["summary"]["integrity_score"]
        assert isinstance(score, float)
        assert 0 <= score <= 100


class TestPhase2Integration:
    """Integration tests para Phase 2"""
    
    def test_phase2_execute_is_deterministic(self):
        """Test: execute() retorna resultados consistentes"""
        phase1 = Phase2ConsistencyCheck()
        result1 = phase1.execute()
        
        phase2 = Phase2ConsistencyCheck()
        result2 = phase2.execute()
        
        # Same structure
        assert result1["summary"]["total_checks"] == result2["summary"]["total_checks"]
        assert result1["summary"]["integrity_score"] == result2["summary"]["integrity_score"]
    
    def test_phase2_phase_number_correct(self):
        """Test: phase_number es 2"""
        phase = Phase2ConsistencyCheck()
        assert phase.phase_number == 2
    
    def test_phase2_phase_name_correct(self):
        """Test: phase_name es correcto"""
        phase = Phase2ConsistencyCheck()
        assert phase.phase_name == "Cross-Referential Consistency Check"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
