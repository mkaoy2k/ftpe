"""
FamilyTrees Personal Edition 1.4 2024/6/27

	Feature Enhancement
        None.
        
	Bug Fix
        1. Fixed function 10 bug to set L10N at run time
        2. Updated function docstrings
        
"""

# Modules required
import pandas as pd     # pip install pandas
import os, time
from dotenv import load_dotenv  # pip install python-dotenv

# Import Web App modules
import streamlit as st  # pip install streamlit
st.set_page_config(
    page_title="FamilyTrees PE",
    page_icon=':books:',
    )

# Import graphviz module
import graphviz as gv   # pip install graphviz

# Import utility functions 
from funcUtils import *

# Import performance logging modules
import glog as log  # pip install glog
from glogTime import func_timer_decorator

# --- Initialize system environment --- from here
load_dotenv(".env")

# --- Set Server logging levels ---
g_log_options=["INFO", "DEBUG"]
g_logging = os.getenv("LOGGING")
log.setLevel(g_logging)    

# --- Internal Functions --- from here
def build_spouse_graph(dbuff):
    """ 
    build family tree graph, starting from mem pointing to spouse(s), 
    and then in turn female spouse pointing to kid(s) if any.

    Args:
        dbuff (dictionary): member's record

    Returns:
        None: Null
    """
    global g_loc
    global g_single, all_members
    
    mem = dbuff['Name']
    born = dbuff['Born']
    
    filter = f"Name == @mem and Born == @born"
    rec = all_members.query(filter)
    log.debug(f"rec={rec}")
    if rec.empty:
        # This male-member not on file
        raise(FileNotFoundError)
    
    # Create a graph object with graphviz
    dot = gv.Digraph(name=mem,
                    comment=f"{mem}'s Graph",
                    engine = 'twopi')
    
    # set graph attributes
    dot.attr("graph", overlap="scalexy", layout='twopi')
    dot.attr("node", shape='circle')

    # Add member node
    mem_label = f"{mem}\n{born}-{dbuff['Died']}"
    if dbuff['Href'].startswith("http"):
        dot.node(mem, mem_label,
                shape='doubleoctagon', style='filled',
                href=dbuff['Href'])
    else:
        dot.node(mem, mem_label,
            shape='doubleoctagon', style='filled')

    # check if this male-member not married
    if rec.Status.iloc[0] == g_single:
        # single
        return dot
    
    # iterating this male-member list of spouses
    cnt_sp = len(rec.Spouse.index)
    for i, w in zip(range(cnt_sp), rec.Spouse):
        married = rec.Married.iloc[i]
        filter = f"Name == @w and Spouse == @mem"
        rec_sp = all_members.query(filter)
        if rec_sp.empty:
            # spouse info is not on file
            spouse_label = f"{w}\n{g_loc['MEMBER_NOT_REG']}\n{g_loc['MARRIED_IN']}{married}"
            href = ""
        else:
            # spouse info exists            
            born = rec_sp.Born.iloc[0]
            died = rec_sp.Died.iloc[0]
            spouse_label = f"{w}\n{born}-{died}\n{g_loc['MARRIED_IN']}{married}"
            href = rec_sp.Href.iloc[0]
        if href.startswith("http"):
            dot.node(w, spouse_label, 
                    {'color':'aquamarine', 'style':'filled'},
                    href=href)
        else:
            dot.node(w, spouse_label, 
                    {'color':'aquamarine', 'style':'filled'})
        
        # Add edges from Dad to Mom
        dot.attr("edge", color="red")
        dot.edge(dbuff['Name'], w, label=g_loc['REL_MARRIED'])

        # search for any kids, whose Mom is 'w'
        filter = f"Mom == @w"
        kids = all_members.query(filter)
        if kids.empty:
            # no kids associated with this Mom
            continue # to the next spouse
        # found kids
        # drop duplicated rows with the same name, and birth-year
        kids =kids.drop_duplicates(subset=['Name','Born'], 
                keep='first')
        # add nodes for kids, associated with this Mom
        with dot.subgraph() as s:
            s.attr(rank='same')
            
            # loop thru the list of kids
            for k in kids.Name:
                # search for right kid
                filter = f"Name == @k and Dad == @dbuff['Name'] and Mom == @w"
                rec_k = all_members.query(filter)
                if rec_k.empty:
                    # kid's info not on file
                    href = ""
                    continue    # to the next kid                 
                else:
                    # kid's info found
                    born = rec_k.Born.iloc[0]
                    died = rec_k.Died.iloc[0]
                    rel = rec_k.Relation.iloc[0]
                    kid_label = f'{k}\n{born}-{died}'
                    href = rec_k.Href.iloc[0]
                
                # add kid node
                if href.startswith("http"):
                    dot.node(k, kid_label, shape='box',
                             href=href)
                else:
                    dot.node(k, kid_label, shape='box')
                    
                # join the subgraph
                s.node(k)
                    
                # Add directed edge from Mom to kid
                if g_lrelation[rel] == g_loc['REL_ADOPT']:
                    dot.attr("edge", color="green")
                    dot.edge(w, k, label=g_loc['REL_ADOPT'])
                elif g_lrelation[rel] == g_loc['REL_STEP']:
                    dot.attr("edge", color="blue")
                    dot.edge(w, k, label=g_loc['REL_STEP'])
                else:
                    dot.attr("edge", color="black")
                    dot.edge(w, k, label=g_loc['REL_BIO'])
    
                # check if kid not married
                if rec_k.Status.iloc[0] == g_single:
                    # single
                    continue # to the next kid
                
                # This kid not single, iterating married kid's spouse list
                cnt_kw = len(rec_k.Spouse.index)
                for i, kw in zip(range(cnt_kw), rec_k.Spouse):
                    # find out marriage-year
                    married = rec_k.Married.iloc[i]
                    
                    # search for kid's spouse
                    filter = f"Name == @kw and Spouse == @k"
                    rec_kw = all_members.query(filter)
                    if rec_kw.empty:
                        # kid's spouse info not registered, skip
                        continue
                    else:
                        born = rec_kw.Born.iloc[0]
                        died = rec_kw.Died.iloc[0]
                        spouse_label = f"{kw}\n{born}-{died}\n{g_loc['MARRIED_IN']}{married}"
                        href = rec_kw.Href.iloc[0]
                        
                        # Add kid's spouse node
                        if href.startswith("http"):
                            dot.node(kw, spouse_label, 
                                    color='lightblue', 
                                    style='filled',
                                    href=href)
                        else:
                            dot.node(kw, spouse_label, 
                                    color='lightblue', style='filled')
                        # join the subgraph
                        s.node(kw)
        
                        # Add directed edge from kid to kw
                        dot.attr("edge", color="red")
                        dot.edge(k, kw, label = g_loc['REL_MARRIED'])
    return dot

