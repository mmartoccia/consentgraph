#!/usr/bin/env python3
"""
ConsentGraph demo — agent trying 4 actions, showing all tiers.
Designed for GIF recording: clear output, deliberate pacing.
"""

import time
import sys

def typewrite(text, delay=0.03):
    for ch in text:
        print(ch, end='', flush=True)
        time.sleep(delay)
    print()

def pause(s=0.6):
    time.sleep(s)

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
ORANGE = "\033[38;5;214m"
RED    = "\033[91m"
CYAN   = "\033[96m"
DIM    = "\033[2m"

TIER_COLOR = {
    "SILENT":  GREEN,
    "VISIBLE": CYAN,
    "FORCED":  YELLOW,
    "BLOCKED": RED,
}

TIER_LABEL = {
    "SILENT":  "✅ SILENT   — executing autonomously",
    "VISIBLE": "👁  VISIBLE  — notifying operator",
    "FORCED":  "⏸  FORCED   — awaiting human approval",
    "BLOCKED": "🚫 BLOCKED  — action permanently denied",
}

ACTIONS = [
    ("ecs",  "list_services",              "SILENT",  0.85),
    ("ecs",  "update_service",             "FORCED",  0.91),
    ("iam",  "attach_role_policy",         "BLOCKED", 0.99),
    ("ec2",  "terminate_instances",        "BLOCKED", 0.97),
]

print()
typewrite(f"{BOLD}{CYAN}▓ ConsentGraph — live policy check{RESET}", delay=0.025)
typewrite(f"{DIM}  graph: aws-ecs-deployment-agent.json{RESET}", delay=0.015)
print()
pause(0.5)

for domain, action, expected_tier, confidence in ACTIONS:
    typewrite(f"{DIM}$ {RESET}check_consent({CYAN}\"{domain}\"{RESET}, {CYAN}\"{action}\"{RESET}, confidence={confidence})", delay=0.018)
    pause(0.55)

    tier = expected_tier
    color = TIER_COLOR[tier]
    label = TIER_LABEL[tier]

    print(f"  {color}{BOLD}{tier}{RESET}  {DIM}{label}{RESET}")

    if tier == "BLOCKED":
        pause(0.3)
        print(f"  {RED}{DIM}  ConsentError: '{domain}.{action}' is permanently blocked by policy{RESET}")

    pause(0.75)

print()
typewrite(f"{DIM}  audit log → ~/.consent-audit.jsonl{RESET}", delay=0.015)
pause(0.4)
typewrite(f"{DIM}  pip install consentgraph  ·  consentgraph.dev{RESET}", delay=0.015)
print()
