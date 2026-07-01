#!/usr/bin/env python3
"""
Test to verify booking flow confirmation steps and traveler loop logic
"""

import sys
sys.path.insert(0, '/home/runner/work/Kali-Safaris/Kali-Safaris/whatsappcrm_backend')

from flows.definitions.booking_flow import BOOKING_FLOW

def test_all_confirmations_use_buttons():
    """Test that all confirmation steps use interactive buttons"""
    print("\n" + "="*80)
    print("TEST: All Confirmation Steps Use Buttons")
    print("="*80)
    
    confirmation_steps = [
        'confirm_selected_dates',
        'confirm_traveler_details', 
        'show_booking_summary'
    ]
    
    for step_name in confirmation_steps:
        step = next((s for s in BOOKING_FLOW['steps'] if s['name'] == step_name), None)
        assert step is not None, f"Step '{step_name}' not found"
        
        config = step.get('config', {})
        message_config = config.get('message_config', {})
        
        # Check message type is interactive
        assert message_config.get('message_type') == 'interactive', \
            f"{step_name}: message_type should be 'interactive'"
        
        # Check interactive type is button
        interactive = message_config.get('interactive', {})
        assert interactive.get('type') == 'button', \
            f"{step_name}: interactive type should be 'button'"
        
        # Check buttons exist
        buttons = interactive.get('action', {}).get('buttons', [])
        assert len(buttons) == 2, \
            f"{step_name}: should have 2 buttons, got {len(buttons)}"
        
        # Check reply config
        reply_config = config.get('reply_config', {})
        assert reply_config.get('expected_type') == 'interactive_id', \
            f"{step_name}: reply_config expected_type should be 'interactive_id'"
        
        print(f"✓ {step_name}: Uses interactive buttons correctly")
    
    print("\n✅ All confirmation steps use buttons correctly\n")
    return True

def test_traveler_loop_logic():
    """Test that traveler loop logic uses correct variable comparisons"""
    print("="*80)
    print("TEST: Traveler Loop Logic")
    print("="*80)
    
    step = next((s for s in BOOKING_FLOW['steps'] if s['name'] == 'add_traveler_to_list'), None)
    assert step is not None, "Step 'add_traveler_to_list' not found"
    
    actions = step.get('config', {}).get('actions_to_run', [])
    
    # Find adult_index action
    adult_index_action = next((a for a in actions if a.get('variable_name') == 'adult_index'), None)
    assert adult_index_action is not None, "adult_index action not found"
    
    adult_template = adult_index_action.get('value_template', '')
    assert 'traveler_index <= num_adults' in adult_template, \
        f"adult_index should use 'traveler_index <= num_adults', got: {adult_template}"
    print(f"✓ adult_index uses correct logic: {adult_template}")
    
    # Find child_index action
    child_index_action = next((a for a in actions if a.get('variable_name') == 'child_index'), None)
    assert child_index_action is not None, "child_index action not found"
    
    child_template = child_index_action.get('value_template', '')
    assert 'traveler_index > num_adults' in child_template, \
        f"child_index should use 'traveler_index > num_adults', got: {child_template}"
    print(f"✓ child_index uses correct logic: {child_template}")
    
    print("\n✅ Traveler loop logic is correct\n")
    return True

def test_automatic_transitions():
    """Test that WhatsApp Flow responses automatically transition to next steps"""
    print("="*80)
    print("TEST: Automatic Transitions After WhatsApp Flows")
    print("="*80)
    
    # Test date picker flow
    date_step = next((s for s in BOOKING_FLOW['steps'] if s['name'] == 'ask_travel_dates'), None)
    assert date_step is not None, "Step 'ask_travel_dates' not found"
    
    reply_config = date_step.get('config', {}).get('reply_config', {})
    assert reply_config.get('expected_type') == 'nfm_reply', \
        "ask_travel_dates should expect 'nfm_reply'"
    
    transitions = date_step.get('transitions', [])
    assert len(transitions) > 0, "ask_travel_dates should have transitions"
    assert transitions[0].get('to_step') == 'process_date_selection', \
        "ask_travel_dates should transition to 'process_date_selection'"
    print("✓ Date picker automatically transitions to process_date_selection")
    
    # Test traveler details flow
    traveler_step = next((s for s in BOOKING_FLOW['steps'] if s['name'] == 'ask_traveler_details_via_flow'), None)
    assert traveler_step is not None, "Step 'ask_traveler_details_via_flow' not found"
    
    reply_config = traveler_step.get('config', {}).get('reply_config', {})
    assert reply_config.get('expected_type') == 'nfm_reply', \
        "ask_traveler_details_via_flow should expect 'nfm_reply'"
    
    transitions = traveler_step.get('transitions', [])
    assert len(transitions) > 0, "ask_traveler_details_via_flow should have transitions"
    assert transitions[0].get('to_step') == 'process_traveler_details_response', \
        "ask_traveler_details_via_flow should transition to 'process_traveler_details_response'"
    print("✓ Traveler details flow automatically transitions to process_traveler_details_response")
    
    # Verify processing step transitions to confirmation
    process_step = next((s for s in BOOKING_FLOW['steps'] if s['name'] == 'process_traveler_details_response'), None)
    assert process_step is not None, "Step 'process_traveler_details_response' not found"
    
    transitions = process_step.get('transitions', [])
    assert len(transitions) > 0, "process_traveler_details_response should have transitions"
    assert transitions[0].get('to_step') == 'confirm_traveler_details', \
        "process_traveler_details_response should transition to 'confirm_traveler_details'"
    print("✓ Processing step automatically transitions to confirm_traveler_details")
    
    print("\n✅ All automatic transitions are correctly configured\n")
    return True