# Display the basic info about member's Dad(s) via Streamlit                
def display_dad(dmem):
    """
    Display the basic info about member's Dad(s) via Streamlit
    Args:
        dmem: dict obj containing member info
    Return:
        None
    """
    global all_members, bio_members, adopt_members, step_members
    global g_loc, g_lrelation

    mem = dmem['Name']
    born = dmem['Born']
    dad_name = dmem['Dad']
    rel = dmem['Relation']
    if dad_name == "?":
        # Dad's info not registered
        desc = f"#### => {g_loc['DAD']}({g_loc['REL_BIO']}): {dad_name} {g_loc['MEMBER_NOT_REG']}"
        st.markdown(desc)
        return
    
    # retrieve bio-Dad info
    if rel == g_lrelation.index(g_loc['REL_BIO']):
        bio_dad_name = dad_name
    else:
        # locate bio-Dad's name
        filter = f"Name == @mem"
        dads = bio_members.query(filter)
        if dads.empty:
            # Member's info not registered
            desc = f"#### => {g_loc['DAD']}({g_loc['REL_BIO']}): {mem} {g_loc['MEMBER_NOT_REG']}"
            st.markdown(desc)
            return
        else:  
            bio_dad_name = dads.Dad.iloc[0]

    filter = f"Name == @bio_dad_name"
    dads = all_members.query(filter)
    if dads.empty:
        # Dad's info not registered
        desc = f"#### => {g_loc['DAD']}({g_loc['REL_BIO']}): {bio_dad_name} {g_loc['MEMBER_NOT_REG']}"
    else:        
        # bio-Dad's info found
        born = dads.Born.iloc[0]
        died = dads.Died.iloc[0]
        dad_label = f'{bio_dad_name} {born}-{died}'
        dad_href = dads.Href.iloc[0]
        desc = f"#### => {g_loc['DAD']}({g_loc['REL_BIO']}): [{dad_label}]({dad_href})"
    st.markdown(desc)
    
    # setup filter for extra Dads?
    filter = f"Name == @mem"
    
    # adopted-Dad?
    if adopt_members.empty != True:
        dads = adopt_members.query(filter)
        if dads.empty != True:
            # display adopted-Dad
            st.markdown(f"#### => {g_loc['DAD']}({g_loc['REL_ADOPT']}): {dads.Dad.iloc[0]}")
    
    # step-Dad?   
    if step_members.empty != True:
        dads = step_members.query(filter)
        if dads.empty != True:
            # display step-Dad
            st.markdown(f"#### => {g_loc['DAD']}({g_loc['REL_STEP']}): {dads.Dad.iloc[0]}")       
    
    return

# Display the basic info about member's Mom(s) via Streamlit
def display_mom(dmem):
    """
    Display the basic info about member's Mom(s) via Streamlit
    Args:
        dmem: dict obj about member
    Return:
        None
    """
    global all_members, bio_members, adopt_members, step_members
    global g_loc, g_lrelation

    mem = dmem['Name']
    born = dmem['Born']
    mom_name = dmem['Mom']
    rel = dmem['Relation']
    if mom_name == "?":
        # Mom's info not registered
        desc = f"#### => {g_loc['MOM']}({g_loc['REL_BIO']}): {mom_name} {g_loc['MEMBER_NOT_REG']}"
        st.markdown(desc)
        return
    
    # retrieve bio-Mom info
    if rel == g_lrelation.index(g_loc['REL_BIO']):
        bio_mom_name = mom_name
    else:
        # locate bio-Mom's name
        filter = f"Name == @mem"
        moms = bio_members.query(filter)
        if moms.empty:
            # Member's info not registered
            desc = f"#### => {g_loc['MOM']}({g_loc['REL_BIO']}): {mem} {g_loc['MEMBER_NOT_REG']}"
            st.markdown(desc)
            return
        else:  
            bio_mom_name = moms.Mom.iloc[0]

    filter = f"Name == @bio_mom_name"
    moms = all_members.query(filter)
    if moms.empty:
        # Mom's info not registered
        desc = f"#### => {g_loc['MOM']}({g_loc['REL_BIO']}): {bio_mom_name} {g_loc['MEMBER_NOT_REG']}"
    else:        
        # bio-Mom's info found
        born = moms.Born.iloc[0]
        died = moms.Died.iloc[0]
        mom_label = f'{bio_mom_name} {born}-{died}'
        mom_href = moms.Href.iloc[0]
        desc = f"#### => {g_loc['MOM']}({g_loc['REL_BIO']}): [{mom_label}]({mom_href})"
    st.markdown(desc)
    display_kids(bio_mom_name)
    
    # setup filter for extra Moms    
    filter = f"Name == @mem"

    # adopted-Mom?
    if adopt_members.empty != True:
        moms = adopt_members.query(filter)
        if moms.empty != True:
            mom_name = moms.Mom.iloc[0]
            # check if adopted-Mom is bio-Mom or not
            if mom_name != bio_mom_name:
                # display adopted-Mom
                st.markdown(f"#### => {g_loc['MOM']}({g_loc['REL_ADOPT']}): {mom_name}")
    
    # step-Mom?   
    if step_members.empty != True:
        moms = step_members.query(filter)
        if moms.empty != True:
            mom_name = moms.Mom.iloc[0]
            # check if adopted-Mom is bio-Mom or not
            if mom_name != bio_mom_name:
                # display step-Mom
                st.markdown(f"#### => {g_loc['MOM']}({g_loc['REL_STEP']}): {mom_name}")       
    return

# Display the basic info about member's Spouse via Streamlit
def display_spouse(dmem):
    # Args:
    #     dmem: dict obj about member
    # Return:
    #     None
    global all_members
    global g_loc

    mem = dmem['Name']
    born = dmem['Born']
    sp_name = dmem['Spouse']
    married = dmem['Married']
    
    # skip if member is still single
    if dmem['Status'] == g_single:
        # member is single, no Spouse found
        return
    
    # member not single, find the list of Spouses
    # get the basic info of spouse
    filter = f"Name == @sp_name and Spouse == @mem"
    rec_sp = all_members.query(filter)
    if rec_sp.empty:
        # spouse info not found
        desc = f"#### => {g_loc['SPOUSE']}: {sp_name} {g_loc['MEMBER_NOT_REG']}"
        st.markdown(desc)
    else:
        # Spouse info exists
        born = rec_sp.Born.iloc[0]
        died = rec_sp.Died.iloc[0]
        spouse_label = f'{sp_name} {born}-{died}'
        spouse_href = rec_sp.Href.iloc[0]
        desc = f"#### => {g_loc['SPOUSE']}：[{spouse_label}]({spouse_href})"

        # display kids if female 
        sp_sex = g_lsex[rec_sp.Sex.iloc[0]]
        if  sp_sex != g_loc['SEX_MALE'] and sp_sex != g_loc['SEX_INLAW_MALE']:
            married = rec_sp.Married.iloc[0]
            desc = desc + f", {g_loc['MARRIED_IN']}{married}"
            st.markdown(desc)
            display_kids(sp_name)
        else:
            st.markdown(desc) 
    return

