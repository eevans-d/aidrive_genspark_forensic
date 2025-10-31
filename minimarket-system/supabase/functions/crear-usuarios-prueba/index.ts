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

        // Usuarios de prueba a crear
        const usuariosPrueba = [
            { email: 'admin@minimarket.com', password: 'password123', nombre: 'Admin Sistema', rol: 'Administrador' },
            { email: 'deposito@minimarket.com', password: 'password123', nombre: 'Juan Depósito', rol: 'Encargado Depósito' },
            { email: 'ventas@minimarket.com', password: 'password123', nombre: 'María Ventas', rol: 'Vendedora' },
        ];

        const usuariosCreados = [];
        const errores = [];

        for (const usuario of usuariosPrueba) {
            try {
                // Crear usuario en Auth
                const authResponse = await fetch(`${supabaseUrl}/auth/v1/admin/users`, {
                    method: 'POST',
                    headers: {
                        'apikey': serviceRoleKey,
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: usuario.email,
                        password: usuario.password,
                        email_confirm: true,
                        user_metadata: {
                            nombre: usuario.nombre
                        }
                    })
                });

                if (!authResponse.ok) {
                    const errorText = await authResponse.text();
                    // Si el usuario ya existe, continuar
                    if (errorText.includes('already registered') || errorText.includes('User already registered')) {
                        usuariosCreados.push({
                            email: usuario.email,
                            nombre: usuario.nombre,
                            rol: usuario.rol,
                            nota: 'Usuario ya existía'
                        });
                        continue;
                    }
                    throw new Error(`Error creando usuario ${usuario.email}: ${errorText}`);
                }

                const authData = await authResponse.json();
                
                // Validar que se haya creado el usuario
                if (!authData || !authData.id) {
                    console.error('Respuesta inesperada de Auth:', authData);
                    throw new Error('No se pudo crear el usuario en Auth');
                }

                // Crear o actualizar registro en tabla personal
                const personalResponse = await fetch(`${supabaseUrl}/rest/v1/personal`, {
                    method: 'POST',
                    headers: {
                        'apikey': serviceRoleKey,
                        'Authorization': `Bearer ${serviceRoleKey}`,
                        'Content-Type': 'application/json',
                        'Prefer': 'resolution=merge-duplicates'
                    },
                    body: JSON.stringify({
                        user_auth_id: authData.id,
                        nombre: usuario.nombre,
                        email: usuario.email,
                        rol: usuario.rol,
                        activo: true
                    })
                });

                if (personalResponse.ok) {
                    usuariosCreados.push({
                        email: usuario.email,
                        nombre: usuario.nombre,
                        rol: usuario.rol
                    });
                }

            } catch (error: any) {
                // Si el error es que el usuario ya existe, no es un error crítico
                if (error.message.includes('already registered')) {
                    usuariosCreados.push({
                        email: usuario.email,
                        nombre: usuario.nombre,
                        rol: usuario.rol,
                        nota: 'Ya existía'
                    });
                } else {
                    errores.push(`Error con ${usuario.email}: ${error.message}`);
                }
            }
        }

        return new Response(JSON.stringify({
            success: true,
            data: {
                usuarios_creados: usuariosCreados.length,
                usuarios: usuariosCreados,
                errores: errores,
                timestamp: new Date().toISOString()
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error: any) {
        console.error('Error en creación de usuarios:', error);

        return new Response(JSON.stringify({
            error: {
                code: 'CREATE_USERS_ERROR',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
