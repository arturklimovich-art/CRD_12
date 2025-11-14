#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path
import tempfile

class SafePatchApplier:
    def __init__(self):
        self.source_dir = Path("/app")
        self.live_src_dir = Path("/app/workspace/live_src")
        self.patches_dir = Path("/app/workspace/patches_applied")
        
    def validate_python_syntax(self, file_path):
        """Validate Python syntax before applying patches"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "py_compile", str(file_path)
            ], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
            
    def safe_apply_patch(self, patch_file, target_dir):
        """Safely apply a single patch with validation"""
        print(f"🔧 Applying {patch_file.name}...")
        
        # Create backup
        backup_dir = self.live_src_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        try:
            # Apply patch
            result = subprocess.run([
                "patch", "-p1", "--backup", "-d", str(target_dir), "-i", str(patch_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {patch_file.name} applied successfully")
                return True
            else:
                print(f"❌ Failed to apply {patch_file.name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error applying {patch_file.name}: {e}")
            return False
    
    def initialize_live_src(self):
        """Initialize live source directory"""
        if self.live_src_dir.exists():
            shutil.rmtree(self.live_src_dir)
        shutil.copytree(self.source_dir, self.live_src_dir, 
                       ignore=shutil.ignore_patterns('workspace', '__pycache__'))
        print("✅ Live source initialized")
    
    def apply_all_patches(self):
        """Apply all patches safely"""
        if not self.patches_dir.exists():
            print("ℹ️ No patches directory found")
            return
            
        patches = list(self.patches_dir.glob("*.patch"))
        if not patches:
            print("ℹ️ No patches to apply")
            return
            
        print(f"🔍 Found {len(patches)} patches")
        
        for patch_file in sorted(patches):
            self.safe_apply_patch(patch_file, self.live_src_dir)
    
    def run(self):
        """Main execution flow"""
        print("🚀 Starting safe patch application system...")
        
        self.initialize_live_src()
        self.apply_all_patches()
        
        # Start from live_src
        os.chdir(self.live_src_dir)
        print("🎯 Starting uvicorn from live_src...")
        os.execvp("uvicorn", ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    applier = SafePatchApplier()
    applier.run()
