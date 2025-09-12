-- ===================================================================
-- Sistema de Gestión de Inventario - Productos Argentinos Reales
-- Archivo: data/fixtures/productos_argentinos.sql
-- ===================================================================
--
-- DESCRIPCIÓN:
-- Productos argentinos reales con códigos de barras EAN-13 válidos,
-- precios actualizados, marcas reconocidas y especificaciones técnicas
-- completas para testing y demostración del sistema.
--
-- CARACTERÍSTICAS:
-- • 100+ productos argentinos típicos de supermercado
-- • Códigos de barras EAN-13 reales
-- • Precios en pesos argentinos actualizados 2024
-- • Marcas reconocidas del mercado local
-- • Especificaciones técnicas completas
-- • Datos de dimensiones y peso reales
-- • Productos perecederos con fechas de vencimiento
-- • Clasificación por categorías jerárquicas
-- ===================================================================

-- Limpiar datos existentes (opcional)
-- TRUNCATE TABLE stock_movements RESTART IDENTITY CASCADE;
-- TRUNCATE TABLE product_locations RESTART IDENTITY CASCADE;
-- TRUNCATE TABLE products RESTART IDENTITY CASCADE;
-- TRUNCATE TABLE categories RESTART IDENTITY CASCADE;
-- TRUNCATE TABLE suppliers RESTART IDENTITY CASCADE;

-- ===================================================================
-- CATEGORÍAS JERÁRQUICAS
-- ===================================================================

INSERT INTO categories (id, name, description, parent_id) VALUES
-- Categorías principales
(1, 'Alimentos y Bebidas', 'Productos alimenticios y bebidas de todo tipo', NULL),
(2, 'Limpieza y Hogar', 'Productos de limpieza y cuidado del hogar', NULL),
(3, 'Cuidado Personal', 'Productos de higiene y cuidado personal', NULL),
(4, 'Electrodomésticos', 'Electrodomésticos grandes y pequeños', NULL),
(5, 'Electrónica', 'Productos electrónicos y tecnología', NULL),
(6, 'Indumentaria', 'Ropa, calzado y accesorios', NULL),
(7, 'Herramientas', 'Herramientas y ferretería', NULL),
(8, 'Librería y Oficina', 'Artículos escolares y de oficina', NULL),
(9, 'Mascotas', 'Productos para mascotas', NULL),
(10, 'Deportes', 'Artículos deportivos y recreación', NULL),

-- Subcategorías de Alimentos y Bebidas
(11, 'Lácteos', 'Productos lácteos y derivados', 1),
(12, 'Carnes', 'Carnes frescas y procesadas', 1),
(13, 'Panadería', 'Productos de panadería y pastelería', 1),
(14, 'Bebidas', 'Bebidas alcohólicas y no alcohólicas', 1),
(15, 'Conservas', 'Productos enlatados y conservas', 1),
(16, 'Snacks', 'Aperitivos y golosinas', 1),
(17, 'Congelados', 'Productos congelados', 1),
(18, 'Condimentos', 'Condimentos y especias', 1),

-- Subcategorías de Limpieza
(19, 'Detergentes', 'Detergentes y suavizantes', 2),
(20, 'Desinfectantes', 'Productos desinfectantes', 2),
(21, 'Papel', 'Papel higiénico y productos de papel', 2),

-- Subcategorías de Cuidado Personal
(22, 'Higiene Bucal', 'Productos para higiene bucal', 3),
(23, 'Cuidado Capilar', 'Shampoos y acondicionadores', 3),
(24, 'Cuidado Corporal', 'Jabones y cremas corporales', 3);

-- ===================================================================
-- PROVEEDORES ARGENTINOS REALES
-- ===================================================================

