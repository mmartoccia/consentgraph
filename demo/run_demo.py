#!/usr/bin/env python3
"""
ConsentGraph demo script — designed for terminal recording (GIF/video).
Run with: python3 run_demo.py
Ideal capture: 120x30 terminal, asciinema or QuickTime crop.
"""

import time
import sys
import json
import os

# ANSI colors
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
GRAY   = "\033[90m"

TIER_COLORS = {
    "SILENT":  GREEN,
    "VISIBLE": CYAN,
    "FORCED":  YELLOW,
    "BLOCKED": RED,
}

TIER_ICONS = {
    "SILENT":  "●",
    "VISIBLE": "◉",
    "FORCED":  "⚠",
    "BLOCKED": "✕",
}


def slow_print(text, delay=0.03, newline=True):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    if newline:
        print()


def pause(t=0.6):
    time.sleep(t)


def print_tier(domain, action, tier, confidence):
    color = TIER_COLORS[tier]
    icon  = TIER_ICONS[tier]
    print(f"\n  {GRAY}checking consent:{RESET}  {CYAN}{domain}{RESET} → {WHITE}{action}{RESET}  {DIM}(confidence: {confidence:.0%}){RESET}")
    pause(0.5)
    print(f"  {color}{BOLD}{icon}  {tier}{RESET}", end="")
    pause(0.2)


def print_separator():
    print(f"\n  {GRAY}{'─' * 58}{RESET}")


def main():
    # Clear screen
    os.system("clear")
    pause(0.4)

    # Header
    print(f"\n  {BOLD}{WHITE}ConsentGraph{RESET}  {GRAY}v0.1.0 — policy-as-code for AI agents{RESET}\n")
    pause(0.5)

    print(f"  {GRAY}loading policy from:{RESET} {CYAN}~/.consentgraph/consent-graph.json{RESET}")
    pause(0.7)
    print(f"  {GREEN}✓{RESET} {GRAY}policy loaded — 3 domains, 12 rules{RESET}")
    pause(0.8)

    print_separator()

    # --- Action 1: SILENT ---
    pause(0.4)
    slow_print(f"\n  {GRAY}agent:{RESET} reading customer_report.csv ...", delay=0.025)
    print_tier("filesystem", "read", "SILENT", 0.97)
    print(f"  {DIM}→ executed autonomously. logged.{RESET}")
    pause(0.9)

    # --- Action 2: VISIBLE ---
    slow_print(f"\n  {GRAY}agent:{RESET} sending weekly digest to internal team ...", delay=0.025)
    print_tier("email", "send_internal", "VISIBLE", 0.91)
    print(f"  {DIM}→ executed. operator notified.{RESET}")
    pause(0.9)

    # --- Action 3: FORCED ---
    slow_print(f"\n  {GRAY}agent:{RESET} forwarding report to external vendor ...", delay=0.025)
    print_tier("email", "send_external", "FORCED", 0.74)
    print(f"  {DIM}→ paused. waiting for operator approval...{RESET}")
    pause(0.6)
    print(f"  {YELLOW}?{RESET}  {BOLD}approve?{RESET} {GRAY}[y/N]{RESET} ", end="")
    sys.stdout.flush()
    pause(1.2)
    slow_print("N", delay=0.08)
    pause(0.3)
    print(f"  {GRAY}→ action cancelled by operator.{RESET}")
    pause(1.0)

    # --- Action 4: BLOCKED (the money shot) ---
    print_separator()
    pause(0.5)
    slow_print(f"\n  {GRAY}agent:{RESET} DELETE FROM users WHERE created_at < '2024-01-01' ...", delay=0.02)
    pause(0.3)
    print_tier("database", "delete", "BLOCKED", 0.99)
    pause(0.2)
    print()
    print(f"  {RED}{BOLD}  action permanently prohibited.{RESET}")
    print(f"  {RED}  operator alerted. event logged to audit trail.{RESET}")
    pause(0.5)
    print(f"\n  {GRAY}audit trail:{RESET} {CYAN}~/.consentgraph/logs/consent-attempts.jsonl{RESET}")
    pause(0.4)

    # Show the log line
    log_entry = {
        "timestamp": "2026-03-10T09:31:44Z",
        "domain": "database",
        "action": "delete",
        "confidence": 0.99,
        "tier": "BLOCKED",
        "reason": "action in blocked list"
    }
    print(f"  {GRAY}{json.dumps(log_entry)}{RESET}")
    pause(1.0)

    print_separator()
    print(f"\n  {GREEN}pip install consentgraph{RESET}  {GRAY}|{RESET}  {CYAN}consentgraph.dev{RESET}\n")
    pause(2.0)


if __name__ == "__main__":
    main()
