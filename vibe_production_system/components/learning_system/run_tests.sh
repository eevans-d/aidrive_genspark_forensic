#!/bin/bash
# VIBE Learning System Test Runner

echo "🧪 Running VIBE Continuous Learning System Tests"
echo "================================================"

# Change to test directory
cd /vibe_production_system/components/learning_system/tests

# Run Python tests
python3 test_learning_system.py

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "🎉 ALL TESTS PASSED!"
    echo "✅ Sistema de Aprendizaje Continuo VERIFIED"
    echo "🚀 Ready for production deployment"
else
    echo ""
    echo "❌ TESTS FAILED!"
    echo "⚠️ Review required before deployment"
fi

exit $EXIT_CODE
