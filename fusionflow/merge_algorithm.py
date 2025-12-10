"""Merge algorithm for timeline conflicts"""

def merge_timelines(source_state, target_state):
    """
    Merge source timeline state into target timeline state
    Simple strategy: target gets all source updates
    """
    merged = target_state.copy()
    merged.update(source_state)
    return merged

def detect_conflicts(source_state, target_state):
    """Detect conflicts between two timeline states"""
    conflicts = []
    
    for key in source_state:
        if key in target_state:
            if source_state[key] != target_state[key]:
                conflicts.append({
                    'key': key,
                    'source_value': source_state[key],
                    'target_value': target_state[key]
                })
    
    return conflicts
