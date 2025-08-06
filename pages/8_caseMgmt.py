
"""
# Add parent directory to path to allow absolute imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


Case Management Page

This module provides a Streamlit interface for managing 
cases including:
new birth, new death, 
adopt within family, adopt outside family, 
divorce/seperation, new marriage/partnership, 
new step child/parent.
"""
from venv import logger
import streamlit as st
import db_utils as dbm
import funcUtils as fu
import context_utils as cu
from pathlib import Path
from dotenv import load_dotenv
import logging
import os

# --- Initialize system environment --- from here
script_path = Path(__file__).resolve()
script_dir = script_path.parent
env_path = script_dir / '.env'

# 載入 .env 文件
load_dotenv(env_path, override=True)

# --- Set Server logging levels ---
g_logging = os.getenv("LOGGING", "INFO").strip('\"\'').upper()  # 預設為 INFO，並移除可能的引號

# 創建日誌器
logger = logging.getLogger(__name__)

# 設置日誌格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

# 設置控制台處理器
console_handler = logging.StreamHandler()

# 根據環境變數設置日誌級別
if g_logging == "DEBUG":
    logger.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)
    logger.debug("Debug logging is enabled")
else:
    logger.setLevel(logging.INFO)
    console_handler.setLevel(logging.INFO)

console_handler.setFormatter(formatter)

# 移除所有現有的處理器，避免重複日誌
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# 添加處理器到日誌器
logger.addHandler(console_handler)

# 確保根日誌器不會干擾
logging.basicConfig(level=logging.WARNING)
logging.getLogger().setLevel(logging.WARNING)

def new_birth_page():
    """ New birth
    Display new birth page
    show a check box to find the bio-parents
    show a check box to add the new member to the family
    """
            
def new_death_page():
    """ New death
    Display new death page
    """
    pass

