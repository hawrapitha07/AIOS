# Read the file
with open(r'aios\developer\operations.py', 'r') as f:
    content = f.read()

# Add import aios after the imports
import_pos = content.find('from pathlib import Path')
if import_pos != -1:
    # Insert after this line
    insert_pos = import_pos + len('from pathlib import Path')
    content = content[:insert_pos] + '\nimport aios\n' + content[insert_pos:]

# Add self.workflows_dir in __init__
# Find the line that sets self.project_manager and add after it
init_pos = content.find('self.project_manager = ProjectManager()')
if init_pos != -1:
    insert_pos = init_pos + len('self.project_manager = ProjectManager()')
    content = content[:insert_pos] + '\n        self.workflows_dir = Path(aios.__file__).parent / "workflows"\n' + content[init_pos:]

# Replace the three workflow_dir lines
content = content.replace("workflow_dir = Path('aios/workflows') / workflow_name", "workflow_dir = self.workflows_dir / workflow_name")
content = content.replace("workflows_dir = Path('aios/workflows')", "workflows_dir = self.workflows_dir")

# Write the file back
with open(r'aios\developer\operations.py', 'w') as f:
    f.write(content)
