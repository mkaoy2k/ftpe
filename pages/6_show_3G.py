"""
# Add parent directory to path to allow absolute imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


Family Tree Visualization - 3 Generations

This script displays a 3-generation family tree centered around a given member ID.
It shows the member, their parents, and their children in a graph visualization.
"""

import streamlit as st
import graphviz as gv
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv
import context_utils as cu

# Import database utilities
import db_utils as dbm

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_family_members(member_id: int) -> Dict[str, Any]:
    """
    Retrieve family members for a given member ID (3 generations).
    
    Args:
        member_id: The ID of the center member
        
    Returns:
        Dict containing:
            - center: The center member
            - parents: List of parents
            - children: List of children
            - grandparents: List of grandparents
            - grandchildren: List of grandchildren
    """
    try:
        # Get the center member
        center = dbm.get_member(member_id)
        if not center:
            st.error(f"No member found with ID: {member_id}")
            return {}
            
        # Initialize result dictionary
        result = {
            'center': center,
            'parents': [],
            'children': [],
            'grandparents': [],
            'grandchildren': []
        }
        
        # Find parents
        result['parents'] = dbm.get_parents(member_id)
        
        for parent in result['parents']:
            # Add parent relation: 
            # Center member has partner as parent
            try:
                relation = {
                    'member_id': member_id,
                    'partner_id': parent['id'],
                    'relation': 'parent',
                    'join_date': center['born']}
                parent_relations = dbm.add_or_update_relation(
                    relation, update=True)
                if not parent_relations:
                    st.error(f"Error adding parent relation: {str(e)}")
                    logger.exception("Error adding parent relation: {str(e)}")
                    
            except Exception as e:
                st.error(f"Error adding parent relation: {str(e)}")
                logger.exception("Error adding parent relation: {str(e)}")

            # Get grandparents (parents of parents)
            grandparents = dbm.get_parents(parent['id'])
            for grandparent in grandparents:
                # Add grandparent relation: 
                # Parent member has partner as grandparent
                try:
                    relation = {
                        'member_id': parent['id'],
                        'partner_id': grandparent['id'],
                        'relation': 'parent',
                        'join_date': parent['born']}
                    grandparent_relations = dbm.add_or_update_relation(
                        relation, update=True)
                    if not grandparent_relations:
                        st.error(f"Error adding grandparent relation: {str(e)}")
                        logger.exception("Error adding grandparent relation: {str(e)}")
                        
                except Exception as e:
                    st.error(f"Error adding grandparent relation: {str(e)}")
                    logger.exception("Error adding grandparent relation: {str(e)}")
                if grandparent and grandparent not in result['grandparents']:
                    result['grandparents'].append(grandparent)
        
        # Find children
        result['children'] = dbm.get_children(member_id)
        # Add child relation: 
        # Center member has partner as child
        for child in result['children']:
            try:
                relation = {
                    'member_id': member_id,
                    'partner_id': child['id'],
                    'relation': 'child',
                    'join_date': child['born']}
                child_relations = dbm.add_or_update_relation(
                    relation, update=True)
                if not child_relations:
                    st.error(f"Error adding child relation: {str(e)}")
                    logger.exception("Error adding child relation: {str(e)}")
                    
            except Exception as e:
                st.error(f"Error adding child relation: {str(e)}")
                logger.exception("Error adding child relation: {str(e)}")
            # Get grandchildren (children of children)
            grandchildren = dbm.get_children(child['id'])
            for grandchild in grandchildren:
                # Add grandchild relation: 
                # Child member has partner as grandchild
                try:
                    relation = {
                        'member_id': child['id'],
                        'partner_id': grandchild['id'],
                        'relation': 'child',
                        'join_date': grandchild['born']}
                    grandchild_relations = dbm.add_or_update_relation(
                        relation, update=True)
                    if not grandchild_relations:
                        st.error(f"Error adding grandchild relation: {str(e)}")
                        logger.exception("Error adding grandchild relation: {str(e)}")
                        
                except Exception as e:
                    st.error(f"Error adding grandchild relation: {str(e)}")
                    logger.exception("Error adding grandchild relation: {str(e)}")
                if grandchild and grandchild not in result['grandchildren']:
                    result['grandchildren'].append(grandchild)
                    
        return result
        
    except Exception as e:
        st.error(f"Error fetching family members: {str(e)}")
        logger.exception("Error in get_family_members")
        return {}

