from typing import List, Dict, Optional
from pathlib import Path
import os
import mimetypes
import subprocess
import platform

class FileManager:
    # Allowed file types
    ALLOWED_EXTENSIONS = {
        '.txt', '.md', '.csv', '.json', '.html', 
        '.py', '.js', '.css', '.yaml', '.yml', 
        '.sh', '.env', '.ini', '.conf',
        # Add viewable file types
        '.pdf', '.png', '.jpg', '.jpeg', '.gif', 
        '.bmp', '.webp', '.tiff'
    }
    
    # Separate viewable types
    VIEWABLE_EXTENSIONS = {
        '.pdf', '.png', '.jpg', '.jpeg', 
        '.gif', '.bmp', '.webp', '.tiff'
    }
    
    # Maximum file sizes
    MAX_READ_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_WRITE_SIZE = 1 * 1024 * 1024  # 1MB

    # Directories to exclude
    EXCLUDED_DIRS = {
        '.ssh', '.aws', '.config', '.gnupg',
        '.keychain', 'Library/Keychains', '.git'
    }

    def __init__(self):
        """Initialize with home directory."""
        self.root_path = Path.home()
        mimetypes.init()

    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is safe to access."""
        try:
            full_path = path.resolve()
            
            # Must be under home directory
            if self.root_path not in full_path.parents and full_path != self.root_path:
                return False
                
            # Check against excluded directories
            for part in full_path.parts:
                if part in self.EXCLUDED_DIRS:
                    return False
                    
            return True
        except Exception:
            return False

    def _is_allowed_file_type(self, file_path: Path) -> bool:
        """Check if file type is allowed."""
        if file_path.is_dir():
            return True
        return file_path.suffix.lower() in self.ALLOWED_EXTENSIONS

    def _should_show_item(self, path: Path, show_hidden: bool = False) -> bool:
        """Determine if a file/folder should be shown."""
        # Always hide these regardless of show_hidden flag
        if path.name in self.EXCLUDED_DIRS:
            return False
            
        # Hide dot files/folders unless show_hidden is True
        if not show_hidden and path.name.startswith('.'):
            return False
            
        return True

    async def search_files(self, query: str, path: str = "~", show_hidden: bool = False) -> List[Dict]:
        """Search for files matching query."""
        results = []
        try:
            search_path = Path(path).expanduser().resolve()
            if not self._is_safe_path(search_path):
                raise ValueError("Invalid search path")

            for file_path in search_path.rglob(f"*{query}*"):
                if (self._is_safe_path(file_path) and 
                    self._is_allowed_file_type(file_path) and 
                    self._should_show_item(file_path, show_hidden)):
                    results.append({
                        "path": str(file_path.relative_to(self.root_path)),
                        "name": file_path.name,
                        "type": "file" if file_path.is_file() else "folder"
                    })
        except Exception as e:
            print(f"Search error: {e}")
        return results

    async def read_file(self, path: str) -> Optional[str]:
        """Read file contents safely."""
        try:
            file_path = Path(path).expanduser().resolve()
            if not self._is_safe_path(file_path):
                raise ValueError("Invalid file path")
            
            if not self._is_allowed_file_type(file_path):
                raise ValueError("Invalid file type")
            
            if file_path.stat().st_size > self.MAX_READ_SIZE:
                raise ValueError(f"File too large (max {self.MAX_READ_SIZE} bytes)")
            
            return file_path.read_text()
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            return None

    async def write_file(self, path: str, content: str) -> bool:
        """Write content to file safely."""
        try:
            file_path = Path(path).expanduser().resolve()
            if not self._is_safe_path(file_path):
                raise ValueError("Invalid file path")
            
            if len(content.encode()) > self.MAX_WRITE_SIZE:
                raise ValueError(f"Content too large (max {self.MAX_WRITE_SIZE} bytes)")
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            
            if not self._is_allowed_file_type(file_path):
                file_path.unlink()
                raise ValueError("Invalid file type")
                
            return True
        except Exception as e:
            print(f"Error writing file {path}: {e}")
            return False

    async def list_directory(self, path: str = "~", show_hidden: bool = False) -> List[Dict]:
        """List contents of a directory."""
        results = []
        try:
            dir_path = Path(path).expanduser().resolve()
            if not self._is_safe_path(dir_path):
                raise ValueError("Invalid directory path")

            for item in dir_path.iterdir():
                if (self._is_safe_path(item) and 
                    self._is_allowed_file_type(item) and 
                    self._should_show_item(item, show_hidden)):
                    results.append({
                        "path": str(item.relative_to(self.root_path)),
                        "name": item.name,
                        "type": "file" if item.is_file() else "folder"
                    })
        except Exception as e:
            print(f"Error listing directory {path}: {e}")
        return results 

    async def open_file(self, path: str) -> bool:
        """Open file with system default application."""
        try:
            file_path = Path(path).expanduser().resolve()
            if not self._is_safe_path(file_path):
                raise ValueError("Invalid file path")
            
            if not file_path.suffix.lower() in self.VIEWABLE_EXTENSIONS:
                raise ValueError("File type not supported for viewing")
            
            # Open file with default system application
            if platform.system() == 'Darwin':       # macOS
                subprocess.run(['open', str(file_path)])
            elif platform.system() == 'Windows':    # Windows
                os.startfile(str(file_path))
            else:                                   # Linux
                subprocess.run(['xdg-open', str(file_path)])
                
            return True
            
        except Exception as e:
            print(f"Error opening file {path}: {e}")
            return False 