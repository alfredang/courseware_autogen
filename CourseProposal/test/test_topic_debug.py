import sys
import os
import json
from docx import Document
import re

def print_docx_content():
    """Parse a document and print topics with their subtopics."""
    # Input document path
    input_docx = "input/TSC_Mapping-TI-ai-storytelling_enhanced.docx"
    
    print(f"Reading document: {input_docx}")
    
    try:
        # Load the document
        doc = Document(input_docx)
        
        # Iterate through all tables in the document
        print("\n=== Tables in document ===")
        for table_idx, table in enumerate(doc.tables):
            print(f"\nTable {table_idx+1} - {len(table.rows)} rows x {len(table.rows[0].cells) if table.rows else 0} columns")
            
            # Iterate through rows and cells
            for row_idx, row in enumerate(table.rows):
                print(f"\nRow {row_idx+1}:")
                for cell_idx, cell in enumerate(row.cells):
                    cell_text = cell.text.strip()
                    print(f"  Cell {cell_idx+1}: {cell_text[:50] + '...' if len(cell_text) > 50 else cell_text}")
                    
                    # If this might be a topic cell, check for subtopics
                    if "T1: Fundamentals of storytelling" in cell_text:
                        print("\n  *** FOUND TOPIC 1 CELL ***")
                        print("  Full cell content:")
                        print(f"  {cell_text}")
                        
                        # Split by newlines to see if there are subtopics
                        lines = [l.strip() for l in cell_text.split('\n') if l.strip()]
                        print(f"\n  Split into {len(lines)} lines:")
                        for line_idx, line in enumerate(lines):
                            print(f"    Line {line_idx+1}: {line}")
                        
                        if len(lines) > 1:
                            topic = lines[0]
                            subtopics = lines[1:]
                            print("\n  Topic and subtopics structure:")
                            print(f"    Topic: {topic}")
                            print(f"    Subtopics ({len(subtopics)}):")
                            for i, subtopic in enumerate(subtopics):
                                print(f"      Subtopic {i+1}: {subtopic}")

    except Exception as e:
        print(f"Error processing document: {e}")

if __name__ == "__main__":
    print_docx_content() 