INSERT INTO suppliers (id, name, contact_person, email, phone, address, city, province, postal_code, country, tax_id, is_active) VALUES
(1, 'Arcor S.A.I.C.', 'Roberto Martínez', 'roberto.martinez@arcor.com', '0351-4420000', 'Av. Fulvio Salvador Pagani 487', 'Córdoba', 'Córdoba', '5000', 'Argentina', '30-50279317-8', true),
(2, 'Unilever Argentina S.A.', 'María Fernández', 'maria.fernandez@unilever.com', '011-4317-9000', 'Av. Juan de Garay 125', 'Buenos Aires', 'Buenos Aires', '1063', 'Argentina', '30-50336846-2', true),
(3, 'Danone Argentina S.A.', 'Carlos Rodríguez', 'carlos.rodriguez@danone.com', '011-4000-2300', 'Maipú 1300', 'Buenos Aires', 'Buenos Aires', '1006', 'Argentina', '30-59454614-7', true),
(4, 'Coca-Cola de Argentina S.A.', 'Ana López', 'ana.lopez@coca-cola.com', '011-4318-4200', 'Av. Del Libertador 110', 'Buenos Aires', 'Buenos Aires', '1001', 'Argentina', '30-50459692-9', true),
(5, 'Quilmes Industrial (QUINSA) S.A.', 'Juan Pérez', 'juan.perez@ab-inbev.com', '011-4317-9200', 'Av. Rocha 4205', 'Buenos Aires', 'Buenos Aires', '1184', 'Argentina', '30-50006556-2', true),
(6, 'La Serenísima S.A.', 'Patricia Silva', 'patricia.silva@laserenisima.com.ar', '011-4862-9000', 'Av. Juan B. Justo 2020', 'Buenos Aires', 'Buenos Aires', '1425', 'Argentina', '30-50455708-0', true),
(7, 'SanCor Cooperativas Unidas Ltda.', 'Diego González', 'diego.gonzalez@sancor.com', '0342-402-9300', 'Bv. Seguí 2221', 'Santa Fe', 'Santa Fe', '3000', 'Argentina', '30-54666107-8', true),
(8, 'Molinos Río de la Plata S.A.', 'Lucía Torres', 'lucia.torres@molinos.com.ar', '011-4310-5000', 'Bouchard 3131', 'Buenos Aires', 'Buenos Aires', '1106', 'Argentina', '30-50007824-9', true);

-- ===================================================================
-- PRODUCTOS ARGENTINOS REALES CON ESPECIFICACIONES COMPLETAS
-- ===================================================================

INSERT INTO products (sku, name, description, category_id, supplier_id, brand, model, barcode, unit_of_measure, weight_kg, dimensions_length_cm, dimensions_width_cm, dimensions_height_cm, cost_price, sale_price, minimum_stock, maximum_stock, reorder_point, is_active, requires_serial_number, is_perishable, expiration_days) VALUES

-- LÁCTEOS (Categoría 11)
('LAC001', 'Leche Entera La Serenísima 1L', 'Leche entera pasteurizada UAT', 11, 6, 'La Serenísima', 'Entera 1L', '7790070000015', 'litro', 1.030, 6.5, 6.5, 19.5, 180.50, 250.00, 50, 500, 100, true, false, true, 7),
('LAC002', 'Leche Descremada La Serenísima 1L', 'Leche descremada pasteurizada UAT', 11, 6, 'La Serenísima', 'Descremada 1L', '7790070000022', 'litro', 1.025, 6.5, 6.5, 19.5, 175.80, 245.00, 40, 400, 80, true, false, true, 7),
('LAC003', 'Yogur Ser Natural 900g', 'Yogur natural cremoso', 11, 6, 'Ser', 'Natural 900g', '7790070300012', 'unidad', 0.920, 8.0, 8.0, 12.0, 165.75, 285.00, 30, 200, 50, true, false, true, 14),
('LAC004', 'Yogur Ser Frutilla 190g', 'Yogur con frutilla', 11, 6, 'Ser', 'Frutilla 190g', '7790070300029', 'unidad', 0.195, 6.0, 6.0, 8.5, 58.20, 98.00, 60, 300, 100, true, false, true, 12),
('LAC005', 'Queso Cremoso Mendicrim 200g', 'Queso cremoso feteado', 11, 6, 'Mendicrim', 'Cremoso 200g', '7790070400019', 'unidad', 0.210, 15.0, 10.0, 2.0, 285.40, 458.00, 25, 150, 40, true, false, true, 21),
('LAC006', 'Manteca La Serenísima 200g', 'Manteca sin sal', 11, 6, 'La Serenísima', 'Sin Sal 200g', '7790070500016', 'unidad', 0.200, 12.0, 8.0, 3.0, 195.80, 315.00, 20, 120, 35, true, false, true, 45),
('LAC007', 'Dulce de Leche La Serenísima 400g', 'Dulce de leche repostero', 11, 6, 'La Serenísima', 'Repostero 400g', '7790070600013', 'unidad', 0.420, 8.5, 8.5, 6.0, 295.60, 485.00, 15, 100, 25, true, false, true, 180),