# Display the basic info about kids who are bilogically 
# related to Mom via Streamlit.
def display_kids(w):
    # Args:
    #     w: mom-name
    # Return:
    #     None

    global all_members
    global g_loc
    
    # search for kids whose Mom has the name, called 'w'
    filter = f"Mom == @w"
    kids = all_members.query(filter)
    if kids.empty:
        # no kids found
        return
    
    # Kids found
    # drop duplocated row with the same name, birth-year and relation
    kids = kids.drop_duplicates(subset=['Name', 'Born', 'Relation'], 
                keep='first')

    # loop thru to retrieve kid's info
    cnt_k = len(kids.index)
    for i, k in zip(range(cnt_k), kids.Name):
        born = kids.Born.iloc[i]
        died = kids.Died.iloc[i]
        kid_sex = g_lsex[kids.Sex.iloc[i]]
        kid_rel = g_lrelation[kids.Relation.iloc[i]]
        kid_label = f'{k} {born}-{died}'
        kid_href = kids.Href.iloc[i]
        
        # associate different emoji with both male and female
        if kid_sex == g_loc['SEX_MALE'] or kid_sex == g_loc['SEX_INLAW_MALE']:
            # kid is male
            desc = f"#### ===> :sunglasses: ({kid_rel}): [{kid_label}]({kid_href})"
        else:
            # kid is female
            desc =f"#### ===> :last_quarter_moon_with_face: ({kid_rel}): [{kid_label}]({kid_href})"
        
        # display kid's info
        st.markdown(desc)
    return

# Display a list of members who are related to members who are within
# three generations via Streamlit.      
def display_3gen(dmem):
    """ 
    Display a list of members who are related across three generations 
        via Streamlit, given by member dict object.
    Each member displays basic info about member, Dad, Mom, and
        Spouse, which is formated as a string, consisting of:
        1. name, 
        2. 'birth-deadth'-years
        3. associated URL 
    In case of female spouse, if any, the marriage year will be added. 
        And followed by all the basic info of her kids.
    """
    global g_loc
    global g_lsex

    mem = dmem['Name']
    born = dmem['Born']
    # format the basic info about member
    mem_label = f"{mem} {born}-{dmem['Died']}"
    desc = f"### {mem_label} [{dmem['Href']}]({dmem['Href']})"
    
    # if given member is not male, show extra info:
    #   1. her marriage year 
    #   2. associated kids if any
    msex = g_lsex[dmem['Sex']]
    if msex != g_loc['SEX_MALE'] and msex != g_loc['SEX_INLAW_MALE']:
        desc = desc + f", {g_loc['MARRIED_IN']}{dmem['Married']}"
        st.markdown(desc)
        # search for her kids to display
        display_kids(mem)
    else:
        st.markdown(desc)

    display_dad(dmem)    
    display_mom(dmem)    
    display_spouse(dmem)       
    return

# Display the detail info about member via Streamlit.
def display_update_member(dbuff):
    # Args:
    #     dbuff: a dict object about the member
    # On the web page, 
    #     1. display fields, arranged in row-column layout.
    #     2. Solicitate user for an update
    
    # Return:
    #     return the modified 'dbuff' dict obj
    global g_loc
    
    # row 1
    c11, c12, c13 = st.columns([3,3,1])
    dbuff["Name"] = c11.text_input(f":blue[{g_loc['L311_FULL_NAME']}]", 
        dbuff["Name"], 
        max_chars=20, 
        help=g_loc['L311_HELP'])
    dbuff["Aka"] = c12.text_input(f":blue[{g_loc['L312_ALIAS']}]", 
        dbuff["Aka"],
        max_chars=60,                             
        help=g_loc['L312_HELP'])

    rec_sex = c13.selectbox(f":blue[{g_loc['L313_SEX']}]", 
        options=g_lsex, 
        index=int(dbuff["Sex"]),
        help=g_loc['L313_HELP'])
    dbuff["Sex"] = g_lsex.index(rec_sex)
    
    # row 2
    c21, c22, c23 = st.columns([3,2,2])
    dbuff["Order"] = c21.text_input(f":blue[{g_loc['L321_GEN_ID']}]", 
        dbuff["Order"],
        max_chars=10,
        help=g_loc['L321_HELP'])
    dbuff["Born"] = c22.text_input(f":blue[{g_loc['L322_BIRTH_YEAR']}]", 
        dbuff["Born"],
        max_chars=10,
        help=g_loc['L322_HELP'])
    dbuff["Died"] = c23.text_input(f":blue[{g_loc['L323_DEATH_YEAR']}]", 
        dbuff["Died"],
        max_chars=10,
        help=g_loc['L323_HELP'])
    
    # row 3
    c31, c32, c33 = st.columns([3,3,1])
    dbuff["Dad"] = c31.text_input(f":blue[{g_loc['L331_DAD_NAME']}]", 
        dbuff["Dad"], 
        max_chars=20,
        help=g_loc['L331_HELP'])
    dbuff["Mom"] = c32.text_input(f":blue[{g_loc['L332_MOM_NAME']}]", 
        dbuff["Mom"], 
        max_chars=20,
        help=g_loc['L332_HELP'])
    rec_rel = c33.selectbox(f":blue[{g_loc['L333_RELATION']}]", 
        options=g_lrelation,
        index=int(dbuff["Relation"]),
        help=g_loc['L333_HELP'])
    dbuff["Relation"] = g_lrelation.index(rec_rel)
    
    # row 4
    c41, c42, c43 = st.columns([2,3,2])
    rec_status = c41.selectbox(f":blue[{g_loc['L341_STATUS']}]", 
        options=g_lstatus,
        index=int(dbuff["Status"]),
        help=g_loc['L341_HELP'])
    dbuff["Status"] = g_lstatus.index(rec_status)
    
    dbuff["Spouse"] = c42.text_input(f":blue[{g_loc['L342_SPOUSE']}]",
        dbuff["Spouse"],
        max_chars=20,
        help=g_loc['L342_HELP'])
    
    dbuff["Married"] = c43.text_input(f":blue[{g_loc['L343_MARRIAGE_YEAR']}]",
        dbuff["Married"],
        max_chars=20,
        help=g_loc['L343_HELP'])
    
    # row 5
    c51, _ = st.columns([6,1])
    dbuff["Href"] = c51.text_input(f":blue[{g_loc['L351_URL']}]", 
        dbuff["Href"], 
        max_chars=120,
        help=g_loc['L351_HELP'])   

