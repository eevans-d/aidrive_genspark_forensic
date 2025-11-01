/**
 * API COMPLETA PARA CONSULTA DE PRECIOS DEL PROVEEDOR
 * Sprint 6 - Integración Maxiconsumo Necochea
 * 
 * Endpoints implementados:
 * - GET /proveedor/precios - Lista precios actuales
 * - GET /proveedor/productos - Productos disponibles
 * - GET /proveedor/comparacion - Comparación con sistema
 * - POST /proveedor/sincronizar - Trigger sincronización manual
 * - GET /proveedor/status - Estado del sistema
 * - GET /proveedor/alertas - Alertas activas
 * - GET /proveedor/estadisticas - Métricas de scraping
 * 
 * @author MiniMax Agent
 * @date 2025-10-31
 */

Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
        'Access-Control-Max-Age': '86400',
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

        if (!supabaseUrl || !serviceRoleKey) {
            throw new Error('Configuración de Supabase faltante');
        }

        // Parsear URL y determinar endpoint
        const url = new URL(req.url);
        const pathSegments = url.pathname.split('/').filter(segment => segment.length > 0);
        
        // El path debería ser: /proveedor/[endpoint]
        const endpoint = pathSegments[1] || 'status';
        const method = req.method;

        console.log(`🔌 API Proveedor - Endpoint: ${endpoint}, Método: ${method}`);

        // Autenticación opcional para endpoints protegidos
        const authHeader = req.headers.get('Authorization');
        const isAuthenticated = authHeader && authHeader.startsWith('Bearer ');

        switch (endpoint) {
            case 'precios':
                return await getPreciosActuales(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated);
            
            case 'productos':
                return await getProductosDisponibles(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated);
            
            case 'comparacion':
                return await getComparacionConSistema(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated);
            
            case 'sincronizar':
                if (method !== 'POST') {
                    throw new Error('Método no permitido. Use POST para sincronizar.');
                }
                return await triggerSincronizacion(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated);
            
            case 'status':
                return await getEstadoSistema(supabaseUrl, serviceRoleKey, url, corsHeaders);
            
            case 'alertas':
                return await getAlertasActivas(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated);
            
            case 'estadisticas':
                return await getEstadisticasScraping(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated);
            
            case 'configuracion':
                return await getConfiguracionProveedor(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated);
            
            default:
                throw new Error(`Endpoint no válido: ${endpoint}`);
        }

    } catch (error) {
        console.error('❌ Error en API Proveedor:', error);
        return new Response(JSON.stringify({
            success: false,
            error: {
                code: 'API_PROVEEDOR_ERROR',
                message: error.message,
                timestamp: new Date().toISOString()
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

/**
 * GET /proveedor/precios - Lista precios actuales
 */
async function getPreciosActuales(
    supabaseUrl: string, 
    serviceRoleKey: string, 
    url: URL, 
    corsHeaders: Record<string, string>,
    isAuthenticated: boolean
) {
    const categoria = url.searchParams.get('categoria') || 'todos';
    const limite = parseInt(url.searchParams.get('limit') || '50');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    const activo = url.searchParams.get('activo') || 'true';

    console.log(`💰 Obteniendo precios - Categoría: ${categoria}, Límite: ${limite}`);

    try {
        // Construir query
        let query = `${supabaseUrl}/rest/v1/precios_proveedor?select=*&fuente=eq.Maxiconsumo Necochea&activo=eq.${activo}`;
        
        if (categoria !== 'todos') {
            query += `&categoria=eq.${encodeURIComponent(categoria)}`;
        }
        
        query += `&order=ultima_actualizacion.desc&limit=${limite}&offset=${offset}`;

        const response = await fetch(query, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`,
            }
        });

        if (!response.ok) {
            throw new Error(`Error obteniendo precios: ${response.statusText}`);
        }

        const productos = await response.json();

        // Obtener total para paginación
        let totalQuery = `${supabaseUrl}/rest/v1/precios_proveedor?select=count&fuente=eq.Maxiconsumo Necochea&activo=eq.${activo}`;
        if (categoria !== 'todos') {
            totalQuery += `&categoria=eq.${encodeURIComponent(categoria)}`;
        }

        const totalResponse = await fetch(totalQuery, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`,
            }
        });

        const totalData = await totalResponse.json();
        const total = totalData[0]?.count || 0;

        const resultado = {
            success: true,
            data: {
                productos: productos,
                paginacion: {
                    total: total,
                    limite: limite,
                    offset: offset,
                    productos_mostrados: productos.length,
                    tiene_mas: (offset + limite) < total
                },
                filtros_aplicados: {
                    categoria: categoria,
                    activo: activo
                },
                timestamp: new Date().toISOString()
            }
        };

        return new Response(JSON.stringify(resultado), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('❌ Error obteniendo precios actuales:', error);
        throw error;
    }
}

/**
 * GET /proveedor/productos - Productos disponibles
 */
async function getProductosDisponibles(
    supabaseUrl: string, 
    serviceRoleKey: string, 
    url: URL, 
    corsHeaders: Record<string, string>,
    isAuthenticated: boolean
) {
    const busqueda = url.searchParams.get('busqueda') || '';
    const categoria = url.searchParams.get('categoria') || 'todos';
    const marca = url.searchParams.get('marca') || '';
    const limite = parseInt(url.searchParams.get('limit') || '100');
    const solo_con_stock = url.searchParams.get('solo_con_stock') === 'true';

    console.log(`📦 Buscando productos - Búsqueda: ${busqueda}, Categoría: ${categoria}`);

    try {
        // Construir query base
        let query = `${supabaseUrl}/rest/v1/precios_proveedor?select=*&fuente=eq.Maxiconsumo Necochea&activo=eq.true`;
        
        // Aplicar filtros
        const filtros = [];
        
        if (busqueda) {
            filtros.push(`or=(nombre.ilike.*${encodeURIComponent(busqueda)}*,marca.ilike.*${encodeURIComponent(busqueda)}*)`);
        }
        
        if (categoria !== 'todos') {
            filtros.push(`categoria=eq.${encodeURIComponent(categoria)}`);
        }
        
        if (marca) {
            filtros.push(`marca=ilike.*${encodeURIComponent(marca)}*`);
        }
        
        if (solo_con_stock) {
            filtros.push(`stock_disponible=gt.0`);
        }
        
        // Agregar filtros a la query
        if (filtros.length > 0) {
            query += '&' + filtros.join('&');
        }
        
        query += `&order=nombre.asc&limit=${limite}`;

        const response = await fetch(query, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`,
            }
        });

        if (!response.ok) {
            throw new Error(`Error obteniendo productos: ${response.statusText}`);
        }

        const productos = await response.json();

        // Obtener estadísticas por categoría
        const categoriasStats = await obtenerEstadisticasCategorias(supabaseUrl, serviceRoleKey);

        const resultado = {
            success: true,
            data: {
                productos: productos,
                estadisticas: {
                    total_productos: productos.length,
                    productos_con_stock: productos.filter((p: any) => p.stock_disponible > 0).length,
                    marcas_unicas: [...new Set(productos.map((p: any) => p.marca).filter(Boolean))].length,
                    categorias_disponibles: categoriasStats
                },
                filtros_aplicados: {
                    busqueda: busqueda,
                    categoria: categoria,
                    marca: marca,
                    solo_con_stock: solo_con_stock
                },
                timestamp: new Date().toISOString()
            }
        };

        return new Response(JSON.stringify(resultado), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('❌ Error obteniendo productos disponibles:', error);
        throw error;
    }
}

/**
 * GET /proveedor/comparacion - Comparación con sistema
 */
async function getComparacionConSistema(
    supabaseUrl: string, 
    serviceRoleKey: string, 
    url: URL, 
    corsHeaders: Record<string, string>,
    isAuthenticated: boolean
) {
    const solo_oportunidades = url.searchParams.get('solo_oportunidades') === 'true';
    const min_diferencia = parseFloat(url.searchParams.get('min_diferencia') || '0');
    const limite = parseInt(url.searchParams.get('limit') || '50');
    const orden = url.searchParams.get('orden') || 'diferencia_absoluta_desc';

    console.log(`🔄 Comparación - Solo oportunidades: ${solo_oportunidades}, Min diferencia: ${min_diferencia}`);

    try {
        // Construir query para vista de oportunidades
        let query = `${supabaseUrl}/rest/v1/vista_oportunidades_ahorro?select=*`;
        
        if (solo_oportunidades) {
            query += `&diferencia_porcentual=gte.${min_diferencia}`;
        }
        
        // Aplicar ordenamiento
        switch (orden) {
            case 'diferencia_absoluta_desc':
                query += `&order=diferencia_absoluta.desc`;
                break;
            case 'diferencia_absoluta_asc':
                query += `&order=diferencia_absoluta.asc`;
                break;
            case 'diferencia_porcentual_desc':
                query += `&order=diferencia_porcentual.desc`;
                break;
            case 'nombre_asc':
                query += `&order=nombre_producto.asc`;
                break;
            default:
                query += `&order=diferencia_absoluta.desc`;
        }
        
        query += `&limit=${limite}`;

        const response = await fetch(query, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`,
            }
        });

        if (!response.ok) {
            throw new Error(`Error obteniendo comparación: ${response.statusText}`);
        }

        const oportunidades = await response.json();

        // Calcular estadísticas de comparación
        const estadisticas = calcularEstadisticasComparacion(oportunidades);

        const resultado = {
            success: true,
            data: {
                oportunidades: oportunidades,
                estadisticas: estadisticas,
                filtros_aplicados: {
                    solo_oportunidades: solo_oportunidades,
                    min_diferencia: min_diferencia,
                    orden: orden
                },
                timestamp: new Date().toISOString()
            }
        };

        return new Response(JSON.stringify(resultado), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('❌ Error obteniendo comparación:', error);
        throw error;
    }
}

/**
 * POST /proveedor/sincronizar - Trigger sincronización manual
 */
async function triggerSincronizacion(
    supabaseUrl: string, 
    serviceRoleKey: string, 
    url: URL, 
    corsHeaders: Record<string, string>,
    isAuthenticated: boolean
) {
    // Verificar autenticación para sincronización manual
    if (!isAuthenticated) {
        return new Response(JSON.stringify({
            success: false,
            error: {
                code: 'AUTH_REQUIRED',
                message: 'Se requiere autenticación para sincronizar manualmente'
            }
        }), {
            status: 401,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }

    const categoria = url.searchParams.get('categoria') || 'todos';
    const force_full = url.searchParams.get('force_full') === 'true';

    console.log(`🔄 Sincronización manual - Categoría: ${categoria}, Forzar completa: ${force_full}`);

    try {
        // Llamar al scraper con parámetros específicos
        const scrapingUrl = `${supabaseUrl}/functions/v1/scraper-maxiconsumo/scrape?categoria=${encodeURIComponent(categoria)}`;
        
        const response = await fetch(scrapingUrl, {
            method: 'POST',
            headers: {
                'Authorization': req.headers.get('Authorization') || '',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                trigger_type: 'manual',
                force_full: force_full,
                categoria: categoria,
                initiated_by: 'api_proveedor_manual'
            })
        });

        if (!response.ok) {
            throw new Error(`Error en sincronización: ${response.statusText}`);
        }

        const resultadoScraping = await response.json();

        // Si la sincronización fue exitosa, generar comparaciones
        let resultadoComparacion = null;
        if (resultadoScraping.success) {
            try {
                const comparacionUrl = `${supabaseUrl}/functions/v1/scraper-maxiconsumo/compare`;
                const comparacionResponse = await fetch(comparacionUrl, {
                    method: 'POST',
                    headers: {
                        'Authorization': req.headers.get('Authorization') || '',
                        'Content-Type': 'application/json'
                    }
                });

                if (comparacionResponse.ok) {
                    resultadoComparacion = await comparacionResponse.json();
                }
            } catch (error) {
                console.warn('Error generando comparaciones automáticas:', error.message);
            }
        }

        const resultado = {
            success: true,
            data: {
                sincronizacion: resultadoScraping,
                comparacion_generada: resultadoComparacion,
                parametros: {
                    categoria: categoria,
                    force_full: force_full,
                    timestamp: new Date().toISOString()
                }
            }
        };

        return new Response(JSON.stringify(resultado), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('❌ Error en sincronización manual:', error);
        throw error;
    }
}

/**
 * GET /proveedor/status - Estado del sistema
 */
async function getEstadoSistema(
    supabaseUrl: string, 
    serviceRoleKey: string, 
    url: URL, 
    corsHeaders: Record<string, string>
) {
    console.log('📊 Obteniendo estado del sistema...');

    try {
        // Obtener estadísticas del último scraping
        const estadisticasResponse = await fetch(
            `${supabaseUrl}/rest/v1/estadisticas_scraping?select=*&order=created_at.desc&limit=1`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`,
                }
            }
        );

        let ultimaEstadistica = null;
        if (estadisticasResponse.ok) {
            const stats = await estadisticasResponse.json();
            ultimaEstadistica = stats[0] || null;
        }

        // Obtener productos totales del proveedor
        const productosTotalesResponse = await fetch(
            `${supabaseUrl}/rest/v1/precios_proveedor?select=count&fuente=eq.Maxiconsumo Necochea&activo=eq.true`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`,
                }
            }
        );

        let totalProductos = 0;
        if (productosTotalesResponse.ok) {
            const countData = await productosTotalesResponse.json();
            totalProductos = countData[0]?.count || 0;
        }

        // Obtener oportunidades de ahorro activas
        const oportunidadesResponse = await fetch(
            `${supabaseUrl}/rest/v1/vista_oportunidades_ahorro?select=count`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`,
                }
            }
        );

        let totalOportunidades = 0;
        if (oportunidadesResponse.ok) {
            const countData = await oportunidadesResponse.json();
            totalOportunidades = countData[0]?.count || 0;
        }

        // Obtener configuración actual
        const configResponse = await fetch(
            `${supabaseUrl}/rest/v1/configuracion_proveedor?select=*&nombre=eq.Maxiconsumo Necochea`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`,
                }
            }
        );

        let configuracion = null;
        if (configResponse.ok) {
            const config = await configResponse.json();
            configuracion = config[0] || null;
        }

        const resultado = {
            success: true,
            data: {
                sistema: {
                    estado: 'operativo',
                    version: '1.0.0',
                    proveedor: 'Maxiconsumo Necochea'
                },
                estadisticas: {
                    ultima_ejecucion: ultimaEstadistica?.created_at || 'Nunca',
                    productos_totales: totalProductos,
                    oportunidades_activas: totalOportunidades,
                    ultima_sincronizacion: configuracion?.ultima_sincronizacion || 'Nunca',
                    proximo_scrape_programado: calcularProximoScrape(configuracion)
                },
                configuracion: configuracion,
                endpoints_disponibles: [
                    'GET /proveedor/precios',
                    'GET /proveedor/productos', 
                    'GET /proveedor/comparacion',
                    'POST /proveedor/sincronizar',
                    'GET /proveedor/status',
                    'GET /proveedor/alertas',
                    'GET /proveedor/estadisticas',
                    'GET /proveedor/configuracion'
                ],
                timestamp: new Date().toISOString()
            }
        };

        return new Response(JSON.stringify(resultado), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('❌ Error obteniendo estado del sistema:', error);
        throw error;
    }
}

/**
 * GET /proveedor/alertas - Alertas activas
 */
async function getAlertasActivas(
    supabaseUrl: string, 
    serviceRoleKey: string, 
    url: URL, 
    corsHeaders: Record<string, string>,
    isAuthenticated: boolean
) {
    const severidad = url.searchParams.get('severidad') || 'todos';
    const tipo = url.searchParams.get('tipo') || 'todos';
    const limite = parseInt(url.searchParams.get('limit') || '20');
    const solo_no_procesadas = url.searchParams.get('solo_no_procesadas') !== 'false';

    console.log(`🚨 Obteniendo alertas - Severidad: ${severidad}, Solo no procesadas: ${solo_no_procesadas}`);

    try {
        // Construir query para vista de alertas activas
        let query = `${supabaseUrl}/rest/v1/vista_alertas_activas?select=*`;
        
        const filtros = [];
        
        if (severidad !== 'todos') {
            filtros.push(`severidad=eq.${severidad}`);
        }
        
        if (tipo !== 'todos') {
            filtros.push(`tipo_cambio=eq.${tipo}`);
        }
        
        if (filtros.length > 0) {
            query += '&' + filtros.join('&');
        }
        
        query += `&order=fecha_alerta.desc&limit=${limite}`;

        const response = await fetch(query, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`,
            }
        });

        if (!response.ok) {
            throw new Error(`Error obteniendo alertas: ${response.statusText}`);
        }

        const alertas = await response.json();

        // Estadísticas de alertas
        const estadisticas = {
            total_alertas: alertas.length,
            criticas: alertas.filter((a: any) => a.severidad === 'critica').length,
            altas: alertas.filter((a: any) => a.severidad === 'alta').length,
            medias: alertas.filter((a: any) => a.severidad === 'media').length,
            bajas: alertas.filter((a: any) => a.severidad === 'baja').length,
            aumentos: alertas.filter((a: any) => a.tipo_cambio === 'aumento').length,
            disminuciones: alertas.filter((a: any) => a.tipo_cambio === 'disminucion').length,
            nuevos_productos: alertas.filter((a: any) => a.tipo_cambio === 'nuevo_producto').length
        };

        const resultado = {
            success: true,
            data: {
                alertas: alertas,
                estadisticas: estadisticas,
                filtros_aplicados: {
                    severidad: severidad,
                    tipo: tipo,
                    solo_no_procesadas: solo_no_procesadas
                },
                timestamp: new Date().toISOString()
            }
        };

        return new Response(JSON.stringify(resultado), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('❌ Error obteniendo alertas:', error);
        throw error;
    }
}

/**
 * GET /proveedor/estadisticas - Métricas de scraping
 */
async function getEstadisticasScraping(
    supabaseUrl: string, 
    serviceRoleKey: string, 
    url: URL, 
    corsHeaders: Record<string, string>,
    isAuthenticated: boolean
) {
    const dias = parseInt(url.searchParams.get('dias') || '7');
    const categoria = url.searchParams.get('categoria') || '';

    console.log(`📈 Obteniendo estadísticas - Días: ${dias}, Categoría: ${categoria}`);

    try {
        // Calcular fecha de inicio
        const fechaInicio = new Date();
        fechaInicio.setDate(fechaInicio.getDate() - dias);
        
        let query = `${supabaseUrl}/rest/v1/estadisticas_scraping?select=*&created_at=gte.${fechaInicio.toISOString()}&order=created_at.desc`;
        
        if (categoria) {
            query += `&categoria_procesada=eq.${encodeURIComponent(categoria)}`;
        }

        const response = await fetch(query, {
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`,
            }
        });

        if (!response.ok) {
            throw new Error(`Error obteniendo estadísticas: ${response.statusText}`);
        }

        const estadisticas = await response.json();

        // Calcular métricas agregadas
        const metricas = calcularMetricasScraping(estadisticas);

        const resultado = {
            success: true,
            data: {
                estadisticas_periodo: estadisticas,
                metricas_agregadas: metricas,
                parametros: {
                    dias_analizados: dias,
                    categoria: categoria,
                    fecha_inicio: fechaInicio.toISOString(),
                    fecha_fin: new Date().toISOString()
                },
                timestamp: new Date().toISOString()
            }
        };

        return new Response(JSON.stringify(resultado), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('❌ Error obteniendo estadísticas:', error);
        throw error;
    }
}

/**
 * GET /proveedor/configuracion - Configuración del proveedor
 */
async function getConfiguracionProveedor(
    supabaseUrl: string, 
    serviceRoleKey: string, 
    url: URL, 
    corsHeaders: Record<string, string>,
    isAuthenticated: boolean
) {
    // La configuración requiere autenticación
    if (!isAuthenticated) {
        return new Response(JSON.stringify({
            success: false,
            error: {
                code: 'AUTH_REQUIRED',
                message: 'Se requiere autenticación para ver la configuración'
            }
        }), {
            status: 401,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }

    console.log('⚙️ Obteniendo configuración del proveedor...');

    try {
        const response = await fetch(
            `${supabaseUrl}/rest/v1/configuracion_proveedor?select=*&nombre=eq.Maxiconsumo Necochea`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`,
                }
            }
        );

        if (!response.ok) {
            throw new Error(`Error obteniendo configuración: ${response.statusText}`);
        }

        const configuraciones = await response.json();
        const configuracion = configuraciones[0] || null;

        const resultado = {
            success: true,
            data: {
                configuracion: configuracion,
                parametros_disponibles: {
                    frecuencia_scraping: ['cada_hora', 'diaria', 'semanal'],
                    severidad_alertas: ['baja', 'media', 'alta', 'critica'],
                    tipos_cambio: ['aumento', 'disminucion', 'nuevo_producto']
                },
                timestamp: new Date().toISOString()
            }
        };

        return new Response(JSON.stringify(resultado), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('❌ Error obteniendo configuración:', error);
        throw error;
    }
}

/**
 * FUNCIONES AUXILIARES
 */

/**
 * Obtener estadísticas por categorías
 */
async function obtenerEstadisticasCategorias(supabaseUrl: string, serviceRoleKey: string) {
    try {
        const response = await fetch(
            `${supabaseUrl}/rest/v1/precios_proveedor?select=categoria&fuente=eq.Maxiconsumo Necochea&activo=eq.true`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`,
                }
            }
        );

        if (!response.ok) return [];

        const productos = await response.json();
        
        // Agrupar por categoría
        const categorias = productos.reduce((acc: any, producto: any) => {
            const cat = producto.categoria || 'Sin categoría';
            acc[cat] = (acc[cat] || 0) + 1;
            return acc;
        }, {});

        return Object.entries(categorias).map(([nombre, cantidad]) => ({
            categoria: nombre,
            cantidad_productos: cantidad
        }));

    } catch (error) {
        console.error('Error obteniendo estadísticas por categorías:', error);
        return [];
    }
}

/**
 * Calcular estadísticas de comparación
 */
function calcularEstadisticasComparacion(oportunidades: any[]) {
    if (oportunidades.length === 0) {
        return {
            total_oportunidades: 0,
            ahorro_total_estimado: 0,
            oportunidad_promedio: 0,
            mejor_oportunidad: null
        };
    }

    const ahorroTotal = oportunidades.reduce((sum, opp) => sum + opp.diferencia_absoluta, 0);
    const oportunidadPromedio = ahorroTotal / oportunidades.length;
    const mejorOportunidad = oportunidades.reduce((best, opp) => 
        opp.diferencia_absoluta > best.diferencia_absoluta ? opp : best
    );

    return {
        total_oportunidades: oportunidades.length,
        ahorro_total_estimado: Math.round(ahorroTotal * 100) / 100,
        oportunidad_promedio: Math.round(oportunidadPromedio * 100) / 100,
        mejor_oportunidad: mejorOportunidad
    };
}

/**
 * Calcular métricas de scraping
 */
function calcularMetricasScraping(estadisticas: any[]) {
    if (estadisticas.length === 0) {
        return {
            total_ejecuciones: 0,
            productos_promedio: 0,
            tasa_exito: 0,
            tiempo_promedio: 0
        };
    }

    const totalEjecuciones = estadisticas.length;
    const productosTotales = estadisticas.reduce((sum, stat) => sum + (stat.productos_encontrados || 0), 0);
    const productosPromedio = Math.round(productosTotales / totalEjecuciones);
    const ejecucionesExitosas = estadisticas.filter(stat => stat.status === 'exitoso').length;
    const tasaExito = Math.round((ejecucionesExitosas / totalEjecuciones) * 100);
    const tiempoTotal = estadisticas.reduce((sum, stat) => sum + (stat.tiempo_ejecucion_ms || 0), 0);
    const tiempoPromedio = Math.round(tiempoTotal / totalEjecuciones);

    return {
        total_ejecuciones: totalEjecuciones,
        productos_promedio: productosPromedio,
        tasa_exito: tasaExito,
        tiempo_promedio_ms: tiempoPromedio
    };
}

/**
 * Calcular próximo scrape programado
 */
function calcularProximoScrape(configuracion: any): string {
    if (!configuracion?.proxima_sincronizacion) {
        // Si no hay configuración, programar para las próximas 6 horas
        const proximo = new Date();
        proximo.setHours(proximo.getHours() + 6);
        return proximo.toISOString();
    }
    
    return configuracion.proxima_sincronizacion;
}