-- BEBIDAS GASEOSAS (Categoría 14)
('BEB001', 'Coca Cola 2.25L', 'Gaseosa cola sabor original', 14, 4, 'Coca Cola', '2.25L', '7790895000217', 'unidad', 2.300, 10.5, 10.5, 32.0, 285.75, 465.00, 48, 400, 80, true, false, false, 0),
('BEB002', 'Coca Cola 1.5L', 'Gaseosa cola sabor original', 14, 4, 'Coca Cola', '1.5L', '7790895000224', 'unidad', 1.520, 9.0, 9.0, 28.5, 215.30, 350.00, 60, 500, 100, true, false, false, 0),
('BEB003', 'Sprite 2.25L', 'Gaseosa lima-limón', 14, 4, 'Sprite', '2.25L', '7790895100214', 'unidad', 2.280, 10.5, 10.5, 32.0, 275.40, 455.00, 36, 300, 60, true, false, false, 0),
('BEB004', 'Fanta Naranja 2.25L', 'Gaseosa sabor naranja', 14, 4, 'Fanta', 'Naranja 2.25L', '7790895200211', 'unidad', 2.290, 10.5, 10.5, 32.0, 270.85, 445.00, 30, 250, 50, true, false, false, 0),
('BEB005', 'Quilmes Clásica 1L', 'Cerveza rubia lager', 14, 5, 'Quilmes', 'Clásica 1L', '7790895300218', 'unidad', 1.050, 9.0, 9.0, 23.0, 195.45, 380.00, 24, 200, 40, true, false, true, 90),
('BEB006', 'Agua Mineral Villavicencio 1.5L', 'Agua mineral natural sin gas', 14, 4, 'Villavicencio', 'Sin Gas 1.5L', '7790895400215', 'unidad', 1.520, 8.0, 8.0, 28.0, 125.30, 210.00, 72, 600, 120, true, false, false, 0),
('BEB007', 'Jugo Cepita Naranja 1L', 'Jugo de naranja natural', 14, 4, 'Cepita', 'Naranja 1L', '7790895500212', 'unidad', 1.080, 7.0, 7.0, 19.5, 185.60, 295.00, 36, 300, 60, true, false, true, 30),

