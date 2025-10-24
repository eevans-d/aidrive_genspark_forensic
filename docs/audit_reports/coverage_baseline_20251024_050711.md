# COBERTURA DE TESTS BASELINE
Generado: 2025-10-24T05:07:12Z

## Pytest Collection
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.4.2, pluggy-1.6.0
rootdir: /home/eevan/ProyectosIA/aidrive_genspark/inventario-retail
plugins: anyio-4.10.0, mock-3.15.1, asyncio-1.2.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 23 items / 6 errors / 1 skipped

<Dir inventario-retail>
  <Dir tests>
    <Dir agente_negocio>
      <Module test_ocr.py>
        <Class TestImagePreprocessor>
          <Function test_preprocess_image_basic>
          <Function test_preprocess_image_with_enhancements>
          <Function test_preprocess_invalid_image>
          <Function test_preprocess_different_formats>
          <Function test_preprocess_large_image>
        <Class TestOCRProcessor>
          <Function test_process_image_success>
          <Function test_process_image_poor_quality>
          <Function test_ocr_processor_initialization>
          <Function test_process_multilingual_invoice>
          <Function test_ocr_error_handling>
        <Class TestInvoiceExtractor>
          <Function test_extract_invoice_data_complete>
          <Function test_extract_partial_invoice_data>
          <Function test_extract_regex_patterns>
          <Function test_extract_product_table>
          <Function test_extract_confidence_scoring>
          <Function test_extract_invalid_ocr_data>
        <Class TestOCRPipeline>
          <Coroutine test_complete_ocr_pipeline>
          <Function test_pipeline_error_propagation>
          <Function test_pipeline_performance_metrics>
        <Class TestOCRIntegration>
          <Function test_ocr_with_real_sample_data>
    <Module test_config.py>
      <Function test_settings_load>
      <Function test_cuit_validation>
      <Function test_precio_format>

==================================== ERRORS ====================================
___________ ERROR collecting tests/agente_deposito/test_complete.py ____________
ImportError while importing test module '/home/eevan/ProyectosIA/aidrive_genspark/inventario-retail/tests/agente_deposito/test_complete.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/agente_deposito/test_complete.py:25: in <module>
    from agente_deposito.main_complete import app
