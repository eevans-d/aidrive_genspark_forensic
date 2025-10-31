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

        // Obtener stock del depósito
        const stockResponse = await fetch(
            `${supabaseUrl}/rest/v1/stock_deposito?select=*`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`,
                }
            }
        );

        if (!stockResponse.ok) {
            throw new Error('Error al obtener stock');
        }

        const stockItems = await stockResponse.json();
        const alertas = [];
        const productosConAlerta = [];

        for (const item of stockItems) {
            // Verificar si está por debajo del mínimo
            if (item.cantidad_actual <= item.cantidad_minima) {
                try {
                    // Obtener información del producto
                    const prodResponse = await fetch(
                        `${supabaseUrl}/rest/v1/productos?id=eq.${item.producto_id}&select=*`,
                        {
                            headers: {
                                'apikey': serviceRoleKey,
                                'Authorization': `Bearer ${serviceRoleKey}`,
                            }
                        }
                    );

                    if (!prodResponse.ok) {
                        continue;
                    }

                    const productos = await prodResponse.json();
                    
                    if (productos.length > 0) {
                        const producto = productos[0];
                        
                        // Obtener proveedor
                        let proveedorNombre = 'Sin asignar';
                        if (producto.proveedor_principal_id) {
                            const provResponse = await fetch(
                                `${supabaseUrl}/rest/v1/proveedores?id=eq.${producto.proveedor_principal_id}&select=nombre`,
                                {
                                    headers: {
                                        'apikey': serviceRoleKey,
                                        'Authorization': `Bearer ${serviceRoleKey}`,
                                    }
                                }
                            );

                            if (provResponse.ok) {
                                const proveedores = await provResponse.json();
                                if (proveedores.length > 0) {
                                    proveedorNombre = proveedores[0].nombre;
                                }
                            }
                        }

                        const nivel = item.cantidad_actual === 0 ? 'crítico' : 
                                     item.cantidad_actual < item.cantidad_minima / 2 ? 'urgente' : 'bajo';

                        alertas.push({
                            producto: producto.nombre,
                            cantidad_actual: item.cantidad_actual,
                            cantidad_minima: item.cantidad_minima,
                            ubicacion: item.ubicacion,
                            proveedor: proveedorNombre,
                            nivel: nivel
                        });

                        productosConAlerta.push(producto.nombre);

                        // Crear tarea automática si está en nivel crítico
                        if (nivel === 'crítico') {
                            const tareaResponse = await fetch(
                                `${supabaseUrl}/rest/v1/tareas_pendientes`,
                                {
                                    method: 'POST',
                                    headers: {
                                        'apikey': serviceRoleKey,
                                        'Authorization': `Bearer ${serviceRoleKey}`,
                                        'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({
                                        titulo: `URGENTE: Stock agotado - ${producto.nombre}`,
                                        descripcion: `El producto ${producto.nombre} está agotado en depósito. Ubicación: ${item.ubicacion}. Proveedor: ${proveedorNombre}`,
                                        prioridad: 'urgente',
                                        estado: 'pendiente',
                                        asignada_a_nombre: 'Encargado Compras',
                                        creada_por_nombre: 'Sistema Automatizado',
                                        fecha_vencimiento: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
                                    })
                                }
                            );

                            if (!tareaResponse.ok) {
                                console.error(`Error creando tarea para ${producto.nombre}`);
                            }
                        }
                    }

                } catch (error) {
                    console.error(`Error procesando item de stock:`, error);
                }
            }
        }

        return new Response(JSON.stringify({
            success: true,
            data: {
                total_items_revisados: stockItems.length,
                alertas_generadas: alertas.length,
                alertas: alertas,
                productos_con_alerta: productosConAlerta,
                timestamp: new Date().toISOString()
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Error en alertas de stock:', error);

        return new Response(JSON.stringify({
            error: {
                code: 'STOCK_ALERT_ERROR',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