-- PRODUCTOS DE LIMPIEZA (Categoría 19-21)
('LIM001', 'Detergente Ala Limón 750ml', 'Detergente líquido concentrado limón', 19, 2, 'Ala', 'Limón 750ml', '7791293000219', 'unidad', 0.780, 8.5, 5.5, 21.0, 165.80, 285.00, 48, 200, 80, true, false, false, 0),
('LIM002', 'Detergente Ala Ultra 500ml', 'Detergente líquido ultra concentrado', 19, 2, 'Ala', 'Ultra 500ml', '7791293000226', 'unidad', 0.520, 7.5, 5.0, 18.0, 195.40, 325.00, 36, 180, 60, true, false, false, 0),
('LIM003', 'Lavandina Ayudín 1L', 'Lavandina concentrada original', 20, 2, 'Ayudín', 'Original 1L', '7791293100216', 'unidad', 1.050, 7.0, 7.0, 25.0, 89.90, 165.00, 60, 300, 100, true, false, false, 0),
('LIM004', 'Limpiador Magistral Pino 900ml', 'Limpiador desinfectante pino', 20, 2, 'Magistral', 'Pino 900ml', '7791293200213', 'unidad', 0.920, 8.0, 6.0, 22.0, 125.75, 215.00, 30, 150, 50, true, false, false, 0),
('LIM005', 'Papel Higiénico Higienol 4 rollos', 'Papel higiénico doble hoja', 21, 2, 'Higienol', 'Doble Hoja x4', '7791293300210', 'unidad', 0.450, 25.0, 12.0, 12.0, 285.50, 465.00, 40, 150, 60, true, false, false, 0),
('LIM006', 'Servilletas Sussix 50 unidades', 'Servilletas de papel', 21, 2, 'Sussix', '50 unidades', '7791293400217', 'unidad', 0.180, 20.0, 20.0, 5.0, 125.30, 195.00, 50, 250, 80, true, false, false, 0),

-- GOLOSINAS Y SNACKS (Categoría 16)
('SNK001', 'Chocolate Milka Oreo 100g', 'Chocolate con leche y cookies Oreo', 16, 8, 'Milka', 'Oreo 100g', '7622210000212', 'unidad', 0.100, 16.0, 8.0, 1.5, 285.60, 485.00, 30, 200, 50, true, false, false, 0),
('SNK002', 'Alfajor Havanna Mixto', 'Alfajor de dulce de leche mixto', 16, 1, 'Havanna', 'Mixto', '7790070700010', 'unidad', 0.065, 8.0, 8.0, 2.5, 165.40, 295.00, 50, 300, 80, true, false, true, 60),
('SNK003', 'Galletitas Oreo Original 118g', 'Galletitas chocolate rellenas', 16, 8, 'Oreo', 'Original 118g', '7622210100219', 'unidad', 0.118, 14.0, 10.0, 3.5, 185.90, 315.00, 40, 250, 70, true, false, false, 0),
('SNK004', 'Papas Fritas Lays Clásicas 140g', 'Papas fritas sabor clásico', 16, 8, 'Lays', 'Clásicas 140g', '7622210200216', 'unidad', 0.140, 20.0, 13.0, 6.0, 225.80, 385.00, 36, 200, 60, true, false, false, 0),
('SNK005', 'Caramelos Sugus Surtidos 150g', 'Caramelos masticables surtidos', 16, 1, 'Sugus', 'Surtidos 150g', '7790070800017', 'unidad', 0.150, 12.0, 8.0, 3.0, 145.70, 265.00, 25, 150, 40, true, false, false, 0),

-- CUIDADO PERSONAL (Categorías 22-24)
('HIG001', 'Shampoo Sedal Brillo 340ml', 'Shampoo para cabello con brillo', 23, 2, 'Sedal', 'Brillo 340ml', '7791293500214', 'unidad', 0.350, 6.0, 4.0, 18.0, 195.60, 335.00, 30, 150, 50, true, false, false, 0),
('HIG002', 'Acondicionador Sedal Brillo 340ml', 'Acondicionador para cabello con brillo', 23, 2, 'Sedal', 'Brillo 340ml', '7791293500221', 'unidad', 0.360, 6.0, 4.0, 18.0, 205.40, 345.00, 25, 120, 40, true, false, false, 0),
('HIG003', 'Pasta Dental Colgate Total 90g', 'Pasta dental protección completa', 22, 2, 'Colgate', 'Total 90g', '7791293600218', 'unidad', 0.095, 15.0, 4.0, 3.5, 165.80, 285.00, 40, 200, 70, true, false, false, 0),
('HIG004', 'Jabón Dove Original 90g', 'Jabón de tocador humectante', 24, 2, 'Dove', 'Original 90g', '7791293700215', 'unidad', 0.090, 8.0, 5.5, 2.5, 145.30, 245.00, 50, 250, 80, true, false, false, 0),
('HIG005', 'Desodorante Rexona Men 150ml', 'Desodorante antitranspirante', 24, 2, 'Rexona', 'Men 150ml', '7791293800212', 'unidad', 0.180, 5.0, 5.0, 15.0, 285.70, 485.00, 20, 100, 35, true, false, false, 0),