def adopt_within_family_page():
    """
    Display adopt within family page
    show a check box to find the adopted-parent(s)
    by member_id or name
    Once adopted-parent(s) is/are selected,show a check box 
    to find the member within the family by member_id or name
    Once the member is selected, add a relation 
    to the dbm.db_table['relations'] table with
    relation_type = 'child adopted within family'
    """
    if not st.session_state.get('adoptive_parents'):
        # Step 1: Find and select adoptive parent(s)
        parents = []
        child = None
    
        with st.form("adopted_parent_form"):
            st.markdown(f"### {UI_TEXTS['search']} {UI_TEXTS['adopted_parent']}")
            search_type = st.radio(
                UI_TEXTS['search_by'],
                [f"{UI_TEXTS['member']} {UI_TEXTS['id']}", f"{UI_TEXTS['member']} {UI_TEXTS['name']}",],
                horizontal=True,
                key="adopted_parent_search_type"
            )
            col11, col12 = st.columns([1, 10])
            with col11:
                parent_id1 = st.number_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['id']}",
                    min_value=0,
                    step=1,
                    key="adopted_parent_id1"
                )
                parent_id2 = st.number_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['id']}",
                    min_value=0,
                    step=1,
                    key="adopted_parent_id2"
                )
            with col12:
                parent_name1 = st.text_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                    value="",
                    key="adopted_parent_name1"
                )
                parent_name2 = st.text_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                    value="",
                    key="adopted_parent_name2"
                )
            search_clicked = st.form_submit_button(UI_TEXTS['search'])
            
            # Display search results if search_clicked:
            if search_clicked:
                if search_type == f"{UI_TEXTS['member']} {UI_TEXTS['id']}":
                    if parent_id1:
                        try:
                            parent = dbm.get_member(int(parent_id1))
                            if parent:
                                parents.append(parent)
                                # save parents to session state
                                st.session_state.adoptive_parents = parents
                            else:
                                st.warning(UI_TEXTS['member_error']['member_not_found'])
                        except ValueError as e:
                            st.error(f"{UI_TEXTS['member_error']}: {str(e)}")
                    if parent_id2:
                        try:
                            parent = dbm.get_member(int(parent_id2))
                            if parent:
                                parents.append(parent)
                                # save parents to session state
                                st.session_state.adoptive_parents = parents
                            else:
                                st.warning(UI_TEXTS['member_error']['member_not_found'])
                        except ValueError as e:
                            st.error(f"{UI_TEXTS['member_error']}: {str(e)}")
                    else:
                        # only one parent selected
                        st.rerun()
                else:
                    # search by name
                    parent_name1 = parent_name1.strip()
                    parent_name2 = parent_name2.strip()
                    if parent_name1:
                        search_results1 = search_members(name=parent_name1)
                        if search_results1:
                            selected_parents = st.selectbox(
                                f"{UI_TEXTS['select']} {UI_TEXTS['adopted_parent']}",
                                [f"{m['id']} - {m.get('name', '')}" for m in search_results1],
                                key='adopted_parent_1'
                            )
                            parent_id1 = int(selected_parents.split(' - ')[0])
                            try:
                                parent = dbm.get_member(int(parent_id1))
                                if parent:
                                    parents.append(parent)
                                    # Save parents to session state
                                    st.session_state.adoptive_parents = parents
                                else:
                                    st.warning(UI_TEXTS['member_error']['member_not_found'])
                            except ValueError as e:
                                st.error(f"{UI_TEXTS['member_error']}: {str(e)}")
                    else:
                        # no members found
                        st.warning(UI_TEXTS['member_error']['no_members_found'])
                    if parent_name2:
                        search_results2 = search_members(name=parent_name2)
                        if search_results2:
                            selected_parents = st.selectbox(
                                f"{UI_TEXTS['select']} {UI_TEXTS['adopted_parent']}",
                                [f"{m['id']} - {m.get('name', '')}" for m in search_results2],
                                key='adopted_parent_2'
                            )
                            parent_id2 = int(selected_parents.split(' - ')[0])
                            try:
                                parent = dbm.get_member(int(parent_id2))
                                if parent:
                                    parents.append(parent)
                                    # Save parents to session state
                                    st.session_state.adoptive_parents = parents
                                    st.rerun()
                                else:
                                    st.warning(UI_TEXTS['member_error']['member_not_found'])
                            except ValueError as e:
                                st.error(f"{UI_TEXTS['member_error']}: {str(e)}")
                        else:
                            # no members found
                            st.warning(UI_TEXTS['member_error']['no_members_found'])
                    else:
                        # only one parent selected
                        st.rerun()
 
    # If parents are selected, search adopted child
    if st.session_state.get('adoptive_parents') and not st.session_state.get('adoptive_child'):
        # Clear any existing form state to ensure the form renders
        if 'adopted_child_form' in st.session_state:
            del st.session_state['adopted_child_form']
            
        with st.form("adopted_child_form"):
            st.markdown(f"### {UI_TEXTS['search']} {UI_TEXTS['adopted_child']}")
            
            # Add a back button to modify parents
            if st.form_submit_button(f"← {UI_TEXTS['back']}"):
                del st.session_state.adoptive_parents
                st.rerun()
                
            child_search_type = st.radio(
                f"{UI_TEXTS['search_by']} {UI_TEXTS['child']}",
                [f"{UI_TEXTS['member']} {UI_TEXTS['id']}", f"{UI_TEXTS['member']} {UI_TEXTS['name']}"],
                key='child_search_type',
                horizontal=True,
                index=0 if 'child_search_type' not in st.session_state else None
            )
            col21, col22 = st.columns([1, 10])
            with col21:
                child_id = st.number_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['id']}",
                    min_value=1,
                    step=1,
                    key="child_id"
                )
            with col22:
                child_name = st.text_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                    key="child_name"
                )
        
            search_clicked = st.form_submit_button(UI_TEXTS['search'])
            # Display search results
            if search_clicked:
                if child_search_type == f"{UI_TEXTS['member']} {UI_TEXTS['id']}":
                    if child_id:
                        try:
                            child = dbm.get_member(int(child_id))
                            if child:
                                # Save child to session state
                                st.session_state.adoptive_child = child
                                st.rerun()
                            else:
                                st.warning(UI_TEXTS['member_error']['member_not_found'])
                        except ValueError as e:
                            st.error(f"{UI_TEXTS['member_error']}: {str(e)}")
                elif child_search_type == f"{UI_TEXTS['member']} {UI_TEXTS['name']}":
                    child_name = child_name.strip()
                    if child_name:
                        search_results = search_members(child_name)
                        if search_results:
                            selected_child = st.selectbox(
                                f"{UI_TEXTS['select']} {UI_TEXTS['child']}",
                                [f"{m['id']} - {m.get('name', '')}" for m in search_results],
                                key='adopted_child'
                            )
                            if selected_child:
                                child_id = int(selected_child.split(' - ')[0])
                                child = next((m for m in search_results if m['id'] == child_id), None)
                                if child:
                                    # Save child to session state
                                    st.session_state.adoptive_child = child
                                    st.rerun()
                                else:
                                    st.warning(UI_TEXTS['member_error']['member_not_found'])
                            else:
                                st.warning(f"{UI_TEXTS['adopted_child']} {UI_TEXTS['required']}")
                        else:
                            st.warning(UI_TEXTS['member_error']['no_members_found'])
                    else:
                        st.warning(f"{UI_TEXTS['adopted_child']} {UI_TEXTS['required']}")
                else:
                    st.warning(f"{UI_TEXTS['adopted_child']} {UI_TEXTS['required']}")
            else:
                st.warning(f"{UI_TEXTS['adopted_child']} {UI_TEXTS['required']}")
    
    # If parents/child selected, show details and confirmation
    if st.session_state.get('adoptive_parents') and st.session_state.get('adoptive_child'):
        st.markdown(f"### {UI_TEXTS['adopt_within_family']} {UI_TEXTS['details']}")
        st.write(f"**{UI_TEXTS['adopted_parent']}:**")
        for parent in st.session_state.adoptive_parents:
            st.write(f"- {parent.get('name', '')} (ID: {parent['id']})")
        st.write(f"**{UI_TEXTS['adopted_child']}:**")
        st.write(f"- {st.session_state.get('adoptive_child').get('name', '')} (ID: {st.session_state.get('adoptive_child')['id']})")
        
        join_date = st.text_input(
            f"{UI_TEXTS['enter']} {UI_TEXTS['relation_join_date']}",
            help=UI_TEXTS['date_placeholder'],
            key='join_date_adopt_within_family'
        )
        
        if st.button(UI_TEXTS['confirm']) and join_date:
            try:
                with st.spinner(UI_TEXTS['in_progress']):
                    # Create adoption relationships for each parent
                    for parent in st.session_state.adoptive_parents:
                        relation_data = {
                            'member_id': parent['id'],
                            'partner_id': st.session_state.adoptive_child['id'],
                            'relation': 'child adopted within family',
                            'join_date': join_date
                        }
                        relation_id = dbm.add_or_update_relation(
                            relation_data,
                            update=True)
                        if relation_id:
                            st.success(UI_TEXTS['relation_created'])
                        else:
                            st.error(f"{UI_TEXTS['relation_not_created']}: {relation_data}")
            except Exception as e:
                message = f"{UI_TEXTS['relation_error']}: {str(e)}"
                st.error(message)
                logger.error(message)
    else:
        st.warning(f"{UI_TEXTS['adopted_parent']} and {UI_TEXTS['adopted_child']} {UI_TEXTS['required']}")
    
