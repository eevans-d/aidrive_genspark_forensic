#!/usr/bin/env python3
"""
Sistema de Verificación para VIBE Continuous Learning System
Verification Test Suite for VIBE Continuous Learning System

Autor: VIBE Intelligence
Fecha: 2024
Version: 1.0.0

Pruebas incluidas:
- Verificación de compatibilidad con RAG Agro-Portuario
- Pruebas de funcionalidad del scheduler
- Verificación de base de datos
- Pruebas de logging
- Pruebas de integración
"""

import os
import sys
import unittest
import tempfile
import shutil
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import time

# Add the learning system to Python path
sys.path.insert(0, '/vibe_production_system/components/learning_system')

try:
    from learning_scheduler import LearningScheduler, RAGCompatibilityInterface, setup_logging
except ImportError as e:
    print(f"❌ Error importing learning system modules: {e}")
    sys.exit(1)

class TestRAGCompatibility(unittest.TestCase):
    """Pruebas de compatibilidad con el sistema RAG existente"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.rag_interface = None

    def test_rag_interface_initialization(self):
        """Prueba inicialización de la interfaz RAG"""
        try:
            self.rag_interface = RAGCompatibilityInterface()
            self.assertIsNotNone(self.rag_interface)
            print("✅ RAG Interface initialization: PASSED")
        except Exception as e:
            print(f"❌ RAG Interface initialization: FAILED - {e}")
            self.fail(f"RAG Interface initialization failed: {e}")

    def test_rag_performance_metrics(self):
        """Prueba obtención de métricas de rendimiento"""
        try:
            self.rag_interface = RAGCompatibilityInterface()
            metrics = self.rag_interface.get_rag_performance_metrics()

            # Verificar que se obtienen métricas
            self.assertIsInstance(metrics, dict)
            self.assertGreater(len(metrics), 0)

            # Verificar métricas específicas
            self.assertIn('semantic_precision', metrics)
            self.assertGreaterEqual(metrics['semantic_precision'], 0.92)  # Mínimo requerido

            print(f"✅ RAG Performance metrics: PASSED")
            print(f"   📊 Semantic precision: {metrics['semantic_precision']:.1%}")

        except Exception as e:
            print(f"❌ RAG Performance metrics: FAILED - {e}")
            self.fail(f"RAG performance metrics test failed: {e}")

    def test_rag_file_compatibility(self):
        """Prueba compatibilidad con archivos del RAG"""
        try:
            self.rag_interface = RAGCompatibilityInterface()

            # Verificar rutas de archivos críticos
            self.assertTrue(self.rag_interface.rag_base_path.exists())

            print("✅ RAG File compatibility: PASSED")
            print(f"   📁 Base path: {self.rag_interface.rag_base_path}")

        except Exception as e:
            print(f"❌ RAG File compatibility: FAILED - {e}")
            self.fail(f"RAG file compatibility test failed: {e}")

class TestLearningScheduler(unittest.TestCase):
    """Pruebas del programador de aprendizaje continuo"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.temp_dir = tempfile.mkdtemp()
        self.scheduler = None

    def tearDown(self):
        """Limpieza después de las pruebas"""
        if self.scheduler:
            self.scheduler.stop_scheduler()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scheduler_initialization(self):
        """Prueba inicialización del scheduler"""
        try:
            self.scheduler = LearningScheduler()
            self.assertIsNotNone(self.scheduler)
            self.assertFalse(self.scheduler.running)

            print("✅ Scheduler initialization: PASSED")
            print(f"   🎯 Performance threshold: {self.scheduler.performance_threshold:.1%}")
            print(f"   📊 Current precision: {self.scheduler.current_precision:.1%}")

        except Exception as e:
            print(f"❌ Scheduler initialization: FAILED - {e}")
            self.fail(f"Scheduler initialization failed: {e}")

    def test_database_initialization(self):
        """Prueba inicialización de la base de datos"""
        try:
            self.scheduler = LearningScheduler()

            # Verificar que la base de datos existe
            self.assertTrue(os.path.exists(self.scheduler.db_path))

            # Verificar estructura de tablas
            conn = sqlite3.connect(self.scheduler.db_path)
            cursor = conn.cursor()

            # Verificar tabla user_feedback
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_feedback'")
            self.assertIsNotNone(cursor.fetchone())

            # Verificar tabla learning_patterns
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_patterns'")
            self.assertIsNotNone(cursor.fetchone())

            # Verificar tabla performance_metrics
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='performance_metrics'")
            self.assertIsNotNone(cursor.fetchone())

            conn.close()

            print("✅ Database initialization: PASSED")
            print(f"   💾 Database path: {self.scheduler.db_path}")

        except Exception as e:
            print(f"❌ Database initialization: FAILED - {e}")
            self.fail(f"Database initialization failed: {e}")

    def test_feedback_processing(self):
        """Prueba procesamiento de feedback"""
        try:
            self.scheduler = LearningScheduler()

            # Generar datos de prueba
            test_feedback = self.scheduler._collect_daily_feedback()
            self.assertGreater(len(test_feedback), 0)

            # Procesar feedback
            processed_count = self.scheduler._process_feedback_batch(test_feedback)
            self.assertEqual(processed_count, len(test_feedback))

            # Verificar almacenamiento en BD
            conn = sqlite3.connect(self.scheduler.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_feedback")
            stored_count = cursor.fetchone()[0]
            conn.close()

            self.assertGreaterEqual(stored_count, processed_count)

            print("✅ Feedback processing: PASSED")
            print(f"   📊 Processed {processed_count} feedback entries")

        except Exception as e:
            print(f"❌ Feedback processing: FAILED - {e}")
            self.fail(f"Feedback processing failed: {e}")

    def test_health_checks(self):
        """Prueba verificaciones de salud del sistema"""
        try:
            self.scheduler = LearningScheduler()

            # Verificar salud de base de datos
            db_health = self.scheduler._check_database_health()
            self.assertTrue(db_health)

            # Verificar salud del sistema RAG
            rag_health = self.scheduler._check_rag_system_health()
            self.assertTrue(rag_health)

            # Verificar salud del sistema de archivos
            fs_health = self.scheduler._check_file_system_health()
            self.assertTrue(fs_health)

            print("✅ Health checks: PASSED")
            print(f"   💾 Database health: {'✅' if db_health else '❌'}")
            print(f"   🤖 RAG system health: {'✅' if rag_health else '❌'}")
            print(f"   📁 File system health: {'✅' if fs_health else '❌'}")

        except Exception as e:
            print(f"❌ Health checks: FAILED - {e}")
            self.fail(f"Health checks failed: {e}")

class TestLoggingSystem(unittest.TestCase):
    """Pruebas del sistema de logging"""

    def test_logging_setup(self):
        """Prueba configuración del sistema de logging"""
        try:
            logger = setup_logging()
            self.assertIsNotNone(logger)

            # Verificar que el logger tiene handlers
            self.assertGreater(len(logger.handlers), 0)

            # Probar logging básico
            logger.info("Test log message")

            print("✅ Logging setup: PASSED")
            print(f"   📝 Logger name: {logger.name}")
            print(f"   🔧 Handlers count: {len(logger.handlers)}")

        except Exception as e:
            print(f"❌ Logging setup: FAILED - {e}")
            self.fail(f"Logging setup failed: {e}")

class TestSystemIntegration(unittest.TestCase):
    """Pruebas de integración del sistema completo"""

    def test_full_system_integration(self):
        """Prueba integración completa del sistema"""
        try:
            # Inicializar sistema completo
            scheduler = LearningScheduler()

            # Verificar componentes críticos
            self.assertIsNotNone(scheduler.rag_interface)
            self.assertIsNotNone(scheduler.logger)
            self.assertTrue(os.path.exists(scheduler.db_path))

            # Verificar directorios requeridos
            for path in [scheduler.feedback_path, scheduler.patterns_path, scheduler.models_path]:
                self.assertTrue(path.exists())

            # Simular captura de feedback
            scheduler._capture_user_feedback()

            # Simular análisis de patrones
            scheduler._analyze_learning_patterns()

            # Verificar métricas de rendimiento
            current_metrics = scheduler.rag_interface.get_rag_performance_metrics()
            self.assertGreaterEqual(current_metrics.get('semantic_precision', 0), 0.92)

            print("✅ Full system integration: PASSED")
            print(f"   🎯 All components integrated successfully")
            print(f"   📊 Current system precision: {current_metrics.get('semantic_precision', 0):.1%}")

        except Exception as e:
            print(f"❌ Full system integration: FAILED - {e}")
            self.fail(f"Full system integration failed: {e}")

def run_verification_suite():
    """Ejecuta el conjunto completo de pruebas de verificación"""
    print("🧪 VIBE Continuous Learning System - Verification Suite")
    print("=" * 60)
    print(f"📅 Test date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Configurar el runner de pruebas
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Agregar conjuntos de pruebas
    suite.addTests(loader.loadTestsFromTestCase(TestRAGCompatibility))
    suite.addTests(loader.loadTestsFromTestCase(TestLearningScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestLoggingSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemIntegration))

    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Generar reporte final
    print("\n" + "=" * 60)
    print("📊 VERIFICATION RESULTS")
    print("=" * 60)
    print(f"✅ Tests passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Tests failed: {len(result.failures)}")
    print(f"⚠️ Test errors: {len(result.errors)}")
    print(f"📈 Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED - Sistema de Aprendizaje Continuo VERIFIED")
        print("✅ Sistema listo para producción")
        return True
    else:
        print("\n❌ SOME TESTS FAILED - Review required")
        if result.failures:
            print("\n💥 Failures:")
            for test, traceback in result.failures:
                print(f"   • {test}: {traceback}")
        if result.errors:
            print("\n⚠️ Errors:")
            for test, traceback in result.errors:
                print(f"   • {test}: {traceback}")
        return False

if __name__ == "__main__":
    success = run_verification_suite()
    sys.exit(0 if success else 1)
