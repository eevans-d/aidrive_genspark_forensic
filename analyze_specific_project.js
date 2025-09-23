const fs = require('fs');
const path = require('path');

function analyzeProject(targetDir = '.') {
    const analysis = {
        project_name: path.basename(path.resolve(targetDir)),
        project_path: path.resolve(targetDir),
        structure: {},
        files: [],
        dependencies: null,
        readme: null,
        config_files: [],
        file_types: {},
        total_files: 0,
        code_files: []
    };
    
    function scanDirectory(dirPath, relativePath = '') {
        try {
            const items = fs.readdirSync(dirPath);
            
            items.forEach(item => {
                // Ignorar directorios y archivos innecesarios
                if (item.startsWith('.') || 
                    item === 'node_modules' || 
                    item === '__pycache__' || 
                    item === 'venv' ||
                    item === '.git' ||
                    item.includes('egg-info')) return;
                
                const fullPath = path.join(dirPath, item);
                const relPath = path.join(relativePath, item);
                
                try {
                    const stats = fs.statSync(fullPath);
                    
                    if (stats.isDirectory()) {
                        analysis.structure[relPath] = scanDirectory(fullPath, relPath);
                    } else {
                        analysis.total_files++;
                        const ext = path.extname(item);
                        analysis.file_types[ext] = (analysis.file_types[ext] || 0) + 1;
                        
                        analysis.files.push({
                            path: relPath,
                            size: stats.size,
                            extension: ext
                        });
                        
                        // Analizar archivos de código principales
                        if (['.js', '.py', '.html', '.css', '.json', '.md', '.txt', '.yml', '.yaml', '.toml'].includes(ext)) {
                            try {
                                const content = fs.readFileSync(fullPath, 'utf8');
                                analysis.code_files.push({
                                    path: relPath,
                                    extension: ext,
                                    size: stats.size,
                                    preview: content.substring(0, 300) + (content.length > 300 ? '...' : '')
                                });
                            } catch (err) {
                                // Ignorar archivos binarios o con problemas de encoding
                            }
                        }
                        
                        // Analizar archivos especiales
                        if (item === 'package.json') {
                            try {
                                analysis.dependencies = JSON.parse(fs.readFileSync(fullPath));
                            } catch (err) {}
                        }
                        if (item.toLowerCase().includes('readme')) {
                            try {
                                analysis.readme = fs.readFileSync(fullPath, 'utf8');
                            } catch (err) {}
                        }
                        if (['package.json', 'requirements.txt', 'pyproject.toml', 'Dockerfile', 'docker-compose.yml', 'Makefile'].includes(item)) {
                            analysis.config_files.push(relPath);
                        }
                    }
                } catch (err) {
                    console.error(`Error processing ${fullPath}: ${err.message}`);
                }
            });
        } catch (err) {
            console.error(`Error reading directory ${dirPath}: ${err.message}`);
        }
    }
    
    scanDirectory(targetDir);
    return analysis;
}

// Usar directorio actual (que debe ser aidrive_genspark)
console.log(JSON.stringify(analyzeProject('.'), null, 2));