def adopt_outside_family_page():
    """ Adopt outside family
    Display adopt outside family page
    """
    adoption_type = st.radio(
                UI_TEXTS['adopted_as'],
                [f"{UI_TEXTS['adopted_parent']}", f"{UI_TEXTS['adopted_child']}",],
                horizontal=True,
                key="adoption_type"
            )
    if adoption_type == UI_TEXTS['adopted_parent']:
        st.markdown(f"#### ✅ {UI_TEXTS['create']} {UI_TEXTS['new_member']} {UI_TEXTS['to_join_as']} {UI_TEXTS['adopted_parent']} ({UI_TEXTS['max']}:2)*")
    if adoption_type == UI_TEXTS['adopted_child']:
        st.markdown(f"#### ✅ {UI_TEXTS['create']} {UI_TEXTS['new_member']} {UI_TEXTS['to_join_as']} {UI_TEXTS['adopted_child']} ({UI_TEXTS['max']}:1)*")
    
    # Display the add_member.png image for instructions
    st.markdown(f"#### {UI_TEXTS['add_member_instructions']}")
    st.image("add_member.png", 
             caption=f"{UI_TEXTS['add_member_instructions']}", 
             width=600)  # Using width to control the image size
    
    st.markdown(f"#### Finally, select '{UI_TEXTS['adopt_within_family']}' tab to finish the adoption process")
    
