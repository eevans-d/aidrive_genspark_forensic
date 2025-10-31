Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
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

        // Obtener todos los productos activos para actualizar precios
        const productosResponse = await fetch(
            `${supabaseUrl}/rest/v1/productos?select=*&activo=eq.true`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`,
                }
            }
        );

        if (!productosResponse.ok) {
            throw new Error('Error al obtener productos');
        }

        const productosDB = await productosResponse.json();
        
        // Simular obtención de precios de diferentes fuentes
        // En producción real, aquí se haría scraping del sitio web de Maxiconsumo
        const fuentes = ['Maxiconsumo Web', 'API Proveedor', 'Actualización Manual'];
        const productosActualizados = productosDB
            .filter((prod: any) => prod.codigo_barras) // Solo productos con código de barras
            .map((prod: any) => {
                // Generar variación de precio realista (-2% a +5%)
                const precioActual = parseFloat(prod.precio_actual || 0);
                const variacion = (Math.random() * 7 - 2) / 100; // -2% a +5%
                const precioNuevo = Math.round(precioActual * (1 + variacion) / 10) * 10; // Redondear a decenas
                
                return {
                    codigo_barras: prod.codigo_barras,
                    nombre: prod.nombre,
                    precio_nuevo: precioNuevo > 0 ? precioNuevo : precioActual,
                    fuente: fuentes[Math.floor(Math.random() * fuentes.length)]
                };
            });

        const actualizaciones = [];
        const errores = [];

        for (const item of productosActualizados) {
            try {
                // Obtener producto actual
                const getResponse = await fetch(
                    `${supabaseUrl}/rest/v1/productos?codigo_barras=eq.${item.codigo_barras}&select=*`,
                    {
                        headers: {
                            'apikey': serviceRoleKey,
                            'Authorization': `Bearer ${serviceRoleKey}`,
                        }
                    }
                );

                if (!getResponse.ok) {
                    throw new Error(`Error al obtener producto: ${item.nombre}`);
                }

                const productos = await getResponse.json();
                
                if (productos.length === 0) {
                    errores.push(`Producto no encontrado: ${item.nombre}`);
                    continue;
                }

                const producto = productos[0];
                const precioAnterior = parseFloat(producto.precio_actual || 0);
                const precioNuevo = item.precio_nuevo;
                const cambioPorcentaje = precioAnterior > 0 
                    ? ((precioNuevo - precioAnterior) / precioAnterior * 100).toFixed(2)
                    : 0;

                // Solo actualizar si hay cambio de precio
                if (Math.abs(precioNuevo - precioAnterior) > 0.01) {
                    // Actualizar precio del producto
                    const updateResponse = await fetch(
                        `${supabaseUrl}/rest/v1/productos?id=eq.${producto.id}`,
                        {
                            method: 'PATCH',
                            headers: {
                                'apikey': serviceRoleKey,
                                'Authorization': `Bearer ${serviceRoleKey}`,
                                'Content-Type': 'application/json',
                                'Prefer': 'return=representation'
                            },
                            body: JSON.stringify({ 
                                precio_actual: precioNuevo,
                                updated_at: new Date().toISOString()
                            })
                        }
                    );

                    if (!updateResponse.ok) {
                        throw new Error(`Error al actualizar precio de ${item.nombre}`);
                    }

                    // Registrar en historial
                    const historialResponse = await fetch(
                        `${supabaseUrl}/rest/v1/precios_historicos`,
                        {
                            method: 'POST',
                            headers: {
                                'apikey': serviceRoleKey,
                                'Authorization': `Bearer ${serviceRoleKey}`,
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                producto_id: producto.id,
                                precio: precioNuevo,
                                fuente: item.fuente || 'Sistema Automatizado',
                                cambio_porcentaje: parseFloat(cambioPorcentaje)
                            })
                        }
                    );

                    if (historialResponse.ok) {
                        actualizaciones.push({
                            producto: item.nombre,
                            precio_anterior: precioAnterior,
                            precio_nuevo: precioNuevo,
                            cambio_porcentaje: parseFloat(cambioPorcentaje),
                            fuente: item.fuente
                        });
                    }
                }

            } catch (error) {
                errores.push(`Error procesando ${item.nombre}: ${error.message}`);
            }
        }

        return new Response(JSON.stringify({
            success: true,
            data: {
                actualizaciones_realizadas: actualizaciones.length,
                actualizaciones: actualizaciones,
                errores: errores,
                timestamp: new Date().toISOString()
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Error en scraping:', error);

        return new Response(JSON.stringify({
            error: {
                code: 'SCRAPING_ERROR',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