def test_confirmation_button_transitions():
    """Test that confirmation buttons have correct transition conditions"""
    print("="*80)
    print("TEST: Confirmation Button Transitions")
    print("="*80)
    
    # Test date confirmation
    confirm_dates = next((s for s in BOOKING_FLOW['steps'] if s['name'] == 'confirm_selected_dates'), None)
    transitions = confirm_dates.get('transitions', [])
    
    # Should have transitions for confirm and edit
    assert any(t.get('condition_config', {}).get('value') == 'confirm_dates' for t in transitions), \
        "confirm_selected_dates should have transition for 'confirm_dates' button"
    assert any(t.get('condition_config', {}).get('value') == 'edit_dates' for t in transitions), \
        "confirm_selected_dates should have transition for 'edit_dates' button"
    print("✓ Date confirmation has correct button transitions")
    
    # Test traveler confirmation
    confirm_traveler = next((s for s in BOOKING_FLOW['steps'] if s['name'] == 'confirm_traveler_details'), None)
    transitions = confirm_traveler.get('transitions', [])
    
    assert any(t.get('condition_config', {}).get('value') == 'confirm_traveler' for t in transitions), \
        "confirm_traveler_details should have transition for 'confirm_traveler' button"
    assert any(t.get('condition_config', {}).get('value') == 'edit_traveler' for t in transitions), \
        "confirm_traveler_details should have transition for 'edit_traveler' button"
    print("✓ Traveler confirmation has correct button transitions")
    
    # Test booking summary confirmation
    show_summary = next((s for s in BOOKING_FLOW['steps'] if s['name'] == 'show_booking_summary'), None)
    transitions = show_summary.get('transitions', [])
    
    assert any(t.get('condition_config', {}).get('value') == 'confirm_booking' for t in transitions), \
        "show_booking_summary should have transition for 'confirm_booking' button"
    assert any(t.get('condition_config', {}).get('value') == 'edit_booking' for t in transitions), \
        "show_booking_summary should have transition for 'edit_booking' button"
    print("✓ Booking summary confirmation has correct button transitions")
    
    print("\n✅ All confirmation button transitions are correctly configured\n")
    return True

def test_traveler_loop_continues():
    """Test that traveler loop continues until all travelers are collected"""
    print("="*80)
    print("TEST: Traveler Loop Continuation")
    print("="*80)
    
    add_traveler = next((s for s in BOOKING_FLOW['steps'] if s['name'] == 'add_traveler_to_list'), None)
    transitions = add_traveler.get('transitions', [])
    
    # Should loop back to query_traveler_details_whatsapp_flow if more travelers
    loop_transition = transitions[0]
    assert loop_transition.get('to_step') == 'query_traveler_details_whatsapp_flow', \
        "First transition should loop back to query_traveler_details_whatsapp_flow"
    
    condition = loop_transition.get('condition_config', {})
    assert condition.get('type') == 'variable_less_than_or_equal', \
        "Loop condition should use 'variable_less_than_or_equal'"
    assert condition.get('variable_name') == 'traveler_index', \
        "Loop condition should check 'traveler_index'"
    print(f"✓ Loop continues while traveler_index <= num_travelers")
    
    # Should exit to ask_email when all travelers collected
    exit_transition = transitions[1]
    assert exit_transition.get('to_step') == 'ask_email', \
        "Second transition should exit to ask_email"
    print(f"✓ Loop exits to ask_email when all travelers collected")
    
    print("\n✅ Traveler loop continuation is correctly configured\n")
    return True

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("BOOKING FLOW CONFIRMATION TESTS")
    print("="*80)
    
    try:
        test_all_confirmations_use_buttons()
        test_traveler_loop_logic()
        test_automatic_transitions()
        test_confirmation_button_transitions()
        test_traveler_loop_continues()
        
        print("="*80)
        print("ALL TESTS PASSED ✅")
        print("="*80 + "\n")
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
