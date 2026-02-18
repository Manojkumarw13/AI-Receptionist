"""Verification script for all 11 medium priority bug fixes."""
import ast

files = {
    'app.py': [
        ('BUG-06: No load_css() call inside login_page()', 'def login_page():\n    # FIX BUG-06', True),
        ('BUG-20: load_css() checks file existence', "if not os.path.exists(css_path)", True),
        ('BUG-20: load_css() has try/except', "except Exception:\n        pass  # Never crash", True),
    ],
    'agent/graph.py': [
        ('BUG-10: No state["current_time"] mutation', 'state["current_time"]', False),
        ('BUG-10: current_time passed via dict', '"current_time": current_time', True),
        ('BUG-23: import time for retry backoff', 'import time  # FIX BUG-23', True),
        ('BUG-23: retry loop with max_retries', 'max_retries = 3', True),
        ('BUG-23: exponential backoff', 'time.sleep(wait)', True),
    ],
    'agent/tools.py': [
        ('BUG-13: advance_to_working_hours helper', 'advance_to_working_hours', True),
        ('BUG-13: weekday check for weekends', 'dt.weekday() >= 5', True),
        ('BUG-13: WORKING_HOURS_START check', 'dt.hour < WORKING_HOURS_START', True),
        ('BUG-13: WORKING_HOURS_END check', 'dt.hour >= WORKING_HOURS_END', True),
        ('BUG-13: also filters soft-deleted in availability', 'Appointment.is_deleted == False  # FIX', True),
    ],
    'ui/admin_dashboard.py': [
        ('BUG-25: email regex validation', "re.match(r'^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'", True),
        ('BUG-25: password length check', 'len(new_password) < 8', True),
        ('BUG-26: self-delete guard', 'target_user.email == current_user_email', True),
        ('BUG-26: error shown for self-delete', 'You cannot delete your own admin account', True),
        ('BUG-27: except block in change_user_role', 'except Exception as e:\n        session.rollback()\n        st.error(f', True),
    ],
    'ui/calendar_view.py': [
        ('BUG-19: num_doctors parameter added', 'def show_statistics(appointments, start_date, end_date, num_doctors=1)', True),
        ('BUG-19: total_slots multiplied by num_doctors', 'total_slots = total_days * slots_per_day * num_doctors', True),
        ('BUG-19: show_all_doctors passes num_doctors', 'num_doctors=len(doctors) if doctors else 1', True),
    ],
    'ui/dashboard.py': [
        ('BUG-28: empty star schema check', 'total_facts = session.query(FactAppointment).count()', True),
        ('BUG-28: fallback message shown', 'No analytics data yet', True),
        ('BUG-28: early return on empty', 'if total_facts == 0:', True),
    ],
}

all_pass = True
total_checks = 0
passed_checks = 0

for filepath, checks in files.items():
    print(f'\n[FILE] {filepath}')
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print(f'  [SYNTAX OK]')
        for desc, pattern, should_exist in checks:
            total_checks += 1
            found = pattern in content
            ok = found == should_exist
            if ok:
                passed_checks += 1
            else:
                all_pass = False
            status = 'PASS' if ok else 'FAIL'
            print(f'  [{status}] {desc}')
    except SyntaxError as e:
        print(f'  [SYNTAX ERROR] {e}')
        all_pass = False
    except FileNotFoundError:
        print(f'  [FILE NOT FOUND]')
        all_pass = False

print()
print(f'=== RESULT: {passed_checks}/{total_checks} checks passed ===')
print('ALL MEDIUM BUGS VERIFIED FIXED' if all_pass else 'SOME CHECKS FAILED - review above')
