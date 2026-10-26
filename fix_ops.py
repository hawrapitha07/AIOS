import sys

# Read the file
with open(sys.argv[1], "r") as f:
    content = f.read()

# Add import aios after the imports
if 'from pathlib import Path' in content:
    content = content.replace('from pathlib import Path', 'from pathlib import Path\nimport aios')

# Add self.workflows_dir in __init__ after self.project_manager = ProjectManager()
if 'self.project_manager = ProjectManager()' in content:
    content = content.replace('self.project_manager = ProjectManager()', 'self.project_manager = ProjectManager()\n        self.workflows_dir = Path(aios.__file__).parent / "workflows"')

# Replace the path references
content = content.replace("Path('aios/workflows')", 'self.workflows_dir')

# Write the file back
with open(sys.argv[1], "w") as f:
    f.write(content)
