# app.py
import streamlit as st
from streamlit_option_menu import option_menu
import cp_generation as cp_generation
import Courseware.courseware_generation as courseware_generation

# Sidebar navigation with streamlit-option-menu
with st.sidebar:
    selected = option_menu(
        "Tertiary Infotech",  # Title of the sidebar
        ["Generate CP", "Generate Courseware", "Generate Assessment", "Generate Slides"],  # Options
        icons=["file-earmark-text", "file-earmark-richtext", "clipboard-check", "file-ppt"],  # Icon names
        menu_icon="boxes",  # Icon for the sidebar title
        default_index=0,  # Default selected item
    )

# Display the selected app
if selected == "Generate CP":
    cp_generation.app()  # Display CP Generation app

elif selected == "Generate Courseware":
    courseware_generation.app()  # Display Courseware Generation app

elif selected == "Generate Assessment":
    st.title("Generate Assessment")
    st.write("This section allows you to create assessments.")
    # Add Assessment Generation-specific functionality here

elif selected == "Generate Slides":
    st.title("Generate Slides")
    st.write("This section allows you to create presentation slides.")
    # Add Slides Generation-specific functionality here
