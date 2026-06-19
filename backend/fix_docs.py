#!/usr/bin/env python3
import re

with open('api/routes/documents.py', 'r') as f:
    content = f.read()

content = re.sub(r'@@+', '@', content)

with open('api/routes/documents.py', 'w') as f:
    f.write(content)

print("[OK] Fixed syntax")
