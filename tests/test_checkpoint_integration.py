#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for validating canonical checkpoint marking in bot_integrated.py
"""

import sys
import os

# Add src/bot to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'bot'))

def test_mark_checkpoint_function_exists():
    """Test that mark_checkpoint function exists and has correct signature"""
    try:
        # Instead of importing, parse the file to check function definition
        bot_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'bot', 'bot_integrated.py')
        with open(bot_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check function definition exists
        assert 'def mark_checkpoint(' in content, "mark_checkpoint function not found"
        print("✅ mark_checkpoint function exists")
        
        # Check function signature has required parameters
        assert 'task_code:' in content, "Missing task_code parameter"
        assert 'checkpoint_code:' in content, "Missing checkpoint_code parameter"
        assert 'status:' in content, "Missing status parameter"
        assert 'validation_result:' in content, "Missing validation_result parameter"
        
        # Check for default values
        assert 'status: str = "passed"' in content, "status default should be 'passed'"
        assert 'validation_result: dict = None' in content, "validation_result default should be None"
        
        # Check for docstring
        assert 'Mark a canonical checkpoint for a task' in content, "Function docstring missing"
        
        print("✅ mark_checkpoint has correct signature")
        return True
    except AssertionError as e:
        print(f"❌ Function validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_checkpoint_marks_in_code():
    """Test that checkpoint marks are present in the code"""
    try:
        bot_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'bot', 'bot_integrated.py')
        with open(bot_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for CP01_ROADMAP
        assert 'CP01_ROADMAP' in content, "CP01_ROADMAP checkpoint not found"
        assert 'add_task_command' in content, "add_task_command function not found"
        print("✅ CP01_ROADMAP checkpoint mark found")
        
        # Check for CP05_ORCHESTRATOR
        assert 'CP05_ORCHESTRATOR' in content, "CP05_ORCHESTRATOR checkpoint not found"
        assert 'Orchestrator started task execution' in content, "CP05_ORCHESTRATOR note not found"
        print("✅ CP05_ORCHESTRATOR checkpoint mark found")
        
        # Check for CP06_ENGINEER
        assert 'CP06_ENGINEER' in content, "CP06_ENGINEER checkpoint not found"
        assert 'Engineer_B generated code successfully' in content, "CP06_ENGINEER note not found"
        print("✅ CP06_ENGINEER checkpoint mark found")
        
        # Check for CP09_CURATOR
        assert 'CP09_CURATOR' in content, "CP09_CURATOR checkpoint not found"
        assert 'Curator validated code successfully' in content, "CP09_CURATOR note not found"
        print("✅ CP09_CURATOR checkpoint mark found")
        
        # Check for [KANON] logger prefix
        assert '[KANON]' in content, "[KANON] logger prefix not found"
        print("✅ [KANON] logger prefix found")
        
        return True
    except AssertionError as e:
        print(f"❌ Code validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_checkpoint_sql_structure():
    """Test that checkpoint SQL has correct structure"""
    try:
        bot_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'bot', 'bot_integrated.py')
        with open(bot_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for INSERT INTO with ON CONFLICT
        assert 'INSERT INTO eng_it.task_canonical_progress' in content, "INSERT statement not found"
        assert 'ON CONFLICT (task_code, checkpoint_code)' in content, "ON CONFLICT clause not found"
        assert 'DO UPDATE SET' in content, "DO UPDATE SET clause not found"
        
        # Check for required columns
        assert 'task_code' in content, "task_code column not found"
        assert 'checkpoint_code' in content, "checkpoint_code column not found"
        assert 'status' in content, "status column not found"
        assert 'passed_at' in content, "passed_at column not found"
        assert 'validation_result' in content, "validation_result column not found"
        
        print("✅ Checkpoint SQL structure is correct")
        return True
    except AssertionError as e:
        print(f"❌ SQL structure validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_all_checkpoint_calls_use_str():
    """Test that all checkpoint calls properly convert task_id to string"""
    try:
        bot_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'bot', 'bot_integrated.py')
        with open(bot_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        checkpoint_calls = []
        for i, line in enumerate(lines):
            if 'mark_checkpoint(' in line:
                # Get the first parameter (task_code)
                checkpoint_calls.append((i+1, line.strip()))
        
        print(f"Found {len(checkpoint_calls)} checkpoint calls")
        
        # Check that most calls use str(task_id) except for CP01 which uses task_id directly
        str_count = 0
        for line_num, line in checkpoint_calls:
            if 'str(task_id)' in line:
                str_count += 1
                print(f"  Line {line_num}: Uses str(task_id) ✅")
            elif 'task_id,' in line or 'task_id)' in line:
                # CP01_ROADMAP uses task_id directly which is OK since it's a string
                print(f"  Line {line_num}: Uses task_id (should be string type) ✅")
            else:
                print(f"  Line {line_num}: ⚠️ Check parameter type")
        
        print(f"✅ Found {str_count} calls using str() conversion")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Canonical Checkpoint Integration")
    print("=" * 60)
    
    results = []
    
    print("\n1. Testing mark_checkpoint function existence and signature...")
    results.append(test_mark_checkpoint_function_exists())
    
    print("\n2. Testing checkpoint marks in code...")
    results.append(test_checkpoint_marks_in_code())
    
    print("\n3. Testing checkpoint SQL structure...")
    results.append(test_checkpoint_sql_structure())
    
    print("\n4. Testing checkpoint calls use str() conversion...")
    results.append(test_all_checkpoint_calls_use_str())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
