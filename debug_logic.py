"""
Comprehensive debug script to identify issues in reconciliation logic.
Tests formulas, functions, and edge cases.
"""

import sys
from io import BytesIO
from logic import StripeReconciliator
import pandas as pd
import json


def test_scenario_1_exact_match():
    """Test 1: Simple exact match - payout == bank deposit"""
    print("\n" + "="*80)
    print("TEST 1: Simple Exact Match")
    print("="*80)
    
    rec = StripeReconciliator()
    
    # Create test data: payout 1000.00 matches bank deposit 1000.00
    balance_csv = b"""Date,Payout ID,Charge Amount,Refund Amount,Fee Amount,Dispute Amount
2024-02-28,payout_001,1000.00,0.00,0.00,0.00"""
    
    payout_csv = b"""Payout ID,Payout Date,Payout Amount
payout_001,2024-02-27,1000.00"""
    
    bank_csv = b"""Date,Description,Credit
2024-02-28,STRIPE TRANSFER,1000.00"""
    
    rec.load_csv(balance_csv, 'balance')
    rec.load_csv(payout_csv, 'payout')
    rec.load_csv(bank_csv, 'bank')
    
    matched, exceptions, summary = rec.run_reconciliation(tolerance=5.0)
    
    print(f"Stripe Payout Amount: $1000.00")
    print(f"Bank Deposit Amount: $1000.00")
    print(f"Tolerance: $5.00")
    print(f"\nExpected: MATCHED with 0 difference")
    print(f"Actual Match Type: {matched['match_type'].values[0]}")
    print(f"Actual Difference: ${matched['difference'].values[0]:.2f}")
    print(f"Exceptions: {len(exceptions)}")
    
    assert matched['match_type'].values[0] == 'MATCHED', "Should be MATCHED"
    assert abs(matched['difference'].values[0]) <= 5.0, "Difference should be within tolerance"
    assert len(exceptions) == 0, "Should have no exceptions"
    print("[PASS] TEST 1 PASSED")


def test_scenario_2_amount_difference_within_tolerance():
    """Test 2: Amount differs but within tolerance"""
    print("\n" + "="*80)
    print("TEST 2: Amount Difference Within Tolerance")
    print("="*80)
    
    rec = StripeReconciliator()
    
    # Payout 1000.00, bank shows 1003.50 (within $5 tolerance)
    balance_csv = b"""Date,Payout ID,Charge Amount,Refund Amount,Fee Amount,Dispute Amount
2024-02-28,payout_001,1000.00,0.00,0.00,0.00"""
    
    payout_csv = b"""Payout ID,Payout Date,Payout Amount
payout_001,2024-02-27,1000.00"""
    
    bank_csv = b"""Date,Description,Credit
2024-02-28,STRIPE TRANSFER,1003.50"""
    
    rec.load_csv(balance_csv, 'balance')
    rec.load_csv(payout_csv, 'payout')
    rec.load_csv(bank_csv, 'bank')
    
    matched, exceptions, summary = rec.run_reconciliation(tolerance=5.0)
    
    print(f"Stripe Payout Amount: $1000.00")
    print(f"Bank Deposit Amount: $1003.50")
    print(f"Difference: $3.50")
    print(f"Tolerance: $5.00")
    print(f"\nExpected: MATCHED with $3.50 difference")
    print(f"Actual Match Type: {matched['match_type'].values[0]}")
    print(f"Actual Difference: ${matched['difference'].values[0]:.2f}")
    
    assert matched['match_type'].values[0] in ['MATCHED', 'PROBABLE_MATCH'], "Should be matched"
    assert abs(matched['difference'].values[0] - 3.50) < 0.01, f"Difference should be $3.50, got {matched['difference'].values[0]}"
    print("[PASS] TEST 2 PASSED")


def test_scenario_3_amount_exceeds_tolerance():
    """Test 3: Amount difference exceeds tolerance"""
    print("\n" + "="*80)
    print("TEST 3: Amount Difference Exceeds Tolerance")
    print("="*80)
    
    rec = StripeReconciliator()
    
    # Payout 1000.00, bank shows 1010.00 (exceeds $5 tolerance)
    balance_csv = b"""Date,Payout ID,Charge Amount,Refund Amount,Fee Amount,Dispute Amount
2024-02-28,payout_001,1000.00,0.00,0.00,0.00"""
    
    payout_csv = b"""Payout ID,Payout Date,Payout Amount
payout_001,2024-02-27,1000.00"""
    
    bank_csv = b"""Date,Description,Credit
2024-02-28,STRIPE TRANSFER,1010.00"""
    
    rec.load_csv(balance_csv, 'balance')
    rec.load_csv(payout_csv, 'payout')
    rec.load_csv(bank_csv, 'bank')
    
    matched, exceptions, summary = rec.run_reconciliation(tolerance=5.0)
    
    print(f"Stripe Payout Amount: $1000.00")
    print(f"Bank Deposit Amount: $1010.00")
    print(f"Difference: $10.00")
    print(f"Tolerance: $5.00")
    print(f"\nExpected: MATCHED but flagged as AMOUNT_MISMATCH exception")
    
    if not matched.empty:
        print(f"Actual Match Type: {matched['match_type'].values[0]}")
        print(f"Actual Difference: ${matched['difference'].values[0]:.2f}")
    
    print(f"Exceptions Found: {len(exceptions)}")
    if len(exceptions) > 0:
        for exc in exceptions['exception_type'].unique():
            print(f"  - {exc}")
    
    # This payout should NOT match because difference exceeds tolerance
    if not matched.empty:
        if 'AMOUNT_MISMATCH' in matched['match_type'].values:
            print("[PASS] TEST 3 PASSED - Flagged as amount mismatch")
        else:
            print("[WARN] TEST 3 WARNING - Should flag amount mismatch")
    else:
        print("[PASS] TEST 3 PASSED - No match")