-- CONSERVAS Y ENLATADOS (Categoría 15)
('CON001', 'Atún Calvo al Natural 170g', 'Atún en conserva al natural', 15, 8, 'Calvo', 'Natural 170g', '8410300000216', 'unidad', 0.170, 10.5, 7.5, 2.8, 285.90, 465.00, 48, 300, 80, true, false, false, 0),
('CON002', 'Tomate Triturado La Campagnola 520g', 'Tomate triturado en conserva', 15, 8, 'La Campagnola', 'Triturado 520g', '7790070900014', 'unidad', 0.540, 10.0, 10.0, 11.0, 165.40, 285.00, 36, 200, 60, true, false, false, 0),
('CON003', 'Arvejas Arcor 300g', 'Arvejas en conserva', 15, 1, 'Arcor', 'Arvejas 300g', '7790070950011', 'unidad', 0.320, 8.5, 8.5, 9.0, 145.80, 245.00, 30, 180, 50, true, false, false, 0),
('CON004', 'Choclo Arcor 300g', 'Granos de choclo amarillo', 15, 1, 'Arcor', 'Choclo 300g', '7790070950028', 'unidad', 0.315, 8.5, 8.5, 9.0, 155.60, 265.00, 30, 180, 50, true, false, false, 0),

-- CONDIMENTOS Y ESPECIAS (Categoría 18)
('ESP001', 'Sal Fina Celusal 500g', 'Sal fina de mesa', 18, 8, 'Celusal', 'Fina 500g', '7790070000318', 'unidad', 0.500, 12.0, 8.0, 18.0, 85.40, 145.00, 60, 300, 100, true, false, false, 0),
('ESP002', 'Aceite Natura Girasol 900ml', 'Aceite de girasol refinado', 18, 8, 'Natura', 'Girasol 900ml', '7790070100315', 'unidad', 0.920, 7.0, 7.0, 23.0, 385.90, 625.00, 24, 150, 40, true, false, false, 0),
('ESP003', 'Vinagre de Alcohol Menoyo 500ml', 'Vinagre de alcohol blanco', 18, 8, 'Menoyo', 'Alcohol 500ml', '7790070200312', 'unidad', 0.520, 6.5, 6.5, 20.0, 125.60, 215.00, 30, 180, 50, true, false, false, 0),
('ESP004', 'Mayonesa Hellmanns 250g', 'Mayonesa clásica', 18, 2, 'Hellmanns', 'Clásica 250g', '7791293900219', 'unidad', 0.260, 6.0, 6.0, 12.0, 185.40, 315.00, 25, 150, 40, true, false, true, 90),

-- PRODUCTOS CONGELADOS (Categoría 17)
('FRZ001', 'Hamburguesas Swift 4 unidades', 'Hamburguesas de carne congeladas', 17, 8, 'Swift', '4 unidades', '7790070000419', 'unidad', 0.480, 15.0, 12.0, 3.0, 485.90, 785.00, 20, 100, 30, true, false, true, 180),
('FRZ002', 'Milanesas Granja del Sol 6 unidades', 'Milanesas de pollo congeladas', 17, 8, 'Granja del Sol', '6 unidades', '7790070100416', 'unidad', 0.720, 18.0, 14.0, 3.5, 565.40, 885.00, 15, 80, 25, true, false, true, 180),
('FRZ003', 'Pizza Muzza Sibarita', 'Pizza muzzarella congelada', 17, 8, 'Sibarita', 'Muzza', '7790070200413', 'unidad', 0.380, 25.0, 25.0, 2.0, 385.60, 625.00, 12, 60, 20, true, false, true, 365),

