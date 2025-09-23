const fs = require('fs');
const analysis = JSON.parse(fs.readFileSync('aidrive_genspark_analysis.json'));

console.log(`# ESPECIFICACIÓN TÉCNICA - ${analysis.project_name.toUpperCase()}

**Directorio:** ${analysis.project_path}
**Total de archivos:** ${analysis.total_files}

## RESUMEN ARQUITECTÓNICO
Este es un proyecto que contiene múltiples componentes relacionados con IA y desarrollo web.

## TIPOS DE ARCHIVO
${Object.entries(analysis.file_types)
  .sort(([,a], [,b]) => b - a)
  .map(([ext, count]) => `- ${ext || 'sin extensión'}: ${count} archivos`)
  .join('\n')}

## ARCHIVOS DE CONFIGURACIÓN DETECTADOS
${analysis.config_files.length > 0 ? analysis.config_files.map(file => `- ${file}`).join('\n') : 'No se detectaron archivos de configuración estándar'}

## DEPENDENCIAS PRINCIPALES
${analysis.dependencies ? 
  `### Dependencies
${JSON.stringify(analysis.dependencies.dependencies || {}, null, 2)}

### DevDependencies  
${JSON.stringify(analysis.dependencies.devDependencies || {}, null, 2)}` : 
  'No se encontró package.json'}

## DOCUMENTACIÓN README
${analysis.readme ? analysis.readme.substring(0, 1500) + (analysis.readme.length > 1500 ? '...' : '') : 'No se encontró README principal'}

## ESTRUCTURA DE DIRECTORIOS
${Object.keys(analysis.structure).length > 0 ? 
  Object.keys(analysis.structure).map(dir => `- ${dir}/`).join('\n') : 
  'Proyecto de estructura plana'}

## ARCHIVOS DE CÓDIGO PRINCIPALES (Top 15)
${analysis.code_files
  .sort((a, b) => b.size - a.size)
  .slice(0, 15)
  .map(file => `
### ${file.path} (${file.extension})
\
\
${file.preview}
\
\
`).join('')}

## CONTEXTO PARA IAS
Este proyecto "${analysis.project_name}" es parte del ecosistema ProyectosIA y contiene ${analysis.total_files} archivos distribuidos en ${Object.keys(analysis.file_types).length} tipos diferentes. 

**Patrones identificados:**
- Proyecto multi-tecnología con componentes web y Python
- Posible sistema de análisis o procesamiento de datos
- Arquitectura modular basada en directorios especializados

**Para desarrollo futuro considerar:**
- Integración de componentes existentes
- Optimización de estructura de archivos
- Documentación de APIs y interfaces
`);