def divorce_seperation_page():
    """
    Display divorce/seperation page
    """
    opt_list = [UI_TEXTS['divorce'], UI_TEXTS['seperation']]
    st.markdown(UI_TEXTS['search_relations_with'])
    col1, col2 = st.columns([1, 10])
    with col1:
        member_id = st.number_input(
            f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['id']}*",
            min_value=1,
            key="member_id")
    with col2:
        st.write("")
    
    if st.button(UI_TEXTS['search']):
        relations = dbm.get_member_relations(member_id) 
        if relations:
            # show relations in a dataframe
            st.dataframe(relations)
            
            # Create a form for updating relationship status
            with st.form("update_relation_form"):
                type = st.radio(
                    UI_TEXTS['relation_type'], 
                    opt_list, 
                    index=0,
                    key="relation_type_radio"
                )
                
                col11, col12 = st.columns([1, 10])

                with col11:
                    spouse_id = st.number_input(
                        f"{UI_TEXTS['enter']} {UI_TEXTS['spouse']} {UI_TEXTS['id']}*",
                        min_value=1,
                        key="spouse_id"
                    )
                
                with col12:
                    end_date = st.text_input(
                        f"{UI_TEXTS['enter']} {UI_TEXTS['relation_end_date']}*",
                        placeholder=UI_TEXTS['date_placeholder'],
                        key="end_date"
                    )
                
                # Form submit button
                submitted = st.form_submit_button(UI_TEXTS['submit'])
                
                if submitted:
                    try:
                        updated_count = dbm.update_member_when_ended(
                            member1_id=member_id,
                            member2_id=spouse_id,
                            relation=f"spouse {type.lower()}",
                            end_date=end_date
                        )
                        if updated_count > 0:
                            message = f"✅ {UI_TEXTS['relation_updated']} {UI_TEXTS['count']}:{updated_count} {member_id}-{spouse_id}"
                            st.session_state.spouse_message = message
                            st.rerun()  # Rerun to show the message in the session state section
                        else:
                            message = f"❌ {UI_TEXTS['relation_error']} : {member_id}-{spouse_id}"
                            st.session_state.spouse_message = message
                            st.rerun()
                    except Exception as e:
                        message = f"❌ {UI_TEXTS['relation_error']} : {str(e)}"
                        st.session_state.spouse_message = message
                        st.rerun()
        else:
            st.warning(UI_TEXTS['relation_not_found'])

