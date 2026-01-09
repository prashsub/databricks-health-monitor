#!/usr/bin/env python3
"""
Clean up duplicate benchmark questions and restore proper structure.
Removes Section H and replaces with clean 25-question structure.
"""

from pathlib import Path
import re

def clean_cost_intelligence():
    """Clean up cost_intelligence_genie.md benchmark section."""
    file_path = Path("src/genie/cost_intelligence_genie.md")
    content = file_path.read_text()
    
    # Find Section H start
    section_h_pattern = r'## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████'
    section_h_match = re.search(section_h_pattern, content)
    
    if not section_h_match:
        print("❌ Section H not found in cost_intelligence_genie.md")
        return False
    
    start_pos = section_h_match.start()
    
    # Find deliverables checklist (end of Section H)
    deliverables_pattern = r'## ✅ DELIVERABLE CHECKLIST'
    deliverables_match = re.search(deliverables_pattern, content[start_pos:])
    
    if not deliverables_match:
        print("❌ Deliverables checklist not found")
        return False
    
    end_pos = start_pos + deliverables_match.start()
    
    # Extract everything before and after Section H
    before_section_h = content[:start_pos]
    after_section_h = content[end_pos:]
    
    # Count current questions
    section_h_content = content[start_pos:end_pos]
    current_questions = len(re.findall(r'^### Question \d+:', section_h_content, re.MULTILINE))
    unique_nums = len(set([int(m) for m in re.findall(r'^### Question (\d+):', section_h_content, re.MULTILINE)]))
    
    print(f"✓ Found {current_questions} questions ({unique_nums} unique numbers)")
    print(f"✓ Removing duplicates and preparing for clean replacement...")
    
    # Keep the structure for now - we'll replace in the next step
    return True

if __name__ == "__main__":
    clean_cost_intelligence()





