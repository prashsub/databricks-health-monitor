#!/usr/bin/env python3
"""
Fix cost_intelligence sample_questions format.

Issue: sample_questions are plain strings, should be objects with {id, question}
Reference: context/genie/genie_space_export.json shows correct format
"""

import json
import uuid

def fix_sample_questions():
    """Convert string sample_questions to object format."""
    
    json_file = "src/genie/cost_intelligence_genie_export.json"
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Fix config.sample_questions
    if "config" in data and "sample_questions" in data["config"]:
        sq = data["config"]["sample_questions"]
        
        if sq and isinstance(sq[0], str):
            # Convert strings to objects
            print(f"Converting {len(sq)} sample_questions from strings to objects...")
            
            new_sq = []
            for question_text in sq:
                new_sq.append({
                    "id": uuid.uuid4().hex,  # Generate 32 hex char ID
                    "question": [question_text]  # Wrap in array
                })
            
            data["config"]["sample_questions"] = new_sq
            print(f"✓ Converted {len(new_sq)} sample questions")
            
            # Show before/after
            print(f"\n❌ BEFORE: ['What is our total spend?', ...]")
            print(f"✅ AFTER: [{{'id': '...', 'question': ['What is our total spend?']}}, ...]")
        else:
            print("✓ sample_questions already in correct format")
    
    # Write back
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Updated: {json_file}")


if __name__ == "__main__":
    fix_sample_questions()
    print("\n✅ Fix complete!")
    print("   Reference: context/genie/genie_space_export.json")
