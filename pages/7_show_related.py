"""
# Add parent directory to path to allow absolute imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


Family Tree Visualization - show partners of a given member from
the dbm.db_tables['relations'] table.

This script displays a relationship tree centered around a given 
member ID via streamlit.
It shows the member (id and name from dbm.db_tables['members'] table), 
their partners (id and name from dbm.db_tables['members'] table), 
and corresponding relation types (as label of edges) 
in a graph visualization using graphviz.
The style of the graph is similar to 
the one in page 6_show_3G.py.
"""

import streamlit as st
import graphviz as gv
import logging
from typing import Dict, List, Optional, Tuple, Any
import db_utils as dbm
import context_utils as cu

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_relationship_data(member_id: int) -> Dict[str, Any]:
    """
    Retrieve relationship data for a given member ID.
    
    Args:
        member_id: The ID of the center member
        
    Returns:
        Dict containing:
            - center: The center member
            - relationships: List of relationships where the member is involved
            - partners: List of partners with their relationship info
    """
    try:
        # Get the center member
        center = dbm.get_member(member_id)
        if not center:
            st.error(f"No member found with ID: {member_id}")
            return {}
            
        # Get all relationships where this member is either member_id or partner_id
        relationships = dbm.get_relations_by_id(member_id)
        
        # Process relationships to get partner information
        partners = []
        for rel in relationships:
            # Determine if the current member is member_id or partner_id
            if rel['member_id'] == member_id:
                partner_id = rel['partner_id']
                relation_type = rel['relation']
            else:
                partner_id = rel['member_id']
                # Reverse the relation for display (e.g., "spouse" remains the same, but "parent" becomes "child")
                relation_type = get_inverse_relation(rel['relation'])
            
            # Get partner details
            partner = dbm.get_member(partner_id)
            if partner:
                partners.append({
                    'id': partner_id,
                    'name': partner.get('name', 'Unknown'),
                    'relation': relation_type,
                    'relation_id': rel.get('id', ''),  # Add relation_id from the relations table
                    'join_date': rel.get('join_date', ''),
                    'end_date': rel.get('end_date', '')
                })
        
        return {
            'center': center,
            'relationships': relationships,
            'partners': partners
        }
        
    except Exception as e:
        st.error(f"Error retrieving relationship data: {str(e)}")
        logger.exception("Error in get_relationship_data")
        return {}

def get_inverse_relation(relation_type: str) -> str:
    """
    Get the inverse of a relationship type.
    
    Args:
        relation_type: The original relation type (e.g., 'parent', 'spouse')
        
    Returns:
        The inverse relation type (e.g., 'child' for 'parent', 'spouse' for 'spouse')
    """
    relation_map = {
        'parent': 'child inversed',
        'child': 'parent inversed',
        'spouse': 'spouse inversed',
        'parent adopted within family': 'child adopted within family inversed',
        'child adopted within family': 'parent adopted within family inversed'
    }
    return relation_map.get(relation_type.lower(), relation_type)

def create_relationship_graph(relationship_data: Dict[str, Any]) -> gv.Digraph:
    """
    Create a Graphviz diagram of the relationship tree.
    
    Args:
        relationship_data: Dictionary containing relationship data
        
    Returns:
        graphviz.Digraph: The generated relationship graph
    """
    # Create a new graph
    graph = gv.Digraph(
        'relationships',
        node_attr={
            'style': 'filled',
            'shape': 'box',
            'fontname': 'Arial',
            'fontsize': '12',
            'margin': '0.2,0.1',
            'height': '0.3',
            'width': '0.5',
            'fillcolor': '#f0f8ff',  # Light blue background
            'color': '#4682b4',      # Steel blue border
            'fontcolor': '#2f4f4f'   # Dark slate gray text
        },
        edge_attr={
            'fontname': 'Arial',
            'fontsize': '10',
            'fontcolor': '#708090',  # Slate gray
            'color': '#a9a9a9',      # Dark gray
            'arrowsize': '0.7'
        }
    )
    
    center = relationship_data.get('center', {})
    partners = relationship_data.get('partners', [])
    
    # Add center node
    center_id = str(center.get('id', 'unknown'))
    center_name = center.get('name', 'Unknown')
    center_label = f"{center_id}: {center_name}"
    
    graph.node(center_id, center_label, 
              shape='ellipse', 
              fillcolor='#ffffe0',  # Light yellow for center
              style='filled,bold',
              penwidth='1.5')
    
    # Add partner nodes and edges
    for partner in partners:
        partner_id = str(partner['id'])
        partner_name = partner['name']
        relation_type = partner['relation']
        
        # Create partner node
        partner_label = f"{partner_id}: {partner_name}"
        graph.node(partner_id, partner_label)
        
        # Add edge with relation type
        graph.edge(center_id, partner_id, label=relation_type)
    
    return graph

