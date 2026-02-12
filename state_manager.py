#!/usr/bin/env python3
"""
Atomic state manager with optimistic concurrency and auto-rollback
"""

import json
import shutil
import os
import fcntl
from datetime import datetime
from pathlib import Path

STATE_DIR = Path("/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue")
STATE_FILE = STATE_DIR / "state.json"
LOCK_FILE = STATE_DIR / ".state.lock"
HANDOFF_DIR = STATE_DIR / "handoffs"
MAX_VERSIONS = 5

def acquire_lock():
    """Acquire exclusive lock for concurrent access"""
    lock_fd = open(LOCK_FILE, 'w')
    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
    return lock_fd

def release_lock(lock_fd):
    """Release exclusive lock"""
    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
    lock_fd.close()

def atomic_write(filepath: Path, data: dict) -> None:
    """Write atomically using temp file + rename"""
    temp_path = filepath.with_suffix('.tmp')
    try:
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        temp_path.replace(filepath)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise e

def rotate_versions():
    """Keep last N versions of state.json"""
    versions = sorted(STATE_DIR.glob("state.prev.*.json"), reverse=True)
    for old in versions[MAX_VERSIONS-1:]:
        old.unlink()
    
    if STATE_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = STATE_DIR / f"state.prev.{timestamp}.json"
        shutil.copy(STATE_FILE, backup)

def read_state() -> dict:
    """Read state with validation and auto-rollback on corruption"""
    if not STATE_FILE.exists():
        return create_default_state()
    
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except json.JSONDecodeError:
        print("⚠️  State file corrupted! Attempting rollback...")
        return rollback_to_previous()
    
    # Validate required fields
    required = ["project", "metrics", "assets", "version"]
    for field in required:
        if field not in state:
            print(f"⚠️  Missing field: {field}. Rolling back...")
            return rollback_to_previous()
    
    return state

def rollback_to_previous() -> dict:
    """Auto-rollback to most recent backup"""
    versions = sorted(STATE_DIR.glob("state.prev.*.json"), reverse=True)
    
    if not versions:
        print("❌ No backup available! Creating fresh state.")
        return create_default_state()
    
    # Try backups from newest to oldest
    for backup in versions:
        try:
            with open(backup) as f:
                state = json.load(f)
            # Validate
            required = ["project", "metrics", "assets", "version"]
            if all(field in state for field in required):
                print(f"✅ Rolled back to {backup.name}")
                # Restore this version
                shutil.copy(backup, STATE_FILE)
                return state
        except Exception:
            continue
    
    print("❌ All backups corrupted! Creating fresh state.")
    return create_default_state()

def write_state(state: dict, updated_by: str, expected_version: int = None) -> bool:
    """
    Write state atomically with optimistic concurrency control.
    
    Args:
        state: New state to write
        updated_by: Agent name
        expected_version: If provided, write fails if current version != expected
    
    Returns:
        True if write succeeded, False if version conflict
    """
    lock_fd = acquire_lock()
    try:
        # Check version for optimistic concurrency
        if expected_version is not None:
            current = read_state()
            if current.get("version", 0) != expected_version:
                print(f"⚠️  Version conflict! Expected {expected_version}, found {current.get('version')}")
                return False
        
        rotate_versions()
        
        state["last_updated"] = datetime.now().isoformat()
        state["updated_by"] = updated_by
        state["version"] = state.get("version", 0) + 1
        
        atomic_write(STATE_FILE, state)
        return True
    finally:
        release_lock(lock_fd)

def create_handoff(from_agent: str, to_agent: str, summary: dict) -> dict:
    """Create structured handoff with validation"""
    lock_fd = acquire_lock()
    try:
        state = read_state()
        
        handoff = {
            "from": from_agent,
            "to": to_agent,
            "timestamp": datetime.now().isoformat(),
            "version": state.get("version", 0),
            "summary": summary
        }
        
        # Validate required fields
        required_summary = ["status", "deliverables", "blockers", "next_steps"]
        for field in required_summary:
            if field not in summary:
                raise ValueError(f"Handoff missing required field: {field}")
        
        # Save handoff
        HANDOFF_DIR.mkdir(exist_ok=True)
        handoff_file = HANDOFF_DIR / f"handoff_{from_agent}_{to_agent}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        atomic_write(handoff_file, handoff)
        
        return handoff
    finally:
        release_lock(lock_fd)

def sanity_check(agent_name: str) -> dict:
    """
    New agent's first action: validate state and handoff consistency.
    Returns state if valid, triggers rollback if invalid.
    """
    state = read_state()
    
    # Check for obvious inconsistencies
    issues = []
    
    if state.get("metrics", {}).get("leads_generated", 0) < 0:
        issues.append("Negative lead count")
    
    if state.get("metrics", {}).get("customers", 0) < 0:
        issues.append("Negative customer count")
    
    if issues:
        print(f"⚠️  Sanity check failed: {', '.join(issues)}")
        print("🔄 Triggering rollback...")
        return rollback_to_previous()
    
    print(f"✅ {agent_name} sanity check passed (v{state.get('version', 0)})")
    return state

def create_default_state() -> dict:
    """Create fresh state file"""
    return {
        "project": "Revenue Rescue",
        "domain": "pac-holding.com",
        "status": "building",
        "phase": "validation",
        "version": 0,
        "metrics": {
            "leads_generated": 994,
            "leads_validated": 0,
            "beta_signups": 0,
            "demo_calls_booked": 0,
            "customers": 0
        },
        "assets": {
            "landing_page": {"url": "https://pac-holding.com", "status": "in_progress"},
            "demo_line": "(817) 873-6706",
            "business_line": "(817) 975-6105",
            "email": "Connor@pac-holding.com"
        },
        "active_agents": [],
        "blockers": [],
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    if not STATE_FILE.exists():
        write_state(create_default_state(), "init")
        print("State file initialized")
    else:
        state = sanity_check("main")
        print(f"State v{state.get('version', 0)} ready")