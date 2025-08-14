#!/usr/bin/env python3
from services import generate_brief_with_variant
from parsing import parse_brief_output, detect_placeholders

# Generate a test brief
keyword = 'best ergonomic office chair'
print(f"Testing content brief generation for: {keyword}")

try:
    output, prompt_used, latency_ms, usage = generate_brief_with_variant(keyword=keyword, variant='A')
    
    print(f"Output length: {len(output)}")
    print("First 500 chars:")
    print(repr(output[:500]))
    print()
    
    # Test parsing
    data, is_json = parse_brief_output(output)
    print(f"Is JSON: {is_json}")
    print(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    print()
    
    # Test placeholder detection
    if is_json:
        placeholders = detect_placeholders(data)
        print(f"Has placeholders: {placeholders}")
    
    # Test heading detection
    heading_count_newline = output.count('\n#') if output else 0
    heading_count_double = output.lower().count('##') if output else 0
    print(f"Headings (newline #): {heading_count_newline}")
    print(f"Headings (##): {heading_count_double}")
    
    # Check auto-flags logic
    auto_flags = []
    
    # Heuristic 1: placeholder detection
    if is_json and detect_placeholders(data):
        auto_flags.append("Detected generic placeholders (e.g., 'Chair Name #1').")
    
    # Heuristic 2: very short output
    if (output or '').strip() and len(output.strip()) < 400:
        auto_flags.append("Output is quite short (<400 chars) – may be truncated or low quality.")
    
    # Heuristic 3: missing headings if JSON has structure but few sections
    if is_json and isinstance(data, dict):
        section_keys = [k for k in data.keys() if any(token in k.lower() for token in ["intro","outline","h1","h2","sections","faq","conclusion","title"])]
        if len(section_keys) <= 2:
            auto_flags.append("Parsed JSON has very few structured sections – might be incomplete.")
    
    # Heuristic 4: count of markdown headings in raw output (only for non-JSON outputs)
    if output and not is_json and output.count("\n#") < 2 and output.lower().count("##") < 2:
        auto_flags.append("Few or no markdown headings detected – consider prompting for structured outline.")
    
    print(f"\nAuto-flags triggered: {len(auto_flags)}")
    for flag in auto_flags:
        print(f"  - {flag}")

except Exception as e:
    print(f"Error: {e}")
