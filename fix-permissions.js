const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * Fix Python executable permissions after Electron build
 */
exports.default = async function(context) {
  console.log('Fixing Python executable permissions...');
  
  const { appOutDir } = context;
  const appPath = path.join(appOutDir, 'ProKeys.app');
  
  if (fs.existsSync(appPath)) {
    // Fix permissions for the bundled Python executable (now in extraResources)
    const pythonExec = path.join(appPath, 'Contents', 'Resources', 'venv_portable', 'bin', 'python');
    
    if (fs.existsSync(pythonExec)) {
      console.log(`Found Python executable at: ${pythonExec}`);
      try {
        execSync(`chmod +x "${pythonExec}"`);
        console.log('Fixed Python executable permissions');
      } catch (error) {
        console.error('Failed to fix Python permissions:', error.message);
      }
    } else {
      console.log('Python executable not found at expected location');
      console.log(`Expected location: ${pythonExec}`);
      
      // Debug: list what's actually in Resources
      const resourcesDir = path.join(appPath, 'Contents', 'Resources');
      if (fs.existsSync(resourcesDir)) {
        console.log('Contents of Resources directory:');
        const contents = fs.readdirSync(resourcesDir);
        contents.forEach(item => {
          console.log(`  - ${item}`);
        });
      }
    }
    
    // Also fix permissions for any other executables in venv_portable/bin
    const venvBin = path.join(appPath, 'Contents', 'Resources', 'venv_portable', 'bin');
    if (fs.existsSync(venvBin)) {
      console.log('Fixing permissions for all venv executables...');
      try {
        const files = fs.readdirSync(venvBin);
        files.forEach(file => {
          const filePath = path.join(venvBin, file);
          if (fs.statSync(filePath).isFile()) {
            execSync(`chmod +x "${filePath}"`);
          }
        });
        console.log('Fixed venv executable permissions');
      } catch (error) {
        console.error('Failed to fix venv permissions:', error.message);
      }
    }
  } else {
    console.log(`App bundle not found at: ${appPath}`);
  }
};