# Return a Pandas dataframe obj
def get_gen(gen_begin, num):
    """ 
    Return a Pandas dataframe obj, containing 
        from given 'gen_begin' generation, to ('num'-1) generations below.
        
    The returned dataframe is sorted by gen id (Order), birth-year (Born).   
    
    Raise 'FileNotFoundError' if not found.
    """
    gen_end = gen_begin + num
    
    # build filter
    filter = f"Order >= @gen_begin and Order <= @gen_end"
    target_members = all_members.query(filter)
    if target_members.empty:
        # no members found in this generation
        raise(FileNotFoundError)

    target_members = target_members.sort_values(['Order', 'Born'])
    return target_members                                

# A generator function, yielding an unique member at a time, 
# given a member-name. 
def get_umember(name, spouse='?', dad='?', mom='?', born='0', order='0'):
    # The selection criteria might include 
    # the following five optional attributes:
    #     1. Spouse-name (optional)
    #     2. Dad-name (optional)
    #     3. Mom-name (optional)
    #     4. Birth-year (optional)
    #     5. Generation-order (optional)
    # Args:
    #     name (mandatory): member-name
    #     spouse (optional): spouse-name
    #     dad (optional): Dad's name, default '?'
    #     mom (optional): Mom's name, default '?'
    #     born (optional): birth-year, default '0'
    #     order (optional): generation-order, default '0'
    # Usecases:
    #     1. To iterate members of the same name is needed.
    #     2. To iterate relations of a given member-name is required.
    # Return:
    #   A member (row index and its associated dict obj) at a time,
    #   or 'FileNotFoundError' if not found

    global all_members, g_loc
    
    # build filter
    filter = f"Name == @name"
    if spouse != '?':
        filter = filter  + f" and Spouse == @spouse" 
    if dad != '?':
        filter = filter  + f" and Dad == @dad"  
    if mom != '?':
        filter = filter + f" and Mom == @mom"
    if born != '0':
        born = int(born)
        filter = filter + f" and Born == @born"
    if order != '0':
        order = int(order)
        filter = filter + f" and Order == @order"
    
    # retrieve matched members into a dataframe
    rec = all_members.query(filter)
    if rec.empty:
        raise(FileNotFoundError)

    didx = rec.to_dict('index')
    for i in didx:
        # yield one member (row index and its dictionary) at a time
        yield i, didx[i]
    
