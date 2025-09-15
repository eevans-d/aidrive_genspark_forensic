# 🏪 DOCUMENTACIÓN MAESTRA MINI MARKET - ESPECIFICACIÓN OPERATIVA
## Integración con Sistema Actual - 14 Septiembre 2025

### ⚠️ **DOCUMENTO CRÍTICO PARA DESARROLLO**
**Esta documentación define la lógica de negocio REAL del mini market del cliente**

---

## 📋 **1. PROVEEDORES PRINCIPALES Y ABREVIATURAS**

### **1.1 Tabla Maestra de Proveedores**

| **Abrev** | **Proveedor/Distribuidora** | **Productos y Categorías Principales** |
|-----------|----------------------------|----------------------------------------|
| **BC** | Bodega Cedeira | Vinos y bebidas alcohólicas (excepto cervezas) |
| **CO** | Coca Cola | Gaseosas Coca-Cola, Sprite, Fanta, Aquarius, Ades, Cepita, Monster, Schweppes |
| **Q** | Quilmes | Cervezas (Quilmes, Brahma, Stella Artois, Andes, Corona), Gatorade, Glaciar, Pepsi, 7up, Paso de los Toros, Eco de los Andes, Red Bull |
| **FA** | Fargo | Panificados Fargo. Distribuye: Levite, Baggio, congelados (Barfy, Friar), lácteos (Paulina, Ilolay), salchichas (Paladini), pastas y arroz (Luchetti, Matarazzo), café (Cabrales), aceite y aderezos Natura |
| **LS** | La Serenísima | Productos La Serenísima, Yogurísimo, Ser, Casancrem, Finlandia, Cremon, Cindor |
| **ACE** | Aceitumar (MDP) | Frutos secos, semillas, snacks, aceites gourmet, especias, salsas y conservas |
| **TER** | Terrabusi (Mondelez) | Galletitas (Terrabusi, Oreo, Pepitos), Chocolates (Milka), Chicles (Beldent), Alfajores |
| **LV** | La Virginia | Cafés, tés, yerba mate |
| **FR** | Frutas y Verduras ("Bicho") | Frutas y verduras frescas |
| **MU** | Multienvase (MDP) | Envases descartables |
| **GA** | Galletitera (MDP) | Galletería artesanal y panadería local |
| **MAX** | Maxiconsumo | Mayorista general - PROVEEDOR POR DEFECTO |

### **1.2 Catálogo Detallado por Proveedor**

#### **BC - Bodega Cedeira**
- **Categorías:** Vino, Fernet, Whisky, Vodka, Ron, Licor, Champagne
- **Productos específicos:**
  - Vino Elementos Malbec
  - Vino Santa Julia Chenin

#### **CO - Coca Cola**
- **Marcas:** Coca-Cola, Sprite, Fanta, Aquarius, Ades, Cepita, Monster, Schweppes
- **Productos específicos:**
  - Coca Cola de litro y medio (1.5L)
  - Coca de 2 litros (2L)
  - Coca-Cola Clásica 2.25L

#### **Q - Quilmes**
- **Cervezas:** Quilmes, Brahma, Stella Artois, Andes, Corona
- **Línea PepsiCo:** Gatorade, Glaciar, Pepsi, 7up, Paso de los Toros, Eco de los Andes, Red Bull

#### **FA - Fargo**
- **Marca propia:** Fargo (Panificados)
- **Marcas distribuidas:**
  - Levite, Baggio, Natura (aderezos/aceite)
  - Luchetti, Matarazzo, Don Vicente (pastas/arroz)
  - Cabrales, Arlistan (café)
  - Congelados: Barfy, Friar, Granja del Sol, Veggies, McCain
  - Lácteos: Paulina, Ilolay (mantecas, quesos)
  - Salchichas: Jet Food, Paladini, Fela

#### **LS - La Serenísima**
- **Marcas:** La Serenísima, Yogurísimo, Ser, Casancrem, Finlandia, Cremon, Cindor

#### **TER - Terrabusi (Mondelez)**
- **Marcas:** Terrabusi, Oreo, Pepitos, Milka, Beldent, Infinit, Rhodesia, Tita

---

## 🎯 **2. LÓGICA DE NEGOCIO CRÍTICA**

### **2.1 Algoritmo de Asignación de Proveedor**

**JERARQUÍA DE REGLAS (ORDEN ESTRICTO):**

1. **Coincidencia Directa de Marca**
   - Si producto es marca = proveedor → Asignar directo
   - Ej: "Leche La Serenísima" → LS

2. **Coincidencia Sub-Marca Específica**
   - Si producto es submarca conocida → Proveedor especialista
   - Ej: "Oreo" → TER, "Levite" → FA

3. **Coincidencia por Categoría Especializada**
   - Vinos/Licores (NO cervezas) → BC
   - Gaseosas línea Coca-Cola → CO
   - Cervezas + Gaseosas línea PepsiCo → Q
   - Frutas/Verduras frescas → FR