def new_marriage_partnership_page():
    """
    Display new marriage/partnership page
    search spouse by id or name
    when the search results are shown, 
    show a radio button to select the spouse
    show a submit button to submit the form
    
    when the form is submitted, 
    create a new member for the spouse if it doesn't exist
    in the dbm.db_table['members'] table
    add the relation to the dbm.db_table['relations'] table
    show a success message
    """
    
    # Search form
    with st.form("search_spouse_form"):
        st.markdown(f"{UI_TEXTS['search']} {UI_TEXTS['spouse']}/{UI_TEXTS['partner']}")
        search_type = st.radio(
            UI_TEXTS['search_by'],
            [f"{UI_TEXTS['member']} {UI_TEXTS['id']}", f"{UI_TEXTS['member']} {UI_TEXTS['name']}",],
            horizontal=True
        )
        col11, col12 = st.columns([1, 10])
        with col11:
            member_id = st.number_input(
                f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['id']}",
                min_value=1,
                step=1,
                key="spouse_search_id"
            )
        with col12:
            name = st.text_input(
                f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                key="spouse_search_name"
            )
        search_clicked = st.form_submit_button(UI_TEXTS['search'])

        # Display search results
        if search_clicked:
            st.session_state.search_results = []
            if search_type == "Member ID" and member_id:
                member = dbm.get_member(member_id)
                if member:
                    st.session_state.search_results = [member]
                else:
                    st.warning(UI_TEXTS['member_not_found'])
            elif search_type == "Name" and name.strip():
                # Search members by name (case insensitive)
                name = name.strip().lower()
                members = dbm.search_members(name=name)
                if members:
                    st.session_state.search_results = members
                else:
                    st.warning(f"{UI_TEXTS['member_not_found']}: {name}")
    
    # Display search results and relationship form
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.subheader(UI_TEXTS['search_results'])
        
        # Display results with radio buttons
        partner_options = {f"{m.get('id')} - {m.get('name', '')}": m for m in st.session_state.search_results}
        selected_partner_key = st.radio(
            f"{UI_TEXTS['select']} {UI_TEXTS['partner']}",
            options=list(partner_options.keys()),
            key="selected_partner"
        )
        
        # Get the selected partner
        selected_partner = partner_options[selected_partner_key]
        
        # Relationship form for new member
        with st.form("marriage_form"):
            
            # Get partner details
            st.write(f"### {UI_TEXTS['partner']} {UI_TEXTS['details']}")
            st.write(f"{UI_TEXTS['name']}: {selected_partner.get('name', 'N/A')}")
            st.write(f"{UI_TEXTS['gen_order']}: {selected_partner.get('gen_order', 'N/A')}")
            st.write(f"{UI_TEXTS['born']}: {selected_partner.get('born', 'N/A')}")
            
            # New Member details
            st.write(f"### {UI_TEXTS['new_member']} {UI_TEXTS['details']}")
            col21, col22 = st.columns(2)
            with col21:
                name = st.text_input(f"{UI_TEXTS['new_member']} {UI_TEXTS['name']}*")
                sex = st.selectbox(
                    UI_TEXTS['sex'],
                    [UI_TEXTS['sex_male'], UI_TEXTS['sex_female'], UI_TEXTS['sex_other']],
                    index=0,
                    key="add_member_sex_2"
                )
                born = st.text_input(
                    f"{UI_TEXTS['born']}*",
                    value="",
                    help=UI_TEXTS['date_placeholder'],
                    key="add_born_date_2"
                )
                family_id = st.number_input(
                    f"{UI_TEXTS['family']} {UI_TEXTS['id']}",
                    min_value=0,
                    step=1,
                    value=0,
                    key="add_member_family_id_2"
                )
                gen_order = st.number_input(
                    f"{UI_TEXTS['gen_order']}*",
                    min_value=0,
                    step=1,
                    value=None,
                key="add_member_gen_order_2"
                )
            with col22:
                alias = st.text_input(
                    UI_TEXTS['alias'], 
                    "", 
                    key="add_alias_2"
                )
            
                email = st.text_input(
                    UI_TEXTS['email'], 
                    "", 
                    key="add_email_2"
                )
                password = st.text_input(
                    UI_TEXTS['password'], 
                    "", 
                    type="password", 
                    key="add_password_2"
                )
                confirm_password = st.text_input(
                    UI_TEXTS['password_confirmed'], 
                    "", 
                    type="password", 
                    key="confirm_password_2"
                )
                if password != confirm_password:
                    st.error(UI_TEXTS['password_error'])
                    return
                url = st.text_input(
                    UI_TEXTS['url'], 
                    "", 
                    key="add_url_2"
                )
        
            # Relationship details
            st.write(f"### {UI_TEXTS['relation']} {UI_TEXTS['details']}")
            join_date = st.text_input(
                f"{UI_TEXTS['relation_join_date']}*",
                value="",
                help=UI_TEXTS['date_placeholder'],
                key="add_join_date_2"
            )
            relationship_type = st.selectbox(
                f"{UI_TEXTS['relation_type']}*",
                [UI_TEXTS['marriage'], UI_TEXTS['domestic_partnership'], UI_TEXTS['civil_union']],
                key="relation_type"
            )
            
            submit_button = st.form_submit_button(f"{UI_TEXTS['create']} {UI_TEXTS['relation']}")
            
            if submit_button:
                # Validate required fields
                if not all([name, gen_order, born, join_date]):
                    st.error("Please fill in all required fields (marked with *)")
                else:
                    try:
                        # Create member record
                        member_data = {
                            'name': name,
                            'sex': sex,
                            'born': born,
                            'email': email,
                            'family_id': selected_member.get('family_id', 0)
                        }
                        member_id = dbm.add_or_update_member(
                            member_data,
                            update_end_date=False)
                        if not member_id:
                            st.error(f"{UI_TEXTS['member_error']} : {member_data}")
                        
                        # Create relationship record
                        relationship_data = {
                            'member_id': member_id,
                            'partner_id': selected_partner['id'],
                            'relation': 'spouse ' + relationship_type,
                            'join_date': join_date,
                            'end_date': '0000-00-00'
                        }
                        
                        # Add the relationship record
                        relation_id = dbm.add_or_update_relation(
                            relationship_data,
                            update_end_date=True)
                        
                        if relation_id:
                            st.success(f"✅ {UI_TEXTS['relation_created']}: {relationship_type} between {selected_member.get('name')} and {partner_name}")
                            # Clear search results after successful submission
                            if 'search_results' in st.session_state:
                                del st.session_state.search_results
                            st.rerun()
                        else:
                            st.error(f"❌ {UI_TEXTS['relation_error']}: {UI_TEXTS['relation_not_created']}")
                            
                    except Exception as e:
                        st.error(f"❌ {UI_TEXTS['relation_error']}: {str(e)}")
            
