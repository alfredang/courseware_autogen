# app.py
import streamlit as st
import os
import tempfile
from CourseProposal.main import main
import asyncio
from CourseProposal.utils.document_parser import parse_document
from CourseProposal.model_configs import MODEL_CHOICES

# Initialize session state variables
if 'processing_done' not in st.session_state:
    st.session_state['processing_done'] = False
if 'output_docx' not in st.session_state:
    st.session_state['output_docx'] = None
if 'cv_output_files' not in st.session_state:
    st.session_state['cv_output_files'] = []
if 'selected_model' not in st.session_state:
    st.session_state['selected_model'] = "DeepSeek-V3"
if 'ka_validation_results' not in st.session_state:
    st.session_state['ka_validation_results'] = {}
if 'validation_displayed' not in st.session_state:
    st.session_state['validation_displayed'] = False

def app():
    st.title("📄 Course Proposal File Processor")

    # Info box at the top
    st.info(
        """
        **This application uses Agentic Process Automation** (APA) that generates Course Proposals and Course Validation forms for Tertiary Infotech.  
        **Note:** The input TSC form must follow the requirements below, or generation may fail or produce errors.
        """
    )

    # Section: Important TSC Details
    st.markdown("### 📝 **Important TSC Details to Look Out For:**")
    st.markdown(
        "Instructional and Assessment method names in the TSC must match the following exactly (case sensitive):"
    )
    st.markdown("Eg. Case studies ❌")
    st.markdown("Eg. Case Study ✅️")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Instructional Methods:**")
        st.markdown("""
- Interactive Presentation
- Didactic Questioning
- Demonstration
- Practical/Practice
- Peer Sharing
- Role Play
- Group Discussion
- Case Study
        """)
    with col2:
        st.markdown("**Assessment Methods:**")
        st.markdown("""
- Written Exam
- Practical Exam
- Case Study
- Oral Questioning
- Role Play
        """)

    # Tips section
    st.markdown("### 💡 **Tips:**")
    st.markdown("""
- Use colons (:) in all section headers, e.g., **LO1: ...**, **T1: ...**
- Topic numbers should be ascending from T1 (e.g., T1, T2, T3, ...)
- Ensure all required sections are present: LU, LO, Course Level, Proficiency Level, Industry, Background Info
- Match Knowledge (K#) and Abilities (A#) exactly as listed
- Instructional and Assessment methods must use the exact names above
- Double-check mapping between LUs, Topics, and K&A factors
    """)

    st.markdown("**Upload a TSC DOCX file**")
    uploaded_file = st.file_uploader(
        "Upload a TSC DOCX file",
        type="docx",
        key='uploaded_file',
        label_visibility="collapsed"
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Model Selection")
        model_keys = list(MODEL_CHOICES.keys())
        # Custom order: DeepSeek-V3, all Gemini, then all GPT/OpenAI
        ordered_models = []
        if 'DeepSeek-V3' in model_keys:
            ordered_models.append('DeepSeek-V3')
        # Add all Gemini models next
        for k in model_keys:
            if 'gemini' in k.lower() and k not in ordered_models:
                ordered_models.append(k)
        # Add all GPT/OpenAI models next
        for k in model_keys:
            if (('gpt' in k.lower() or 'openai' in k.lower()) and k not in ordered_models):
                ordered_models.append(k)
        # Add any remaining models
        for k in model_keys:
            if k not in ordered_models:
                ordered_models.append(k)

        model_choice = st.selectbox(
            "Select LLM Model:",
            options=ordered_models,
            index=ordered_models.index("DeepSeek-V3") if "DeepSeek-V3" in ordered_models else 0
        )
        st.session_state['selected_model'] = model_choice
    with col2:
        st.subheader("Course Proposal Type")
        cp_type_display = st.selectbox(
            "Select CP Type:",
            options=["Excel CP", "Docx CP"],
            index=0
        )
        cp_type_mapping = {
            "Excel CP": "New CP",
            "Docx CP": "Old CP"
        }
        st.session_state['cp_type'] = cp_type_mapping[cp_type_display]

    if uploaded_file is not None:
        st.success(f"Uploaded file: {uploaded_file.name}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_input:
            tmp_input.write(uploaded_file.getbuffer())
            input_tsc_path = tmp_input.name

        if st.button("🚀 Process File"):
            run_processing(input_tsc_path)
            st.session_state['processing_done'] = True

        if st.session_state.get('processing_done'):
            display_validation_results()
            st.subheader("Download Processed Files")
            cp_type = st.session_state.get('cp_type', "New CP")
            file_downloads = st.session_state.get('file_downloads', {})
            cp_docx = file_downloads.get('cp_docx')
            if cp_type == "Old CP":
                if cp_docx and os.path.exists(cp_docx['path']):
                    with open(cp_docx['path'], 'rb') as f:
                        data = f.read()
                    st.download_button(
                        label="📄 Download CP Document",
                        data=data,
                        file_name=cp_docx['name'],
                        mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    )
            if cp_type == "New CP":
                excel_file = file_downloads.get('excel')
                if excel_file and os.path.exists(excel_file['path']):
                    with open(excel_file['path'], 'rb') as f:
                        data = f.read()
                    st.download_button(
                        label="📊 Download CP Excel",
                        data=data,
                        file_name=excel_file['name'],
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                elif cp_type == "New CP":
                    st.warning("Excel file was not generated. This may be normal if processing was interrupted.")
            cv_docs = file_downloads.get('cv_docs', [])
            if cv_docs:
                st.markdown("### Course Validation Documents")
                cols = st.columns(min(3, len(cv_docs)))
                for idx, doc in enumerate(cv_docs):
                    if os.path.exists(doc['path']):
                        with open(doc['path'], 'rb') as f:
                            data = f.read()
                        file_base = os.path.basename(doc['name'])
                        validator_name = file_base.split('_')[3].capitalize()
                        col_idx = idx % len(cols)
                        with cols[col_idx]:
                            st.download_button(
                                label=f"📝 {validator_name}",
                                data=data,
                                file_name=doc['name'],
                                mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                            )

def run_processing(input_file: str):
    """
    1. Runs your main pipeline, which writes docs to 'output_docs/' 
    2. Copies those docs into NamedTemporaryFiles and stores them in session state.
    """
    st.info("Running pipeline (this might take some time) ...")
    
    # Get CP type from session state
    cp_type = st.session_state.get('cp_type', "New CP")

    # 1) Run the pipeline (async), passing the TSC doc path
    asyncio.run(main(input_file))

    # Set validation as displayed
    st.session_state['validation_displayed'] = True

    # 2) Now copy the relevant docx files from 'output_docs' to NamedTemporaryFiles
    # Common files for both CP types
    cp_doc_path = "CourseProposal/output_docs/CP_output.docx"
    cv_doc_paths = [
        "CourseProposal/output_docs/CP_validation_template_bernard_updated.docx",
        "CourseProposal/output_docs/CP_validation_template_dwight_updated.docx",
        "CourseProposal/output_docs/CP_validation_template_ferris_updated.docx",
    ]
    
    # Excel file - only for "New CP"
    excel_path = "CourseProposal/output_docs/CP_template_metadata_preserved.xlsx"
    
    # Store file info based on CP type
    st.session_state['file_downloads'] = {
        'cp_docx': None,
        'cv_docs': [],
        'excel': None
    }

    # Copy CP doc into tempfile
    if os.path.exists(cp_doc_path):
        with open(cp_doc_path, 'rb') as infile, tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as outfile:
            outfile.write(infile.read())
            st.session_state['file_downloads']['cp_docx'] = {
                'path': outfile.name,
                'name': "CP_output.docx"
            }

    # Copy CV docs
    for doc_path in cv_doc_paths:
        if os.path.exists(doc_path):
            with open(doc_path, 'rb') as infile, tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as outfile:
                outfile.write(infile.read())
                desired_name = os.path.basename(doc_path)
                st.session_state['file_downloads']['cv_docs'].append({
                    'path': outfile.name,
                    'name': desired_name
                })

    # Copy Excel file - only for New CP
    if cp_type == "New CP" and os.path.exists(excel_path):
        with open(excel_path, 'rb') as infile, tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as outfile:
            outfile.write(infile.read())
            st.session_state['file_downloads']['excel'] = {
                'path': outfile.name,
                'name': "CP_Excel_output.xlsx"
            }

    st.success("Processing complete. Download your files below!")

def display_validation_results():
    """Display Knowledge and Ability validation results"""
    if 'ka_validation_results' in st.session_state and st.session_state['ka_validation_results']:
        validation_results = st.session_state['ka_validation_results'].get('validation_results', {})
        fix_results = st.session_state['ka_validation_results'].get('fix_results', {})
        
        if validation_results:
            with st.expander("Knowledge and Ability Validation Results", expanded=not validation_results.get('success', False)):
                # Show summary results
                if validation_results.get('success', False):
                    st.success("✅ SUCCESS: All Knowledge and Ability factors are accounted for.")
                else:
                    st.error(f"❌ FAIL: {len(validation_results.get('missing_factors', []))} missing factors, {len(validation_results.get('undefined_factors', []))} undefined factors")
                
                # Show coverage metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total K&A Factors", validation_results.get('total_factors', 0))
                with col2:
                    st.metric("Covered Factors", len(validation_results.get('covered_factors', [])))
                with col3:
                    st.metric("Coverage %", f"{validation_results.get('coverage_percentage', 0):.1f}%")
                
                # Show missing factors if any
                if validation_results.get('missing_factors'):
                    st.subheader("Missing Factors")
                    for factor in validation_results.get('missing_factors', []):
                        st.markdown(f"- {factor}")
                    
                    st.markdown("""
                    **How to fix:**
                    - Ensure all Knowledge and Ability statements are referenced in at least one topic
                    - Check if any Learning Units are missing their K&A factors in parentheses
                    """)
                
                # Show undefined factors if any
                if validation_results.get('undefined_factors'):
                    st.subheader("Undefined Factors")
                    for factor in validation_results.get('undefined_factors', []):
                        st.markdown(f"- {factor}")
                    
                    st.markdown("""
                    **How to fix:**
                    - Remove references to non-existent K&A factors from topics
                    - Or add these factors to the Knowledge/Ability lists
                    """)
        
        # Show fix results if any topics were fixed
        if fix_results and fix_results.get('fixed_count', 0) > 0:
            with st.expander("Knowledge and Ability Auto-Fix Results", expanded=True):
                st.success(f"✅ {fix_results.get('fixed_count', 0)} topics fixed with missing K&A references")
                
                # Show detailed fix information
                for i, fix in enumerate(fix_results.get('fixed_topics', []), 1):
                    st.markdown(f"**Fix {i}:**")
                    st.markdown(f"- Learning Unit: {fix.get('learning_unit')}")
                    st.markdown(f"- Original: {fix.get('original')}")
                    st.markdown(f"- Fixed: {fix.get('fixed')}")
                    st.markdown(f"- Added factors: {', '.join(fix.get('added_factors', []))}")
                    st.markdown("---")

if __name__ == "__main__":
    app()
