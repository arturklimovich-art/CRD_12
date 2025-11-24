"""
Smoke-???? ??? TradLab
????????? ??????? ??????????? ? ???????
"""
import sys
from pathlib import Path

def test_imports():
    """???????? ????????"""
    results = {}
    
    # ???? 1: ??????????? ??????????
    try:
        import json
        import datetime
        results["stdlib"] = "OK"
    except Exception as e:
        results["stdlib"] = f"FAIL: {e}"
    
    # ???? 2: PostgreSQL
    try:
        import psycopg2
        results["psycopg2"] = "OK"
    except Exception as e:
        results["psycopg2"] = f"FAIL: {e}"
    
    # ???? 3: Pandas (???????????)
    try:
        import pandas
        results["pandas"] = "OK"
    except Exception as e:
        results["pandas"] = f"NOT_INSTALLED: {e}"
    
    # ???? 4: NumPy (???????????)
    try:
        import numpy
        results["numpy"] = "OK"
    except Exception as e:
        results["numpy"] = f"NOT_INSTALLED: {e}"
    
    return results

def test_db_connection():
    """???????? ??????????? ? ??"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            "postgresql://crd_user:crd12@crd12_pgvector:5432/crd12"
        )
        conn.close()
        return "OK"
    except Exception as e:
        return f"FAIL: {e}"

if __name__ == "__main__":
    print("=" * 60)
    print("TradLab Smoke Test")
    print("=" * 60)
    
    print("\n1. ???????? ????????:")
    imports = test_imports()
    for lib, status in imports.items():
        print(f"   {lib:15s} : {status}")
    
    print("\n2. ???????? ??????????? ? ??:")
    db_status = test_db_connection()
    print(f"   PostgreSQL      : {db_status}")
    
    print("\n" + "=" * 60)
    
    # ?????????? ????? ??????
    critical_fails = [k for k, v in imports.items() 
                      if k in ["stdlib", "psycopg2"] and "FAIL" in v]
    
    if critical_fails or "FAIL" in db_status:
        print("? CRITICAL: Smoke test failed")
        sys.exit(1)
    else:
        print("? SUCCESS: Basic functionality ready")
        if "NOT_INSTALLED" in str(imports.values()):
            print("??  WARNING: Optional dependencies missing (pandas/numpy)")
        sys.exit(0)