# --- Main Web Widget --- from here
@func_timer_decorator
def main_page(lname_idx, dbuff):
    global g_username, g_nav, g_lname
    global g_loc, g_loc_key, g_L10N_options, g_L10N
    global g_df
    global g_fTree, g_path_dir
    global g_dirtyUser, g_dirtyTree
    
    # Upon selecting a side-bar function, 
    # take an action accordingly by 
    # displaying output on the main widget 
    
    # --- Function 1 --- from here
    # display a family graph by male-member
    if g_nav == g_loc['MENU_DISP_GRAPH_BY_MALE']:
        # display a family graph starting from a male-member 
        # selected with associated spousees who have related kids

        st.subheader(g_loc['T1_DISP_GRAPH_BY_MALE'])
        
        if lname_idx <= 1:
            # at least 2 generations
            st.error(f"{g_loc['MENU_DISP_GRAPH_BY_MALE']} {g_loc['QUERY']} {g_loc['MEMBER_NOT_FOUND']}")
            return g_nav
        
        # select a generation
        max_gen = dbuff['Order'] 
        
        default_gen = load_male_gen(g_lname, base=g_dirtyTree)

        fgen = st.slider(g_loc['S1_GEN_ORDER'], 
                        1, 
                        max_gen, default_gen,
                        help=g_loc['S1_HELP'])
        
        c11, c12 = st.columns([5,5])
        fborn1 = c11.slider(g_loc['S1_BORN_FROM'], 
                        0, 
                        2050, 1950,
                        step=10,
                        help=g_loc['S1_HELP'])
        
        fborn2 = c12.slider(g_loc['S1_BORN_TO'], 
                        0, 
                        2050, 2000,
                        step=10,
                        help=g_loc['S1_HELP'])
        
        try:
            # build a male list, given selected generation
            lname = slice_male_list(fgen, fborn1, fborn2, base=g_dirtyTree)
            lname_idx = len(lname) - 1
            tmem = st.selectbox(g_loc['L1_SELECTBOX'],
                                        options=lname, 
                                        index=lname_idx,
                                        help=g_loc['L1_HELP'])
            log.debug(f"tmem={tmem}")
            order, mem, born = tmem
            lname_idx = lname.index(tmem)
            try:
                # _, dbuff = get_1st_mbr_dict(g_df, mem, born)
                memgen = get_umember(mem, 
                                    order=order,
                                    born=born)
                for idx, dbuff in memgen:
                    mem = dbuff['Name']
                    born = dbuff['Born']
                    order = dbuff['Order']
                    sex = g_lsex[dbuff['Sex']]
                    st.markdown(f"#### {g_loc['GEN_ORDER']}: {order} {g_loc['MEMBER']}{g_loc['INDEX']}: {idx} {mem}({born},{sex})")
                    break
                # build the graph using the first member got
                log.debug(f"dbuff={dbuff}")
                dot = build_spouse_graph(dbuff)                        
            except:
                st.error(g_loc['MEMBER_NOT_FOUND'])
                return g_nav
                        
            # Show graph on Streamlit Page
            log.debug(dot.source)
            st.graphviz_chart(dot,
                    use_container_width = True)
        except:
            st.warning(g_loc['MEMBER_NOT_FOUND'])
            # continue to adjust sliders
                
        st.success(f"{g_loc['MENU_DISP_GRAPH_BY_MALE']} {g_loc['QUERY']} {g_loc['DONE']}")
        return g_nav      
        
    # --- Function 2 --- from here
    # list a family info by male-member    
    if g_nav == g_loc['MENU_QUERY_3G_BY_MALE']:
        # list immediate family basic info with respect to a 
        # given a tuple (male-member -name, birth-year)
        st.subheader(g_loc['T2_QUERY_3G_BY_MALE'])
        
        if lname_idx <= 1:
            # at least 2 generations
            st.error(f"{g_loc['MENU_QUERY_3G_BY_MALE']} {g_loc['QUERY']} {g_loc['MEMBER_NOT_FOUND']}")
            return g_nav
        
        # select a generation
        max_gen = dbuff['Order'] 
        
        default_gen = load_male_gen(g_lname, base=g_dirtyTree)

        fgen = st.slider(g_loc['S1_GEN_ORDER'], 
                        1, 
                        max_gen, default_gen,
                        help=g_loc['S1_HELP'])

        c11, c12 = st.columns([5,5])
        fborn1 = c11.slider(g_loc['S1_BORN_FROM'], 
                        0, 
                        2050, 1950,
                        step=10,
                        help=g_loc['S1_HELP'])
        
        fborn2 = c12.slider(g_loc['S1_BORN_TO'], 
                        0, 
                        2050, 2000,
                        step=10,
                        help=g_loc['S1_HELP'])
        
        try:
            # build a male list, given selected generation
            lname = slice_male_list(fgen, fborn1, fborn2, base=g_dirtyTree)
            lname_idx = len(lname) - 1
            tmem = st.selectbox(g_loc['L1_SELECTBOX'],
                                        options=lname, 
                                        index=lname_idx,
                                        help=g_loc['L1_HELP'])
            order, mem, born = tmem
            lname_idx = lname.index(tmem)
            
            try:
                # _, dbuff = get_1st_mbr_dict(g_df, mem, born)
                memgen = get_umember(mem, 
                                    order=order,
                                    born=born)
                for idx, dbuff in memgen:
                    mem = dbuff['Name']
                    born = dbuff['Born']
                    order = dbuff['Order']
                    sex = g_lsex[dbuff['Sex']]
                    st.markdown(f"#### {g_loc['GEN_ORDER']}: {order} {g_loc['MEMBER']}{g_loc['INDEX']}: {idx} {mem}({born},{sex})")
                    break
            except:
                st.error(f"{g_loc['MENU_QUERY_3G_BY_MALE']} {g_loc['QUERY']} {g_loc['FAILED']}")
                return g_nav
            
            # display current generation, plus one level up and down
            display_3gen(dbuff)
            st.success(f"{g_loc['MENU_QUERY_3G_BY_MALE']} {g_loc['QUERY']} {g_loc['DONE']}")
            return g_nav      
        except:
            st.warning(g_loc['MEMBER_NOT_FOUND'])
            # continue to adjust sliders
    
    # --- Function 3 --- from here
    # add a new Family Member
    if g_nav == g_loc['MENU_MEMBER_ADD']:
        st.subheader(g_loc['T3_MEMBER_ADD'])
        
        display_update_member(dbuff)
        
        if st.button(g_loc['B3_MEMBER_ADD']):
            with st.spinner(g_loc['IN_PROGRESS']):
            
                st.write(f"{g_loc['MENU_MEMBER_ADD']}: {dbuff['Name']}")

                # create a dict object with list values from buffer 'dbuff' 
                to_add = {key: [value] for key, value in dbuff.items()}
                
                # convert dictionary to dataframe
                to_add = pd.DataFrame.from_dict(to_add)
                try:
                    # append to the end of family tree
                    to_add.to_csv(g_fTree,
                                mode='a',
                                header = False,
                                index= False)
                    st.success(f"{g_loc['MENU_MEMBER_ADD']}: {dbuff['Name']} {g_loc['ADD']} {g_loc['DONE']}")
                    # force to create a new tree cache upon return
                    os.environ['DIRTY_TREE'] = str(time.time())
                except:
                    st.error(f"{g_loc['MENU_MEMBER_ADD']}: {dbuff['Name']} {g_loc['ADD']} {g_loc['FAILED']}")        
        return g_nav      
  
    # --- Function 4 --- from here
    # update an existed Family Member
    if g_nav == g_loc['MENU_MEMBER_UPDATE']:
        # update an existed Family Member
        # given by the member index of dataframe
        st.subheader(g_loc['T4_MEMBER_UPDATE'])
        
        default_gen = dbuff['Order']
    
        idx = st.text_input(f":blue[{g_loc['L41_MEMBER_INDEX']}]",
            default_gen,
            max_chars=10,
            help=g_loc['L41_HELP'])
        
        # Target Series obj, identified by 'idx'
        idx = int(idx)
        try:
            # safe guard person not found
            rcd = g_df.iloc[idx]
        except:
            st.error(f"{g_loc['MEMBER_NOT_FOUND']}") 
            return g_nav      
        
        # convert to dict buffer
        dbuff = {key: value for key, value in rcd.items()}
               
        display_update_member(dbuff)
        
        st.info(f"{g_loc['MEMBER']}{g_loc['INDEX']}: {idx} {dbuff['Name']} {g_loc['L42_CONFIRM_UPDATE']}")
        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button(g_loc['B4_MEMBER_UPDATE']):
                with st.spinner(g_loc['IN_PROGRESS']):
                    # To update a row, by index with a dict obj 'dbuff'
                    g_df.loc[idx] = dbuff
                    try:
                        # backup the current family tree
                        os.rename(g_fTree, g_fTree_Backup)
                        
                        # create a new family tree
                        g_df.to_csv(g_fTree,
                                    mode='w',
                                    header = True,
                                    index= False)
                        # force to create a new tree cache upon return
                        os.environ['DIRTY_TREE'] = str(time.time())
                        
                        st.success(f"{g_loc['MEMBER']}{g_loc['INDEX']}: {idx} {dbuff['Name']} {g_loc['UPDATE']} {g_loc['DONE']}")
                    except:
                        st.error(f"{g_loc['MEMBER']}{g_loc['UPDATE']} {g_loc['FAILED']}")        
        with btn2: 
            if st.button(g_loc['B4_MEMBER_DELETE']):
                with st.spinner(g_loc['IN_PROGRESS']):
                    # To drop a row, by index
                    g_df.drop([idx], inplace=True)
                    
                    try:
                        # backup the current family tree
                        os.rename(g_fTree, g_fTree_Backup)
                        
                        # create a new family tree
                        g_df.to_csv(g_fTree,
                                    mode='w',
                                    header = True,
                                    index= False)
                        # force to create a new tree cache upon return
                        os.environ['DIRTY_TREE'] = str(time.time())
                        
                        st.success(f"{g_loc['MEMBER']} {g_loc['INDEX']}: {idx} {dbuff['Name']} {g_loc['DELETE']} {g_loc['DONE']}")
                    except:
                        st.error(f"{g_loc['MEMBER']}{g_loc['DELETE']} {g_loc['FAILED']}")        
                
        return g_nav      

    # --- Function 5 --- from here
    # inquire the basic info across 3 generations by mamber-name
    if g_nav == g_loc['MENU_QUERY_TBL_BY_NAME']:
        # ALl member detail info of three generations, 
        #     given by any member name of the middle generation.

        st.subheader(g_loc['T5_QUERY_TBL_BY_NAME'])
        
        rec_name = st.text_input(g_loc['L51_FULL_NAME'], 
                dbuff['Name'], 
                max_chars=20, 
                help=g_loc['L51_HELP'])
                
        if st.button(g_loc['B5_MEMBER_INQUERY']):
            with st.spinner(g_loc['IN_PROGRESS']): 
                filter = f"Name == @rec_name"
                df2 = g_df.query(filter)
                if df2.empty:
                    st.error(f"{rec_name} {g_loc['MENU_QUERY_TBL_BY_NAME']} {g_loc['FAILED']}")
                else:  
                    st.table(df2)
                    st.success(f"{rec_name} {g_loc['MENU_QUERY_TBL_BY_NAME']} {g_loc['DONE']}")                  
        return g_nav      

    # --- Function 6: --- from here   
    # inquire the detail info of members by alias(es)
    if g_nav == g_loc['MENU_QUERY_TBL_BY_ALIAS']:
        st.subheader(g_loc['T6_QUERY_TBL_BY_ALIAS'])
        
        rec_aka = st.text_input(g_loc['L61_ALIAS'], 
                    dbuff['Name'], 
                    max_chars=120, 
                    help=g_loc['L61_HELP'])
                    
        if st.button(g_loc['B6_MEMBER_INQUERY']):
            with st.spinner(g_loc['IN_PROGRESS']):
                l_grp = rec_aka.split(',')
                filter = "Aka in ("
                for w in l_grp:
                    # strip off leading and trailing spaces
                    kw = w.strip()
                    filter = filter + f"'{kw}',"
                    
                # finally, strip off the last ','
                rec_grp = filter.strip(',') + ")"
                df2 = g_df.query(rec_grp)
                if df2.empty:
                    st.error(f"{g_loc['MENU_QUERY_TBL_BY_ALIAS']} {g_loc['FAILED']}")
                else:   
                    st.table(df2)
                    st.success(f"{g_loc['MENU_QUERY_TBL_BY_ALIAS']} {g_loc['DONE']}")              
        return g_nav      

    # --- Function 7 --- from here
    # inquire the detail info of members by generation-id
    if g_nav == g_loc['MENU_QUERY_TBL_BY_1GEN']:
        st.subheader(g_loc['T7_QUERY_TBL_BY_1GEN'])
        
        st.markdown(f"{g_loc['HEAD_COUNT_TOTAL']}{len(bio_members.index)}")
        st.markdown(f"{g_loc['HEAD_COUNT_MALE']}{len(m_members.index)}")
                
        # set an upper bound above the max gen order
        max_gen = dbuff['Order'] + 1
        if max_gen <= 0:
            # at least 1 generation
            st.error(f"{g_loc['MENU_QUERY_TBL_BY_1GEN']} {g_loc['QUERY']} {g_loc['MEMBER_NOT_FOUND']}")
            return g_nav
            
        default_gen = load_male_gen(g_lname, base=g_dirtyTree)

        gen = st.slider(g_loc['S1_GEN_ORDER'], 
                        1, 
                        max_gen, default_gen,
                        help=g_loc['S1_HELP'])
        
        st.markdown(f"{g_loc['L711_GEN_FROM']} {gen} {g_loc['L712_GEN_TO']}")
        try:
            # list current generation
            g1_members = get_gen(gen, 0)
            st.markdown(f"{g_loc['HEAD_COUNT_SELECTED']}{len(g1_members.index)}")
            st.table(g1_members)
            st.success(f"{g_loc['MENU_QUERY_TBL_BY_1GEN']} {g_loc['DONE']}")        
        except:
            st.error(g_loc['INFO_NOT_FOUND'])        
        return g_nav      
    
    # --- Function 8 --- from here
    # inquire the basic info of members by member-name etc.
    if g_nav == g_loc['MENU_QUERY_3G_BY_NAME']:
        # inquire the basic info of members by member-name (mandatory)
        # and two optional attributes:
        # 1. bith-year,
        # 2. spouse

        st.subheader(g_loc['T8_QUERY_3G_BY_NAME'])

        
        rec_name = st.text_input(g_loc['L81_ENTER_NAME'], 
                    dbuff['Name'], 
                    max_chars=20, 
                    help=g_loc['L81_HELP'])
        
        c11, c12 = st.columns([4,6])
        
        rec_born = c11.text_input(g_loc['L82_ENTER_BORN'],
                    "0", 
                    max_chars=20, 
                    help=g_loc['L82_HELP'])
        
        rec_spouse = c12.text_input(g_loc['L83_ENTER_SPOUSE'], 
                    "?",
                    help=g_loc['L83_HELP'])
                
        if st.button(g_loc['B8_QUERY_3G']):
            try:
                memgen = get_umember(rec_name, 
                                spouse=rec_spouse,
                                born=rec_born)
                for idx, dmem in memgen:
                    mem = dmem['Name']
                    born = dmem['Born']
                    order = dmem['Order']
                    sex = g_lsex[dmem['Sex']]
                    st.markdown(f"#### {g_loc['GEN_ORDER']}:{order} {g_loc['MEMBER']}{g_loc['INDEX']}:{idx} {mem}({born}, {sex})")
                    display_3gen(dmem)
                    st.markdown("---")    

                st.success(f"{rec_name} {g_loc['MENU_QUERY_3G_BY_NAME']} {g_loc['DONE']}")
            except:
                st.error(f"{rec_name} {g_loc['MENU_QUERY_3G_BY_NAME']} {g_loc['FAILED']}")
        return g_nav      

    # --- Function 9 --- from here
    # list the detail info of 3-generation view
    if g_nav == g_loc['MENU_QUERY_TBL_BY_3GEN']:
        # list the detail info of 3-generation view, given by 
        # member-name                  
        st.subheader(g_loc['T9_QUERY_TBL_BY_3GEN'])
        
        st.markdown(f"{g_loc['HEAD_COUNT_TOTAL']}{len(bio_members.index)}")
        st.markdown(f"{g_loc['HEAD_COUNT_MALE']}{len(m_members.index)}")
                
        # select a begining generation and list 2 generations below
        max_gen = dbuff['Order'] 
        if max_gen <= 1:
            # at least 2 generations
            st.error(f"{g_loc['MENU_QUERY_TBL_BY_3GEN']} {g_loc['QUERY']} {g_loc['MEMBER_NOT_FOUND']}")
            return g_nav
        
        default_gen = load_male_gen(g_lname, base=g_dirtyTree)

        gen = st.slider(g_loc['S1_GEN_ORDER'], 
                        1, 
                        max_gen, default_gen,
                        help=g_loc['S1_HELP'])
        
        try:
            st.markdown(f"{g_loc['L911_GEN_FROM']} {gen} {g_loc['L912_GEN_TO']}")
            # current + 2 = 3 generations
            g3_members = get_gen(gen, 2)
            st.markdown(f"{g_loc['HEAD_COUNT_SELECTED']}{len(g3_members.index)}")
            st.table(g3_members)
            st.success(f"{g_loc['MENU_QUERY_TBL_BY_3GEN']} {g_loc['DONE']}")
        except:
            st.error(g_loc['INFO_NOT_FOUND'])       
        return g_nav   

    # --- Function 10 --- from here
    # Configure User Settings                  
    if g_nav == g_loc['MENU_SETTINGS']:
        # Three settings are supported:
        # 1. Update User setting: L10N
        # 2. Import CVS to merge into family tree
        # 3. Export current family tree to local 'Download' folder

        st.subheader(g_loc['T10_USR_SETTINGS'])
    
        # --- User L10N Settings --- from here 
        c1, c2 = st.columns([3,7])

        # User L10N setting   
        g_loc_key = c1.selectbox(f":blue[{g_loc['SX_L10N']}]", 
            options=g_L10N_options, 
            index=g_L10N_options.index(g_loc_key),
            help=g_loc['SX_L10N_HELP'])

        # enter CSV file name (no .csv) to export/download
        lexport = f":blue[{g_loc['BX_EXPORT_HELP']}]"
        filename = c2.text_input(lexport, 
            placeholder=g_loc['BX_EXPORT_HELP'])
        
        # --- User Export CSV --- from here
        # # enter file name to export
        with c2:
            with open(g_fTree) as f:
                fn = f"{filename}.csv"
                if c2.download_button(g_loc['BX_EXPORT'], f, f"{filename}.csv"):
                    st.success(f"{g_loc['BX_EXPORT']} {fn} {g_loc['DONE']}")
        
        # set L10N upon click 
        with c1:
            if st.button(g_loc['BX_USR_SETTINGS']):
                g_loc = g_L10N[g_loc_key]
                os.environ['L10N'] = g_loc_key
                try:
                    st.info(f"{g_loc_key}: {g_loc['LANGUAGE_MODE_AFTER_RELOAD']}")
                    
                    # force to create a new UserDB cache upon return
                    os.environ['DIRTY_USER'] = str(time.time())
                except Exception as err:
                    st.warning(f"Caught '{err}'. class is {type(err)}")
                    st.error(f"{g_loc['MENU_SETTINGS']} {g_username} {g_loc['FAILED']}")        

        # --- User Import CSV --- from here
        # drag and drop CSV file to import
        f = st.file_uploader(f":blue[{g_loc['BX_IMPORT_HELP']}]")
        
        # merge two family trees vertically upon click
        if st.button(g_loc['BX_IMPORT']):
            with st.spinner(g_loc['IN_PROGRESS']):
                df = pd.read_csv(f)
                if df.iloc[0].Name == "?":
                    # make sure Dataframe no placeholder row 
                    mbrs = df.drop(index=0)
                
                if mbrs.empty:
                    return g_nav # no merge needed
                    
                g_df = pd.concat([g_df, mbrs])
                
                # make sure no duplicates
                g_df.drop_duplicates(inplace=True)
                
                # sort in order by Gen-Order, Birth-year, and Name
                g_df.sort_values(by=['Order', 'Born', 'Name'],
                            inplace=True)

                try:
                    # backup existing current family tree
                    os.rename(g_fTree, g_fTree_Backup)
                    
                    # create new .csv family tree if exists
                    g_df.to_csv(g_fTree,
                                mode='w',
                                header = True,
                                index= False)
                    st.success(f"{g_loc['BX_IMPORT']} {g_loc['DONE']}")
                    
                    # force to create a new tree cache upon return
                    os.environ['DIRTY_TREE'] = str(time.time())
                    
                except:
                    st.error(f"{g_loc['BX_IMPORT']} {g_loc['FAILED']}")        
    return g_nav
          
