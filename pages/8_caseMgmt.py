"""
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
import pandas as pd
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
    """
    Display new birth page
    - Search bio-parents by id or name vua a search form.
    - When the search results are displayed, show a check box to select the 
    bio-Dad and bio-Mom.
    - Show a submit button to add the new born member to the family.
    - Show a reset button to clear the session state and form.
    - Add the relations between the new born member and the bio-Dad and 
    bio-Mom with the join_date of the new born_date in the dbm.db_table['relations'] table.
    """
    # Initialize session state for search results and selected parents
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_parents' not in st.session_state:
        st.session_state.selected_parents = {'father': None, 'mother': None}
    logger.debug(f"{fu.get_function_name()}: {UI_TEXTS['new']} {UI_TEXTS['birth']} {UI_TEXTS['page']}")
    
    # Only show search form if either father or mother is not selected
    if st.session_state.selected_parents['father'] is None or st.session_state.selected_parents['mother'] is None:
        with st.form("search_parents_form"):
            st.markdown(f"### {UI_TEXTS['search']} {UI_TEXTS['member']}: {UI_TEXTS['parent']} {UI_TEXTS['details']}")
            
            # Show which parent we're searching for
            if st.session_state.selected_parents['father'] is None and st.session_state.selected_parents['mother'] is None:
                st.info(f"{UI_TEXTS['search_for']} {UI_TEXTS['dad']} {UI_TEXTS['and']} {UI_TEXTS['mom']}")
            elif st.session_state.selected_parents['father'] is None:
                st.info(f"{UI_TEXTS['search_for']} {UI_TEXTS['dad']}")
            else:
                st.info(f"{UI_TEXTS['search_for']} {UI_TEXTS['mom']}")
            
            search_type = st.radio(
                f"{UI_TEXTS['search_by']} {UI_TEXTS['member']} {UI_TEXTS['id']} {UI_TEXTS['or']} {UI_TEXTS['name']}*",
                [f"{UI_TEXTS['member']} {UI_TEXTS['id']}", f"{UI_TEXTS['member']} {UI_TEXTS['name']}",],
                horizontal=True,
                key="search_parent_type",
                index=0
            )
            col11, col12 = st.columns([1, 10])
            with col11:
                parent_id = st.number_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['id']}",
                    min_value=0,
                    step=1,
                key="search_parent_id"
                )
            
            with col12:
                parent_name = st.text_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                    value="",
                    key="search_parent_name"
                )

            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
            with btn_col2:
                reset_search = st.form_submit_button(f"{UI_TEXTS['reset']} {UI_TEXTS['search']}", type="secondary")
            with btn_col1:
                search_clicked = st.form_submit_button(UI_TEXTS['search'], type="primary")
            with btn_col3:
                refresh_clicked = st.form_submit_button(UI_TEXTS['refresh'], type="secondary")
            # Handle reset
            if reset_search:
                st.session_state.search_results = []
                st.session_state.selected_parents = {'father': None, 'mother': None}
                st.rerun()
            # Handle refresh
            if refresh_clicked:
                st.rerun()
            if search_clicked:
                # Search by id or name
                if search_type == f"{UI_TEXTS['member']} {UI_TEXTS['id']}":
                    # Search by id
                    try:
                        parent = dbm.get_member(int(parent_id))
                        if parent:
                            if parent.get('sex', '').lower() == 'male':
                                st.session_state.selected_parents['father'] = parent['id']
                            elif parent.get('sex', '').lower() == 'female':
                                st.session_state.selected_parents['mother'] = parent['id']
                            st.session_state.search_results.append(parent)
                        else:
                            st.warning(f"⚠️ {parent_id}: {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                    except ValueError as e:
                        st.warning(f"⚠️ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                elif search_type == f"{UI_TEXTS['member']} {UI_TEXTS['name']}":
                    # Search by name
                    parent_name = parent_name.strip().lower()
                    try:
                        if parent_name:
                            members = dbm.search_members(name=parent_name)
                            if members:
                                for member in members:
                                    st.session_state.search_results.append(member)
                            else:
                                st.warning(f"❌ {parent_name}: {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                    except ValueError as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
            
    # Display search results with checkboxes for father/mother selection
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.subheader(f"{UI_TEXTS['search']} {UI_TEXTS['results']}")
        
        # Display results with radio buttons for parent selection
        for idx, member in enumerate(st.session_state.search_results):
            col1, col2, col3 = st.columns([1, 1, 10])
            with col1:
                st.write(f"**{UI_TEXTS['id']}:** {member.get('id')}")
            with col2:
                st.write(f"**{UI_TEXTS['name']}:** {member.get('name', '?')}")
            with col3:
                # Create a container for inline radio button with label
                col_label, col_radio = st.columns([1, 10])
                with col_label:
                    st.write(f"{UI_TEXTS['select']} {UI_TEXTS['as']}:", unsafe_allow_html=True)
                with col_radio:
                    # Create a unique key for each radio button using both member ID and index
                    radio_key = f"new_birth_parent_role_{member['id']}_{idx}"
                    parent_role = st.radio(
                        "",  # Empty label since we're using our own
                        ["None", UI_TEXTS['dad'], UI_TEXTS['mom']],
                        key=radio_key,
                        horizontal=True,
                        index=0,
                        label_visibility="collapsed"
                    )
                
                # Update selected parents based on radio selection
                if parent_role == UI_TEXTS['dad']:
                    st.session_state.selected_parents['father'] = member['id']
                    # Clear any previous father selection
                    for m_idx, m in enumerate(st.session_state.search_results):
                        if m['id'] != member['id']:
                            m_radio_key = f"new_birth_parent_role_{m['id']}_{m_idx}"
                            if st.session_state.get(m_radio_key) == UI_TEXTS['dad']:
                                st.session_state[m_radio_key] = "None"
                elif parent_role == UI_TEXTS['mom']:
                    st.session_state.selected_parents['mother'] = member['id']
                    # Clear any previous mother selection
                    for m_idx, m in enumerate(st.session_state.search_results):
                        if m['id'] != member['id']:
                            m_radio_key = f"new_birth_parent_role_{m['id']}_{m_idx}"
                            if st.session_state.get(m_radio_key) == UI_TEXTS['mom']:
                                st.session_state[m_radio_key] = "None"
                else:
                    # If "None" is selected, clear this member from selected_parents if they were selected
                    if st.session_state.selected_parents.get('father') == member['id']:
                        st.session_state.selected_parents['father'] = None
                    if st.session_state.selected_parents.get('mother') == member['id']:
                        st.session_state.selected_parents['mother'] = None
    # Show new birth form if either father or mother is selected
    if st.session_state.selected_parents.get('father') or st.session_state.selected_parents.get('mother'):
        # New member form
        with st.form("new_birth_form"):
            st.subheader(f"### {UI_TEXTS['new']} {UI_TEXTS['member']}: {UI_TEXTS['child']} {UI_TEXTS['details']}")
            
            # Selected parents info
            father = dbm.get_member(st.session_state.selected_parents.get('father', 0)) if st.session_state.selected_parents.get('father') else None
            mother = dbm.get_member(st.session_state.selected_parents.get('mother', 0)) if st.session_state.selected_parents.get('mother') else None
            
            if father:
                st.write(f"**{UI_TEXTS['dad']}:** {father.get('name', '?')} (ID: {father['id']} {UI_TEXTS['born']}: {father['born']} {UI_TEXTS['gen_order']}: {father['gen_order']})")
            if mother:
                st.write(f"**{UI_TEXTS['mom']}:** {mother.get('name', '?')} (ID: {mother['id']} {UI_TEXTS['born']}: {mother['born']} {UI_TEXTS['gen_order']}: {mother['gen_order']})")
            if not father and not mother:
                st.warning(f"⚠️ {UI_TEXTS['select']} {UI_TEXTS['at_least_one']} {UI_TEXTS['dad']} {UI_TEXTS['or']} {UI_TEXTS['mom']} {UI_TEXTS['from']} {UI_TEXTS['search']} {UI_TEXTS['form']}.")
            
            # New member details
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(f"{UI_TEXTS['name']}*")
                sex = st.selectbox(
                        UI_TEXTS['sex'],
                        [UI_TEXTS['sex_male'], UI_TEXTS['sex_female'], UI_TEXTS['sex_other']],
                        index=0,
                        key="add_new_birth_child_sex_2"
                    )
                born = st.text_input(
                    f"{UI_TEXTS['born']}*",
                    placeholder=UI_TEXTS['date_placeholder'],
                    key="add_new_birth_child_born_2"
                )
                family_id = father.get('family_id', 0) if father else mother.get('family_id', 0) if mother else 0
                if family_id == 0:
                    st.error(f"❌ {UI_TEXTS['unauthorized']} {UI_TEXTS['add']} {UI_TEXTS['member']} {UI_TEXTS['page']}")
                    st.stop()
                st.write(f"**{UI_TEXTS['family']} {UI_TEXTS['id']}:**")
                st.write(family_id)
                
                # Auto-calculate generation if parents exist
                parent_gen = None
                if father and father.get('gen_order'):
                    parent_gen = father['gen_order']
                elif mother and mother.get('gen_order'):
                    parent_gen = mother['gen_order']
                    
                gen_order = st.number_input(
                    f"{UI_TEXTS['gen_order']}*",
                    min_value=1,
                    step=1,
                    value=parent_gen + 1 if parent_gen is not None else 1,
                    key="add_new_birth_child_gen_order_2"
                )
            
            with col2:
                alias = st.text_input(
                        f"{UI_TEXTS['alias']}",
                        key="add_new_birth_child_alias_2"
                    )
                email = st.text_input(f"{UI_TEXTS['email']}", 
                                    placeholder=UI_TEXTS['email'],
                                    key="add_new_birth_child_email_2")
                password = st.text_input(
                        f"{UI_TEXTS['password']}",
                        type="password",
                        placeholder=UI_TEXTS['password'],
                        key="add_new_birth_child_password_2"
                    )
                confirm_password = st.text_input(
                        f"{UI_TEXTS['password_confirmed']}",
                        type="password",
                        placeholder=UI_TEXTS['password_confirmed'],
                        key="add_new_birth_child_confirm_password_2"
                    )
                if password != confirm_password:
                    st.error(f"❌ {UI_TEXTS['password_error']}")
                    return
                url = st.text_input(
                    f"{UI_TEXTS['url']}",
                    placeholder=UI_TEXTS['url'],
                    key="add_new_birth_child_url_2"
                )
            
            # Form actions
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
            with col_btn1:
                submit_clicked = st.form_submit_button(
                    f"{UI_TEXTS['create']} {UI_TEXTS['member']}",
                    type="primary"
                )
            with col_btn2:
                reset_clicked = st.form_submit_button(UI_TEXTS['reset'], type="secondary")
            with col_btn3:
                refresh_clicked = st.form_submit_button(UI_TEXTS['refresh'], type="secondary")
            # Handle reset
            if reset_clicked:
                st.session_state.search_results = []
                st.session_state.selected_parents = {'father': None, 'mother': None}
                st.rerun()
            # Handle refresh
            if refresh_clicked:
                st.rerun()
            # Handle form submission
            if submit_clicked:
                # Validate required fields
                if not all([name, born, gen_order]):
                    st.error(f"❌ {UI_TEXTS['required']} fields are marked with *")
                elif not father and not mother:
                    st.error(f"❌ Please select at least one {UI_TEXTS['dad']} {UI_TEXTS['or']} {UI_TEXTS['mom']}.")
                else:
                    try:
                        # Create new member
                        new_member_data = {
                            'name': name,
                            'sex': sex,
                            'born': born,
                            'email': email,
                            'gen_order': gen_order,
                            'alias': alias,
                            'dad_id': father['id'] if father else 0,
                            'mom_id': mother['id'] if mother else 0,
                            'password': password,
                            'url': url,
                            'family_id': family_id
                        }
                        
                        new_member_id = dbm.add_or_update_member(new_member_data, update=False)
                        
                        if new_member_id:
                            # Add parent-child relationships
                            success_count = 0
                            
                            # Add father relationship if selected
                            if father:
                                relation_data = {
                                    'member_id': new_member_id,
                                    'partner_id': father['id'],
                                    'relation': 'parent',  # This is from parent's perspective
                                    'join_date': born
                                }
                                if dbm.add_or_update_relation(relation_data, update=True):
                                    success_count += 1
                            
                            # Add mother relationship if selected
                            if mother:
                                relation_data = {
                                    'member_id': new_member_id,
                                    'partner_id': mother['id'],
                                    'relation': 'parent',  # This is from parent's perspective
                                    'join_date': born
                                }
                                if dbm.add_or_update_relation(relation_data, update=True):
                                    success_count += 1
                            
                            if success_count > 0:
                                st.success(f"✅ {UI_TEXTS['member_created']} (ID: {new_member_id}) with {success_count} {UI_TEXTS['relation']}(s)")
                                # Clear form and search results
                                st.session_state.search_results = []
                                st.session_state.selected_parents = {'father': None, 'mother': None}
                            else:
                                st.error(f"❌ {UI_TEXTS['member_created']} but failed to add {UI_TEXTS['relation']}s")
                        else:
                            st.error(f"❌ {UI_TEXTS['member_error']}: {UI_TEXTS['member_not_created']}")
                            
                    except Exception as e:
                        st.error(f"❌ {UI_TEXTS['member_error']}: {str(e)}")
                # Check optional user email and password if given for
                # subscription, create an user in the dbm.db_table['users'] table
                if email and password:
                    try:
                        user_data = {
                            'is_admin': User_State['f_member'],
                            'is_active': Subscriber_State['active'],
                            'family_id': family_id,
                            'member_id': member_id
                        }
                        result, error_msg = dbm.add_or_update_user(
                            email,
                            password,
                            user_data=user_data,
                            update=False)
                        if result:
                            st.success(f"✅ {UI_TEXTS['user_created']}: {email}")
                        else:
                            st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']} : {error_msg}")
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']}: {str(e)}")
            
def new_death_page():
    """
    Display new death page
    - Search the member by id or name via a search form.
    - When the search results are displayed, show a check box to select the 
    member.
    - Show a submit button to update the die_date of the member in the 
    dbm.db_table['members'] table.
    - Show a reset button to clear the session state and form.
    - Update the end_dates of all the relations involved in the member 
    with the die_date in the dbm.db_table['relations'] table 
    if not yet ended or later than die_date.
    
    Return:
    - None
    """
    logger.debug(f"{fu.get_function_name()}: {UI_TEXTS['new']} {UI_TEXTS['death']} {UI_TEXTS['page']}")
    
    # Search form
    with st.form("search_member_to_end_form"):
        st.markdown(f"### {UI_TEXTS['search']} {UI_TEXTS['deceased']} {UI_TEXTS['member']}")
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
                key="member_to_end_id"
            )
            search_clicked = st.form_submit_button(UI_TEXTS['search'], type="primary")

        with col12:
            name = st.text_input(
                f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                key="member_to_end_name"
            )
            reset_clicked = st.form_submit_button(UI_TEXTS['reset'], type="secondary")
        
        # Handle reset
        if reset_clicked:
            st.session_state.search_results = []
            st.rerun()
        # Display search results
        if search_clicked:
            st.session_state.search_results = []
            if search_type == f"{UI_TEXTS['member']} {UI_TEXTS['id']}" and member_id:
                try:
                    member = dbm.get_member(member_id)
                    if member:
                        st.session_state.search_results = [member]
                    else:
                        st.warning(f"⚠️ {member_id}: {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                except ValueError as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
            elif search_type == f"{UI_TEXTS['member']} {UI_TEXTS['name']}" and name.strip():
                # Search members by name (case insensitive)
                name = name.strip().lower()
                try:
                    if name:
                        members = dbm.search_members(name=name)
                        if members:
                            st.session_state.search_results = members
                        else:
                            st.warning(f"⚠️ {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}: {name}")
                except ValueError as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
    
    # Display search results and marriage_form
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.subheader(f"{UI_TEXTS['search']} {UI_TEXTS['results']}")
        
        # Display results with radio buttons
        member_options = {f"{m.get('id')} - {m.get('name', '?')} {UI_TEXTS['gen_order']}: {m.get('gen_order', '?')} ({m.get('born', '?')}~{m.get('died', '?')})": m for m in st.session_state.search_results}
        selected_member_key = st.radio(
            f"{UI_TEXTS['select']} {UI_TEXTS['member']}",
            options=list(member_options.keys()),
            key="selected_member_to_end"
        )
        
        # Get the selected member
        selected_member = member_options[selected_member_key]
        
        # Death form for selected member
        with st.form("death_form"):
            
            # Get partner details
            st.write(f"### {UI_TEXTS['member']} {UI_TEXTS['details']}")
            st.write(f"{UI_TEXTS['name']}: {selected_member.get('name', 'N/A')}")
            st.write(f"{UI_TEXTS['gen_order']}: {selected_member.get('gen_order', 'N/A')}")
            st.write(f"{UI_TEXTS['born']}: {selected_member.get('born', 'N/A')}")
            
            # Death date
            death_date = st.text_input(
                f"{UI_TEXTS['enter']} {UI_TEXTS['died']}",
                placeholder=UI_TEXTS['date_placeholder'],
                key="member_to_end_date"
            )
            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                submit_clicked = st.form_submit_button(UI_TEXTS['submit'], type="primary")
            with btn_col2:
                reset_clicked = st.form_submit_button(UI_TEXTS['reset'], type="secondary")
            
            # Handle reset
            if reset_clicked:
                st.session_state.search_results = []
                st.rerun()
            # Handle form submission
            if submit_clicked:
                try:
                    # Update member table and relations table
                    update = dbm.update_relations_when_died(
                        selected_member['id'],
                        death_date
                    )
                    if update[0]:
                        st.success(f"✅ {UI_TEXTS['member_updated']}")
                        
                        # Update user sucscripion if email is not empty
                        if selected_member['email']:
                            try:
                                success = dbm.remove_subscriber(selected_member['email'])
                                if success:
                                    st.success(f"✅ {UI_TEXTS['member_subscription_removed']}")
                                else:
                                    st.error(f"❌ {UI_TEXTS['member_error']} {UI_TEXTS['member_subscriber_not_found']}")
                            except Exception as e:
                                st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                        
                        # Clear form and search results
                        st.session_state.search_results = []
                    else:
                        st.error(f"❌ {fu.get_function_name()} {UI_TEXTS['member_error']} {UI_TEXTS['member_not_updated']}: {error_msg}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")

def new_adopted_child_page():
    """
    Display new adopted-child page
    - To search parents (father and/or mother) member by member_id or name.
    - Once parent member is selected, show adopted_child_confirm_form 
    to add new adopted-child as new member in the dbm.db_table['members'] 
    table and join_date to confirm the relationship in the 
    dbm.db_table['relations'] table with default relation type of 
    'child adopted from another family'.
    """
    # Initialize session state for search results and selected parents
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_parents' not in st.session_state:
        st.session_state.selected_parents = {'father': None, 'mother': None}
    logger.debug(f"{fu.get_function_name()}: {UI_TEXTS['new']} {UI_TEXTS['adopted_child']} {UI_TEXTS['page']}")
    
    # Only show search form if either father or mother is not selected
    if st.session_state.selected_parents['father'] is None or st.session_state.selected_parents['mother'] is None:
        with st.form("search_adopted_parent_form"):
            st.markdown(f"### {UI_TEXTS['search']} {UI_TEXTS['member']}: {UI_TEXTS['parent']} {UI_TEXTS['details']}")
    
            # Show which parent we're searching for
            if st.session_state.selected_parents['father'] is None and st.session_state.selected_parents['mother'] is None:
                st.info(f"{UI_TEXTS['search_for']} {UI_TEXTS['dad']} {UI_TEXTS['and']} {UI_TEXTS['mom']}")
            elif st.session_state.selected_parents['father'] is None:
                st.info(f"{UI_TEXTS['search_for']} {UI_TEXTS['dad']}")
            else:
                st.info(f"{UI_TEXTS['search_for']} {UI_TEXTS['mom']}")
            
            # Step 1: Find adopted parent by id or name
            search_type = st.radio(
                    f"{UI_TEXTS['search_by']} {UI_TEXTS['member']} {UI_TEXTS['id']} {UI_TEXTS['or']} {UI_TEXTS['name']}",
                [f"{UI_TEXTS['member']} {UI_TEXTS['id']}", f"{UI_TEXTS['member']} {UI_TEXTS['name']}",],
                horizontal=True,
                key="adopted_parent_search_type",
                index=0
            )
            col11, col12 = st.columns([1, 10])
            with col11:
                parent_id = st.number_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['id']}",
                    min_value=0,
                    step=1,
                key="adopted_parent_id"
            )
            
            with col12:
                parent_name = st.text_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                    value="",
                    key="adopted_parent_name"
                )
            
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
            with btn_col2:
                reset_search = st.form_submit_button(f"{UI_TEXTS['reset']} {UI_TEXTS['search']}", type="secondary")
            with btn_col1:
                search_clicked = st.form_submit_button(UI_TEXTS['search'], type="primary")
            with btn_col3:
                refresh_clicked = st.form_submit_button(UI_TEXTS['refresh'], type="secondary")
            
            # Handle reset
            if reset_search:
                st.session_state.search_results = []
                st.session_state.selected_parents = {'father': None, 'mother': None}
                st.rerun()
            
            # Handle refresh
            if refresh_clicked:
                st.rerun()
        
            if search_clicked:
                st.session_state.search_results = []
                if search_type == f"{UI_TEXTS['member']} {UI_TEXTS['id']}":
                    # Search by id
                    try:
                        parent = dbm.get_member(int(parent_id))
                        if parent:
                            if parent.get('sex', '').lower() == 'male':
                                st.session_state.selected_parents['father'] = parent['id']
                            elif parent.get('sex', '').lower() == 'female':
                                st.session_state.selected_parents['mother'] = parent['id']
                            st.session_state.search_results.append(parent)
                        else:
                            st.warning(f"⚠️ {parent_id}: {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                    except ValueError as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                elif search_type == f"{UI_TEXTS['member']} {UI_TEXTS['name']}":
                    # Search by name
                    parent_name = parent_name.strip().lower()
                    try:
                        if parent_name:
                            parents = dbm.search_members(name=parent_name)
                            if parents:
                                for parent in parents:
                                    st.session_state.search_results.append(parent)
                        else:
                            st.warning(f"⚠️ {parent_name}: {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                    except ValueError as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
            
    # Display search results with checkboxes for father/mother selection
    if st.session_state.search_results: 
        st.subheader(f"{UI_TEXTS['search']} {UI_TEXTS['results']}")
        
        # Display results with checkboxes for father/mother selection
        for idx, member in enumerate(st.session_state.search_results):
            col1, col2, col3 = st.columns([1, 1, 10])
            with col1:
                st.write(f"**{UI_TEXTS['id']}:** {member.get('id')}")
            with col2:
                st.write(f"**{UI_TEXTS['name']}:** {member.get('name', '?')}")
            with col3:
                # Create a container for inline radio button with label
                col_label, col_radio = st.columns([1, 10])
                with col_label:
                    st.write(f"{UI_TEXTS['select']} {UI_TEXTS['as']}:", unsafe_allow_html=True)
                with col_radio:
                    # Create a unique key for each radio button using both member ID and index
                    radio_key = f"adopted_parent_role_{member['id']}_{idx}"
                    parent_role = st.radio(
                        "",  # Empty label since we're using our own
                        ["None", UI_TEXTS['dad'], UI_TEXTS['mom']],
                        key=radio_key,
                        horizontal=True,
                        index=0,
                        label_visibility="collapsed"
                    )
                
                # Update selected parents based on radio selection
                if parent_role == UI_TEXTS['dad']:
                    st.session_state.selected_parents['father'] = member['id']
                    # Clear any previous father selection
                    for m_idx, m in enumerate(st.session_state.search_results):
                        if m['id'] != member['id']:
                            m_radio_key = f"adopted_parent_role_{m['id']}_{m_idx}"
                            if st.session_state.get(m_radio_key) == UI_TEXTS['dad']:
                                st.session_state[m_radio_key] = "None"
                elif parent_role == UI_TEXTS['mom']:
                    st.session_state.selected_parents['mother'] = member['id']
                    # Clear any previous mother selection
                    for m_idx, m in enumerate(st.session_state.search_results):
                        if m['id'] != member['id']:
                            m_radio_key = f"adopted_parent_role_{m['id']}_{m_idx}"
                            if st.session_state.get(m_radio_key) == UI_TEXTS['mom']:
                                st.session_state[m_radio_key] = "None"
                else:
                    # If "None" is selected, clear this member from selected_parents if they were selected
                    if st.session_state.selected_parents.get('father') == member['id']:
                        st.session_state.selected_parents['father'] = None
                    if st.session_state.selected_parents.get('mother') == member['id']:
                        st.session_state.selected_parents['mother'] = None
       
    # New member form
    with st.form("new_adopted_child_form"):
        st.subheader(f"{UI_TEXTS['new']} {UI_TEXTS['member']}: {UI_TEXTS['adopted_child']} {UI_TEXTS['details']}")
        # Selected parents info
        father = dbm.get_member(st.session_state.selected_parents.get('father', 0)) if st.session_state.selected_parents.get('father') else None
        mother = dbm.get_member(st.session_state.selected_parents.get('mother', 0)) if st.session_state.selected_parents.get('mother') else None
        
        if father:
            st.write(f"**{UI_TEXTS['dad']}:** {father.get('name', '?')} (ID: {father['id']} {UI_TEXTS['born']}: {father['born']} {UI_TEXTS['gen_order']}: {father['gen_order']})")
        if mother:
            st.write(f"**{UI_TEXTS['mom']}:** {mother.get('name', '?')} (ID: {mother['id']} {UI_TEXTS['born']}: {mother['born']} {UI_TEXTS['gen_order']}: {mother['gen_order']})")
        if not father and not mother:
            st.warning(f"⚠️ {UI_TEXTS['select']} {UI_TEXTS['at_least_one']} {UI_TEXTS['dad']} {UI_TEXTS['or']} {UI_TEXTS['mom']} {UI_TEXTS['from']} {UI_TEXTS['search']} {UI_TEXTS['member']} {UI_TEXTS['form']}.")
        
        col31, col32 = st.columns(2)
        with col31:
            name = st.text_input(
                f"{UI_TEXTS['new']} {UI_TEXTS['member']} {UI_TEXTS['name']}*",
                key="add_adopted_child_name_2"
            )
            sex = st.selectbox(
                UI_TEXTS['sex'],
                [UI_TEXTS['sex_male'], UI_TEXTS['sex_female'], UI_TEXTS['sex_other']],
                index=0,
                key="add_adopted_child_sex_2"
            )
            born = st.text_input(
                f"{UI_TEXTS['born']}*",
                placeholder=UI_TEXTS['date_placeholder'],
                key="add_adopted_child_born_2"
            )
            family_id = father.get('family_id', 0) if father else (mother.get('family_id', 0) if mother else 0)
            st.write(f"**{UI_TEXTS['family']} {UI_TEXTS['id']}:** {family_id}")

            # Auto-calculate generation if parents exist
            parent_gen = None
            if father and father.get('gen_order'):
                parent_gen = father['gen_order']
            elif mother and mother.get('gen_order'):
                parent_gen = mother['gen_order']
                
            gen_order = st.number_input(
                f"{UI_TEXTS['gen_order']}*",
                min_value=1,
                step=1,
                value=parent_gen + 1 if parent_gen is not None else 1,
                key="add_adopted_child_gen_order_2"
            )
        with col32:
            alias = st.text_input(
                f"{UI_TEXTS['alias']}",
                key="add_adopted_child_alias_2"
            )
            email = st.text_input(
                f"{UI_TEXTS['email']}",
                key="add_adopted_child_email_2"
            )
            password = st.text_input(
                f"{UI_TEXTS['password']}",
                type="password",
                key="add_adopted_child_password_2"
            )
            confirm_password = st.text_input(
                f"{UI_TEXTS['password_confirmed']}",
                type="password",
                key="add_adopted_child_confirm_password_2"
            )
            if password != confirm_password:
                st.error(f"❌ {UI_TEXTS['password_error']}")
                return
            url = st.text_input(
                f"{UI_TEXTS['url']}",
                key="add_adopted_child_url_2"
            )
            
        # Relation details
        st.write(f"### {UI_TEXTS['relation']} {UI_TEXTS['details']}")
        col31, col32 = st.columns([1, 1])
        with col31:
            join_date = st.text_input(
                f"{UI_TEXTS['enter']} {UI_TEXTS['relation_join_date']}*",
                placeholder=UI_TEXTS['date_placeholder'],
                key='join_date_adopt_within_family'
            )
        with col32:
            adopted_relations = [dbm.Relation_Type['child ai'], dbm.Relation_Type['child ao']]
            relation_type = st.selectbox(
                f"{UI_TEXTS['relation_type']}*",
                adopted_relations,
                help=UI_TEXTS['relation_type'],
                key="adopted_relation_type",
                index=0
            )
        
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
        with btn_col2:
            reset_clicked = st.form_submit_button(UI_TEXTS['reset'], type="secondary")
        with btn_col1:
            submit_clicked = st.form_submit_button(UI_TEXTS['submit'], type="primary")
        with btn_col3:
            refresh_clicked = st.form_submit_button(UI_TEXTS['refresh'], type="secondary")
        # Handle form submission
        if reset_clicked:
            st.session_state.search_results = []
            st.session_state.selected_parents = {'father': None, 'mother': None}
            st.rerun()
        if refresh_clicked:
            st.rerun()
        if submit_clicked:
            # Validate required fields
            if not all([name, born, gen_order, join_date, relation_type]):
                st.error(f"❌ {UI_TEXTS['relation']} {UI_TEXTS['field']} {UI_TEXTS['required']}")
            elif not selected_parents:
                st.error(f"❌ {UI_TEXTS['select']} {UI_TEXTS['at_least_one']} {UI_TEXTS['dad']} {UI_TEXTS['or']} {UI_TEXTS['mom']} {UI_TEXTS['from']} {UI_TEXTS['search']} {UI_TEXTS['member']} {UI_TEXTS['form']}.")
            else:
                try:
                    # Create member record
                    member_data = {
                        'name': name,
                        'sex': sex,
                        'born': born,
                        'email': email,
                        'family_id': family_id,
                        'gen_order': gen_order,
                        'alias': alias,
                        'url': url,
                        'password': password,
                        'confirm_password': confirm_password
                        }
                    member_id = dbm.add_or_update_member(
                        member_data,
                        update=False
                    )
                    if not member_id:
                        st.error(f"❌ {UI_TEXTS['member_error']} : {member_data}")
                        return
                        
                    # Create adoption relationships for each selected parent
                    success_count = 0
                    for parent in selected_parents:
                        relation_data = {
                            'member_id': member_id,
                            'partner_id': parent['id'],
                            'relation': relation_type,
                            'join_date': join_date,
                            'end_date': '0000-00-00'
                        }
                            
                        # Add the relationship record
                        relation_id = dbm.add_or_update_relation(
                            relation_data,
                            update=True
                        )
                        if relation_id:
                            success_count += 1
                            st.success(f"✅ {UI_TEXTS['relation_created']}: {relation_type} between {parent.get('name')} and {name}")
                        else:
                            st.error(f"❌ {UI_TEXTS['relation_error']}: {UI_TEXTS['relation_not_created']} for {parent.get('name')}")
                        
                        # Clear search results after successful submission if all relations were created
                        if success_count == len(selected_parents):
                            if 'search_results' in st.session_state:
                                del st.session_state.search_results
                    
                except Exception as e:
                    message = f"❌ {fu.get_function_name()}: {UI_TEXTS['relation_error']}: {str(e)}"
                    st.error(message)
            # Check optional user email and password if given for
            # subscription, create an user in the dbm.db_table['users'] table
            if email and password:
                try:
                    user_data = {
                        'is_admin': User_State['f_member'],
                        'is_active': Subscriber_State['active'],
                        'family_id': family_id,
                        'member_id': member_id
                    }
                    result, error_msg = dbm.add_or_update_user(
                        email,
                        password,
                        user_data=user_data,
                        update=False)
                    if result:
                        st.success(f"✅ {UI_TEXTS['user_created']}: {email}")
                    else:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']} : {error_msg}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']}: {str(e)}")
            
def new_adopted_parent_page():
    """
    Display new adopted-parent page
    - To search child member by member_id or name.
    - Once child member is selected, show adopted_parent_confirm_form
    to add new adopted-parent as new member in the dbm.db_table['members']
    table and join_date to confirm the relationship in the 
    dbm.db_table['relations'] table with default relation type of 
    'parent adopted from another family'.
    """
    logger.debug(f"{fu.get_function_name()}: {UI_TEXTS['new']} {UI_TEXTS['adopted_parent']} {UI_TEXTS['page']}")
    
    # Search form 
    with st.form("search_adopted_child_form"):
        st.markdown(f"### {UI_TEXTS['search']} {UI_TEXTS['member']}: {UI_TEXTS['child']} {UI_TEXTS['details']}")
        search_type = st.radio(
            f"{UI_TEXTS['search_by']} {UI_TEXTS['member']} {UI_TEXTS['id']} {UI_TEXTS['or']} {UI_TEXTS['name']}",
            [f"{UI_TEXTS['member']} {UI_TEXTS['id']}", f"{UI_TEXTS['member']} {UI_TEXTS['name']}",],
            horizontal=True,
            key="adopted_child_search_type",
            index=0
        )
        col11, col12 = st.columns([1, 10])
        with col11:
            child_id = st.number_input(
                f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['id']}",
                min_value=0,
                step=1,
                key="adopted_child_id"
            )
        with col12:
            child_name = st.text_input(
                f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                value="",
                key="adopted_child_name"
            )
        search_clicked = st.form_submit_button(UI_TEXTS['search'], type="primary")
        
        # Display search results
        if search_clicked:
            st.session_state.search_results = []
            if search_type == f"{UI_TEXTS['member']} {UI_TEXTS['id']}" and child_id:
                try:
                    child = dbm.get_member(child_id)
                    if child:
                        st.session_state.search_results = [child]
                    else:
                        st.warning(f"⚠️ {child_id}: {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                except ValueError as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
            elif search_type == f"{UI_TEXTS['member']} {UI_TEXTS['name']}" and child_name.strip():
                # Search members by name (case insensitive)
                name = child_name.strip().lower()
                try:
                    if name:
                        members = dbm.search_members(name=name)
                        if members:
                            st.session_state.search_results = members
                        else:
                            st.warning(f"⚠️ {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}: {name}")
                except ValueError as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
    
    # Display search results and adopted parent form
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.subheader(f"{UI_TEXTS['search']} {UI_TEXTS['results']}")
        
        # Display results with radio buttons
        child_options = {f"{m.get('id')} - {m.get('name', '?')} {UI_TEXTS['gen_order']}: {m.get('gen_order', '?')} ({m.get('born', '?')}~{m.get('died', '?')})": m for m in st.session_state.search_results}
        selected_child_key = st.radio(
            f"{UI_TEXTS['select']} {UI_TEXTS['child']}",
            options=list(child_options.keys()),
            key="selected_child_2"
        )
        
        # Get the selected child
        selected_child = child_options[selected_child_key]
        
        # Display adopted parent form for new member
        with st.form("adopted_parent_form"):
            
            # Get child details
            st.write(f"### {UI_TEXTS['child']} {UI_TEXTS['details']}")
            st.write(f"{UI_TEXTS['name']}: {selected_child.get('name', 'N/A')}")
            st.write(f"{UI_TEXTS['gen_order']}: {selected_child.get('gen_order', 'N/A')}")
            st.write(f"{UI_TEXTS['born']}: {selected_child.get('born', 'N/A')}")
            
            # New Member details
            st.write(f"### {UI_TEXTS['new']} {UI_TEXTS['member']}: {UI_TEXTS['adopted_parent']} {UI_TEXTS['details']}")
            col21, col22 = st.columns(2)
            with col21:
                name = st.text_input(f"{UI_TEXTS['new']} {UI_TEXTS['member']} {UI_TEXTS['name']}*")
                sex = st.selectbox(
                    UI_TEXTS['sex'],
                    [UI_TEXTS['sex_male'], UI_TEXTS['sex_female'], UI_TEXTS['sex_other']],
                    index=0,
                    key="add_adopted_parent_sex_2"
                )
                born = st.text_input(
                    f"{UI_TEXTS['born']}*",
                    value="",
                    help=UI_TEXTS['date_placeholder'],
                    key="add_adopted_parent_born_date_2"
                )
                family_id = st.number_input(
                    f"{UI_TEXTS['family']} {UI_TEXTS['id']}",
                    min_value=0,
                    step=1,
                    value=0,
                    key="add_adopted_parent_family_id_2"
                )
                gen_order = st.number_input(
                    f"{UI_TEXTS['gen_order']}*",
                    min_value=0,
                    step=1,
                    value=None,
                key="add_adopted_parent_gen_order_2"
                )
            with col22:
                alias = st.text_input(
                    UI_TEXTS['alias'], 
                    "", 
                    key="add_adopted_parent_alias_2"
                )
            
                email = st.text_input(
                    UI_TEXTS['email'], 
                    "", 
                    key="add_adopted_parent_email_2"
                )
                password = st.text_input(
                    UI_TEXTS['password'], 
                    "", 
                    type="password", 
                    key="add_adopted_parent_password_2"
                )
                confirm_password = st.text_input(
                    UI_TEXTS['password_confirmed'], 
                    "", 
                    type="password", 
                    key="add_adopted_parent_confirm_password_2"
                )
                if password != confirm_password:
                    st.error(f"❌ {UI_TEXTS['password_error']}")
                    return
                url = st.text_input(
                    UI_TEXTS['url'], 
                    "", 
                    key="add_adopted_parent_url_2"
                )
            
            # Relation details
            st.write(f"### {UI_TEXTS['relation']} {UI_TEXTS['details']}")
            col31, col32 = st.columns(2)
            with col31:
                relation_join_date = st.text_input(
                    f"{UI_TEXTS['relation_join_date']}*",
                    value="",
                    help=UI_TEXTS['date_placeholder'],
                    key="add_adopted_parent_relation_join_date_2"
                )
                submit_clicked = st.form_submit_button(UI_TEXTS['submit'], type="primary")
            with col32:
                adopted_relations = [dbm.Relation_Type['parent ai'], dbm.Relation_Type['parent ao']]
                relation_type = st.selectbox(
                    f"{UI_TEXTS['relation_type']}*",
                    adopted_relations,
                    help=UI_TEXTS['relation_type'],
                    key="add_adopted_parent_relation_type_2",
                    index=0
                )
                reset_clicked = st.form_submit_button(UI_TEXTS['reset'], type="secondary")
            if reset_clicked:
                if 'search_results' in st.session_state:
                    del st.session_state['search_results']
                st.rerun()
            if submit_clicked:
                if not all([name, gen_order, born, join_date, relation_type]):
                    st.error(f"❌ {UI_TEXTS['relation']} {UI_TEXTS['field']} {UI_TEXTS['required']}")
                else:
                    try:
                        # Create member record
                        member_data = {
                            'name': name,
                            'sex': sex,
                            'born': born,
                            'email': email,
                            'family_id': family_id,
                            'gen_order': gen_order,
                            'alias': alias,
                            'url': url,
                            'password': password,
                            'confirm_password': confirm_password,
                            'relation_join_date': relation_join_date,
                            'relation_type': relation_type
                        }
                        member_id = dbm.add_or_update_member(
                            member_data,
                            update=False)
                        if not member_id:
                            st.error(f"❌ {UI_TEXTS['member_error']} : {member_data}")
                    
                        # Create relationship record
                        relationship_data = {
                            'member_id': member_id,
                            'partner_id': selected_child['id'],
                            'relation': relation_type,
                            'join_date': relation_join_date,
                            'end_date': '0000-00-00'
                        }
                    
                        # Add the relationship record
                        relation_id = dbm.add_or_update_relation(
                            relationship_data,
                            update=True)
                    
                        if relation_id:
                            st.success(f"✅ {UI_TEXTS['relation_created']}: {relationship_type} between {selected_member.get('name')} and {partner_name}")
                            # Clear search results after successful submission
                            if 'search_results' in st.session_state:
                                del st.session_state['search_results']   
                        else:
                            st.error(f"❌ {UI_TEXTS['relation_error']}: {UI_TEXTS['relation_not_created']}: {relationship_data}")
                
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                    
                    # Check optional user email and password if given for
                    # subscription, create an user in the dbm.db_table['users'] table
                    if email and password:
                        try:
                            user_data = {
                                'is_admin': User_State['f_member'],
                                'is_active': Subscriber_State['active'],
                                'family_id': family_id,
                                'member_id': member_id
                            }
                            result, error_msg = dbm.add_or_update_user(
                                email,
                                password,
                                user_data=user_data,
                                update=False)
                            if result:
                                st.success(f"✅ {UI_TEXTS['user_created']}: {email}")
                            else:
                                st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']} : {error_msg}")
                        except Exception as e:
                            st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']}: {str(e)}")
                    
def divorce_seperation_page():
    """
    Display divorce/seperation page
    - To search two involved parties by id or name.
    - Once two parties are selected by id or name, show relation_type and end_date to 
    confirm the relationship in the dbm.db_table['relations'] table.
    """
    # Initialize session state for search results and selected partners
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_parties' not in st.session_state:
        st.session_state.selected_parties = {'partner1': None, 'partner2': None}
    logger.debug(f"{fu.get_function_name()}: {UI_TEXTS['divorce']} {UI_TEXTS['or']} {UI_TEXTS['seperation']} {UI_TEXTS['page']}")
    
    # Only show search form if either partner1 or partner2 is not selected
    if st.session_state.selected_parties['partner1'] is None or st.session_state.selected_parties['partner2'] is None:
        with st.form("search_spouse_to_end_form"):
            st.markdown(f"### {UI_TEXTS['search']} {UI_TEXTS['spouse']} {UI_TEXTS['as']} {UI_TEXTS['partner']}")
            
            # Show which partner we're searching for
            if st.session_state.selected_parties['partner1'] is None and st.session_state.selected_parties['partner2'] is None:
                st.info(f"{UI_TEXTS['search_for']} {UI_TEXTS['partner']}-1 {UI_TEXTS['and']} {UI_TEXTS['partner']}-2")
            elif st.session_state.selected_parties['partner1'] is None:
                st.info(f"{UI_TEXTS['search_for']} {UI_TEXTS['partner']}-1")
            else:
                st.info(f"{UI_TEXTS['search_for']} {UI_TEXTS['partner']}-2")
            
            search_type = st.radio(
                f"{UI_TEXTS['search_by']} {UI_TEXTS['member']} {UI_TEXTS['id']} {UI_TEXTS['or']} {UI_TEXTS['name']}*",
                [f"{UI_TEXTS['member']} {UI_TEXTS['id']}", f"{UI_TEXTS['member']} {UI_TEXTS['name']}",],
                horizontal=True,
                key="search_spouse_to_end_type",
                index=0
            )
            col11, col12 = st.columns([1, 10])
            with col11:
                member_id = st.number_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['id']}",
                    min_value=1,
                    step=1,
                    key="spouse_to_end_id"
                )
            with col12:
                name = st.text_input(
                    f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                    key="spouse_to_end_name"
                )
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
            with btn_col2:
                reset_search = st.form_submit_button(f"{UI_TEXTS['reset']} {UI_TEXTS['search']}", type="secondary")
            with btn_col1:
                search_clicked = st.form_submit_button(UI_TEXTS['search'], type="primary")
            with btn_col3:
                refresh_clicked = st.form_submit_button(UI_TEXTS['refresh'], type="secondary")
            # Handle reset
            if reset_search:
                st.session_state.search_results = []
                st.session_state.selected_parties = {'partner1': None, 'partner2': None}
                st.rerun()
            # Handle refresh
            if refresh_clicked:
                st.rerun()
            if search_clicked:
                # Search by id or name
                if search_type == f"{UI_TEXTS['member']} {UI_TEXTS['id']}" and member_id:
                    try:
                        member = dbm.get_member(member_id)
                        if member:
                            if st.session_state.selected_parties['partner1'] is None:
                                st.session_state.selected_parties['partner1'] = member
                            else:
                                st.session_state.selected_parties['partner2'] = member
                            st.session_state.search_results.append(member)
                        else:
                            st.warning(f"⚠️ {member_id}: {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                    except ValueError as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                elif search_type == f"{UI_TEXTS['member']} {UI_TEXTS['name']}" and name.strip():
                    # Search members by name (case insensitive)
                    name = name.strip().lower()
                    try:
                        if name:
                            members = dbm.search_members(name=name)
                            if members:
                                for member in members:
                                    st.session_state.search_results.append(member)
                            else:
                                st.warning(f"⚠️ {name}: {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                    except ValueError as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
    
    # Display search results with checkboxes for selection
    if st.session_state.search_results:
        st.subheader(f"{UI_TEXTS['search']} {UI_TEXTS['results']}")
        
        # Display results with checkboxes
        for member in st.session_state.search_results:
            col1, col2, col3 = st.columns([1, 2, 9])
            with col1:
                st.write(f"**{UI_TEXTS['id']}:** {member.get('id')}")
            with col2:
                st.write(f"**{UI_TEXTS['name']}:** {member.get('name', '?')}")
            with col3:
                # Create a container for inline radio button with label
                col_label, col_radio = st.columns([1, 10])
                with col_label:
                    st.write(f"{UI_TEXTS['select']} {UI_TEXTS['as']}:", unsafe_allow_html=True)
                with col_radio:
                    partner_role = st.radio(
                        "",  # Empty label since we're using our own
                        ["None", UI_TEXTS['partner']+'-1', UI_TEXTS['partner']+'-2'],
                        key=f"partner_role_{member['id']}",
                        horizontal=True,
                        index=0,
                        label_visibility="collapsed"
                    )
                
                # Update selected partners based on radio selection
                if partner_role == UI_TEXTS['partner']+'-1':
                    st.session_state.selected_parties['partner1'] = member['id']
                    # Clear any previous partner selection
                    for m in st.session_state.search_results:
                        if m['id'] != member['id'] and st.session_state.get(f"partner_role_{m['id']}") == UI_TEXTS['partner']+'-1':
                            st.session_state[f"partner_role_{m['id']}"] = "None"
                elif partner_role == UI_TEXTS['partner']+'-2':
                    st.session_state.selected_parties['partner2'] = member['id']
                    # Clear any previous partner selection
                    for m in st.session_state.search_results:
                        if m['id'] != member['id'] and st.session_state.get(f"partner_role_{m['id']}") == UI_TEXTS['partner']+'-2':
                            st.session_state[f"partner_role_{m['id']}"] = "None"
                else:
                    # If "None" is selected, clear this member from selected_partners if they were selected
                    if st.session_state.selected_parties.get('partner1') == member['id']:
                        st.session_state.selected_parties['partner1'] = None
                    if st.session_state.selected_parties.get('partner2') == member['id']:
                        st.session_state.selected_parties['partner2'] = None
    
    if st.session_state.selected_parties['partner1'] and st.session_state.selected_parties['partner2']:
        # Divorce/Seperation form 
        with st.form("divorce_seperation_form"):
            st.subheader(f"{UI_TEXTS['divorce']} {UI_TEXTS['or']} {UI_TEXTS['seperation']}")
            
            # Selected partners info
            partner1 = dbm.get_member(st.session_state.selected_parties.get('partner1', 0)) if st.session_state.selected_parties.get('partner1') else None
            partner2 = dbm.get_member(st.session_state.selected_parties.get('partner2', 0)) if st.session_state.selected_parties.get('partner2') else None
        
            if partner1:
                st.write(f"**{UI_TEXTS['partner']}-1:** {partner1.get('name', '?')} (ID: {partner1['id']} {UI_TEXTS['born']}: {partner1['born']} {UI_TEXTS['gen_order']}: {partner1['gen_order']})")
            if partner2:
                st.write(f"**{UI_TEXTS['partner']}-2:** {partner2.get('name', '?')} (ID: {partner2['id']} {UI_TEXTS['born']}: {partner2['born']} {UI_TEXTS['gen_order']}: {partner2['gen_order']})")
            if not partner1 and not partner2:
                st.warning(f"⚠️ {UI_TEXTS['select']} {UI_TEXTS['partner']}-1 {UI_TEXTS['and']} {UI_TEXTS['partner']}-2 {UI_TEXTS['from']} {UI_TEXTS['search']} {UI_TEXTS['form']}.")
          
            if partner1 and partner2:
                # Get all spouse relations between the two partners
                relations = dbm.get_relations_by_id(partner1['id'], relation="spouse")
                
                if relations:
                    enhanced_data = []
                    for rel in relations:
                        # Determine who is member and who is partner based on the relation direction
                        if rel['member_id'] == partner1['id'] and rel['partner_id'] == partner2['id']:
                            member = partner1
                            partner = partner2
                        elif rel['member_id'] == partner2['id'] and rel['partner_id'] == partner1['id']:
                            member = partner2
                            partner = partner1
                        else:
                            # relation is not between the two partners
                            continue
                        enhanced_data.append({
                            'Relation ID': rel['id'],
                            'Member ID': member['id'],
                            'Member Name': member.get('name', ''),
                            'Member Gen': member.get('gen_order', ''),
                            'Member Birth': member.get('born', ''),
                            'Relation Type': rel['relation'],
                            'Partner ID': partner['id'],
                            'Partner Name': partner.get('name', ''),
                            'Partner Gen': partner.get('gen_order', ''),
                            'Join Date': rel['join_date'],
                            'End Date': rel.get('end_date', 'Current')
                        })
                    
                    df = pd.DataFrame(enhanced_data)
                    st.dataframe(df)
                    
                    # Store relation IDs in session state for update
                    st.session_state['relation_ids'] = [str(rel['id']) for rel in relations]
                else:
                    st.warning(f"⚠️ {UI_TEXTS['relation_not_found']}")
                    if 'relation_ids' in st.session_state:
                        del st.session_state['relation_ids']
    
            # relation type and end date inputs
            col1, col2 = st.columns(2)
            with col1:
                # Relation type selection
                # options are spouse, spouse divorced, spouse separated
                opt_list = [dbm.Relation_Type['spouse divorced'], dbm.Relation_Type['spouse separated']]
                relation_type = st.radio(
                    UI_TEXTS['relation_type'],
                    options=opt_list,
                    index=0,
                    key="divorce_relation_type_radio"
                )
            
            with col2:
                end_date = st.text_input(
                    f"{UI_TEXTS['relation_end_date']}*",
                    placeholder=UI_TEXTS['date_placeholder'],
                    key="divorce_end_date_input"
                )
            
            # Form action buttons
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
            with col_btn1:
                submit_clicked = st.form_submit_button(
                    UI_TEXTS['submit'],
                    type="primary"
                )
            with col_btn2:
                reset_clicked = st.form_submit_button(UI_TEXTS['reset'], type="secondary")
            with col_btn3:
                refresh_clicked = st.form_submit_button(UI_TEXTS['refresh'], type="secondary")
            
            # Handle reset
            if reset_clicked:
                st.session_state.search_results = []
                st.session_state.selected_parties = {'partner1': None, 'partner2': None}
                if 'relation_ids' in st.session_state:
                    del st.session_state['relation_ids']
                st.rerun()
            
            # Handle refresh
            if refresh_clicked:
                st.rerun()
            
            # Handle form submission
            if submit_clicked:
                # Validate required fields
                if not end_date:
                    st.error(f"❌ {UI_TEXTS['relation_end_date']} {UI_TEXTS['is_required']}")
                elif not partner1 or not partner2:
                    st.error(f"❌ {UI_TEXTS['relation_not_found']}")
                else:
                    try:
                        updated_count = dbm.update_relation_when_ended(
                                member1_id=partner1['id'],
                                member2_id=partner2['id'],
                                relation=relation_type,
                                end_date=end_date
                            )
                        
                        if updated_count > 0:
                            message = f"✅ {UI_TEXTS['relation_updated']} {UI_TEXTS['count']}: {updated_count}"
                            st.success(message)
                            
                            # Clear form and search results
                            st.session_state.search_results = []
                            st.session_state.selected_parties = {'partner1': None, 'partner2': None}
                            if 'relation_ids' in st.session_state:
                                del st.session_state['relation_ids']
                        else:
                            st.error(f"❌ {UI_TEXTS['relation_error']}")
                        
                    except Exception as e:
                        st.error(f"❌ {UI_TEXTS['relation_error']}: {str(e)}")

def new_marriage_partnership_page():
    """
    Display new marriage/partnership page
    - Search spouse by id or name via a search form.
    - When the search results are shown, show a radio button to select the spouse.
    - Show a submit button to submit the marriage form
    - When the submit button is clicked, create a new member for the spouse if he/she
    doesn't exist in the dbm.db_table['members'] table.
    - When the reset button is clicked, clear the session state and form.
    - Add the relation to the dbm.db_table['relations'] table.
  
    Return:
    - None
    """
    logger.debug(f"{fu.get_function_name()}: {UI_TEXTS['new']} {UI_TEXTS['marriage']} {UI_TEXTS['or']} {UI_TEXTS['partnership']} {UI_TEXTS['page']}")
    
    # Search form
    with st.form("search_spouse_to_join_form"):
        st.markdown(f"### {UI_TEXTS['search']} {UI_TEXTS['spouse']} {UI_TEXTS['as']} {UI_TEXTS['partner']}")
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
                key="spouse_to_join_id"
            )
        with col12:
            name = st.text_input(
                f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                key="spouse_to_join_name"
            )
        search_clicked = st.form_submit_button(UI_TEXTS['search'])

        # Display search results
        if search_clicked:
            st.session_state.search_results = []
            if search_type == f"{UI_TEXTS['member']} {UI_TEXTS['id']}" and member_id:
                try:
                    member = dbm.get_member(member_id)
                    if member:
                        st.session_state.search_results.append(member)
                    else:
                        st.warning(f"⚠️ {member_id}: {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
            elif search_type == f"{UI_TEXTS['member']} {UI_TEXTS['name']}" and name.strip():
                # Search members by name (case insensitive)
                name = name.strip().lower()
                try:
                    if name:
                        members = dbm.search_members(name=name)
                        if members:
                            st.session_state.search_results.extend(members)
                        else:
                            st.warning(f"⚠️ {UI_TEXTS['member_error']} {UI_TEXTS['member']} {UI_TEXTS['not_found']}: {name}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
    
    # Display search results and the marriage form
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.subheader(f"{UI_TEXTS['search']} {UI_TEXTS['results']}")
        
        # Display results with radio buttons
        partner_options = {f"{m.get('id')} - {m.get('name', '?')} {UI_TEXTS['gen_order']}: {m.get('gen_order', '?')} ({m.get('born', '?')}~{m.get('died', '?')})": m for m in st.session_state.search_results}
        selected_partner_key = st.radio(
            f"{UI_TEXTS['select']} {UI_TEXTS['partner']}",
            options=list(partner_options.keys()),
            key="selected_partner_to_join"
        )
        
        # Get the selected partner
        selected_partner = partner_options[selected_partner_key]
        
        # Marriage form for new member
        with st.form("marriage_form"):
            
            # Get partner details
            st.write(f"### {UI_TEXTS['partner']} {UI_TEXTS['details']}")
            st.write(f"{UI_TEXTS['name']}: {selected_partner.get('name', 'N/A')}")
            st.write(f"{UI_TEXTS['gen_order']}: {selected_partner.get('gen_order', 'N/A')}")
            st.write(f"{UI_TEXTS['born']}: {selected_partner.get('born', 'N/A')}")
            
            # New Member details
            st.write(f"### {UI_TEXTS['new']} {UI_TEXTS['member']} {UI_TEXTS['spouse']} {UI_TEXTS['details']}")
            col21, col22 = st.columns(2)
            with col21:
                name = st.text_input(f"{UI_TEXTS['new']} {UI_TEXTS['member']} {UI_TEXTS['name']}*")
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
                    st.error(f"❌ {UI_TEXTS['password_error']}")
                    return
                url = st.text_input(
                    UI_TEXTS['url'], 
                    "", 
                    key="add_url_2"
                )
        
            # Relationship details
            st.write(f"### {UI_TEXTS['relation']} {UI_TEXTS['details']}")
            col31, col32 = st.columns(2)
            with col31:
                join_date = st.text_input(
                    f"{UI_TEXTS['relation_join_date']}*",
                    value="",
                    help=UI_TEXTS['date_placeholder'],
                    key="add_join_date_2"
                )
                submit_button = st.form_submit_button(f"{UI_TEXTS['create']} {UI_TEXTS['relation']}")
            with col32:
                relationship_type = st.selectbox(
                    f"{UI_TEXTS['relation_type']}*",
                    [dbm.Relation_Type['spouse'], dbm.Relation_Type['spouse dp'], dbm.Relation_Type['spouse cu']],
                    key="relation_type"
                )
                reset_button = st.form_submit_button(f"{UI_TEXTS['reset']}")
            if reset_button:
                if 'search_results' in st.session_state:
                    del st.session_state.search_results
                st.rerun()
            if submit_button:
                # Validate required fields
                if not all([name, gen_order, born, join_date, relationship_type]):
                    st.error(f"{UI_TEXTS['relation']} {UI_TEXTS['field']} {UI_TEXTS['required']}")
                else:
                    try:
                        # Create member record
                        member_data = {
                            'name': name,
                            'sex': sex,
                            'born': born,
                            'email': email,
                            'family_id': family_id,
                            'gen_order': gen_order,
                            'alias': alias,
                            'url': url,
                            'password': password,
                            'confirm_password': confirm_password
                        }
                        member_id = dbm.add_or_update_member(
                            member_data,
                            update=False)
                        if not member_id:
                            st.error(f"❌ {UI_TEXTS['member_error']} : {member_data}")
                        
                        # Create relationship record
                        relationship_data = {
                            'member_id': member_id,
                            'partner_id': selected_partner['id'],
                            'relation': relationship_type.lower(),
                            'join_date': join_date,
                            'end_date': '0000-00-00'
                        }
                        
                        # Add the relationship record
                        relation_id = dbm.add_or_update_relation(
                            relationship_data,
                            update=True)
                        
                        if relation_id:
                            st.success(f"✅ {UI_TEXTS['relation_created']}: {relationship_type} between {selected_member.get('name')} and {partner_name}")
                            # Clear search results after successful submission
                            if 'search_results' in st.session_state:
                                del st.session_state.search_results
                        else:
                            st.error(f"❌ {UI_TEXTS['relation_error']}: {UI_TEXTS['relation_not_created']}: {relationship_data}")
                            
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['relation_error']}: {str(e)}")
                
                # Check optional user email and password if given for
                # subscription, create an user in the dbm.db_table['users'] table
                if email and password:
                    try:
                        user_data = {
                            'is_admin': User_State['f_member'],
                            'is_active': Subscriber_State['active'],
                            'family_id': family_id,
                            'member_id': member_id
                        }
                        result, error_msg = dbm.add_or_update_user(
                            email,
                            password,
                            user_data=user_data,
                            update=False)
                        if result:
                            st.success(f"✅ {UI_TEXTS['user_created']}: {email}")
                        else:
                            st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']} : {error_msg}")
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']}: {str(e)}")
                    
def new_step_child_page():
    """ 
    Display the new step child page.
    - Search member as a step parent by id or name via a search form.
    - When the search results are shown as a list of radio buttons
    to select.
    - When a radio button is selected, display the member's details
    in the add_step_child form.
    - When the submit button is clicked, create a new step child
    record in the dbm.db_table['members'] table and the relationship
    record in the dbm.db_table['relations'] table.
    - When the reset button is clicked, clear the session states 
    and rerun the page.
    
    Returns:
        None
    """
    logger.debug(f"{fu.get_function_name()}: {UI_TEXTS['new']} {UI_TEXTS['step_child']} {UI_TEXTS['page']}")
    
    # Search form
    with st.form("search_step_parent_to_join_form"):
        st.markdown(f"### {UI_TEXTS['search']} {UI_TEXTS['step_parent']} {UI_TEXTS['member']}")
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
                key="step_parent_to_join_id"
            )
        with col12:
            name = st.text_input(
                f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                key="step_parent_to_join_name"
            )
        search_clicked = st.form_submit_button(UI_TEXTS['search'], type="primary", use_container_width=True)

        # Display search results
        if search_clicked:
            st.session_state.search_results = []
            if search_type == f"{UI_TEXTS['member']} {UI_TEXTS['id']}":
                try:
                    member = dbm.get_member(member_id)
                    if member:
                        st.session_state.search_results.append(member)
                    else:
                        st.warning(f"⚠️ {member_id} {UI_TEXTS['member_error']}: {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
            elif search_type == f"{UI_TEXTS['member']} {UI_TEXTS['name']}" and name.strip():
                name = name.strip().lower()
                try:
                    members = dbm.search_members(name=name)
                    if members:
                        st.session_state.search_results.extend(members)
                    else:
                        st.warning(f"⚠️ {name} {UI_TEXTS['member_error']}: {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")

    # Display search results and the step child form
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.subheader(f"{UI_TEXTS['search']} {UI_TEXTS['results']}")
        
        # Display results with radio buttons
        step_parent_options = {f"{m.get('id')} - {m.get('name', '?')} {UI_TEXTS['gen_order']}: {m.get('gen_order', '?')} ({m.get('born', '?')}~{m.get('died', '?')})": m for m in st.session_state.search_results}
        selected_step_parent_key = st.radio(
            f"{UI_TEXTS['select']} {UI_TEXTS['step_parent']}",
            options=list(step_parent_options.keys()),
            key="selected_step_parent_to_join"
        )
        
        # Get the selected step parent
        selected_step_parent = step_parent_options.get(selected_step_parent_key)
        
        # Display the step child form
        with st.form("new_step_child_form"):
            
            # Get step parent details
            st.write(f"### {UI_TEXTS['step_parent']} {UI_TEXTS['details']}")
            st.write(f"{UI_TEXTS['name']}: {selected_step_parent.get('name', 'N/A')}")
            st.write(f"{UI_TEXTS['gen_order']}: {selected_step_parent.get('gen_order', 'N/A')}")
            st.write(f"{UI_TEXTS['born']}: {selected_step_parent.get('born', 'N/A')}")
            
            # New Member details
            st.write(f"### {UI_TEXTS['new']} {UI_TEXTS['member']}: {UI_TEXTS['step_child']} {UI_TEXTS['details']}")
            col21, col22 = st.columns(2)
            with col21:
                name = st.text_input(f"{UI_TEXTS['new']} {UI_TEXTS['member']} {UI_TEXTS['name']}*")
                sex = st.selectbox(
                    UI_TEXTS['sex'],
                    [UI_TEXTS['sex_male'], UI_TEXTS['sex_female'], UI_TEXTS['sex_other']],
                    index=0,
                    key="add_step_child_sex_2"
                )
                born = st.text_input(
                    f"{UI_TEXTS['born']}*",
                    value="",
                    help=UI_TEXTS['date_placeholder'],
                    key="add_step_child_born_date_2"
                )
                family_id = st.number_input(
                    f"{UI_TEXTS['family']} {UI_TEXTS['id']}",
                    min_value=0,
                    step=1,
                    value=selected_step_parent.get('family_id', 0),
                    key="add_step_child_family_id_2"
                )
                gen_order = st.number_input(
                    f"{UI_TEXTS['gen_order']}*",
                    min_value=0,
                    step=1,
                    value=selected_step_parent.get('gen_order', 0) + 1,
                    key="add_step_child_gen_order_2"
                )
            with col22:
                alias = st.text_input(
                    UI_TEXTS['alias'], 
                    "", 
                    key="add_step_child_alias_2"
                )
            
                email = st.text_input(
                    UI_TEXTS['email'], 
                    "", 
                    key="add_step_child_email_2"
                )
                password = st.text_input(
                    UI_TEXTS['password'], 
                    "", 
                    type="password", 
                    key="add_step_child_password_2"
                )
                confirm_password = st.text_input(
                    UI_TEXTS['password_confirmed'], 
                    "", 
                    type="password", 
                    key="add_step_child_confirm_password_2"
                )
                if password != confirm_password:
                    st.error(f"❌ {UI_TEXTS['password_error']}")
                    return
                url = st.text_input(
                    UI_TEXTS['url'], 
                    "", 
                    key="add_step_child_url_2"
                )
        
            # Relationship details
            st.write(f"### {UI_TEXTS['relation']} {UI_TEXTS['details']}")
            col31, col32 = st.columns(2)
            with col31:
                join_date = st.text_input(
                    f"{UI_TEXTS['relation_join_date']}*",
                    value="",
                    help=UI_TEXTS['date_placeholder'],
                    key="add_step_child_join_date_2"
                )
                submit_button = st.form_submit_button(f"{UI_TEXTS['create']} {UI_TEXTS['relation']}")
            with col32:
                relationship_type = st.selectbox(
                    f"{UI_TEXTS['relation_type']}*",
                    [dbm.Relation_Type['child step'], dbm.Relation_Type['parent step']],
                    index=0,
                    key="add_step_child_relationship_type_2"
                )
                reset_button = st.form_submit_button(f"{UI_TEXTS['reset']}")
            if reset_button:
                if 'search_results' in st.session_state:
                    del st.session_state.search_results
                st.rerun()
            if submit_button:
                # Validate required fields
                if not all([name, gen_order, born, join_date, relationship_type]):
                    st.error(f"❌ {UI_TEXTS['relation']} {UI_TEXTS['field']} {UI_TEXTS['required']}")
                else:
                    try:
                        # Create member record
                        member_data = {
                            'name': name,
                            'sex': sex,
                            'born': born,
                            'email': email,
                            'family_id': family_id,
                            'gen_order': gen_order,
                            'alias': alias,
                            'url': url,
                            'password': password,
                            'confirm_password': confirm_password
                        }
                        member_id = dbm.add_or_update_member(
                            member_data,
                            update=False)
                        if not member_id:
                            st.error(f"❌ {UI_TEXTS['member_error']} : {member_data}")
                        
                        # Create relationship record
                        relationship_data = {
                            'member_id': member_id,
                            'partner_id': selected_step_parent['id'],
                            'relation': relationship_type.lower(),
                            'join_date': join_date,
                            'end_date': '0000-00-00'
                        }
                        
                        # Add the relationship record
                        relation_id = dbm.add_or_update_relation(
                            relationship_data,
                            update=True)
                        
                        if relation_id:
                            st.success(f"✅ {UI_TEXTS['relation_created']}: {relationship_type} between {selected_member.get('name')} and {partner_name}")
                            # Clear search results after successful submission
                            if 'search_results' in st.session_state:
                                del st.session_state.search_results
                        else:
                            st.error(f"❌ {UI_TEXTS['relation_error']}: {UI_TEXTS['relation_not_created']}: {relationship_data}")
                            
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['relation_error']}: {str(e)}")
                
                # Check optional user email and password if given for
                # subscription, create an user in the dbm.db_table['users'] table
                if email and password:
                    try:
                        user_data = {
                            'is_admin': User_State['f_member'],
                            'is_active': Subscriber_State['active'],
                            'family_id': family_id,
                            'member_id': member_id
                        }
                        result, error_msg = dbm.add_or_update_user(
                            email,
                            password,
                            user_data=user_data,
                            update=False)
                        if result:
                            st.success(f"✅ {UI_TEXTS['user_created']}: {email}")
                        else:
                            st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']} : {error_msg}")
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']}: {str(e)}")

def new_step_parent_page():
    """ 
    Display the new step parent page.
    - Search member as a step child by id or name via a search form.
    - When the search results are shown as a list of radio buttons
    to select.
    - When a radio button is selected, display the member's details
    in the add_step_parent form.
    - When the submit button is clicked, create a new step parent
    record in the dbm.db_table['members'] table and the relationship
    record in the dbm.db_table['relations'] table.
    - When the reset button is clicked, clear the session states 
    and rerun the page.
    
    Returns:
        None
    """
    logger.debug(f"{fu.get_function_name()}: {UI_TEXTS['new']} {UI_TEXTS['step_parent']} {UI_TEXTS['page']}")
    
    # Search form
    with st.form("search_step_child_to_join_form"):
        st.markdown(f"### {UI_TEXTS['search']} {UI_TEXTS['step_child']} {UI_TEXTS['member']}")
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
                key="step_child_to_join_id"
            )
        with col12:
            name = st.text_input(
                f"{UI_TEXTS['enter']} {UI_TEXTS['member']} {UI_TEXTS['name']}",
                key="step_child_to_join_name"
            )
        search_clicked = st.form_submit_button(UI_TEXTS['search'], type="primary", use_container_width=True)

        # Display search results
        if search_clicked:
            st.session_state.search_results = []
            if search_type == f"{UI_TEXTS['member']} {UI_TEXTS['id']}":
                try:
                    member = dbm.get_member(member_id)
                    if member:
                        st.session_state.search_results.append(member)
                    else:
                        st.warning(f"⚠️ {member_id} {UI_TEXTS['member_error']}: {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")
            elif search_type == f"{UI_TEXTS['member']} {UI_TEXTS['name']}" and name.strip():
                name = name.strip().lower()
                try:
                    members = dbm.search_members(name=name)
                    if members:
                        st.session_state.search_results.extend(members)
                    else:
                        st.warning(f"⚠️ {name} {UI_TEXTS['member_error']}: {UI_TEXTS['member']} {UI_TEXTS['not_found']}")
                except Exception as e:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['member_error']}: {str(e)}")

    # Display search results and the step child form
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.subheader(f"{UI_TEXTS['search']} {UI_TEXTS['results']}")
        
        # Display results with radio buttons
        step_child_options = {f"{m.get('id')} - {m.get('name', '?')} {UI_TEXTS['gen_order']}: {m.get('gen_order', '?')} ({m.get('born', '?')}~{m.get('died', '?')})": m for m in st.session_state.search_results}
        selected_step_child_key = st.radio(
            f"{UI_TEXTS['select']} {UI_TEXTS['step_child']}",
            options=list(step_child_options.keys()),
            key="selected_step_child_to_join"
        )
        
        # Get the selected step child
        selected_step_child = step_child_options.get(selected_step_child_key)
        
        # Display the step parent form
        with st.form("new_step_parent_form"):
            
            # Get step child details
            st.write(f"### {UI_TEXTS['step_child']} {UI_TEXTS['details']}")
            st.write(f"{UI_TEXTS['name']}: {selected_step_child.get('name', 'N/A')}")
            st.write(f"{UI_TEXTS['gen_order']}: {selected_step_child.get('gen_order', 'N/A')}")
            st.write(f"{UI_TEXTS['born']}: {selected_step_child.get('born', 'N/A')}")
            
            # New Member details
            st.write(f"### {UI_TEXTS['new']} {UI_TEXTS['member']}: {UI_TEXTS['step_parent']} {UI_TEXTS['details']}")
            col21, col22 = st.columns(2)
            with col21:
                name = st.text_input(f"{UI_TEXTS['new']} {UI_TEXTS['member']} {UI_TEXTS['name']}*")
                sex = st.selectbox(
                    UI_TEXTS['sex'],
                    [UI_TEXTS['sex_male'], UI_TEXTS['sex_female'], UI_TEXTS['sex_other']],
                    index=0,
                    key="add_step_parent_sex_2"
                )
                born = st.text_input(
                    f"{UI_TEXTS['born']}*",
                    value="",
                    help=UI_TEXTS['date_placeholder'],
                    key="add_step_parent_born_date_2"
                )
                family_id = st.number_input(
                    f"{UI_TEXTS['family']} {UI_TEXTS['id']}",
                    min_value=0,
                    step=1,
                    value=selected_step_child.get('family_id', 0),
                    key="add_step_parent_family_id_2"
                )
                gen_order = st.number_input(
                    f"{UI_TEXTS['gen_order']}*",
                    min_value=0,
                    step=1,
                    value=selected_step_child.get('gen_order', 0) - 1,
                    key="add_step_parent_gen_order_2"
                )
            with col22:
                alias = st.text_input(
                    UI_TEXTS['alias'], 
                    "", 
                    key="add_step_parent_alias_2"
                )
            
                email = st.text_input(
                    UI_TEXTS['email'], 
                    "", 
                    key="add_step_parent_email_2"
                )
                password = st.text_input(
                    UI_TEXTS['password'], 
                    "", 
                    type="password", 
                    key="add_step_parent_password_2"
                )
                confirm_password = st.text_input(
                    UI_TEXTS['password_confirmed'], 
                    "", 
                    type="password", 
                    key="add_step_parent_confirm_password_2"
                )
                if password != confirm_password:
                    st.error(f"❌ {UI_TEXTS['password_error']}")
                    return
                url = st.text_input(
                    UI_TEXTS['url'], 
                    "", 
                    key="add_step_parent_url_2"
                )
        
            # Relationship details
            st.write(f"### {UI_TEXTS['relation']} {UI_TEXTS['details']}")
            col31, col32 = st.columns(2)
            with col31:
                join_date = st.text_input(
                    f"{UI_TEXTS['relation_join_date']}*",
                    value="",
                    help=UI_TEXTS['date_placeholder'],
                    key="add_step_parent_join_date_2"
                )
                submit_button = st.form_submit_button(f"{UI_TEXTS['create']} {UI_TEXTS['relation']}")
            with col32:
                relationship_type = st.selectbox(
                    f"{UI_TEXTS['relation_type']}*",
                    [dbm.Relation_Type['parent step'], dbm.Relation_Type['child step']],
                    index=0,
                    key="add_step_parent_relationship_type_2"
                )
                reset_button = st.form_submit_button(f"{UI_TEXTS['reset']}")
            if reset_button:
                if 'search_results' in st.session_state:
                    del st.session_state.search_results
                st.rerun()
            if submit_button:
                # Validate required fields
                if not all([name, gen_order, born, join_date, relationship_type]):
                    st.error(f"{UI_TEXTS['relation']} {UI_TEXTS['field']} {UI_TEXTS['required']}")
                else:
                    try:
                        # Create member record
                        member_data = {
                            'name': name,
                            'sex': sex,
                            'born': born,
                            'email': email,
                            'family_id': family_id,
                            'gen_order': gen_order,
                            'alias': alias,
                            'url': url,
                            'password': password,
                            'confirm_password': confirm_password
                        }
                        member_id = dbm.add_or_update_member(
                            member_data,
                            update=False)
                        if not member_id:
                            st.error(f"{UI_TEXTS['member_error']} : {member_data}")
                        
                        # Create relationship record
                        relationship_data = {
                            'member_id': member_id,
                            'partner_id': selected_step_child['id'],
                            'relation': relationship_type,
                            'join_date': join_date,
                            'end_date': '0000-00-00'
                        }
                        
                        # Add the relationship record
                        relation_id = dbm.add_or_update_relation(
                            relationship_data,
                            update=True)
                        
                        if relation_id:
                            st.success(f"✅ {UI_TEXTS['relation_created']}: {relationship_type} between {selected_member.get('name')} and {partner_name}")
                            # Clear search results after successful submission
                            if 'search_results' in st.session_state:
                                del st.session_state.search_results
                        else:
                            st.error(f"❌ {UI_TEXTS['relation_error']}: {UI_TEXTS['relation_not_created']}: {relationship_data}")
                            
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['relation_error']}: {str(e)}")
                
                # Check optional user email and password if given for
                # subscription, create an user in the dbm.db_table['users'] table
                if email and password:
                    try:
                        user_data = {
                            'is_admin': User_State['f_member'],
                            'is_active': Subscriber_State['active'],
                            'family_id': family_id,
                            'member_id': member_id
                        }
                        result, error_msg = dbm.add_or_update_user(
                            email,
                            password,
                            user_data=user_data,
                            update=False)
                        if result:
                            st.success(f"✅ {UI_TEXTS['user_created']}: {email}")
                        else:
                            st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']} : {error_msg}")
                    except Exception as e:
                        st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['user_error']}: {str(e)}")

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
    st.header(f"📋 {UI_TEXTS['case_mgmt']}")
    
    # Main tab groups
    case_tabs = st.tabs([
        "New Birth", 
        "New Death", 
        "New Adopted Child",
        "New Adopted Parent",
        "Divorce/Seperation",
        "New Marriage/Partnership",
        "New Step Child",
        "New Step Parent"
        ])
    
    with case_tabs[0]:  # New Birth
        st.subheader(f"{UI_TEXTS['new_birth']} 👶")
        new_birth_page()
        
    with case_tabs[1]:  # New Death
        st.subheader(f"{UI_TEXTS['new_death']} ✝️")       
        new_death_page()
        
    with case_tabs[2]:  # New Adopted Child
        st.subheader(f"{UI_TEXTS['new']} {UI_TEXTS['adopted_child']} 👶")
        new_adopted_child_page()
        
    with case_tabs[3]:  # New Adopted Parent
        st.subheader(f"{UI_TEXTS['new']} {UI_TEXTS['adopted_parent']} 👨‍👩‍👧️")
        new_adopted_parent_page()
       
    with case_tabs[4]:  # Divorce/Seperation
        st.subheader(f"{UI_TEXTS['divorce']} {UI_TEXTS['or']} {UI_TEXTS['seperation']} 💔")        
        divorce_seperation_page()
        
    with case_tabs[5]:  # New Marriage/Partnership
        st.subheader(f"{UI_TEXTS['new']} {UI_TEXTS['marriage']} {UI_TEXTS['or']} {UI_TEXTS['partnership']} ❤️")        
        new_marriage_partnership_page()
        
    with case_tabs[6]:  # Step Child
        st.subheader(f"{UI_TEXTS['new']} {UI_TEXTS['step_child']} 👶")
        new_step_child_page()

    with case_tabs[7]:  # Step Parent
        st.subheader(f"{UI_TEXTS['new']} {UI_TEXTS['step_parent']} 👨‍👩‍👧")
        new_step_parent_page()

# Initialize session state and app/ui context
if 'app_context' not in st.session_state:
    cu.init_session_state()

# Get UI_TEXTS with a fallback to English if needed
try:
    UI_TEXTS = st.session_state.ui_context[st.session_state.app_context.get('language', 'US')]
except (KeyError, AttributeError):
    # Fallback to English if there's any issue
    UI_TEXTS = st.session_state.ui_context['US']

if __name__ == "__main__":
    # Check authentication
    if not st.session_state.get('authenticated', False):
        st.switch_page("ftpe_ui.py")
    else:
        sidebar()
        main()