agente_deposito/main_complete.py:25: in <module>
    from .dependencies import (
agente_deposito/dependencies.py:25: in <module>
    from .models import Base
E   ModuleNotFoundError: No module named 'agente_deposito.models'
_____________ ERROR collecting tests/agente_deposito/test_main.py ______________
ImportError while importing test module '/home/eevan/ProyectosIA/aidrive_genspark/inventario-retail/tests/agente_deposito/test_main.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/agente_deposito/test_main.py:6: in <module>
    from agente_deposito.main import app
agente_deposito/main.py:26: in <module>
    from shared.auth import require_role, DEPOSITO_ROLE
E   ModuleNotFoundError: No module named 'shared.auth'
_________ ERROR collecting tests/agente_deposito/test_main_completo.py _________
tests/agente_deposito/test_main_completo.py:17: in <module>
    from agente_deposito.main import app
agente_deposito/main.py:4: in <module>
    REQUEST_COUNT = Counter('agente_deposito_requests_total', 'Total de requests', ['method', 'endpoint', 'http_status'])
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/prometheus_client/metrics.py:132: in __init__
    registry.register(self)
../../../.local/lib/python3.12/site-packages/prometheus_client/registry.py:43: in register
    raise ValueError(
E   ValueError: Duplicated timeseries in CollectorRegistry: {'agente_deposito_requests', 'agente_deposito_requests_created', 'agente_deposito_requests_total'}
____ ERROR collecting tests/agente_deposito/test_stock_manager_completo.py _____
ImportError while importing test module '/home/eevan/ProyectosIA/aidrive_genspark/inventario-retail/tests/agente_deposito/test_stock_manager_completo.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/agente_deposito/test_stock_manager_completo.py:13: in <module>
    from agente_deposito.database import Base
agente_deposito/database.py:251: in <module>
    db_manager = DatabaseManager()
                 ^^^^^^^^^^^^^^^^^
agente_deposito/database.py:36: in __init__
    self.engine = create_engine(
../../../.local/lib/python3.12/site-packages/sqlalchemy/util/deprecations.py:281: in warned
    return fn(*args, **kwargs)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/sqlalchemy/engine/create.py:617: in create_engine
    dbapi = dbapi_meth(**dbapi_args)
            ^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/psycopg2.py:696: in import_dbapi
    import psycopg2
E   ModuleNotFoundError: No module named 'psycopg2'
________ ERROR collecting tests/agente_negocio/ocr/test_preprocessor.py ________
ImportError while importing test module '/home/eevan/ProyectosIA/aidrive_genspark/inventario-retail/tests/agente_negocio/ocr/test_preprocessor.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/agente_negocio/ocr/test_preprocessor.py:7: in <module>
    import cv2
E   ModuleNotFoundError: No module named 'cv2'
_________ ERROR collecting tests/integration/test_database_completo.py _________
ImportError while importing test module '/home/eevan/ProyectosIA/aidrive_genspark/inventario-retail/tests/integration/test_database_completo.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_database_completo.py:15: in <module>
    from agente_deposito.database import DatabaseManager, Base
agente_deposito/database.py:251: in <module>
    db_manager = DatabaseManager()
                 ^^^^^^^^^^^^^^^^^
agente_deposito/database.py:36: in __init__
    self.engine = create_engine(
../../../.local/lib/python3.12/site-packages/sqlalchemy/util/deprecations.py:281: in warned
    return fn(*args, **kwargs)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/sqlalchemy/engine/create.py:617: in create_engine
    dbapi = dbapi_meth(**dbapi_args)
            ^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/psycopg2.py:696: in import_dbapi
    import psycopg2
E   ModuleNotFoundError: No module named 'psycopg2'
=============================== warnings summary ===============================
shared/config.py:92
  /home/eevan/ProyectosIA/aidrive_genspark/inventario-retail/shared/config.py:92: PydanticDeprecatedSince20: Pydantic V1 style `@validator` validators are deprecated. You should migrate to Pydantic V2 style `@field_validator` validators, see the migration guide for more details. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
    @validator("DATABASE_URL")

shared/config.py:103
  /home/eevan/ProyectosIA/aidrive_genspark/inventario-retail/shared/config.py:103: PydanticDeprecatedSince20: Pydantic V1 style `@validator` validators are deprecated. You should migrate to Pydantic V2 style `@field_validator` validators, see the migration guide for more details. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
    @validator("INFLACION_MENSUAL")

shared/config.py:110
  /home/eevan/ProyectosIA/aidrive_genspark/inventario-retail/shared/config.py:110: PydanticDeprecatedSince20: Pydantic V1 style `@validator` validators are deprecated. You should migrate to Pydantic V2 style `@field_validator` validators, see the migration guide for more details. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
    @validator("TEMPORADA")

../../../.local/lib/python3.12/site-packages/pydantic/_internal/_config.py:323
  /home/eevan/.local/lib/python3.12/site-packages/pydantic/_internal/_config.py:323: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.11/migration/
    warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)

shared/database.py:17
  /home/eevan/ProyectosIA/aidrive_genspark/inventario-retail/shared/database.py:17: MovedIn20Warning: The ``declarative_base()`` function is now available as sqlalchemy.orm.declarative_base(). (deprecated since: 2.0) (Background on SQLAlchemy 2.0 at: https://sqlalche.me/e/b8d9)
    Base = declarative_base()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/agente_deposito/test_complete.py
ERROR tests/agente_deposito/test_main.py
ERROR tests/agente_deposito/test_main_completo.py - ValueError: Duplicated ti...
ERROR tests/agente_deposito/test_stock_manager_completo.py
ERROR tests/agente_negocio/ocr/test_preprocessor.py
ERROR tests/integration/test_database_completo.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
==================== 23 tests collected, 6 errors in 3.38s =====================
Pytest collection falló

## Cobertura Dashboard
ERROR: usage: pytest [options] [file_or_dir] [file_or_dir] [...]
pytest: error: unrecognized arguments: --cov=web_dashboard --cov-report=term-missing
  inifile: None
  rootdir: /home/eevan/ProyectosIA/aidrive_genspark/inventario-retail

Cobertura falló
