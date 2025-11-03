#!/bin/bash
# Simple validation test for CI

echo "🔍 Starting Roadmap validation..."

# Check if files exist
if [ ! -f "ROADMAP/GENERAL_PLAN.yaml" ]; then
    echo "❌ GENERAL_PLAN.yaml not found"
    exit 1
fi

if [ ! -f "SPEC/ROADMAP_SCHEMA.yaml" ]; then
    echo "❌ ROADMAP_SCHEMA.yaml not found"
    exit 1
fi

# Basic Python validation
python3 -c "
import yaml
from jsonschema import validate

try:
    with open('SPEC/ROADMAP_SCHEMA.yaml', 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    with open('ROADMAP/GENERAL_PLAN.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    validate(instance=data, schema=schema)
    print('✅ Roadmap validation passed')
    
except Exception as e:
    print(f'❌ Validation failed: {e}')
    exit(1)
"

if [ True -eq 0 ]; then
    echo "🎉 All validation checks passed!"
    exit 0
else
    echo "💥 Validation failed"
    exit 1
fi