def create_family_graph(family_data: Dict[str, Any], height: int = 12, width: int = 15, engine: str = 'dot') -> gv.Digraph:
    """
    Create a Graphviz diagram of the family tree.
    
    Args:
        family_data: Dictionary containing family members data
        height: Height of the graph in inches (default: 12)
        width: Width of the graph in inches (default: 15)
        engine: Graphviz layout engine ('dot', 'neato', 'fdp', 'sfdp', 'twopi', 'circo')
        
    Returns:
        graphviz.Digraph: The generated family tree graph
    """
    # Base graph attributes
    graph_attrs = {
        'size': f'{width},{height}!',
        'center': 'true',
        'margin': '0.2',
        'pad': '0.5',
        'dpi': '150',
        'ratio': 'auto',
        'splines': 'ortho' if engine in ['dot', 'neato'] else 'spline',
        'overlap': 'false',
        'splines': 'true',
        'nodesep': '0.5',
        'ranksep': '0.8',
        'newrank': 'true',
        'fontname': 'Arial'
    }
    
    # Engine-specific adjustments
    if engine == 'dot':
        graph_attrs.update({
            'rankdir': 'TB',
            'nodesep': '0.6',
            'ranksep': '1.0',
            'concentrate': 'true'
        })
    elif engine == 'neato':
        graph_attrs.update({
            'mode': 'major',
            'model': 'subset',
            'start': '1',
            'epsilon': '0.0001',
            'maxiter': '1000',
            'damping': '0.99'
        })
    elif engine in ['fdp', 'sfdp']:
        graph_attrs.update({
            'K': '1.0',
            'maxiter': '1000',
            'start': '1',
            'overlap_scaling': '4',
            'repulsiveforce': '1.0'
        })
    elif engine == 'twopi':
        graph_attrs.update({
            'ranksep': '2.0',
            'rank': 'same',
            'root': 'center'
        })
    elif engine == 'circo':
        graph_attrs.update({
            'mindist': '1.0',
            'nodesep': '0.75',
            'ranksep': '1.5'
        })

    # Create the graph with the specified engine and attributes
    graph = gv.Digraph(
        'family_tree',
        node_attr={
            'shape': 'box',
            'style': 'rounded,filled',
            'fillcolor': 'white',
            'fontname': 'Arial',
            'fontsize': '14',
            'margin': '0.15,0.2',
            'width': '2.5',
            'height': '0.8',
            'penwidth': '1.0',
            'color': 'black',
            'fixedsize': 'true'
        },
        edge_attr={
            'arrowhead': 'normal',
            'arrowsize': '0.7',
            'penwidth': '1.5',
            'color': '#333333',
            'constraint': 'true'
        },
        graph_attr=graph_attrs,
        format='svg',
        engine=engine
    )
    # Define node attributes
    def get_node_style(member: Dict[str, Any]) -> Dict[str, str]:
        """Get node style based on member attributes."""
        style = {
            'fillcolor': 'lightblue',
            'color': 'black',
            'fontcolor': 'black',
            'penwidth': '1'
        }
        
        # Highlight center member
        if member.get('id') == family_data.get('center', {}).get('id'):
            style.update({
                'fillcolor': '#FFD700',  # Gold
                'color': 'black',
                'penwidth': '2',
                'style': 'filled,rounded',
                'fontweight': 'bold'
            })
            
        # Style based on gender if available
        gender = member.get('sex', '').lower()
        if gender == 'f':
            style['fillcolor'] = '#FFB6C1'  # Light pink
        elif gender == 'm':
            style['fillcolor'] = '#ADD8E6'  # Light blue
            
        return style
    
    # Add nodes to the graph
    def add_member_node(
        member: Dict[str, Any]
    ) -> None:
        """Add a member node to the graph."""
        member_id = str(member['id'])
        
        # Create label with name and optional birth date
        name = member.get('name', 'Unknown')
        born = member.get('born', '')
        died = member.get('died', '')
        generation = member.get('gen_order', '0')
        
        label = f"{name}"
        if born:
            try:
                # Try parsing as YYYY-MM-DD first
                if '-' in born:
                    birth_year = datetime.strptime(born, '%Y-%m-%d').year
                else:  # Handle YYYY format
                    birth_year = int(born)
                label += f"\n*{birth_year}"
            except (ValueError, TypeError):
                # If parsing fails, just use the raw value
                if born and str(born).strip() not in ('', '0', '0000-00-00'):
                    label += f"\n*{born}"
                
        if died and str(died).strip() not in ('', '0', '0000-00-00'):
            try:
                # Try parsing as YYYY-MM-DD first
                if '-' in died:
                    death_year = datetime.strptime(died, '%Y-%m-%d').year
                else:  # Handle YYYY format
                    death_year = int(died)
                label += f"\n†{death_year}"
            except (ValueError, TypeError):
                # If parsing fails, just use the raw value
                label += f"\n†{died}"
        label += f" ({generation})"
        
        # Add node with attributes
        graph.node(
            member_id,
            label=label,
            **get_node_style(member)
        )
    
    # Add center member
    if 'center' in family_data and family_data['center']:
        add_member_node(family_data['center'])
    
    # Add parents
    parent_nodes = []
    for parent in family_data.get('parents', []):
        add_member_node(parent)
        parent_nodes.append(str(parent['id']))
        
        # Connect to center
        if 'center' in family_data and family_data['center']:
            graph.edge(str(parent['id']), str(family_data['center']['id']))
    
    # Add children
    child_nodes = []
    for child in family_data.get('children', []):
        add_member_node(child)
        child_nodes.append(str(child['id']))
        
        # Connect to center
        if 'center' in family_data and family_data['center']:
            graph.edge(str(family_data['center']['id']), str(child['id']))
    
    # Add grandparents
    grandparent_nodes = []
    for grandparent in family_data.get('grandparents', []):
        add_member_node(grandparent)
        grandparent_nodes.append(str(grandparent['id']))
        
        # Connect to parents
        for parent in family_data.get('parents', []):
            parent_relations = dbm.get_member_relations(parent['id'])
            for rel in parent_relations:
                if rel['relation'] == 'parent' and rel['partner_id'] == grandparent['id']:
                    graph.edge(str(grandparent['id']), str(parent['id']))
    
    # Add grandchildren
    grandchild_nodes = []
    for grandchild in family_data.get('grandchildren', []):
        add_member_node(grandchild)
        grandchild_nodes.append(str(grandchild['id']))
        
        # Connect to children
        for child in family_data.get('children', []):
            child_relations = dbm.get_member_relations(child['id'])
            for rel in child_relations:
                if rel['relation'] == 'child' and rel['partner_id'] == grandchild['id']:
                    graph.edge(str(child['id']), str(grandchild['id']))
    
    # Organize nodes into ranks for proper layout
    with graph.subgraph() as s:
        s.attr(rank='same')
        for node in grandparent_nodes:
            s.node(node)
    
    with graph.subgraph() as s:
        s.attr(rank='same')
        for node in parent_nodes:
            s.node(node)
    
    with graph.subgraph() as s:
        s.attr(rank='same')
        if 'center' in family_data and family_data['center']:
            s.node(str(family_data['center']['id']))
    
    with graph.subgraph() as s:
        s.attr(rank='same')
        for node in child_nodes:
            s.node(node)
    
    with graph.subgraph() as s:
        s.attr(rank='same')
        for node in grandchild_nodes:
            s.node(node)
    
    # Add invisible edges to help with layout
    if len(parent_nodes) > 1:
        for i in range(len(parent_nodes) - 1):
            graph.edge(parent_nodes[i], parent_nodes[i+1], style='invis')
    
    if len(child_nodes) > 1:
        for i in range(len(child_nodes) - 1):
            graph.edge(child_nodes[i], child_nodes[i+1], style='invis')
    
    return graph

