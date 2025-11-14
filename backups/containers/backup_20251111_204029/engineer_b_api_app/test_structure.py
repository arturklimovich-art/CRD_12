import sys
import os
print("Python path:")
for p in sys.path:
    print(f"  {p}")
print("\nCurrent directory:", os.getcwd())
print("Files in current directory:")
for f in os.listdir('.'):
    print(f"  {f}")
print("\nAttempting to find curator...")
try:
    import importlib.util
    spec = importlib.util.find_spec("curator")
    if spec:
        print(f"Found curator at: {spec.origin}")
    else:
        print("Curator not found in Python path")
except Exception as e:
    print(f"Error searching for curator: {e}")
