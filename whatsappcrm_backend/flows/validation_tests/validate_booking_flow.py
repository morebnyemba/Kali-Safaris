#!/usr/bin/env python3
"""
Validation script for booking flow to ensure:
1. All confirmation steps use buttons
2. Traveler loop logic is correct
3. All interactive confirmations use proper button structure
"""

import sys
import json

# Import the booking flow
sys.path.insert(0, '/home/runner/work/Kali-Safaris/Kali-Safaris/whatsappcrm_backend')
from flows.definitions.booking_flow import BOOKING_FLOW

def validate_booking_flow():
    """Validate that booking flow meets all requirements"""
    print("=" * 80)
    print("BOOKING FLOW VALIDATION")
    print("=" * 80)
    
    issues = []
    confirmations_found = []
    
    # Find all confirmation steps
    for step in BOOKING_FLOW['steps']:
        step_name = step.get('name', 'unnamed')
        step_type = step.get('type')
        config = step.get('config', {})
        
        # Check if this is a confirmation step (by name pattern or button usage)
        is_confirmation = 'confirm' in step_name.lower() or step_name == 'show_booking_summary'
        
        if is_confirmation:
            confirmations_found.append(step_name)
            print(f"\n✓ Found confirmation step: {step_name}")
            
            # Check if it uses interactive buttons
            message_config = config.get('message_config', {})
            message_type = message_config.get('message_type')
            
            if message_type == 'interactive':
                interactive = message_config.get('interactive', {})
                interactive_type = interactive.get('type')
                
                if interactive_type == 'button':
                    buttons = interactive.get('action', {}).get('buttons', [])
                    print(f"  ✓ Uses interactive buttons ({len(buttons)} buttons found)")
                    
                    # List the button options
                    for btn in buttons:
                        btn_title = btn.get('reply', {}).get('title', 'N/A')
                        btn_id = btn.get('reply', {}).get('id', 'N/A')
                        print(f"    - {btn_title} (id: {btn_id})")
                    
                    # Check reply_config
                    reply_config = config.get('reply_config', {})
                    expected_type = reply_config.get('expected_type')
                    if expected_type == 'interactive_id':
                        print(f"  ✓ Correct reply_config: {expected_type}")
                    else:
                        issues.append(f"{step_name}: reply_config expected_type should be 'interactive_id', got '{expected_type}'")
                        print(f"  ✗ ISSUE: reply_config expected_type should be 'interactive_id', got '{expected_type}'")
                    
                    # Check transitions use interactive_reply_id_equals
                    transitions = step.get('transitions', [])
                    for trans in transitions:
                        condition = trans.get('condition_config', {})
                        cond_type = condition.get('type')
                        if cond_type in ['interactive_reply_id_equals', 'always_true']:
                            print(f"  ✓ Transition condition: {cond_type}")
                        else:
                            issues.append(f"{step_name}: transition should use 'interactive_reply_id_equals', got '{cond_type}'")
                            print(f"  ✗ ISSUE: transition should use 'interactive_reply_id_equals', got '{cond_type}'")
                
                else:
                    issues.append(f"{step_name}: interactive type should be 'button', got '{interactive_type}'")
                    print(f"  ✗ ISSUE: interactive type should be 'button', got '{interactive_type}'")
            else:
                issues.append(f"{step_name}: should use 'interactive' message_type, got '{message_type}'")
                print(f"  ✗ ISSUE: should use 'interactive' message_type, got '{message_type}'")
    
    # Check the traveler loop logic
    print("\n" + "=" * 80)
    print("TRAVELER LOOP LOGIC VALIDATION")
    print("=" * 80)
    
    add_traveler_step = None
    for step in BOOKING_FLOW['steps']:
        if step.get('name') == 'add_traveler_to_list':
            add_traveler_step = step
            break
    
    if add_traveler_step:
        print("\n✓ Found 'add_traveler_to_list' step")
        actions = add_traveler_step.get('config', {}).get('actions_to_run', [])
        
        # Check adult_index increment logic
        for action in actions:
            if action.get('variable_name') == 'adult_index':
                template = action.get('value_template', '')
                print(f"\nadult_index increment logic:")
                print(f"  {template}")
                if 'traveler_index <= num_adults' in template:
                    print("  ✓ Uses 'traveler_index' for comparison (CORRECT)")
                elif 'adult_index <= num_adults' in template:
                    issues.append("adult_index: Should use 'traveler_index' for comparison, not 'adult_index'")
                    print("  ✗ ISSUE: Should use 'traveler_index' for comparison, not 'adult_index'")
            
            if action.get('variable_name') == 'child_index':
                template = action.get('value_template', '')
                print(f"\nchild_index increment logic:")
                print(f"  {template}")
                if 'traveler_index > num_adults' in template:
                    print("  ✓ Uses 'traveler_index' for comparison (CORRECT)")
                elif 'adult_index > num_adults' in template:
                    issues.append("child_index: Should use 'traveler_index' for comparison, not 'adult_index'")
                    print("  ✗ ISSUE: Should use 'traveler_index' for comparison, not 'adult_index'")
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"\nConfirmation steps found: {len(confirmations_found)}")
    for conf in confirmations_found:
        print(f"  - {conf}")
    
    print(f"\nIssues found: {len(issues)}")
    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
        print("\n❌ VALIDATION FAILED")
        return False
    else:
        print("  ✓ All checks passed!")
        print("\n✅ VALIDATION SUCCESSFUL")
        return True

if __name__ == '__main__':
    success = validate_booking_flow()
    sys.exit(0 if success else 1)
