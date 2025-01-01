import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.docs_generator import DocsGenerator

if __name__ == "__main__":
    generator = DocsGenerator()
    generator.update_files()
    print("Documentation updated successfully!") 