import json

count_with_type = 0
count_without_type = 0
total = 0

with open('data/evals.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        total += 1
        data = json.loads(line)
        has_type_top = 'type' in data
        has_type_extra = 'type' in (data.get('extra', {}) or {})
        
        if has_type_top or has_type_extra:
            count_with_type += 1
            if has_type_extra:
                print(f'Entry {total}: extra.type = {data["extra"]["type"]}')
        else:
            count_without_type += 1
            print(f'Entry {total}: NO TYPE FIELD')

print(f'\nSummary:')
print(f'Total entries: {total}')
print(f'Entries with type field: {count_with_type}')
print(f'Entries without type field: {count_without_type}')