4. **Coincidencia Marca Distribuida**
   - Si marca está en catálogo distribuido → Proveedor correspondiente
   - Ej: "Manteca Paulina" → FA

5. **Proveedor por Defecto**
   - Si ninguna regla aplica → MAX (Maxiconsumo)

### **2.2 Turnos de Empleados**
- **Turno Mañana:** 08:00 a 14:30 hs
- **Turno Tarde:** 14:30 a 23:30 hs  
- **Turno Apoyo:** 17:00 a 23:30 hs

---

## 🔄 **3. FLUJOS DE TRABAJO OPERATIVOS**

### **3.1 Flujo: Registrar Productos Faltantes/Realizar Pedido**

**COMANDOS DE ACTIVACIÓN:**
```
"Pedir [Producto] [Cantidad]"
"Falta [Producto]"
"Anotar [Producto] para el pedido"
"Necesito traer [Producto] [Cantidad]"
"Agregar a la lista de [Proveedor]: [Producto]"
```

**EJEMPLOS REALES:**
- "Pedir Salchichas Paladini x 6 y también x 12. Y falta Coca Cola de litro y medio."
- "Anotame que no hay más Brahma, ni Quilmes, ni Andes."
- "Falta Leche" (requiere clarificación)

**PROCESO DEL AGENTE:**
1. Identificar intención "pedir"
2. Extraer producto y cantidad
3. Aplicar Lógica de Asignación de Proveedor (Sección 2.1)
4. Registrar en lista "Productos a Pedir" asociado al proveedor
5. Marcar como "Pendiente"

### **3.2 Flujo: Gestionar Stock del Depósito**

**PRODUCTOS TÍPICOS DEL DEPÓSITO:**
- Frutas y verduras (cajones/bolsas)
- Bidones de agua
- Leña y carbón (bolsas)
- Cajas de vinos
- Bolsones papel higiénico y rollos cocina
- Bultos puré tomate, legumbres, aceites, lavandina
- Packs gaseosas, aguas, latas cerveza
- Insumos: rollos bolsas, cajas snacks

#### **3.2.1 Sub-flujo ENTRADA:**

**COMANDOS:**
```
"Dejé [Cantidad] [Producto]"
"Ingresó [Cantidad] [Producto]"
"Traje [Cantidad] [Producto] para guardar"
"Sumar al stock [Cantidad] [Producto]"
/entrada "[Producto]" [Cantidad] "[Proveedor/Origen]"
```

**EJEMPLOS REALES:**
- "Deje 4 bananas ecuador, 2 tomates, 1 elementos MALBEC, 2 Santa Julia chennin."
- `/entrada "Tornillos TX2" 50 "Proveedor ACME"`

#### **3.2.2 Sub-flujo SALIDA:**

**COMANDOS:**
```
"Saqué [Cantidad] [Producto] del depósito"
"Me llevo [Cantidad] [Producto] para el local"
"Retiro [Cantidad] [Producto]"
"Descontar del stock [Cantidad] [Producto]"
/salida "[Producto]" [Cantidad] "[Destino]"
```

**EJEMPLOS REALES:**
- "Saqué 2 paquetes de galletitas Oreo y 1 botella de Coca de 2 litros."
- `/salida "Tuercas M5" 20 "Proyecto Beta"`

---

## 💬 **4. LÉXICO DE INTERACCIÓN COMPLETO**

### **4.1 Comandos Formales**
```bash
/stock "[Término de Búsqueda]"          # Consultar stock
/merma "[Producto]" [Cantidad] "[Motivo]"  # Registrar merma
/corregir id=[ID] cantidad=[Nueva] motivo="[Motivo]"  # Corregir registro
/calibrar producto="[Producto]" stock_real=[Cantidad] justificacion="[Justificación]"  # Calibrar stock
/informe_stock                          # Generar informe
/ayuda                                  # Mostrar ayuda
```

### **4.2 Directivas de Interacción**

#### **CLARIFICACIÓN:**
- Si solicitud ambigua → Preguntar detalles específicos
- Ej: "Falta queso" → "¿Qué tipo de queso o marca?"

#### **CONFIRMACIÓN:**
- Para acciones críticas → Solicitar confirmación explícita
- Antes de modificar datos de pedidos/stock

#### **MANEJO DE NOVEDADES:**
- Si producto desconocido → Preguntar si añadir
- Solicitar información: categoría, proveedor, etc.

---

## 🔧 **5. INTEGRACIÓN CON SISTEMA ACTUAL**

### **5.1 Archivos a Actualizar/Crear**

#### **AGENTE NEGOCIO:**
- `inventario-retail/agente_negocio/main_complete.py` - Integrar lógica proveedores
- `inventario-retail/agente_negocio/provider_logic.py` - **CREAR NUEVO**