# ---- READ Family Tree from CSV ----
# Clear all caches every 5 min = 300 seconds
@st.cache_data(ttl=300)
def get_data_from_csv(f, base=None):
    # Load the family tree from a CSV file, into a dataframe, 'g_df'.
    # and strip out the first record into a dataframe, 'all_members', 
    #   containing all family members, duplicated names included.
    # The first '?'-record, is a place-holder for non-registered 
    # (i.e. "?") members.
    try:
        fileCSV = open(f, 'r')
    except:
        # create a new CSV for new family admin
        with open(g_fTree_template, 'r') as temp:
            temp_contents = temp.read()
        with open(f, 'w') as ft:
            print(temp_contents, file=ft)
        log.debug(f"{f} not existed, CREATED a NEW family tree.")

    df = pd.read_csv(f)
    members = df.drop(index=0)
    log.debug(f"{f} LOADED.")
    log.debug(f"{df.tail(3)}")
    log.debug(f"{members.head(3)}")
 
    return df, members

# --- Selecting records from all family members --- from here
@st.cache_data(ttl=300)
def load_dataframe(members, rel, base=None):
    # return members in a Pandas Dataframe
    # whose key is defined as: Generation Order + Born 
    # (i.e. birth-year). Only first duplicated member is kept.

    filter = f"Relation == @rel"
    df1 = members.query(filter).sort_values(
        by=['Order','Born'])
    return df1

