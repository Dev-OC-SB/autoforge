#!/usr/bin/env python3
"""
Update imports after reorganization
"""

import os
import re
from pathlib import Path

# Define import mappings
IMPORT_MAPPINGS = {
    # Core modules moved to core/
    'from core.client import': 'from core.client import',
    'from core.agent import': 'from core.agent import',
    'from core.registry import': 'from core.registry import',
    'from core.security import': 'from core.security import',
    'from core.prompts import': 'from core.prompts import',
    'from core.progress import': 'from core.progress import',
    'from core.rate_limit_utils import': 'from core.rate_limit_utils import',
    'from core.env_constants import': 'from core.env_constants import',
    'from core.auth import': 'from core.auth import',
    'from core.autoforge_paths import': 'from core.autoforge_paths import',
    'from core.parallel_orchestrator import': 'from core.parallel_orchestrator import',
    'from core.temp_cleanup import': 'from core.temp_cleanup import',
    'from core.autonomous_agent_demo import': 'from core.autonomous_agent_demo import',
    
    'import core.client as client': 'import core.client as client',
    'import core.agent as agent': 'import core.agent as agent',
    'import core.registry as registry': 'import core.registry as registry',
    'import core.security as security': 'import core.security as security',
    'import core.prompts as prompts': 'import core.prompts as prompts',
    'import core.progress as progress': 'import core.progress as progress',
    
    # Adapter modules moved to core/
    'from core.adapter_client import': 'from core.adapter_client import',
    'from core.message_adapters import': 'from core.message_adapters import',
    'from core.unified_client import': 'from core.unified_client import',
    
    'import core.adapter_client as adapter_client': 'import core.adapter_client as adapter_client',
    'import core.message_adapters as message_adapters': 'import core.message_adapters as message_adapters',
    'import core.unified_client as unified_client': 'import core.unified_client as unified_client',
}

def update_file_imports(filepath):
    """Update imports in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all import mappings
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = content.replace(old_import, new_import)
        
        # Only write if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return False

def main():
    """Update all Python files."""
    base_dir = Path('/root/seaforge')
    
    # Directories to process
    dirs_to_process = [
        base_dir / 'core',
        base_dir / 'server',
        base_dir / 'tests',
        base_dir / 'api',
        base_dir / 'mcp_server',
        base_dir,  # Root level files
    ]
    
    updated_files = []
    
    for directory in dirs_to_process:
        if not directory.exists():
            continue
            
        # Find all Python files
        for py_file in directory.rglob('*.py'):
            # Skip venv and __pycache__
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            if update_file_imports(py_file):
                updated_files.append(py_file)
                print(f"✓ Updated: {py_file.relative_to(base_dir)}")
    
    print(f"\n✅ Updated {len(updated_files)} files")
    
    if updated_files:
        print("\nUpdated files:")
        for f in updated_files:
            print(f"  - {f.relative_to(base_dir)}")

if __name__ == '__main__':
    main()
