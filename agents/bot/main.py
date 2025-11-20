# agents/bot/main.py
"""
Bot v2: Intelligent Planner for CRD12

Main entry point for Bot commands:
- Roadmap-Load: Load and validate ROADMAP.yaml
- Roadmap-GenerateTZ: Generate TZ for Engineer_B
- Roadmap-UpdateStatus: Update task status and JOURNAL
- Roadmap-Sync: Detect DRIFT between YAML and MD
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    parser = argparse.ArgumentParser(description="Bot v2: Intelligent Planner")
    parser.add_argument("command", choices=["load", "generate-tz", "update-status", "sync"],
                        help="Command to execute")
    parser.add_argument("--task-id", help="Task ID (for generate-tz)")
    parser.add_argument("--status", help="New status (for update-status)")
    parser.add_argument("--commit", help="Commit SHA (for update-status)")
    
    args = parser.parse_args()
    
    if args.command == "load":
        from commands.roadmap_load import roadmap_load
        roadmap_load()
    
    elif args.command == "generate-tz":
        if not args.task_id:
            print("ERROR: --task-id required for generate-tz")
            sys.exit(1)
        from commands.roadmap_generate_tz import roadmap_generate_tz
        roadmap_generate_tz(args.task_id)
    
    elif args.command == "update-status":
        if not args.task_id or not args.status:
            print("ERROR: --task-id and --status required for update-status")
            sys.exit(1)
        from commands.roadmap_update_status import roadmap_update_status
        roadmap_update_status(args.task_id, args.status, args.commit)
    
    elif args.command == "sync":
        from commands.roadmap_sync import roadmap_sync
        roadmap_sync()

if __name__ == "__main__":
    main()