def test_scenario_4_missing_payout():
    """Test 4: Bank deposit with no matching payout"""
    print("\n" + "="*80)
    print("TEST 4: Missing Payout (Extra Bank Deposit)")
    print("="*80)
    
    rec = StripeReconciliator()
    
    # Bank has 1000.00 but no payout record
    balance_csv = b"""Date,Payout ID,Charge Amount,Refund Amount,Fee Amount,Dispute Amount
2024-02-28,payout_001,500.00,0.00,0.00,0.00"""
    
    payout_csv = b"""Payout ID,Payout Date,Payout Amount
payout_001,2024-02-27,500.00"""
    
    bank_csv = b"""Date,Description,Credit
2024-02-28,STRIPE TRANSFER,1000.00"""
    
    rec.load_csv(balance_csv, 'balance')
    rec.load_csv(payout_csv, 'payout')
    rec.load_csv(bank_csv, 'bank')
    
    matched, exceptions, summary = rec.run_reconciliation(tolerance=5.0)
    
    print(f"Stripe Payout Amount: $500.00")
    print(f"Bank Deposit Amount: $1000.00")
    print(f"\nExpected: Bank deposit flagged as EXTRA_IN_BANK")
    
    print(f"Exceptions Found: {len(exceptions)}")
    for exc in exceptions['exception_type'].unique():
        print(f"  - {exc}")
    
    assert any(exceptions['exception_type'] == 'EXTRA_IN_BANK'), "Should flag extra in bank"
    print("[PASS] TEST 4 PASSED")


def test_scenario_5_combined_match():
    """Test 5: Two small payouts matching one larger bank deposit"""
    print("\n" + "="*80)
    print("TEST 5: Combined Match (2 Payouts -> 1 Bank)")
    print("="*80)
    
    rec = StripeReconciliator()
    
    # Two payouts 400 + 600 = 1000, one bank deposit 1000
    balance_csv = b"""Date,Payout ID,Charge Amount,Refund Amount,Fee Amount,Dispute Amount
2024-02-28,payout_001,400.00,0.00,0.00,0.00
2024-02-28,payout_002,600.00,0.00,0.00,0.00"""
    
    payout_csv = b"""Payout ID,Payout Date,Payout Amount
payout_001,2024-02-27,400.00
payout_002,2024-02-27,600.00"""
    
    bank_csv = b"""Date,Description,Credit
2024-02-28,STRIPE TRANSFER,1000.00"""
    
    rec.load_csv(balance_csv, 'balance')
    rec.load_csv(payout_csv, 'payout')
    rec.load_csv(bank_csv, 'bank')
    
    matched, exceptions, summary = rec.run_reconciliation(tolerance=5.0)
    
    print(f"Stripe Payouts: $400.00 + $600.00 = $1000.00 (2 payouts)")
    print(f"Bank Deposit: $1000.00 (1 deposit)")
    print(f"\nExpected: COMBINED_MATCH")
    
    print(f"Matched rows: {len(matched)}")
    if not matched.empty:
        print(f"Match types: {matched['match_type'].unique()}")
        print(f"Payout amounts: {matched['payout_amount'].values}")
        if 'COMBINED_MATCH' in matched['match_type'].values:
            print("[PASS] TEST 5 PASSED - Combined match detected")
        else:
            print("[WARN] TEST 5 WARNING - Combined match not detected")


