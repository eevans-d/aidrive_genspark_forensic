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

        // Obtener tareas pendientes que necesitan notificación
        const tareasResponse = await fetch(
            `${supabaseUrl}/rest/v1/tareas_pendientes?estado=eq.pendiente&select=*`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`,
                }
            }
        );

        if (!tareasResponse.ok) {
            throw new Error('Error al obtener tareas pendientes');
        }

        const tareas = await tareasResponse.json();
        const notificacionesEnviadas = [];
        const errores = [];

        for (const tarea of tareas) {
            try {
                // Verificar si ya se envió notificación en las últimas 2 horas
                const dosHorasAtras = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
                
                const ultimaNotifResponse = await fetch(
                    `${supabaseUrl}/rest/v1/notificaciones_tareas?tarea_id=eq.${tarea.id}&fecha_envio=gte.${dosHorasAtras}&order=fecha_envio.desc&limit=1`,
                    {
                        headers: {
                            'apikey': serviceRoleKey,
                            'Authorization': `Bearer ${serviceRoleKey}`,
                        }
                    }
                );

                if (!ultimaNotifResponse.ok) {
                    throw new Error(`Error al verificar notificaciones de tarea ${tarea.titulo}`);
                }

                const ultimasNotif = await ultimaNotifResponse.json();

                // Si no hay notificación reciente o han pasado más de 2 horas, enviar nueva
                if (ultimasNotif.length === 0) {
                    const mensaje = `Recordatorio: Tarea "${tarea.titulo}" asignada a ${tarea.asignada_a_nombre || 'ti'}. Prioridad: ${tarea.prioridad}. Vence: ${tarea.fecha_vencimiento ? new Date(tarea.fecha_vencimiento).toLocaleString('es-AR') : 'Sin fecha'}`;

                    // Crear notificación
                    const notifResponse = await fetch(
                        `${supabaseUrl}/rest/v1/notificaciones_tareas`,
                        {
                            method: 'POST',
                            headers: {
                                'apikey': serviceRoleKey,
                                'Authorization': `Bearer ${serviceRoleKey}`,
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                tarea_id: tarea.id,
                                tipo: 'recordatorio_automatico',
                                mensaje: mensaje,
                                usuario_destino_nombre: tarea.asignada_a_nombre,
                                usuario_destino_id: tarea.asignada_a_id,
                                leido: false
                            })
                        }
                    );

                    if (notifResponse.ok) {
                        notificacionesEnviadas.push({
                            tarea: tarea.titulo,
                            asignado_a: tarea.asignada_a_nombre,
                            prioridad: tarea.prioridad
                        });
                    }
                }

            } catch (error) {
                errores.push(`Error procesando tarea ${tarea.titulo}: ${error.message}`);
            }
        }

        return new Response(JSON.stringify({
            success: true,
            data: {
                tareas_procesadas: tareas.length,
                notificaciones_enviadas: notificacionesEnviadas.length,
                notificaciones: notificacionesEnviadas,
                errores: errores,
                timestamp: new Date().toISOString()
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Error en notificaciones:', error);

        return new Response(JSON.stringify({
            error: {
                code: 'NOTIFICATION_ERROR',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
