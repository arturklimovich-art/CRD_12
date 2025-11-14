#!/bin/bash
echo '=== Container Structure Test ==='
echo 'Files in /app:'
ls -la /app | head -10
echo ''
echo 'Checking for curator:'
find /app -name '*curator*' -type f 2>/dev/null || echo 'Curator not found'
echo ''
echo 'Python path:'
python -c \"import sys; print('\\n'.join(sys.path))\" | head -10