#### **AGENTE DEPÓSITO:**
- `inventario-retail/agente_deposito/main.py` - Integrar comandos stock
- `inventario-retail/agente_deposito/stock_commands.py` - **CREAR NUEVO**

#### **BASE DE DATOS:**
- `inventario-retail/shared/models.py` - Añadir tablas proveedores
- `inventario-retail/shared/database.py` - Migrations proveedores

### **5.2 Nuevas Entidades de Base de Datos**

```python
# Tabla Proveedores
class Proveedor(Base):
    __tablename__ = "proveedores"
    id = Column(Integer, primary_key=True)
    abreviatura = Column(String(10), unique=True)
    nombre = Column(String(100))
    categoria_principal = Column(String(50))
    marcas_distribuidas = Column(JSON)  # Lista marcas
    contacto = Column(String(100))
    
# Tabla Pedidos
class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))
    producto = Column(String(100))
    cantidad = Column(Integer)
    estado = Column(String(20))  # Pendiente, Solicitado, Recibido
    fecha_pedido = Column(DateTime)
    empleado_turno = Column(String(20))
```

### **5.3 Implementación Lógica de Proveedores**

```python
class ProviderLogic:
    """Lógica de asignación de proveedores según especificación mini market"""
    
    PROVIDER_MAPPING = {
        'BC': {'categorias': ['vino', 'fernet', 'whisky', 'vodka', 'ron', 'licor', 'champagne']},
        'CO': {'marcas': ['coca-cola', 'sprite', 'fanta', 'aquarius', 'ades', 'cepita', 'monster', 'schweppes']},
        'Q': {'marcas': ['quilmes', 'brahma', 'stella artois', 'andes', 'corona', 'gatorade', 'glaciar', 'pepsi', '7up']},
        'FA': {'marcas': ['fargo', 'levite', 'baggio', 'natura', 'luchetti', 'matarazzo', 'cabrales', 'paulina', 'ilolay', 'paladini']},
        'LS': {'marcas': ['la serenisima', 'yogurisimo', 'ser', 'casancrem', 'finlandia', 'cremon', 'cindor']},
        'TER': {'marcas': ['terrabusi', 'oreo', 'pepitos', 'milka', 'beldent', 'rhodesia', 'tita']},
        # ... resto de proveedores
    }
    
    def asignar_proveedor(self, producto: str) -> str:
        """Aplica lógica de asignación según jerarquía definida"""
        # 1. Coincidencia directa marca
        # 2. Sub-marca específica  
        # 3. Categoría especializada
        # 4. Marca distribuida
        # 5. Proveedor por defecto (MAX)
```

---

## ⚠️ **6. PRIORIDADES IMPLEMENTACIÓN MINI MARKET**

### **6.1 CRÍTICO - SEMANA 1:**
- ✅ Implementar lógica proveedores en Agente Negocio
- ✅ Crear comandos stock en Agente Depósito  
- ✅ Base de datos proveedores/pedidos
- ✅ Flujo básico "pedir producto"

### **6.2 IMPORTANTE - SEMANA 2:**
- ✅ Comandos formales (/entrada, /salida, /stock)
- ✅ Clarificación automática productos ambiguos
- ✅ Confirmación acciones críticas
- ✅ Interfaz simple empleados

### **6.3 OPCIONAL - DESPUÉS:**
- 🚫 ~~Integraciones AFIP~~ (NO para mini market)
- 🚫 ~~Compliance automático~~ (NO requerido)
- ✅ Reportes simples operativos
- ✅ Backup datos diario

---

## 📋 **7. DOCUMENTACIÓN PENDIENTE DE VALIDAR**

### **7.1 COINCIDENCIAS CON SISTEMA ACTUAL:**
- OCR facturas ✅ (ya implementado)
- Dashboard web ✅ (ya implementado)
- Base inventario ✅ (ya implementado)

### **7.2 FALTANTE EN SISTEMA ACTUAL:**
- ❌ Lógica específica proveedores mini market
- ❌ Comandos naturales stock depósito
- ❌ Abreviaturas proveedores estandarizadas
- ❌ Flujo pedidos por proveedor
- ❌ Turnos empleados integrados

### **7.3 DATOS ERRÓNEOS A CORREGIR:**
- Proveedores genéricos → Proveedores específicos reales
- Lógica asignación automática → Lógica mini market
- Categorías productos → Catálogo real cliente

---

## ✅ **CONFIRMACIÓN PARA DESARROLLO**

**ESTA DOCUMENTACIÓN ES LA BASE DE CONOCIMIENTO REAL DEL NEGOCIO**
- Define lógica operativa exacta del mini market
- Especifica proveedores, productos y flujos reales
- Prioriza funcionalidad práctica sobre robustez enterprise
- Guía implementación próximas 2-3 semanas

**PRÓXIMO PASO:** Implementar esta lógica específica en el sistema actual manteniendo toda la robustez ya desarrollada.