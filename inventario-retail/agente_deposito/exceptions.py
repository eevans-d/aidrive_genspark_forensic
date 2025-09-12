"""
Excepciones personalizadas para AgenteDepósito
"""

class InventarioBaseError(Exception):
    """Excepción base del sistema de inventario"""
    pass

class StockInsuficienteError(InventarioBaseError):
    """Error cuando no hay stock suficiente"""
    def __init__(self, message: str, stock_actual: int = None):
        super().__init__(message)
        self.stock_actual = stock_actual

class ProductoNoEncontradoError(InventarioBaseError):
    """Error cuando no se encuentra el producto"""
    pass

class ValidacionError(InventarioBaseError):
    """Error de validación de datos"""
    pass

class TransaccionError(InventarioBaseError):
    """Error en transacciones de base de datos"""
    pass