# --- Load up Male Members --- from here
@st.cache_data(ttl=300)
def load_male_gen(lname, base=None):
    # return the latest generation ordeer from male members list, 'lname'
    # assume lname is a ordered list of tuple, consisting of
    # (Generation-order, Member-name, Year-born)
    
    if not lname:
        return 0
    order, _, _ = lname[-1]
    return order

# --- Load up Male Members --- from here
@st.cache_data(ttl=300)
def slice_male_list(order, born1, born2, base=None):
    # return male members in a list, given by generation order, 'order'
    # The list consists of tuples with
    # (Generation-order, Member-name, Year-born)
    global g_lname
    
    lname = []
    born1 = int(born1)
    born2 = int(born2)
    for o, m, b in g_lname:
        b = int(b)
        if o == order and b >= born1 and b <= born2:
            lname.append((o, m, b))
    return lname

# --- Load up Male Members --- from here
@st.cache_data(ttl=300)
def load_male_members(members, base=None):
    # return male members in a dataframe, 'm_members', 
    # containing male-members, 
    # droping duplcated rows with the same 
    # generation order, name, and birth-year
    global g_loc, g_lsex

    m_members = members.drop_duplicates(subset=['Order','Name',
                                                'Dad', 'Born'], 
            keep='first')

    # sorted by birth-year in accending order.
    male1 =  g_lsex.index(g_loc['SEX_MALE'])
    male2 =  g_lsex.index(g_loc['SEX_INLAW_MALE'])
    
    m_members = m_members.query(
        "Sex == @male1 or Sex == @male2"
        ).sort_values(by=['Order', 'Born', 'Name'])

    # create the global name list of all male-members.
    g_lname = [(o, m, b) for o, m, b in zip(
        m_members.Order, m_members.Name, m_members.Born)] 
    return m_members, g_lname
     
