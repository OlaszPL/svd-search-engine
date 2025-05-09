import streamlit as st
import sqlite3
import time
from search import Search, Mode

# Page configuration
st.set_page_config(
    page_title="Wiki Search Engine",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'search_engine' not in st.session_state:
    st.session_state.search_engine = None
if 'k_value' not in st.session_state:
    st.session_state.k_value = 0
if 'needs_initialization' not in st.session_state:
    st.session_state.needs_initialization = False

# Define callback for search submission
def handle_search():
    st.session_state.search_submitted = True

# Database connection
def get_db_connection():
    return sqlite3.connect("./data/wiki.db")

# Main title
st.title("🔍 Wiki Search Engine")
st.markdown("Search through Wikipedia articles")

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")
    
    # SVD dimension with continuous slider
    k = st.slider(
        "SVD Dimension (k)", 
        min_value=0,
        max_value=1024,
        value=st.session_state.k_value,
        step=16,
        help="k=0 means no dimensionality reduction"
    )
    
    # Only mark for initialization, don't initialize yet
    if k != st.session_state.k_value:
        st.session_state.needs_initialization = True
        st.session_state.k_value = k
    
    # Search mode
    mode_option = st.radio(
        "Search Algorithm",
        ["Cosine Similarity", "ANN (Approximate Nearest Neighbors)"]
    )
    search_mode = Mode.COSINE if mode_option == "Cosine Similarity" else Mode.ANN
    
    # ANN warning
    if search_mode == Mode.ANN and k == 0:
        st.warning("⚠️ ANN requires k > 0")
    
    # Number of results
    num_results = st.slider("Results to show", 1, 50, 10)
    
    st.markdown("---")
    st.markdown("### About")
    st.info("""
        This search engine uses count vectors and singular value decomposition 
        to find semantically similar articles.
    """)

# Main search area with properly aligned search button
with st.form(key="search_form"):
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input(
            label="Search query", 
            placeholder="Search for something...",
            label_visibility="collapsed",
            key="query"
        )
    with col2:
        search_button = st.form_submit_button(
            "🔎 Search", 
            use_container_width=True, 
            type="primary",
            on_click=handle_search
        )

# Execute search when form is submitted
if search_button:
    search_submitted = True
else:
    search_submitted = False

if search_submitted:
    if not query.strip():
        st.warning("Please enter a search query.")
    else:
        try:
            # Initialize search engine if needed
            if st.session_state.needs_initialization or st.session_state.search_engine is None:
                with st.spinner(f"Initializing search engine with k={st.session_state.k_value}..."):
                    try:
                        st.session_state.search_engine = Search(st.session_state.k_value)
                        st.session_state.needs_initialization = False
                    except Exception as e:
                        st.error(f"Error initializing search engine: {str(e)}")
                        st.stop()
            
            conn = get_db_connection()
            
            with st.spinner("Searching..."):
                # Execute search
                start_time = time.time()
                results = st.session_state.search_engine.search(query, search_mode, num_results)
                search_time = time.time() - start_time
                
                if results:
                    # Fetch article metadata including text excerpt
                    cursor = conn.cursor()
                    placeholders = ','.join(['?'] * len(results))
                    db_query = f"SELECT title, url, text FROM articles WHERE id IN ({placeholders})"
                    cursor.execute(db_query, [idx for idx, _ in results])
                    articles = cursor.fetchall()
                    
                    # Display search stats
                    st.success(f"Found {len(results)} results in {search_time:.3f} seconds")
                    
                    # Display results
                    for i, ((idx, match_score), (title, url, text)) in enumerate(zip(results, articles), 1):
                        with st.container():
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                st.markdown(f"#### {i}. {title}")
                                st.markdown(f"[{url}]({url})")
                                # Show text excerpt (limited to first 300 chars)
                                text_excerpt = text[:300] + "..." if text and len(text) > 300 else text
                                st.markdown(f"<small><em>{text_excerpt}</em></small>", unsafe_allow_html=True)
                            with col2:
                                st.metric("Score", f"{match_score:.4f}")
                            st.divider()
                else:
                    if search_mode == Mode.ANN and k == 0:
                        st.error("ANN search requires k > 0. Please change your configuration.")
                    else:
                        st.info("No results found for your query.")
        
        except Exception as e:
            st.error(f"Error during search: {str(e)}")