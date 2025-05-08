import json
import os
import sys
import traceback
from CourseProposal.utils.excel_conversion_pipeline import map_new_key_names_excel
from CourseProposal.utils.excel_replace_xml import process_excel_update, preserve_excel_metadata

def cleanup_old_files(modified_path, preserved_path):
    """Remove any existing output files to avoid confusion."""
    for path in [modified_path, preserved_path]:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Removed existing file: {path}")
            except Exception as e:
                print(f"Warning: Could not remove {path}: {e}")

def test_excel_generation():
    try:
        # Define paths
        json_data_path = "CourseProposal/json_output/generated_mapping.json"
        generated_mapping_path = "CourseProposal/json_output/generated_mapping.json"
        output_json_file = "CourseProposal/json_output/generated_mapping.json"
        excel_data_path = "CourseProposal/json_output/excel_data.json"
        ensemble_output_path = "CourseProposal/json_output/ensemble_output.json"
        excel_template_path = "CourseProposal/templates/course_proposal_form_01apr2025_template.xlsx"
        output_excel_path_modified = "CourseProposal/output_docs/CP_template_updated_cells_output.xlsx"
        output_excel_path_preserved = "CourseProposal/output_docs/CP_template_metadata_preserved.xlsx"
        
        # Ensure output directory exists
        os.makedirs("CourseProposal/output_docs", exist_ok=True)
        
        # Load necessary files
        print("\n1. Loading JSON files...")
        with open(generated_mapping_path, 'r') as f:
            generated_mapping = json.load(f)
            print(f"  - Loaded generated_mapping from {generated_mapping_path}")
        
        with open(ensemble_output_path, 'r') as f:
            ensemble_output = json.load(f)
            print(f"  - Loaded ensemble_output from {ensemble_output_path}")
        
        # Verify required files exist
        print("\n2. Verifying template file exists...")
        if not os.path.exists(excel_template_path):
            print(f"ERROR: Template file not found: {excel_template_path}")
            return
        print(f"  - Template file exists: {excel_template_path}")
        
        # Clean up existing files
        print("\n3. Cleaning up any existing output files...")
        cleanup_old_files(output_excel_path_modified, output_excel_path_preserved)
        
        # Run mapping function
        print("\n4. Running mapping function...")
        try:
            map_new_key_names_excel(
                generated_mapping_path,
                generated_mapping,
                output_json_file,
                excel_data_path,
                ensemble_output
            )
            print("  - Mapping complete")
        except Exception as e:
            print(f"ERROR in mapping function: {e}")
            traceback.print_exc()
            return
        
        # Process Excel update
        print("\n5. Processing Excel update...")
        try:
            process_excel_update(
                json_data_path,
                excel_template_path,
                output_excel_path_modified,
                ensemble_output_path
            )
            print(f"  - Excel update complete, file created: {output_excel_path_modified}")
        except Exception as e:
            print(f"ERROR in Excel update: {e}")
            traceback.print_exc()
            return
        
        # Preserve Excel metadata
        print("\n6. Preserving Excel metadata...")
        try:
            preserve_excel_metadata(
                excel_template_path,
                output_excel_path_modified,
                output_excel_path_preserved
            )
            print(f"  - Metadata preservation complete, final file created: {output_excel_path_preserved}")
        except Exception as e:
            print(f"ERROR in metadata preservation: {e}")
            traceback.print_exc()
            return
        
        # Verify output files exist
        print("\n7. Verifying output files...")
        if os.path.exists(output_excel_path_modified):
            print(f"  - Modified Excel file created: {output_excel_path_modified}")
        else:
            print(f"ERROR: Modified Excel file not created: {output_excel_path_modified}")
        
        if os.path.exists(output_excel_path_preserved):
            print(f"  - Final Excel file created: {output_excel_path_preserved}")
        else:
            print(f"ERROR: Final Excel file not created: {output_excel_path_preserved}")
        
        print("\nExcel generation complete!")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_excel_generation() 