def step_child_parent_page():
    pass

def sidebar() -> None:
    """Sidebar application entry point."""
    # Sidebar --- from here
    with st.sidebar:
        if st.session_state.user_state == dbm.User_State['p_admin']:
            # Show default navigation for padmin users
            if 'user_email' in st.session_state and st.session_state.user_email:
                st.markdown(
                    f"<div style='background-color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; margin: 1rem 0;'>"
                    f"<p style='color: white; margin: 0; font-weight: bold; text-align: center;'>{st.session_state.user_email}</p>"
                    "</div>",
                    unsafe_allow_html=True)
                cu.update_context({
                    'email_user': st.session_state.user_email
                })
                
                # Add logout button at the bottom for admin
                if st.button(UI_TEXTS['logout'], type="primary", use_container_width=True, key="fam_mgmt_admin_logout"):
                    st.session_state.authenticated = False
                    st.session_state.user_email = None
                    st.rerun()
        else:
            # For non-admin users
            # Hide the default navigation for non-padmin users
            st.markdown("""
            <style>
                [data-testid="stSidebarNav"] {
                    display: none !important;
                }
            </style>""", unsafe_allow_html=True)
            
            if 'user_email' in st.session_state and st.session_state.user_email:
                st.markdown(
                    f"<div style='background-color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;'>"
                    f"<p style='color: white; margin: 0; font-weight: bold; text-align: center;'>{st.session_state.user_email}</p>"
                    "</div>",
                    unsafe_allow_html=True)
                cu.update_context({
                    'email_user': st.session_state.user_email
                })
            
            st.subheader(UI_TEXTS['navigation'])
            st.page_link("ftpe_ui.py", label="Home", icon="🏠")
            st.page_link("pages/3_csv_editor.py", label="CSV Editor", icon="🔧")
            st.page_link("pages/4_json_editor.py", label="JSON Editor", icon="🪛")
            st.page_link("pages/5_ftpe.py", label="FamilyTreePE", icon="📊")
            st.page_link("pages/6_show_3G.py", label="Show 3 Generations", icon="👥")
            st.page_link("pages/7_show_related.py", label="Show Related", icon="👨‍👩‍👧‍👦")
            if st.session_state.user_state == dbm.User_State['f_admin']:
                st.page_link("pages/9_birthday.py", label="Birthday", icon="🎂")
                st.page_link("pages/2_famMgmt.py", label="Family Management", icon="🌲")
             
            # Add logout button at the bottom for non-admin users
            if st.button(UI_TEXTS['logout'], type="primary", use_container_width=True, key="fam_mgmt_user_logout"):
                st.session_state.authenticated = False
                st.session_state.user_email = None
                st.rerun()

