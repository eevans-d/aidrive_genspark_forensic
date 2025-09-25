// Funciones base compartidas por todas las páginas
function formatNumber(num){return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");}
function updateTimestamp(){const now=new Date();const ts=now.toLocaleString('es-AR');document.querySelectorAll('.timestamp').forEach(el=>el.textContent=ts);}updateTimestamp();setInterval(updateTimestamp,60000);

function showAlert(message,type='info'){const alertDiv=document.createElement('div');alertDiv.className=`alert alert-${type} alert-dismissible fade show`;alertDiv.innerHTML=`${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;const container=document.querySelector('.main-content');if(container){container.insertBefore(alertDiv,container.firstChild);}setTimeout(()=>{alertDiv&&alertDiv.remove();},5000);}

async function loadData(url){try{const headers={};const apiKeyMeta=document.querySelector('meta[name="x-api-key"]');if(apiKeyMeta&&apiKeyMeta.content){headers['X-API-Key']=apiKeyMeta.content;}const resp=await fetch(url,{headers});if(!resp.ok) throw new Error(`HTTP ${resp.status}`);return await resp.json();}catch(e){console.error('Error loading data:',e);showAlert('Error cargando datos: '+e.message,'danger');return null;}}

async function refreshMetrics(){const data=await loadData('/api/summary');if(data){const metrics={'total-proveedores':data.total_proveedores,'total-pedidos':data.total_pedidos,'productos-pedidos':data.total_productos_pedidos,'movimientos':data.total_movimientos};Object.entries(metrics).forEach(([id,val])=>{const el=document.getElementById(id);if(el) el.textContent=formatNumber(val);});}}
setInterval(refreshMetrics,300000);
