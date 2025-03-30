import os
import json

MODULE_DIR = "./module/"  # Your module folder
PACKAGE_DIR = "./plusscript_packages/"
PACKAGE_DB = "packages.json"

# Ensure directories exist
if not os.path.exists(MODULE_DIR):
    os.makedirs(MODULE_DIR)

# Built-in features (from previous packages.json)
BUILTINS = {
    "core": {"version": "1.0.0", "deps": [], "description": "Core language features", "features": ["variables", "functions", "classes", "async", "threading"]},
    "game": {"version": "1.0.0", "deps": ["core"], "description": "2D and 3D game development tools", "features": ["game", "game3d", "draw", "physics", "animate"]},
    "gui": {"version": "1.0.0", "deps": ["core"], "description": "GUI development with CSS-like styling", "features": ["gui", "style"]},
    "web": {"version": "1.0.0", "deps": ["core"], "description": "Web development tools", "features": ["web", "server", "domain", "api", "keygen", "ws"]},
    "database": {"version": "1.0.0", "deps": ["core"], "description": "Database support", "features": ["sql"]},
    "network": {"version": "1.0.0", "deps": ["core"], "description": "Networking capabilities", "features": ["net", "ws"]},
    "ai": {"version": "1.0.0", "deps": ["core"], "description": "AI and machine learning tools", "features": ["ai", "tensor", "ai_code"]},
    "blockchain": {"version": "1.0.0", "deps": ["core"], "description": "Blockchain interaction", "features": ["blockchain", "block_tx"]},
    "cloud": {"version": "1.0.0", "deps": ["core"], "description": "Cloud computing integration", "features": ["cloud", "cloud_put"]},
    "iot": {"version": "1.0.0", "deps": ["core"], "description": "Internet of Things support", "features": ["iot", "iot_pub"]},
    "crypto": {"version": "1.0.0", "deps": ["core"], "description": "Cryptography tools", "features": ["crypto", "encrypt", "decrypt"]},
    "sci": {"version": "1.0.0", "deps": ["core"], "description": "Scientific computing", "features": ["sci", "sci_solve"]},
    "desktop": {"version": "1.0.0", "deps": ["core"], "description": "Desktop app development", "features": ["desktop"]},
    "devops": {"version": "1.0.0", "deps": ["core"], "description": "DevOps tools", "features": ["devops"]},
    "audio": {"version": "1.0.0", "deps": ["core"], "description": "Audio processing", "features": ["audio"]},
    "realtime": {"version": "1.0.0", "deps": ["core"], "description": "Real-time systems", "features": ["realtime"]},
    "app": {"version": "1.0.0", "deps": ["core"], "description": "Cross-platform app building", "features": ["app", "android", "wasm", "vr", "ar"]},
    "framework": {"version": "1.0.0", "deps": ["core"], "description": "Framework development", "features": ["framework"]},
    "php": {"version": "1.0.0", "deps": ["core"], "description": "PHP integration", "features": ["php"]},
    "gem": {"version": "1.0.0", "deps": ["core"], "description": "Ruby Gems integration", "features": ["gem"]},
    "performance": {"version": "1.0.0", "deps": ["core"], "description": "Performance optimization tools", "features": ["compile", "parallel", "gpu"]},
    "interop": {"version": "1.0.0", "deps": ["core"], "description": "Interoperability with other languages", "features": ["bridge"]},
    "pkg_manager": {"version": "1.0.0", "deps": ["core"], "description": "Package management system", "features": ["pkg", "pkg_install", "pkg_list"]},
    "devtools": {"version": "1.0.0", "deps": ["core"], "description": "Development tools", "features": ["ide", "test", "template", "deploy"]},
    "quantum": {"version": "1.0.0", "deps": ["core"], "description": "Quantum computing support", "features": ["quantum"]},
    "ai_dev": {"version": "1.0.0", "deps": ["core"], "description": "AI-driven development", "features": ["ai_code"]},
    "typing": {"version": "1.0.0", "deps": ["core"], "description": "Static typing support", "features": ["type"]},
    "macros": {"version": "1.0.0", "deps": ["core"], "description": "Metaprogramming with macros", "features": ["macro"]}
}

def generate_module_list():
    # List modules in module folder
    modules = {}
    for filename in os.listdir(MODULE_DIR):
        if filename.endswith('.ps'):
            name = filename[:-3]  # Remove .ps extension
            path = os.path.join(MODULE_DIR, filename)
            with open(path, 'r') as f:
                code = f.read()
                metadata = {"version": "1.0.0", "deps": [], "description": "Custom module"}
                for line in code.split('\n'):
                    if line.startswith('# pkg_name:'):
                        metadata['name'] = line.split(':')[1].strip()
                    elif line.startswith('# pkg_version:'):
                        metadata['version'] = line.split(':')[1].strip()
                    elif line.startswith('# pkg_deps:'):
                        metadata['deps'] = [d.strip() for d in line.split(':')[1].split(',') if d.strip()]
                    elif line.startswith('# description:'):
                        metadata['description'] = line.split(':')[1].strip()
            modules[name] = {
                "source": path,
                "version": metadata['version'],
                "deps": metadata['deps'],
                "description": metadata['description'],
                "path": path
            }

    # List installed packages
    with open(PACKAGE_DB, 'r') as f:
        installed = json.load(f)

    # Combine into JSON
    all_modules = {
        "modules": modules,
        "installed_packages": installed,
        "builtins": BUILTINS
    }

    with open("all_modules_and_packages.json", 'w') as f:
        json.dump(all_modules, f, indent=2)

    return all_modules

if __name__ == "__main__":
    generate_module_list()
    print("Generated all_modules_and_packages.json")