def main() -> None:
    """Main application entry point."""
    st.title(f"📋 {UI_TEXTS['case_mgmt']}")
    
    # Main tab groups
    case_tabs = st.tabs([
        "New Birth", 
        "New Death", 
        "Adopt within family",
        "Adopt outside family",
        "Divorce/Seperation",
        "New Marriage/Partnership",
        "Step Child/Parent"
        ])
    
    with case_tabs[0]:  # New Birth
        st.subheader(f"{UI_TEXTS['new_birth']} 👶")
        new_birth_page()
        
    with case_tabs[1]:  # New Death
        st.subheader(f"{UI_TEXTS['new_death']} ✝️")       
        new_death_page()
        
    with case_tabs[2]:  # Adopt within family
        st.subheader(f"{UI_TEXTS['adopt_within_family']} ☂️")
        # initialize session state
        if 'adoptive_parents' not in st.session_state:
            st.session_state.adoptive_parents = []
        if 'adoptive_child' not in st.session_state:
            st.session_state.adoptive_child = None
        
        adopt_within_family_page()
        
    with case_tabs[3]:  # Adopt outside family
        st.subheader(f"{UI_TEXTS['adopt_outside_family']} 📚")
        adopt_outside_family_page()
        
    with case_tabs[4]:  # Divorce/Seperation
        st.subheader(f"{UI_TEXTS['divorce']} / {UI_TEXTS['seperation']} 💔")        
        if 'spouse_message' not in st.session_state:
            st.session_state.spouse_message = None
        divorce_seperation_page()
        
    with case_tabs[5]:  # New Marriage/Partnership
        st.subheader(f"{UI_TEXTS['new_marriage_partnership']} ❤️")        
        new_marriage_partnership_page()
        
    with case_tabs[6]:  # Step Child/Parent
        st.subheader(f"{UI_TEXTS['new_step_child_parent']} 👨‍👩‍👧")
        step_child_parent_page()
    
    # Display session state if any and clear session state
    
    if st.session_state.adoptive_child:
        st.info(f"Adoptive child: {st.session_state.adoptive_child}")
        del st.session_state.adoptive_child
    
    if st.session_state.adoptive_parents:
        st.info(f"Adoptive parents: {st.session_state.adoptive_parents}")
        del st.session_state.adoptive_parents
    
    if 'spouse_message' in st.session_state and st.session_state.spouse_message:
        st.info(st.session_state.spouse_message)
        # Don't delete immediately, let it persist for one more render
        st.session_state._keep_spouse_message = False
    elif hasattr(st.session_state, '_keep_spouse_message') and not st.session_state._keep_spouse_message:
        # Clean up on the next render if we're not keeping the message
        if 'spouse_message' in st.session_state:
            del st.session_state.spouse_message
        del st.session_state._keep_spouse_message

# Initialize session state and app/ui context
cu.init_session_state()
lang = st.session_state.app_context.get('language')
UI_TEXTS = st.session_state.ui_context[lang]

if __name__ == "__main__":
    # Check authentication
    if not st.session_state.get('authenticated', False):
        st.switch_page("ftpe_ui.py")
    else:
        sidebar()
        main()