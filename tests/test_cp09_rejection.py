#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to validate CP09_CURATOR checkpoint marking on rejection scenario
"""

import sys
import os

# Add src/bot to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'bot'))


def test_cp09_marked_on_rejection():
    """Test that CP09_CURATOR checkpoint is marked when curator rejects code"""
    try:
        bot_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'bot', 'bot_integrated.py')
        with open(bot_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the rejection block (else: after decision == "approve")
        assert 'else:' in content, "Rejection else block not found"
        assert 'Код отклонён' in content, "Rejection message not found"
        
        # Check that mark_checkpoint is called in the rejection block
        # We need to verify the checkpoint call comes after update_task_status with "failed"
        lines = content.split('\n')
        
        found_rejection_block = False
        found_failed_status = False
        found_cp09_mark = False
        found_rejection_reasons = False
        
        for i, line in enumerate(lines):
            # Look for rejection block
            if 'Код отклонён с оценкой' in line:
                found_rejection_block = True
                print(f"✅ Found rejection block at line {i+1}")
            
            # After rejection block, check for update_task_status with "failed"
            if found_rejection_block and not found_failed_status:
                if 'update_task_status' in line and '"failed"' in line:
                    found_failed_status = True
                    print(f"✅ Found update_task_status('failed') at line {i+1}")
            
            # After failed status, check for CP09_CURATOR checkpoint
            if found_failed_status and not found_cp09_mark:
                if 'mark_checkpoint' in line and 'CP09_CURATOR' in line:
                    found_cp09_mark = True
                    print(f"✅ Found CP09_CURATOR checkpoint at line {i+1}")
            
            # Check for rejection_reasons in validation_result
            if found_cp09_mark and not found_rejection_reasons:
                if 'rejection_reasons' in line:
                    found_rejection_reasons = True
                    print(f"✅ Found rejection_reasons in validation_result at line {i+1}")
                    break
        
        assert found_rejection_block, "❌ Rejection block not found"
        assert found_failed_status, "❌ update_task_status('failed') not found in rejection block"
        assert found_cp09_mark, "❌ CP09_CURATOR checkpoint not marked in rejection block"
        assert found_rejection_reasons, "❌ rejection_reasons not included in validation_result"
        
        print("\n✅ All checks passed: CP09_CURATOR is marked on rejection")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def test_cp09_validation_result_fields():
    """Test that CP09_CURATOR validation_result contains all required fields for rejection"""
    try:
        bot_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'bot', 'bot_integrated.py')
        with open(bot_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the mark_checkpoint call in rejection block
        lines = content.split('\n')
        
        in_rejection_checkpoint = False
        found_notes = False
        found_source = False
        found_curator_decision = False
        found_curator_score = False
        found_rejection_reasons = False
        
        for i, line in enumerate(lines):
            # Look for mark_checkpoint in rejection context
            if 'mark_checkpoint' in line and 'CP09_CURATOR' in line:
                # Check if this is after "failed" status (rejection block)
                # Look back a few lines to see if we're in rejection context
                context = '\n'.join(lines[max(0, i-10):i])
                if '"failed"' in context and 'отклонён' in context:
                    in_rejection_checkpoint = True
                    print(f"✅ Found CP09 checkpoint in rejection context at line {i+1}")
            
            # Check validation_result fields within the checkpoint call
            if in_rejection_checkpoint:
                if 'notes' in line and 'rejected' in line:
                    found_notes = True
                    print(f"✅ Found 'notes' with 'rejected' at line {i+1}")
                if '"source"' in line:
                    found_source = True
                    print(f"✅ Found 'source' field at line {i+1}")
                if 'curator_decision' in line:
                    found_curator_decision = True
                    print(f"✅ Found 'curator_decision' field at line {i+1}")
                if 'curator_score' in line:
                    found_curator_score = True
                    print(f"✅ Found 'curator_score' field at line {i+1}")
                if 'rejection_reasons' in line:
                    found_rejection_reasons = True
                    print(f"✅ Found 'rejection_reasons' field at line {i+1}")
                    break  # Stop after finding all fields
        
        assert in_rejection_checkpoint, "❌ CP09_CURATOR checkpoint not found in rejection block"
        assert found_notes, "❌ 'notes' field not found or doesn't mention 'rejected'"
        assert found_source, "❌ 'source' field not found"
        assert found_curator_decision, "❌ 'curator_decision' field not found"
        assert found_curator_score, "❌ 'curator_score' field not found"
        assert found_rejection_reasons, "❌ 'rejection_reasons' field not found"
        
        print("\n✅ All validation_result fields present for rejection scenario")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def test_cp09_status_is_passed():
    """Test that CP09_CURATOR status is 'passed' even when code is rejected"""
    try:
        bot_file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'bot', 'bot_integrated.py')
        with open(bot_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Find CP09 checkpoint in rejection block and verify status is "passed"
        found_checkpoint_with_passed_status = False
        
        for i, line in enumerate(lines):
            if 'mark_checkpoint' in line and 'CP09_CURATOR' in line:
                # Check if this is in rejection context
                context = '\n'.join(lines[max(0, i-10):i])
                if '"failed"' in context and 'отклонён' in context:
                    # Check if "passed" is in the checkpoint call
                    # Look at the next few lines to find the full call
                    checkpoint_call = '\n'.join(lines[i:min(len(lines), i+10)])
                    if '"passed"' in checkpoint_call:
                        found_checkpoint_with_passed_status = True
                        print(f"✅ CP09_CURATOR in rejection block uses status='passed' at line {i+1}")
                        break
        
        assert found_checkpoint_with_passed_status, "❌ CP09_CURATOR in rejection block doesn't use status='passed'"
        
        print("\n✅ CP09_CURATOR status is 'passed' in rejection scenario (checkpoint passed, not task)")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def main():
    """Run all CP09 rejection tests"""
    print("=" * 70)
    print("Testing CP09_CURATOR Checkpoint Marking on Rejection")
    print("=" * 70)
    
    results = []
    
    print("\n1. Testing CP09_CURATOR is marked in rejection block...")
    results.append(test_cp09_marked_on_rejection())
    
    print("\n2. Testing CP09_CURATOR validation_result fields...")
    results.append(test_cp09_validation_result_fields())
    
    print("\n3. Testing CP09_CURATOR status is 'passed' even on rejection...")
    results.append(test_cp09_status_is_passed())
    
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("✅ All CP09 rejection tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
