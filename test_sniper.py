import sys
import os

# UTF-8 stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from agent import load_env, run_scan_cycle

print("""
===================================================================
             🎯 TESTING AI JOB SNIPER (1-CYCLE TEST)
===================================================================
""")
config = load_env()
seen = set()  # Clean set for testing
print("Scanning live tech job boards and matching against candidate profile...")
run_scan_cycle(config, seen, is_initial=False, max_alerts_per_cycle=2)
print("\n✅ Test cycle completed! Check your Telegram for the job alerts! 🚀")