# --- Load up User L10N --- from here
@st.cache_data(ttl=300)
def load_user_l10n(base=None):
        # --- Initialize System L10N Settings ---- from here
    # set system L10N setting as default locator key , 'g_loc_key'
    # and associated language dictionary, 'g_loc'
    
    g_loc_key = os.getenv("L10N")    
    g_loc = g_L10N[g_loc_key]
    return g_loc_key, g_loc

# --- Main Program --- from here
if __name__ == '__main__':
    st.empty()
        
    g_dirtyTree = os.getenv("DIRTY_TREE")    
    g_dirtyUser = os.getenv("DIRTY_USER")    
    
    # --- Set Server logging levels ---
    g_logging = os.getenv("LOGGING")
    log.setLevel(g_logging)      

    # --- global L10N dictionary --- from here
    # Load 'g_L10N', for all languages
    # Load global list, 'g_L10N_options', for all languages
    g_L10N = load_L10N(base=g_dirtyUser)
    g_L10N_options = list(g_L10N.keys())
    
    # --- Load User L10N --- from here
    g_loc_key, g_loc = load_user_l10n(base=g_dirtyUser)
    
    # logging check-points --- here
    log.debug(f"{g_loc['SVR_LOGGING']}: {g_logging}")
    log.debug(f"{g_loc['SVR_L10N']}: {g_loc_key}")
    log.debug(f"DIRTY_TREE: {g_dirtyTree}")
    log.debug(f"DIRTY_USER: {g_dirtyUser}")

    # Set default user's L10N settings
    g_username = "me"
    g_fullname = "Personal Edition"
    
    # Set user-specific L10N dict obj
    g_loc = g_L10N[g_loc_key]
    log.debug(f"{g_loc['SX_L10N']}: {g_loc_key}")

    # ---- SIDEBAR ---- from here
    # Define the title of sidebar widget
    g_SBAR_TITLE = f"{g_fullname}{g_loc['FAMILY_TREE']}\n---\n## {g_loc['WELCOME']} {g_fullname}"
    st.sidebar.title(g_SBAR_TITLE)
    
    # Show side-bar 9 functions
    g_nav = st.sidebar.radio(g_loc['MENU_TITLE'],
            [g_loc['MENU_DISP_GRAPH_BY_MALE'],
            g_loc['MENU_QUERY_3G_BY_MALE'],
            g_loc['MENU_MEMBER_ADD'],
            g_loc['MENU_MEMBER_UPDATE'],
            g_loc['MENU_QUERY_TBL_BY_NAME'],
            g_loc['MENU_QUERY_TBL_BY_ALIAS'],
            g_loc['MENU_QUERY_TBL_BY_1GEN'],
            g_loc['MENU_QUERY_3G_BY_NAME'],
            g_loc['MENU_QUERY_TBL_BY_3GEN'],
            g_loc['MENU_SETTINGS'],
            ])

    # ---- SIDEBAR ---- end here

    # Define global repository settings
    g_path_dir = "data"
    g_fTree = f"{g_path_dir}/{g_username}.csv"
    g_fTree_template = f"{g_path_dir}/template.csv"
    g_fTree_Backup = f"{g_path_dir}/{g_username}_bak.csv"

    g_df, all_members = get_data_from_csv(g_fTree, base=g_dirtyTree)        

    # Define global list, 'g_lview', used for inquery
    g_lview = [g_loc['VIEW_NAME'], 
                g_loc['VIEW_STATUS'], 
                g_loc['VIEW_RECORD']]
    
    # Define global list, 'g_lsex', containing member sex info
    # NOTE: The list order must NOT be changed, 
    #   since the list index is used to store in the family tree.
    g_lsex = [g_loc['SEX_MALE'], 
                g_loc['SEX_FEMALE'], 
                g_loc['SEX_INLAW_MALE'], 
                g_loc['SEX_INLAW_FEMALE']
                ]
    
    # Define golbal list, 'g_lrelation', 
    #   containing relationship between member and parents
    # NOTE: The list order must NOT be changed, 
    #   since the list index is used to store in the family tree.
    g_lrelation = [g_loc['REL_BIO'], 
                    g_loc['REL_ADOPT'], 
                    g_loc['REL_STEP']
                    ]

    # Define golbal list, 'g_lstatus', 
    #   containing relationship between member and spouse
    # NOTE: The list order must stay un-changed once family tree initialized, 
    #   since the list index is used as value to store in the family tree.
    g_lstatus = [g_loc['REL_SINGLE'], 
                    g_loc['REL_MARRIED'], 
                    g_loc['REL_TOGETHER']
                    ]
    
    # Define global variables
    # The value of 'Status' attribute of member info
    g_single = g_lstatus.index(g_loc['REL_SINGLE'])
    
    # Define global dataframe 'adopt_members' for adopted members
    rel = g_lrelation.index(g_loc['REL_ADOPT'])
    adopt_members = load_dataframe(all_members, 
                                    rel, 
                                    base=g_dirtyTree)
    
    # Define global dataframe 'step_members' for step-members
    rel = g_lrelation.index(g_loc['REL_STEP'])
    step_members = load_dataframe(all_members, 
                                    rel, 
                                    base=g_dirtyTree)

    # Define global dataframe, 'bio_members' for bio-members
    rel = g_lrelation.index(g_loc['REL_BIO'])
    bio_members = load_dataframe(all_members, 
                                    rel,
                                    base=g_dirtyTree)

    m_members, g_lname = load_male_members(bio_members,
                                            base=g_dirtyTree)
    if m_members.empty:
        g_lname = []
        lname_idx = -1
        mem = g_df.tail(1).Name.iloc[0]
        born = g_df.tail(1).Born.iloc[0]
    else:
        # initialize index to the latest joined member, i.e.
        # the end of g_lname list
        lname_idx = len(g_lname) - 1
        log.debug(f"lname_idx={lname_idx}")
        
        mem = m_members.tail(1).Name.iloc[0]
        born = m_members.tail(1).Born.iloc[0]
            
    try:
        # initialize a dict obj, 'dbuff' as a starting template.
        _, dbuff = get_1st_mbr_dict(g_df, mem, born)
        log.debug(f"dbuff={dbuff}")
    except:
        st.error(f"{g_loc['MAIN_TITLE']} launched {g_loc['FAILED']}")
        exit
        
    
    # Invoke main page
    g_nav = main_page(lname_idx, dbuff)   
    log.debug (f"{g_nav} <=== FINISHED.")
                
