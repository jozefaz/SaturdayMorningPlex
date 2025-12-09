#!/usr/bin/env python3
"""
Simple test script to verify the application structure without dependencies
"""
import os
import sys

print("Testing SaturdayMorningPlex Application Structure")
print("=" * 50)

# Check if files exist
files_to_check = [
    'app.py',
    'requirements.txt',
    'Dockerfile',
    'docker-compose.yml',
    'templates/index.html',
    'unraid-template.xml'
]

all_good = True
for file in files_to_check:
    exists = os.path.exists(file)
    status = "✓" if exists else "✗"
    print(f"{status} {file}: {'Found' if exists else 'MISSING'}")
    if not exists:
        all_good = False

print("\n" + "=" * 50)
if all_good:
    print("✓ All required files are present!")
    print("\nTo run the application, you need to install:")
    print("  - Docker (recommended for UnRAID deployment)")
    print("  - OR Python dependencies: pip3 install -r requirements.txt")
else:
    print("✗ Some files are missing!")
    sys.exit(1)
