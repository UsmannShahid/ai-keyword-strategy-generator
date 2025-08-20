import json
import os
from datetime import datetime

# Backup the original file first
backup_file = 'data/evals_backup.jsonl'
original_file = 'data/evals.jsonl'

print("Creating backup...")
with open(original_file, 'r', encoding='utf-8') as src:
    with open(backup_file, 'w', encoding='utf-8') as dst:
        dst.write(src.read())

print("Backup created as evals_backup.jsonl")

# Read, update, and write back
updated_entries = []
total_updated = 0

with open(original_file, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
            
        data = json.loads(line)
        
        # Check if type field is missing
        has_type_top = 'type' in data
        has_type_extra = 'type' in (data.get('extra', {}) or {})
        
        if not has_type_top and not has_type_extra:
            # Add the missing type field
            if 'extra' not in data:
                data['extra'] = {}
            elif data['extra'] is None:
                data['extra'] = {}
                
            # Default to content_brief since most entries appear to be briefs
            data['extra']['type'] = 'content_brief'
            total_updated += 1
            print(f"Updated entry {line_num}: Added type = content_brief")
        
        updated_entries.append(data)

# Write back the updated data
with open(original_file, 'w', encoding='utf-8') as f:
    for entry in updated_entries:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

print(f"\nBackfill complete!")
print(f"Total entries processed: {len(updated_entries)}")
print(f"Entries updated: {total_updated}")
print(f"Original file backed up as: {backup_file}")