def test_scenario_6_split_match():
    """Test 6: One large payout matching two smaller bank deposits"""
    print("\n" + "="*80)
    print("TEST 6: Split Match (1 Payout -> 2 Banks)")
    print("="*80)
    
    rec = StripeReconciliator()
    
    # One payout 1000, two bank deposits 400 + 600 = 1000
    balance_csv = b"""Date,Payout ID,Charge Amount,Refund Amount,Fee Amount,Dispute Amount
2024-02-28,payout_001,1000.00,0.00,0.00,0.00"""
    
    payout_csv = b"""Payout ID,Payout Date,Payout Amount
payout_001,2024-02-27,1000.00"""
    
    bank_csv = b"""Date,Description,Credit
2024-02-28,STRIPE TRANSFER,400.00
2024-02-28,STRIPE TRANSFER,600.00"""
    
    rec.load_csv(balance_csv, 'balance')
    rec.load_csv(payout_csv, 'payout')
    rec.load_csv(bank_csv, 'bank')
    
    matched, exceptions, summary = rec.run_reconciliation(tolerance=5.0)
    
    print(f"Stripe Payout: $1000.00 (1 payout)")
    print(f"Bank Deposits: $400.00 + $600.00 = $1000.00 (2 deposits)")
    print(f"\nExpected: SPLIT_MATCH")
    
    print(f"Matched rows: {len(matched)}")
    if not matched.empty:
        print(f"Match types: {matched['match_type'].unique()}")
        print(f"Matched bank amount: {matched['matched_bank_amount'].values}")
        if 'SPLIT_MATCH' in matched['match_type'].values:
            print("[PASS] TEST 6 PASSED - Split match detected")
        else:
            print("[WARN] TEST 6 WARNING - Split match not detected")


def test_scenario_7_net_activity_calculation():
    """Test 7: Net activity formula accuracy"""
    print("\n" + "="*80)
    print("TEST 7: Net Activity Calculation")
    print("="*80)
    
    rec = StripeReconciliator()
    
    # Charges: 1000, Refunds: -200, Fees: -50, Disputes: -25
    # Net = 1000 - 200 - 50 - 25 = 725
    balance_csv = b"""Date,Payout ID,Charge Amount,Refund Amount,Fee Amount,Dispute Amount
2024-02-28,payout_001,1000.00,-200.00,-50.00,-25.00"""
    
    rec.load_csv(balance_csv, 'balance')
    activity = rec.calculate_net_activity()
    
    print(f"Charges: ${activity['charges']:.2f}")
    print(f"Refunds: ${activity['refunds']:.2f}")
    print(f"Fees: ${activity['fees']:.2f}")
    print(f"Disputes: ${activity['disputes']:.2f}")
    
    expected_net = 1000 - 200 - 50 - 25
    actual_net = activity['charges'] + activity['refunds'] + activity['fees'] + activity['disputes']
    
    print(f"\nExpected Net: ${expected_net:.2f}")
    print(f"Actual Net: ${actual_net:.2f}")
    
    assert abs(actual_net - expected_net) < 0.01, f"Net activity mismatch: expected {expected_net}, got {actual_net}"
    print("[PASS] TEST 7 PASSED")


def test_scenario_8_summary_calculation():
    """Test 8: Summary totals and reconciliation status"""
    print("\n" + "="*80)
    print("TEST 8: Summary Calculation and Reconciliation Status")
    print("="*80)
    
    rec = StripeReconciliator()
    
    # Setup: 2 payouts totaling 1500, 2 bank deposits totaling 1500
    balance_csv = b"""Date,Payout ID,Charge Amount,Refund Amount,Fee Amount,Dispute Amount
2024-02-28,payout_001,1000.00,0.00,0.00,0.00
2024-02-28,payout_002,500.00,0.00,0.00,0.00"""
    
    payout_csv = b"""Payout ID,Payout Date,Payout Amount
payout_001,2024-02-27,1000.00
payout_002,2024-02-27,500.00"""
    
    bank_csv = b"""Date,Description,Credit
2024-02-28,STRIPE TRANSFER,1000.00
2024-02-28,STRIPE TRANSFER,500.00"""
    
    rec.load_csv(balance_csv, 'balance')
    rec.load_csv(payout_csv, 'payout')
    rec.load_csv(bank_csv, 'bank')
    
    matched, exceptions, summary = rec.run_reconciliation(tolerance=5.0)
    
    print(f"Total Stripe Payouts: ${summary['total_stripe_payouts']:.2f}")
    print(f"Total Bank Deposits: ${summary['total_bank_deposits']:.2f}")
    print(f"Matched Total: ${summary['matched_total']:.2f}")
    print(f"Unmatched Stripe: ${summary['unmatched_stripe_total']:.2f}")
    print(f"Unmatched Bank: ${summary['unmatched_bank_total']:.2f}")
    print(f"Difference: ${summary['difference']:.2f}")
    print(f"Status: {summary['status']}")
    
    assert summary['total_stripe_payouts'] == 1500, "Total stripe should be 1500"
    assert summary['total_bank_deposits'] == 1500, "Total bank should be 1500"
    assert abs(summary['difference']) < 0.01, "Difference should be 0"
    assert summary['status'] == 'RECONCILED', "Status should be RECONCILED"
    print("[PASS] TEST 8 PASSED")


if __name__ == '__main__':
    try:
        test_scenario_1_exact_match()
        test_scenario_2_amount_difference_within_tolerance()
        test_scenario_3_amount_exceeds_tolerance()
        test_scenario_4_missing_payout()
        test_scenario_5_combined_match()
        test_scenario_6_split_match()
        test_scenario_7_net_activity_calculation()
        test_scenario_8_summary_calculation()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
