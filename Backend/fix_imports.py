import os
import re

files_to_fix = [
    './routers/metrics.py',
    './routers/users.py',
    './routers/feedback.py',
    './routers/recommendations.py',
    './routers/actions.py',
    './routers/objectives.py',
    './routers/organizations.py',
    './routers/insights.py',
    './core/permissions.py',
    './api.py'
]

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if file uses get_db_context
    if 'get_db_context' not in content:
        continue
    
    # Check if already imports get_db_context
    if 'get_db_context' in content and 'from core.database import' in content:
        # Update existing import
        content = re.sub(
            r'from core\.database import get_db\b',
            'from core.database import get_db, get_db_context',
            content
        )
    elif 'get_db_context' in content:
        # Add new import at the top
        content = 'from core.database import get_db_context\n' + content
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed: {filepath}")

print("Done!")