def main():
    """Main function to render the Streamlit app."""
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
            st.page_link("pages/7_show_related.py", label="Show Related", icon="👨‍👩‍👧‍👦")
            st.page_link("pages/2_famMgmt.py", label="Family Management", icon="🌲")
            
        # Add logout button at the bottom
        if st.button("Logout", type="primary", use_container_width=True, key="show_3g_logout"):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()
    
    # Main content area --- from here
        
    st.title("Family Tree Visualization")
    st.subheader("View 3 Generations of Family Members")
    
    # Add a form for better user experience
    with st.form("family_tree_form"):
        # Get member ID from user input
        member_id = st.number_input(
            "Enter Member ID (center of the family tree):",
            min_value=1,
            step=1,
            value=1,
            help="Enter the ID of the family member to center the tree on"
        )
        
        # Add graph configuration options
        col1, col2, col3 = st.columns(3)
        with col1:
            graph_height = st.slider(
                "Graph Height (inches):",
                min_value=1,
                max_value=30,
                value=12,
                step=1,
                help="Adjust the height of the family tree graph"
            )
        with col2:
            graph_width = st.slider(
                "Graph Width (inches):",
                min_value=1,
                max_value=30,
                value=5,
                step=1,
                help="Adjust the width of the family tree graph"
            )
        with col3:
            graph_engine = st.selectbox(
                "Layout Engine:",
                options=['dot', 'neato', 'fdp', 'sfdp', 'twopi', 'circo'],
                index=0,
                help="Choose the layout engine for the graph"
            )
        
        submitted = st.form_submit_button("Generate Family Tree", type="primary")
    
    if submitted:
        if not member_id:
            st.warning("Please enter a valid member ID.")
            st.stop()
            
        # Create a container for the tree visualization
        tree_container = st.container()
        
        with st.spinner("Generating family tree..."):
            try:
                # Get family data with error handling
                family_data = get_family_members(member_id)
                
                if not family_data or 'center' not in family_data:
                    st.error("❌ No family data found for the given member ID.")
                    st.stop()
                
                # Display the tree in the container
                with tree_container:
                    st.success("✅ Successfully generated family tree!")
                    
                    # Create and display the graph with user-specified settings
                    try:
                        graph = create_family_graph(
                            family_data, 
                            height=graph_height, 
                            width=graph_width,
                            engine=graph_engine
                        )
                        
                        # Create a scrollable container for the graph
                        graph_svg = graph.pipe(format='svg').decode('utf-8')
                        
                        # Add CSS for the scrollable container
                        st.markdown("""
                        <style>
                        .graph-container {
                            width: 100%;
                            max-height: 800px;
                            overflow: auto;
                            border: 1px solid #e0e0e0;
                            border-radius: 0.5rem;
                            padding: 1rem;
                            background-color: white;
                            margin: 1rem 0;
                        }
                        .graph-container svg {
                            min-width: 100%;
                            min-height: 100%;
                        }
                        /* Custom scrollbar */
                        .graph-container::-webkit-scrollbar {
                            width: 10px;
                            height: 10px;
                        }
                        .graph-container::-webkit-scrollbar-track {
                            background: #f1f1f1;
                            border-radius: 5px;
                        }
                        .graph-container::-webkit-scrollbar-thumb {
                            background: #888;
                            border-radius: 5px;
                        }
                        .graph-container::-webkit-scrollbar-thumb:hover {
                            background: #555;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        # Display the graph in the scrollable container
                        st.markdown(
                            f'<div class="graph-container">{graph_svg}</div>',
                            unsafe_allow_html=True
                        )
                    except Exception as e:
                        st.error(f"❌ Failed to generate family tree visualization: {str(e)}")
                        logger.exception("Error generating graph")
                    
                    # Display family information in an expandable section
                    center = family_data.get('center', {})
                    with st.expander(f"👨‍👩‍👧‍👦 View Family Details for {center.get('name', 'Unknown')} (ID: {center.get('id', 'N/A')})", expanded=True):
                        # Display family members in a structured way
                        cols = st.columns(3)
                        
                        with cols[0]:
                            if family_data.get('grandparents'):
                                st.markdown("### 👴👵 Grandparents")
                                for gp in family_data['grandparents']:
                                    st.write(f"- {gp.get('name', 'Unknown')} (ID: {gp.get('id', 'N/A')})")
                                st.write("")
                            else:
                                st.info("No grandparents found")
                        
                        with cols[1]:
                            if family_data.get('parents'):
                                st.markdown("### 👨‍👩‍👦 Parents")
                                for p in family_data['parents']:
                                    st.write(f"- {p.get('name', 'Unknown')} (ID: {p.get('id', 'N/A')})")
                                st.write("")
                            else:
                                st.info("No parents found")
                            
                            st.markdown("### 👤 Center Member")
                            st.write(f"- {center.get('name', 'Unknown')} (ID: {center.get('id', 'N/A')})")
                            
                            if family_data.get('children'):
                                st.markdown("### 👶 Children")
                                for c in family_data['children']:
                                    st.write(f"- {c.get('name', 'Unknown')} (ID: {c.get('id', 'N/A')})")
                                st.write("")
                            else:
                                st.info("No children found")
                        
                        with cols[2]:
                            if family_data.get('grandchildren'):
                                st.markdown("### 👶👶 Grandchildren")
                                for gc in family_data['grandchildren']:
                                    st.write(f"- {gc.get('name', 'Unknown')} (ID: {gc.get('id', 'N/A')})")
                                st.write("")
                            else:
                                st.info("No grandchildren found")
                
            except Exception as e:
                st.error(f"❌ An error occurred while generating the family tree: {str(e)}")
                logger.exception("Error in main")
                
                # Show helpful error message
                st.info("💡 Tip: Make sure the member ID exists and has family relationships in the database.")

# Initialize session state
cu.init_session_state()
    
# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("ftpe_ui.py")
else:
    if 'app_context' not in st.session_state:
        st.session_state.app_context = cu.init_context()
    main()