def main():
    """
    Main function to render the Streamlit app.
    """
    st.set_page_config(
        page_title="Family Relationships",
        page_icon="👨‍👩‍👧‍👦",
        layout="wide"
    )
    # Sidebar --- from here
    with st.sidebar:
        if st.session_state.user_state != dbm.User_State['p_admin']:
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
            cu.update_context({'email_user': st.session_state.user_email})
        
        if st.session_state.user_state != dbm.User_State['p_admin']:
            st.subheader("Navigation")
            st.page_link("ftpe_ui.py", label="Home", icon="🏠")
            st.page_link("pages/3_csv_editor.py", label="CSV Editor", icon="🔧")
            st.page_link("pages/4_json_editor.py", label="JSON Editor", icon="🪛")
            st.page_link("pages/5_ftpe.py", label="FamilyTreePE", icon="📊")
            st.page_link("pages/6_show_3G.py", label="Show 3 Generations", icon="👥")
            if st.session_state.user_state == dbm.User_State['f_admin']:
                st.page_link("pages/8_caseMgmt.py", label="Case Management", icon="📋")
                st.page_link("pages/9_birthday.py", label="Birthday of the Month", icon="🎂")
                st.page_link("pages/2_famMgmt.py", label="Family Management", icon="🌲")
            
        # Add logout button at the bottom
        if st.button("Logout", type="primary", use_container_width=True, key="show_3g_logout"):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
    
    # Main page --- from here
    st.title("👨‍👩‍👧‍👦 Family Relationships")
    st.write("Visualize relationships for a family member.")
    
    # Get member ID from URL parameters or input
    member_id = int(st.query_params.get('id', 0))
    
    # Member ID input
    col1, col2 = st.columns([1, 3])
    with col1:
        member_id = st.number_input(
            "Enter Member ID:",
            min_value=0,
            value=member_id if member_id > 0 else 0,
            step=1
        )
    
    if st.button("Show Relationships") or member_id > 0:
        with st.spinner("Loading relationship data..."):
            # Get relationship data
            relationship_data = get_relationship_data(member_id)
            
            if not relationship_data:
                st.warning("No relationship data found for this member.")
                return
                
            # Display the member name as a header
            st.subheader(f"Relationships for {relationship_data['center'].get('name', 'Unknown')}")
            
            # Display the graph
            graph = create_relationship_graph(relationship_data)
            st.graphviz_chart(graph, use_container_width=True)
            
            # Create a container for relationship details below the graph
            with st.container():
                st.subheader("Relationship Details")
                if not relationship_data['partners']:
                    st.info("No relationships found for this member.")
                else:
                    # Create columns for better organization of partner details
                    cols = st.columns(2)  # 2 columns for partner details
                    
                    for i, partner in enumerate(relationship_data['partners']):
                        # Alternate between columns for better use of space
                        with cols[i % 2]:
                            with st.expander(f"{partner['name']} (ID: {partner['id']})"):
                                st.markdown(f"**Relation ID:** {partner.get('relation_id', 'N/A')}")
                                st.markdown(f"**Relation:** {partner['relation'].title()}")
                                if partner.get('join_date'):
                                    st.markdown(f"**Since:** {partner['join_date']}")
                                if partner.get('end_date'):
                                    st.markdown(f"**Ended:** {partner['end_date']}")
                            st.markdown("---")

# Initialize session state
cu.init_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("ftpe_ui.py")
else:
    if 'app_context' not in st.session_state:
        st.session_state.app_context = cu.init_context()
    main()