# app.py
import streamlit as st
from streamlit_option_menu import option_menu
import Assessment.assessment_generation as assessment_generation
import Courseware.courseware_generation  as courseware_generation
import Brochure.brochure_generation as brochure_generation
import AnnexAssessment.annex_assessment as annex_assessment
import CourseProposal.app as course_proposal_app
import SupDocs.sup_doc as sup_doc
import base64

# import CourseProposal_excel.app as course_proposal_excel_app

st.set_page_config(layout="wide")

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Convert the local image to a base64 string
image_base64 = get_base64_image("utils/logo/tertiary_infotech_pte_ltd.jpg")

with st.sidebar:
    st.markdown(
        f"""
        <div style="display: flex; justify-content: left;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="flex-shrink: 0;">
                    <img src="data:image/jpeg;base64,{image_base64}" width="70">
                </div>
                <div style="height:70px; display: flex; align-items: left; justify-content: flex-start;">
                    <h1 style="margin: 0; font-size: 1.8rem;">Tertiary Infotech</h1>
                </div>
            </div>
        </div>
        <br/>
        """,
        unsafe_allow_html=True
    )
    selected = option_menu(
        "",  # Title of the sidebar
        ["Generate CP", "Generate AP/FG/LG/LP", "Generate Assessment", "Generate Brochure","Add Assessment to AP", "Check Documents"],  # Options
        icons=["filetype-doc", "file-earmark-richtext", "clipboard-check", "files-alt", "folder-symlink"],  # Icon names
        menu_icon="boxes",  # Icon for the sidebar title
        default_index=0,  # Default selected item
    )

# Display the selected app
if selected == "Generate CP":
    course_proposal_app.app()  # Display CP Generation app

elif selected == "Generate AP/FG/LG/LP":
    courseware_generation.app()  # Display Courseware Generation app

elif selected == "Generate Assessment":
    assessment_generation.app()
    # Add Assessment Generation-specific functionality here

elif selected == "Check Documents":
    sup_doc.app()

elif selected == "Generate Brochure":
    brochure_generation.app() # Display Brochure Generation app
    # Add Assessment Generation-specific functionality here

elif selected == "Add Assessment to AP":
    annex_assessment.app()  # Display Annex Assessment app