# app.py
import streamlit as st
from streamlit_option_menu import option_menu
from generate_ap_fg_lg_lp.utils.organizations import get_organizations, get_default_organization
import base64

# Lazy loading functions for better performance
def lazy_import_assessment():
    import generate_assessment.assessment_generation as assessment_generation
    return assessment_generation

def lazy_import_courseware():
    import generate_ap_fg_lg_lp.courseware_generation as courseware_generation
    return courseware_generation

def lazy_import_brochure_v2():
    import generate_brochure_v2.brochure_generation_v2 as brochure_generation_v2
    return brochure_generation_v2

def lazy_import_annex():
    import add_assessment_to_ap.annex_assessment as annex_assessment
    return annex_assessment

def lazy_import_course_proposal():
    import generate_cp.app as course_proposal_app
    return course_proposal_app

def lazy_import_docs():
    import check_documents.sup_doc as sup_doc
    return sup_doc

def lazy_import_settings():
    import settings.settings as settings
    return settings


st.set_page_config(layout="wide")

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        # Fallback to default logo if file not found
        with open("common/logo/tertiary_infotech_pte_ltd.jpg", "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()

# Initialize API system
try:
    from settings.api_manager import initialize_api_system
    initialize_api_system()
except ImportError:
    pass

# Get organizations and setup company selection
organizations = get_organizations()
default_org = get_default_organization()

with st.sidebar:
    # Company Selection
    if organizations:
        company_names = [org["name"] for org in organizations]

        # Validate stored index to prevent out-of-range errors
        stored_idx = st.session_state.get('selected_company_idx', 0)
        if stored_idx >= len(organizations):
            stored_idx = 0

        selected_company_idx = st.selectbox(
            "🏢 Select Company:",
            range(len(company_names)),
            format_func=lambda x: company_names[x],
            index=stored_idx
        )

        # Store selection in session state
        st.session_state['selected_company_idx'] = selected_company_idx
        selected_company = organizations[selected_company_idx]
    else:
        selected_company = default_org
        st.session_state['selected_company_idx'] = 0
    
    # Store selected company in session state for other modules
    st.session_state['selected_company'] = selected_company
    
    # Convert the company logo to a base64 string
    logo_path = selected_company.get("logo", "common/logo/tertiary_infotech_pte_ltd.jpg")
    image_base64 = get_base64_image(logo_path)
    
    # Display company info
    company_display_name = selected_company["name"].replace(" Pte Ltd", "").replace(" LLP", "")
    st.markdown(
        f"""
        <div style="display: flex; justify-content: left;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="flex-shrink: 0;">
                    <img src="data:image/jpeg;base64,{image_base64}" width="70">
                </div>
                <div style="height:70px; display: flex; align-items: left; justify-content: flex-start;">
                    <h1 style="margin: 0; font-size: 1.5rem;">{company_display_name}</h1>
                </div>
            </div>
        </div>
        <br/>
        """,
        unsafe_allow_html=True
    )
    selected = option_menu(
        "",  # Title of the sidebar
        ["Generate CP", "Generate AP/FG/LG/LP", "Generate Assessment", "Generate Brochure v2", "Add Assessment to AP", "Check Documents", "Settings"],  # Options
        icons=["filetype-doc", "file-earmark-richtext", "clipboard-check", "file-earmark-pdf", "folder-symlink", "search", "gear"],  # Icon names
        menu_icon="boxes",  # Icon for the sidebar title
        default_index=0,  # Default selected item
    )

# Display the selected app - using lazy loading for performance
if selected == "Generate CP":
    course_proposal_app = lazy_import_course_proposal()
    course_proposal_app.app()  # Display CP Generation app

elif selected == "Generate AP/FG/LG/LP":
    courseware_generation = lazy_import_courseware()
    courseware_generation.app()  # Display Courseware Generation app

elif selected == "Generate Assessment":
    assessment_generation = lazy_import_assessment()
    assessment_generation.app()

elif selected == "Check Documents":
    sup_doc = lazy_import_docs()
    sup_doc.app()

elif selected == "Generate Brochure v2":
    brochure_generation_v2 = lazy_import_brochure_v2()
    brochure_generation_v2.app()

elif selected == "Add Assessment to AP":
    annex_assessment = lazy_import_annex()
    annex_assessment.app()  # Display Annex Assessment app

elif selected == "Settings":
    settings = lazy_import_settings()
    settings.app()  # Display Settings app