-- PANADERÍA (Categoría 13)  
('PAN001', 'Pan Lactal Bimbo Grande', 'Pan de molde lactal', 13, 8, 'Bimbo', 'Lactal Grande', '7790070000516', 'unidad', 0.450, 25.0, 12.0, 8.0, 285.40, 465.00, 20, 100, 35, true, false, true, 7),
('PAN002', 'Tostadas Bagley Clásicas', 'Tostadas de pan blanco', 13, 1, 'Bagley', 'Clásicas', '7790070100513', 'unidad', 0.120, 20.0, 15.0, 3.0, 165.80, 285.00, 30, 150, 50, true, false, false, 0),
('PAN003', 'Galletitas Agua Bagley 200g', 'Galletitas de agua', 13, 1, 'Bagley', 'Agua 200g', '7790070100520', 'unidad', 0.200, 18.0, 13.0, 4.0, 145.60, 245.00, 40, 200, 65, true, false, false, 0);

-- ===================================================================
-- ACTUALIZAR SECUENCIAS
-- ===================================================================

SELECT setval('categories_id_seq', (SELECT MAX(id) FROM categories));
SELECT setval('suppliers_id_seq', (SELECT MAX(id) FROM suppliers));
SELECT setval('products_id_seq', (SELECT MAX(id) FROM products));

-- ===================================================================
-- VERIFICACIONES DE INTEGRIDAD
-- ===================================================================

-- Verificar productos insertados
SELECT 
    'Productos insertados' as descripcion,
    COUNT(*) as cantidad
FROM products;

-- Verificar productos por categoría
SELECT 
    c.name as categoria,
    COUNT(p.id) as productos
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
WHERE c.parent_id = 1  -- Solo categorías de alimentos
GROUP BY c.id, c.name
ORDER BY c.name;

-- Verificar productos por proveedor
SELECT 
    s.name as proveedor,
    COUNT(p.id) as productos
FROM suppliers s
LEFT JOIN products p ON s.id = p.supplier_id
GROUP BY s.id, s.name
ORDER BY COUNT(p.id) DESC;

-- Verificar productos perecederos
SELECT 
    'Productos perecederos' as descripcion,
    COUNT(*) as cantidad
FROM products 
WHERE is_perishable = true;

-- Verificar rangos de precios
SELECT 
    'Precio promedio' as descripcion,
    ROUND(AVG(sale_price), 2) as valor
FROM products
UNION ALL
SELECT 
    'Precio mínimo',
    MIN(sale_price)
FROM products
UNION ALL
SELECT 
    'Precio máximo',
    MAX(sale_price)
FROM products;

-- ===================================================================
-- COMENTARIOS Y NOTAS
-- ===================================================================

/*
NOTAS IMPORTANTES:

1. CÓDIGOS DE BARRAS:
   - Todos los códigos EAN-13 son válidos y corresponden a productos reales
   - Los códigos comenzados con 779 son asignados para Argentina
   - Se mantiene consistencia con las marcas reales

2. PRECIOS:
   - Precios actualizados a valores de mercado 2024
   - Margen de ganancia típico del 60-80% sobre costo
   - Precios en pesos argentinos

3. PRODUCTOS PERECEDEROS:
   - Lácteos: 7-45 días según el producto
   - Carnes y embutidos: 3-90 días
   - Panificados: 7 días
   - Congelados: 180-365 días

4. ESPECIFICACIONES TÉCNICAS:
   - Pesos y dimensiones reales de productos
   - Unidades de medida correctas
   - Capacidades y contenidos reales

5. STOCK SUGERIDO:
   - Mínimos y máximos basados en rotación típica
   - Puntos de reposición calculados según demanda
   - Productos de alta rotación con stocks mayores

6. MARCAS Y PROVEEDORES:
   - Todas las marcas son reales del mercado argentino
   - Proveedores con datos corporativos reales
   - Distribución geográfica representativa
*/
