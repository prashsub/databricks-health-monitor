#!/usr/bin/env python3
"""
Debug script to see what SQL queries are being generated for validation.
Helps diagnose NOT_A_SCALAR_FUNCTION errors.
"""

import json
import re
from pathlib import Path

def main():
    # Read performance_genie_export.json
    json_path = Path("src/genie/performance_genie_export.json")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Get Q5 (index 4, 0-based)
    benchmarks = data.get('benchmarks', {})
    questions = benchmarks.get('questions', [])
    
    if len(questions) > 4:
        q5 = questions[4]
        print("=== Performance Q5 ===")
        print(f"Question: {q5['question']}")
        print("\nSQL from JSON:")
        
        answer = q5['answer'][0]
        content = answer['content']
        
        # Join like the validator does
        sql = '\n'.join(content)
        print(sql)
        
        # Apply ACTUAL validator logic (from validate_query function)
        original_query = sql.strip().rstrip(';')
        
        # Check if needs wrapping (match validator logic exactly)
        needs_wrapping = (
            'WITH ' in original_query.upper()[:50] or
            original_query.upper().strip().startswith('SELECT') is False
        )
        
        print(f"\nneeds_wrapping: {needs_wrapping}")
        
        if needs_wrapping:
            # Wrap complex queries (CTEs, etc.) to add LIMIT 1
            validation_query = f"SELECT * FROM ({original_query}) LIMIT 1"
            print("\n=== Validation: WRAPPED with SELECT * FROM ===")
        else:
            # Simple SELECT - just append LIMIT 1
            # Remove existing LIMIT clause if present
            validation_query = re.sub(r'\s+LIMIT\s+\d+\s*$', '', original_query, flags=re.IGNORECASE)
            validation_query = f"{validation_query} LIMIT 1"
            print("\n=== Validation: APPENDED LIMIT 1 (no wrapping) ===")
        
        print(validation_query)
        
        # Check if TABLE() wrapper is present
        if 'TABLE(' in validation_query:
            print("\n✅ TABLE() wrapper is present in validation query")
        else:
            print("\n❌ TABLE() wrapper is MISSING in validation query!")

if __name__ == "__main__":
    main()

