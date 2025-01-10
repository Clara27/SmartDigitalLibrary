
import streamlit as st
st.set_page_config(
            page_title="Smart Digital Library",
            layout="wide"
        ) 

from back import SnowparkManager
from bookshelf_views import render_traditional_view, render_column_view, render_hybrid_view
from datetime import datetime
import json
import time
import psutil
from typing import Dict, List, Any, Optional
import hashlib
import uuid
from trulens.apps.custom import instrument
import random
from streamlit.runtime.scriptrunner import RerunException
from truelens_utils import TruLensEvaluator
import os
import tempfile
from gtts import gTTS


  
  
class PDFLibraryApp:
    def __init__(self):
        """Initialize the application"""
        # Add API key validation state
        if 'api_key_valid' not in st.session_state:
            st.session_state.api_key_valid = False

        # Store cleanup status
        if 'cleanup_registered' not in st.session_state:
            st.session_state.cleanup_registered = False

        if 'current_view' not in st.session_state:
            st.session_state.current_view = "bookshelf"
            
        if 'selected_book' not in st.session_state:
            st.session_state.selected_book = None
            
        if "button_clicked" not in st.session_state:
            st.session_state.button_clicked = False
            
        self.setup_page()
        self.initialize_session_state()
        
        # Register cleanup only once
        if not st.session_state.cleanup_registered:
            self.register_cleanup()
            st.session_state.cleanup_registered = True

        # Add search state
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
        if 'show_search' not in st.session_state:
            st.session_state.show_search = False
            
        
        session = SnowparkManager.get_session()
        if session:
            try:
                query = "SELECT * FROM TESTDB.MYSCHEMA.BOOK_METADATA"
                results = session.sql(query).collect()
                st.session_state.files = [
                    {
                        "name": row["FILENAME"],
                        "category": row["CATEGORY"],
                        "date_added": row["DATE_ADDED"].strftime("%Y-%m-%d"),
                        "size": row["SIZE"],
                        "usage_stats": json.loads(row["USAGE_STATS"])
                    }
                    for row in results
                ]
            except Exception as e:
                st.error(f"Failed to retrieve book metadata: {str(e)}")
            finally:
                session.close()  
 
            
 

    def add_bg_image(self):
        """Add a background image to the app."""
        st.markdown(
            f"""
            <style>
                .stApp {{
                    background-image: url("https://i.postimg.cc/6qdjjp4S/Picture116.png");
                    background-size: cover;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                }}
                
                /* Semi-transparent overlay for better readability */
                .stApp::before {{
                    content: "";
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(17, 0, 28, 0.85);
                    z-index: -1;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )

    def register_cleanup(self):
        """Register cleanup handler for session end"""
        try:
            import atexit

            def cleanup():
                try:
                    session = SnowparkManager.get_session()
                    if session:
                        st.info("Cleaning up database tables...")
                        # Delete all records from TESTDB.MYSCHEMA.RAG_DOCUMENTS_TMP table
                        delete_rag_query = "DELETE FROM TESTDB.MYSCHEMA.RAG_DOCUMENTS_TMP"
                        session.sql(delete_rag_query).collect()
                        # Delete all records from TESTDB.MYSCHEMA.ANALYTICS_METRICS table
                        delete_metrics_query = "DELETE FROM TESTDB.MYSCHEMA.ANALYTICS_METRICS"
                        session.sql(delete_metrics_query).collect()
                        session.commit()
                        st.info("Database cleanup completed.")
                    else:
                        st.warning("Failed to establish database connection for cleanup.")
                except Exception as e:
                    session.rollback()
                    st.error(f"Error during database cleanup: {str(e)}")
                finally:
                    if session:
                        session.close()

            atexit.register(cleanup)
        except:
            pass

    def setup_page(self):
        """Configure page settings"""

        self.add_bg_image()
         # Create elegant header with logo and title
        header_cols = st.columns([0.8, 4, 0.4])  # Adjusted ratios for better spacing
        
        with header_cols[0]:
            st.markdown(
                """
                <div style="margin-top: -50px; text-align: left;">
                    <img src="https://i.postimg.cc/cJrXGrxd/PALicon.png" width="130">
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with header_cols[1]:
            st.markdown("""                 
                <div style="                     
                    display: flex;                      
                    flex-direction: column;                      
                    align-items: flex-start;                      
                    gap: 2px;                      
                    margin-top: -25px;                     
                    margin-left: -10px;                     
                    margin-right: 300px;                     
                    align-items: center;                     
                    padding: 10px 0;">                     
                    <h1 style="                         
                        margin: 0;                          
                        padding: 0;                          
                        font-size: 52px;                          
                        font-weight: 600;                          
                        line-height: 1.0;                          
                        color: #4B006E;                          
                        background: linear-gradient(45deg, #4B006E, #9b4dca);                          
                        -webkit-background-clip: text;                          
                        -webkit-text-fill-color: transparent;">                         
                        Personal AI Library                     
                    </h1>                     
                    <h2 style="                         
                        margin: 0;                          
                        padding: 0;                          
                        font-size: 22px;                          
                        font-weight: 350;                          
                        line-height: 1.4;                         
                        margin-left:10px;                          
                        color: #F7E7CE;">                         
                        Streamline Your Files, Empower Your Knowledge.                     
                    </h2>                 
                </div>                 
            """, unsafe_allow_html=True)
  
                   
       
        st.markdown("""
            <style>
            [data-testid="stSidebar"] {
                background-color: #4E2A84;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <style>
            /* Main background */
            .stApp {
                background-color: #220135;
                color: #FFFFFF;
            }
            
            /* Sidebar */
            .css-1d391kg {
                background-color: #663046;
            }
            
            /* Cards and containers */
            div.stMarkdown {
                color: #FFFFFF;
            }
            
            /* Buttons */
            .stButton button {
                background-color: #3B0B59;
                color: #FFFFFF;
                border: 1px solid #541680;
            }
            
            .stButton button:hover {
                background-color: #541680;
                border: 1px solid #6B1F9E;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 1px;
                background-color: #1E0935;
            }
            
            .stTabs [data-baseweb="tab"] {
                background-color: #3B0B59;
                color: #FFFFFF;
            }
            
            .stTabs [aria-selected="true"] {
                background-color: #541680;
            }
            
            /* Select boxes and inputs */
            .stSelectbox [data-baseweb="select"] {
                background-color: #1E0935;
            }
            
            .stTextInput input {
                background-color: #3B0B59;
                color: #FFFFFF;
            }
            
            /* Progress bars */
            .stProgress > div > div {
                background-color: #541680;
            }
            
            /* File uploader */
            .stFileUploader {
                background-color: #4E2A84;
            }
            
            /* Expander */
            .streamlit-expanderHeader {
                background-color: #4E2A84;
                color: #FFFFFF;
            }
            
            /* DataFrames and tables */
            .streamlit-table {
                background-color: #4E2A84;
                color: #FFFFFF;
            }
        </style>
    """, unsafe_allow_html=True)
        
        
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        # Basic app state initialization...
        if 'files' not in st.session_state:
            st.session_state.files = []
        if 'selected_book' not in st.session_state:
            st.session_state.selected_book = None
        if 'mistral_api_key' not in st.session_state:
            st.session_state.mistral_api_key = ""
        if 'book_keys' not in st.session_state:
            st.session_state.book_keys = {}

        # Add cleanup status
        if 'cleanup_status' not in st.session_state:
            st.session_state.cleanup_status = False
            
        if 'active_category' not in st.session_state:
            st.session_state.active_category = 'All'

        # Add qa_history initialization
        if 'qa_history' not in st.session_state:
            st.session_state.qa_history = {}    
            
        if 'get_document_summary' not in st.session_state:
           st.session_state.get_document_summary = SnowparkManager.get_document_summary

        # View states
        if 'current_view' not in st.session_state:
            st.session_state.current_view = "bookshelf"
        if 'show_qa' not in st.session_state:
            st.session_state.show_qa = False
        if 'show_summary' not in st.session_state:
            st.session_state.show_summary = False
        if 'show_metrics' not in st.session_state:
            st.session_state.show_metrics = False
        if 'bookshelf_view' not in st.session_state:
            st.session_state.bookshelf_view = 'traditional'
            
        # QA states
        if 'current_question' not in st.session_state:
            st.session_state.current_question = ""
        if 'qa_results' not in st.session_state:
            st.session_state.qa_results = None
            
        # # Performance tracking
        # if 'metrics_tracker' not in st.session_state:
        #     st.session_state.metrics_tracker = MetricsTracker()
            
        # Initialize TruLens evaluator only when API key is available and valid
        if 'trulens_evaluator' not in st.session_state:
            st.session_state.trulens_evaluator = None
            
            
        # Try to initialize TruLens evaluator if API key is available
        if ('mistral_api_key' in st.session_state and 
            st.session_state.mistral_api_key and 
            hasattr(st.session_state, 'api_key_valid') and 
            st.session_state.api_key_valid):
            try:
                if st.session_state.trulens_evaluator is None:
                    st.session_state.trulens_evaluator = TruLensEvaluator()
            except Exception as e:
                print(f"Error initializing TruLens evaluator: {str(e)}")
                st.session_state.trulens_evaluator = None
                
        # Interaction tracking
        if 'interaction_start_time' not in st.session_state:
            st.session_state.interaction_start_time = time.time()
            
        # Initialize database connection and fetch files
        session = SnowparkManager.get_session()
        if session:
            try:
                query = """
                SELECT 
                    BOOK_ID,
                    FILENAME,
                    CATEGORY,
                    DATE_ADDED,
                    SIZE,
                    USAGE_STATS
                FROM TESTDB.MYSCHEMA.BOOK_METADATA
                """
                results = session.sql(query).collect()
                st.session_state.files = [
                    {
                        "name": row["FILENAME"],
                        "category": row["CATEGORY"],
                        "date_added": row["DATE_ADDED"].strftime("%Y-%m-%d"),
                        "size": row["SIZE"],
                        "usage_stats": json.loads(row["USAGE_STATS"]) if isinstance(row["USAGE_STATS"], str) else row["USAGE_STATS"]
                    }
                    for row in results
                ]
            except Exception as e:
                st.error(f"Failed to retrieve book metadata: {str(e)}")
            finally:
                session.close()
            
            
    def handle_current_view(self):
        print("Inside handle_current_view")
        print("Current view:", st.session_state.current_view)
        print("Selected book:", st.session_state.selected_book)
        
        if st.session_state.current_view == "details" and st.session_state.selected_book:
            self.show_book_details(st.session_state.selected_book)
        else:
            print("Calling render_bookshelf_view")
            self.render_bookshelf_view()
    
   # @st.cache_data
    def load_book_list(self):
        return [book['name'] for book in st.session_state.files]
    
    
    def run(self):
        """Main application flow"""
        # Main content area first
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
                <div style="
                    display: flex; 
                    justify-content: center; /* Centers horizontally */
                    text-align: center;">
                    <h3 style="
                        margin-top: -30px; /* Moves the header up by 20 pixels */
                        margin-left: 100px
                        font-size: 24px; 
                        font-weight: 400; 
                        color: #333; 
                        display: flex; 
                        align-items: center; 
                        gap: 10px;">
                        📚 Smart Digital Library
                    </h3>
                </div>
                """, 
                unsafe_allow_html=True
            )
       
        
        # API Key input in main content
        # api_key = col1.text_input(
        #     "Enter your Mistral API Key",
        #     value=st.session_state.mistral_api_key,
        #     type="password",
        #     help="Enter your Mistral API key",
        #     placeholder="Enter your Mistral API key here..."
        # )
        
        api_key = st.secrets["MISTRAL_API_KEY"]
        
        # Validate API key only when it changes
        if api_key != st.session_state.mistral_api_key:
            st.session_state.mistral_api_key = api_key
            
            if api_key:
                if SnowparkManager.validate_api_key(api_key):
                    st.session_state.api_key_valid = True
                    #st.success("✅ API Key validated successfully!")
                else:
                    st.session_state.api_key_valid = False
                    st.error("❌ Invalid API Key")

       
        # Sidebar content
        with st.sidebar:
            self.render_book_management()
                    

        # Main content area based on API key and view state
              
        if st.session_state.mistral_api_key:
            if st.session_state.get('api_key_valid', False):
                self.handle_current_view()  
                                      
            else:
                # Show API key related messages
                if not st.session_state.mistral_api_key:
                    print("👆 Please enter your Mistral API key above to get started")
                else:
                    st.error("❌ Invalid API Key")
        else:
            st.info("👆 Please enter your Mistral API key above to get started")
            
            
        if st.button("🔍 Search Library", key="Search_Library_Here", use_container_width=False):
            st.session_state.show_search = not st.session_state.show_search
        
        # Show search interface if toggled
        if st.session_state.show_search:
            self.render_search_interface()
    
               
    @staticmethod
    @instrument
    def search_books(query: str) -> List[Dict]:
        """Search for books by title and metadata"""
        session = SnowparkManager.get_session()
        if not session:
            return []
        
        try:
            query = query.lower()
            matching_books = [
                book for book in st.session_state.files
                if query in book['name'].lower() or
                query in book['category'].lower()
            ]
            return matching_books
        finally:
            session.close()

    def render_document_reader(self, book):
            """Add reading functionality to book details with dark mode"""
            session = SnowparkManager.get_session()
            if not session:
                st.error("Could not establish database connection.")
                return

            try:
                # Get all pages of the document in order
                query = f"""
                SELECT 
                    CONTENT,
                    METADATA:page_number::INTEGER as PAGE_NUMBER
                FROM RAG_DOCUMENTS_TMP
                WHERE FILENAME = '{book['name'].replace("'", "''")}'
                ORDER BY PAGE_NUMBER
                """
                results = session.sql(query).collect()
                
                if not results:
                    st.warning("No content found for this document.")
                    return

                # Initialize page numbers and navigation
                total_pages = len(results)
                slider_key = f"page_slider_{book['name']}"
                view_mode_key = f"view_mode_{book['name']}"
                
                # Initialize session state for page number if not exists
                if slider_key not in st.session_state:
                    st.session_state[slider_key] = 1
                    
                # Initialize view mode if not exists
                if view_mode_key not in st.session_state:
                    st.session_state[view_mode_key] = "Single Page"
                
                # Navigation controls at the top
                col1, col2, col3 = st.columns([2, 3, 2])
                
                with col1:
                    st.write(f"Total Pages: {total_pages}")
                    # Add view mode selector
                    view_mode = st.radio(
                        "View Mode",
                        ["Single Page", "Full Document"],
                        key=view_mode_key
                    )
                
                with col2:
                    # Only show page selector in single page mode
                    if view_mode == "Single Page":
                        current_page = st.selectbox(
                            "Select Page",
                            options=list(range(1, total_pages + 1)),
                            index=st.session_state[slider_key] - 1,
                            key=f"page_select_{book['name']}"
                        )
                        # Update session state for page number
                        st.session_state[slider_key] = current_page
                
                with col3:
                    if view_mode == "Single Page":
                        st.write(f"Current Page: {st.session_state[slider_key]}")

                # Display content based on view mode
                st.markdown("---")
                st.markdown("### 📖 Document Content")

                if view_mode == "Single Page":
                    # Display single page content
                    current_content = next(
                        (row['CONTENT'] for row in results if row['PAGE_NUMBER'] == st.session_state[slider_key]),
                        "Content not found for this page."
                    )
                    self.display_content_block(current_content)

                    # Navigation controls for single page mode
                    if total_pages > 1:
                        col1, col2, col3 = st.columns([1, 3, 1])
                        
                        with col1:
                            if st.session_state[slider_key] > 1:
                                if st.button("◀️ Previous", key=f"prev_{book['name']}", use_container_width=True):
                                    st.session_state[slider_key] = st.session_state[slider_key] - 1
                                    st.rerun()
                        
                        with col2:
                            progress = (st.session_state[slider_key] - 1) / (total_pages - 1) if total_pages > 1 else 1
                            st.progress(progress, text=f"Reading Progress: {progress*100:.1f}%")
                        
                        with col3:
                            if st.session_state[slider_key] < total_pages:
                                if st.button("Next ▶️", key=f"next_{book['name']}", use_container_width=True):
                                    st.session_state[slider_key] = st.session_state[slider_key] + 1
                                    st.rerun()
                else:
                    # Display full document content
                    full_content = "\n\n--- Page Break ---\n\n".join(
                        f"Page {row['PAGE_NUMBER']}:\n{row['CONTENT']}"
                        for row in sorted(results, key=lambda x: x['PAGE_NUMBER'])
                    )
                    self.display_content_block(full_content)

            except Exception as e:
                st.error(f"Error loading document: {str(e)}")
                st.write("Debug info:", {
                    "book_name": book['name'],
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                })
            finally:
                session.close()


    def on_read_click(self, book):
        if book:
            slider_key = f"page_slider_{book['name']}"
            page_num = book.get('page', 1)

            st.session_state.current_view = "details"
            st.session_state.selected_book = book
            st.session_state.show_search = False
            st.session_state.show_qa = False
            st.session_state.show_summary = False
            st.session_state[slider_key] = page_num
            
            # if 'current_book_details' not in st.session_state:
            #  st.session_state.current_book_details = {}

            print(f"Calling render_document_reader for book: {book['name']}")
            self.render_document_reader(book)
            
            
    @st.fragment
    def show_book_content(self, found_book):
        if st.button("← Back"):
            return
        self.show_book_details(found_book)
            

    @st.fragment
    def render_search_result(self, result, idx):
        col1, col2 = st.columns([5, 1])

        page_num = result['page'] if isinstance(result['page'], int) else 1
            
    @st.fragment
    def display_book_view(self, book):
        if st.button("← Back", key=f"back_{book['name']}"):
            return
        st.markdown("### 📖 Reading Book")
        self.show_book_details(book)

    @st.fragment
    def render_search_result(self, result, idx):
        """Render a simplified search result with content and read button"""
        # Display search result content
        st.markdown(f"""
            <div style="
                padding: 1rem;
                border-radius: 1.5rem;
                border: 1px solid #541680;
                margin-bottom: 0.5rem;
                background-color: #4E2A84 !important;
            ">
                <div style="color: #FFFFFF; margin-bottom: 0.5rem;">
                    <strong>{result['filename']}</strong> (Page {result['page']})
                </div>
                <div style="color: #FFFFFF; font-style: italic;">
                    "{result['content']}"
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Full width read button
        found_book = next((b for b in st.session_state.files if b['name'] == result['filename']), None)
        if found_book and st.button("📖 Read", key=f"read_btn_{idx}", use_container_width=True):
            self.display_book_view(found_book)
                
 
    def render_search_interface(self):
        with st.container():
            search_type = st.radio(
                "Search Type",
                ["Browse Books", "Search Within Books"],
                horizontal=True
            )

            if search_type == "Browse Books":
                book_list = self.load_book_list()
                selected_book_name = st.selectbox(
                    "Select a Book",
                    book_list,
                    index=None,
                    placeholder="Choose a book..."
                )

                if selected_book_name:
                    book = next((b for b in st.session_state.files if b['name'] == selected_book_name), None)
                    if book:
                        st.markdown(f"""
                            <div style="
                                padding: 1.5rem;
                                border-radius: 8px;
                                border: 1px solid #541680;
                                background-color: #4E2A84;
                                margin: 1rem 0;
                            ">
                                <h3 style="color: #FFFFFF; margin-bottom: 1rem;">📚 {book['name']}</h3>
                                <p style="color: #FFFFFF;"><strong>Category:</strong> {book['category']}</p>
                                <p style="color: #FFFFFF;"><strong>Added:</strong> {book['date_added']}</p>
                                <p style="color: #FFFFFF;"><strong>Size:</strong> {book['size']}</p>
                            </div>
                        """, unsafe_allow_html=True)

                        col1, col2, col3 = st.columns([1, 1, 1])

                        with col1:
                            if st.button("📖 Read Book", use_container_width=True):
                                self.on_read_click(book)

                        with col2:
                            if st.button("📝 Summary", use_container_width=True):
                                st.session_state.current_view = "details"
                                st.session_state.selected_book = book
                                st.session_state.show_summary = True
                                st.session_state.show_search = False
                                st.rerun()

                        with col3:
                            if st.button("❓ Q&A", use_container_width=True):
                                st.session_state.current_view = "details"
                                st.session_state.selected_book = book
                                st.session_state.show_qa = True
                                st.session_state.show_search = False
                                st.rerun()

            else:
                search_col1, search_col2 = st.columns([6, 1])

                with search_col1:
                    search_query = st.text_input(
                        "Search Query",
                        value=st.session_state.search_query,
                        placeholder="Search content within books...",
                        key="search_input",
                        label_visibility="collapsed"
                    )

                with search_col2:
                    search_clicked = st.button(
                        "🔍 Search",
                        type="primary",
                        use_container_width=True
                    )

                if search_clicked and search_query:
                    st.session_state.search_query = search_query
                    with st.spinner("Searching..."):
                        try:
                            results = SnowparkManager.semantic_search_with_llm(
                                query=search_query,
                                filename=None,
                                operation_type="SEARCH",
                                limit=10,
                                similarity_threshold=0.3
                            )

                            if results and results.get('sources'):
                                st.markdown("### 📄 Content Results")
                                st.session_state.search_results = results['sources']

                                for idx, result in enumerate(results['sources']):
                                    self.render_search_result(result, idx)

                        except Exception as e:
                            st.error(f"Search error: {str(e)}")
                            print(f"Search error details: {str(e)}")
        
    
    def render_book_management(self):
        """Sidebar book management section"""
        st.header("Personal AI Librarian")
        
        #st.sidebar.image("https://i.postimg.cc/BXSNChRp/robot-dashboard.png", width=100, use_container_width=True)
    
        # if st.sidebar.button("🔍 Search Library", use_container_width=True):
        #     st.session_state.show_search = not st.session_state.show_search
        # Create tabs
        add_tab, delete_tab = st.tabs(["📥 Add Document", "🗑️ Delete Document"])
        
        # Add Document tab
        with add_tab:
            uploaded_file = st.file_uploader(
                "Choose a file to Upload",
                type=["pdf","doc","docx","txt"],
                help="Upload a PDF, Word or Text document (Max size: 10MB)"
            )
            
            if uploaded_file:
                if uploaded_file.size > 10 * 1024 * 1024:
                    st.error("❌ File too large! Please upload a PDF smaller than 10MB")
                    return
                        
                category = st.selectbox("Category", ["Book", "PDF", "Research Paper", "Article", "Other"])
                
                # Use a unique key for the button
                upload_button_key = f"upload_button_{uploaded_file.name}"
                
                # Track upload state
                if "upload_started" not in st.session_state:
                    st.session_state.upload_started = False
                
                if st.button("Add to Bookshelf", key=upload_button_key) and not st.session_state.upload_started:
                    st.session_state.upload_started = True
                    
                    file_details = {
                        "name": uploaded_file.name,
                        "category": category,
                        "date_added": datetime.now().strftime("%Y-%m-%d"),
                        "size": f"{uploaded_file.size / 1024:.1f} KB",
                        "usage_stats": {
                            "queries": 0,
                            "summaries": 0
                        }
                    }
                    
                    if 'files' not in st.session_state:
                        st.session_state.files = []
                    
                    # Remove any existing entries for this file
                    st.session_state.files = [f for f in st.session_state.files if f['name'] != uploaded_file.name]
                    st.session_state.files.append(file_details)
                    
                    with st.spinner("Processing Document..."):
                        session = SnowparkManager.get_session()
                        if not session:
                            st.error("❌ Could not connect to database")
                            return

                        try:
                            if not SnowparkManager.setup_snowflake_context(session):
                                return

                            if not SnowparkManager.ensure_table_exists(session):
                                return
                            chunk_size = SnowparkManager.CHUNK_SIZE_OPTIONS["Medium"]   
                            success, error_msg, documents = SnowparkManager.process_pdf(
                                uploaded_file.read(), 
                                uploaded_file.name, 
                                uploaded_file.type,
                                chunk_size
                            )

                            if success:
                                st.write("Debug: Starting document upload")
                                upload_success = SnowparkManager.upload_documents(
                                    session,
                                    documents,
                                    uploaded_file.name,
                                    uploaded_file.type,
                                    st.session_state.mistral_api_key
                                )
                                
                                if upload_success:
                                    st.success("✅ Document processed and added successfully!")
                                else:
                                    st.session_state.files.remove(file_details)
                                    st.error("❌ Failed to process document")
                            else:
                                st.session_state.files.remove(file_details)
                                st.error(f"❌ {error_msg}")

                        except Exception as e:
                            st.error(f"❌ Error processing document: {str(e)}")
                            st.session_state.files.remove(file_details)
                        finally:
                            session.close()
                            st.session_state.upload_started = False  # Reset the upload state

            with delete_tab:
                if st.session_state.files:
                    st.subheader("Select Document to Delete")
                    book_names = [f"{book['name']} ({book['category']})" for book in st.session_state.files]
                    book_to_delete = st.selectbox(
                        "Choose document",
                        book_names,
                        key="delete_book_selectbox"
                    )
                    
                    if st.button("🗑️ Delete Document", type="primary"):
                        try:
                            # Extract original filename from the display name
                            selected_filename = book_to_delete.split(" (")[0]
                            
                            # Delete from database first
                            session = SnowparkManager.get_session()
                            if session:
                                try:
                                    # Delete from BOOK_METADATA
                                    delete_metadata_sql = f"""
                                    DELETE FROM TESTDB.MYSCHEMA.BOOK_METADATA 
                                    WHERE FILENAME = '{selected_filename.replace("'", "''")}'
                                    """
                                    session.sql(delete_metadata_sql).collect()
                                    
                                    # Delete from RAG_DOCUMENTS_TMP
                                    delete_rag_sql = f"""
                                    DELETE FROM {SnowparkManager.RAG_TABLE}
                                    WHERE FILENAME = '{selected_filename.replace("'", "''")}'
                                    """
                                    session.sql(delete_rag_sql).collect()
                                    
                                    # Remove from session state
                                    st.session_state.files = [
                                        f for f in st.session_state.files 
                                        if f['name'] != selected_filename
                                    ]
                                    
                                    st.success(f"✅ Document '{selected_filename}' deleted successfully!")
                                    time.sleep(1)  # Brief pause to show success message
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Failed to delete from database: {str(e)}")
                                finally:
                                    session.close()
                            else:
                                st.error("Could not connect to database")
                                
                        except Exception as e:
                            st.error(f"Error during deletion: {str(e)}")
                else:
                    st.info("No documents available to delete")

    
    def render_bookshelf_view(self):
        try:
            print("Inside render_bookshelf_view")
            print("Files in session state:", st.session_state.files)
            
            view_options = ['Traditional', 'Column', 'Hybrid']
        # Fix case issue by capitalizing the stored view
            if 'bookshelf_view' not in st.session_state:
                st.session_state.bookshelf_view = 'Traditional'
            else:
                st.session_state.bookshelf_view = st.session_state.bookshelf_view.title()
                
            print("Current bookshelf view:", st.session_state.bookshelf_view)
            
            selected_view = st.radio(
                'Select Bookshelf View', 
                view_options, 
                index=view_options.index(st.session_state.bookshelf_view),
                key='bookshelf_view_selector',
                horizontal=True
            )

            if selected_view != st.session_state.bookshelf_view:
                st.session_state.bookshelf_view = selected_view
                    
            try:
                print(f"Attempting to render {st.session_state.bookshelf_view} view")
                if st.session_state.bookshelf_view == 'Traditional': 
                    from bookshelf_views import render_traditional_view
                    print("About to call traditional view with files:", st.session_state.files)
                    render_traditional_view(st.session_state.files)
                    print("after calling render_tranditional_view")
                elif st.session_state.bookshelf_view == 'Column':
                    from bookshelf_views import render_column_view
                    render_column_view(st.session_state.files)
                elif st.session_state.bookshelf_view == 'Hybrid':
                    from bookshelf_views import render_hybrid_view
                    render_hybrid_view(st.session_state.files)
            except Exception as view_error:
                print(f"Error rendering view: {str(view_error)}")
                st.error(f"Error rendering view: {str(view_error)}")
                
        except Exception as e:
            print(f"Error in render_bookshelf_view: {str(e)}")
            st.error(f"Error in bookshelf view: {str(e)}")
            

    def handle_summary_generation(self, book):
        """Handle summary generation with optimized flow"""
        from back import SnowparkManager

        st.markdown("### 📝 Document Summary")

        # Summary preferences section
        col1, col2 = st.columns(2)
        with col1:
            style = st.selectbox(
                "Style", 
                ["Concise", "Detailed", "Academic"],
                help="Choose how detailed the summary should be"
            )
            max_tokens = st.slider(
                "Summary Length", 
                500, 1000, 750,
                help="Control the length of the summary"
            )
        with col2:
            format_type = st.selectbox(
                "Format", 
                ["Structured", "Bullet Points", "Narrative"],
                help="Choose how the summary is formatted"
            )
            include_key_points = st.checkbox(
                "Include Key Points", 
                value=True,
                help="Add a section highlighting main points"
            )

        if st.button("Generate Summary", key="Generate Summary", use_container_width=True):
            with st.spinner("Generating summary..."):
                try:
                    # Start performance tracking
                    start_time = time.time()
                    process = psutil.Process()
                    start_memory = process.memory_info().rss

                    # Get document content for both summary and evaluation
                    session = SnowparkManager.get_session()
                    if not session:
                        st.error("Could not connect to database")
                        return

                    try:
                        # Get original content
                        query = f"""
                        SELECT CONTENT, METADATA:page_number::INTEGER as PAGE_NUM
                        FROM RAG_DOCUMENTS_TMP
                        WHERE FILENAME = '{book['name'].replace("'", "''")}'
                        ORDER BY PAGE_NUM
                        """
                        results = session.sql(query).collect()
                        
                        if not results:
                            st.error("No content found for this document")
                            return

                        contexts = [{"CONTENT": row['CONTENT']} for row in results]
                        
                                         
                        # Generate summary
                        summary = st.session_state.get_document_summary(
                            filename=book['name'],
                            style=style,
                            format_type=format_type,
                            max_tokens=max_tokens,
                            include_key_points=include_key_points,
                            operation_type="SUMMARY" 
                        )
                        st.session_state.trulens_evaluator = TruLensEvaluator()
                        print("Debug: Created new TruLens evaluator")
                        if summary and summary.get('summary'):
                            # Display summary
                            st.markdown("### 📄 Generated Summary")
                            st.write(summary['summary'])

                            # Show metadata in expander
                            with st.expander("📊 Summary Details", expanded=False):
                                st.write(f"- **Document**: {summary['filename']}")
                                st.write(f"- **Pages**: {len(results)}")
                                st.write(f"- **Style**: {style}")
                                st.write(f"- **Format**: {format_type}")
                                st.write(f"- **Length**: {len(summary['summary'].split())} words")
                                # print("before calling evaluate_rag_pipeline from handle_summary_generation function")
                                # Evaluate quality if TruLens is available
                                # if (hasattr(st.session_state, 'trulens_evaluator') and 
                                #         st.session_state.trulens_evaluator and 
                                #         st.session_state.trulens_evaluator.initialized):
                                        
                                #         eval_results = st.session_state.trulens_evaluator.evaluate_rag_pipeline(
                                #             query="Generate a summary of this document",
                                #             response=summary['summary'],
                                #             contexts=contexts,
                                #             operation_type="SUMMARY",
                                #             style=style,
                                #             format_type=format_type,
                                #             output_token_count=max_tokens
                                #         )
                                # print("after calling evaluate_rag_pipeline from handle_summary_generation front.py ")
                                # Display metrics if available
                                # if eval_results and eval_results.get('summary'):
                                #     st.markdown("### 📊 Quality Metrics")
                                #     st.markdown(eval_results['summary'])

                                #     # Update style metrics
                                #     update_query = f"""
                                #     UPDATE TESTDB.MYSCHEMA.TRULENS_METRICS
                                #     SET STYLE = '{style}',
                                #         FORMAT_TYPE = '{format_type}',
                                #         OUTPUT_TOKEN_COUNT = {max_tokens}
                                #     WHERE METRIC_ID = (
                                #         SELECT METRIC_ID 
                                #         FROM TESTDB.MYSCHEMA.TRULENS_METRICS 
                                #         ORDER BY TIMESTAMP DESC 
                                #         LIMIT 1
                                #     )
                                #     """
                                #     session.sql(update_query).collect()

                        else:
                            st.error("Failed to generate summary")

                    finally:
                        session.close()

                except Exception as e:
                    st.error(f"Error during summary generation: {str(e)}")
         
     
     
      
    def show_book_details(self, book):
        """Display book details with reading functionality"""
        # Back button
        if st.button("← Back to Bookshelf", key="back_to_bookshelf_button"):
            st.session_state.current_view = "bookshelf"
            st.session_state.selected_book = None
            st.session_state.show_qa = False
            st.session_state.show_summary = False
            st.rerun()

         # Create a 1/4 - 3/4 column layout
        col1, col2 = st.columns([1, 3])  # 1:3 ratio makes col1 take up 1/4 of the width
        
        with col1:
            # Book details section in the left column
            st.markdown(f"""
                <div style="
                    background-color: #593163;
                    padding: 1.2rem;
                    border-radius: 8px;
                    border: 1px solid #541680;
                    margin-bottom: 1rem;
                    width: 100%;
                ">
                    <h3 style="color: #FFFFFF; font-size: 1.1em; margin-bottom: 0.8rem;">📖 {book['name']}</h3>
                    <p style="color: #FFFFFF; font-size: 0.9em; margin: 0.3rem 0;"><strong>Category:</strong> {book['category']}</p>
                    <p style="color: #FFFFFF; font-size: 0.9em; margin: 0.3rem 0;"><strong>Size:</strong> {book['size']}</p>
                    <p style="color: #FFFFFF; font-size: 0.9em; margin: 0.3rem 0;"><strong>Added:</strong> {book['date_added']}</p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            # Tab style remains the same
            tab_style = """
            <style>
            .stTabs [data-baseweb="tab-list"] button {
                width: 150px;
                padding: 8px 16px;
                font-size: 18px;
                background-color: #3B0B59;
                color:rgb(234, 229, 229);
                border-radius: 4px;
                margin-right: 8px;
            }
            .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
                font-size: 18px;
                font-weight: bold;
            }
            </style>
            """
            st.markdown(tab_style, unsafe_allow_html=True)
        
        
        #     # Create tabs for different functions with larger font size
        # tab_style = """
        # <style>
        # .stTabs [data-baseweb="tab-list"] button {
        #     width: 150px;
        #     padding: 8px 16px;
        #     font-size: 18px;
        #     background-color: #3B0B59;
        #     color:rgb(234, 229, 229);
        #     border-radius: 4px;
        #     margin-right: 8px;
        # }
        # .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        #     font-size: 18px;
        #     font-weight: bold;
        # }
        # </style>
        # """
        # st.markdown(tab_style, unsafe_allow_html=True)
       
        # Create tabs for different functions
        read_tab, summary_tab, qa_tab = st.tabs(["📚 Read", "📝 Summary", "❓ Q&A"])
        
        with read_tab:
            self.render_document_reader(book)
            
        with summary_tab:
            if st.button("Generate Summary", key=f"generate_summary_button_{book['name']}", use_container_width=True):
             st.session_state.show_summary = True
             st.session_state.show_qa = False
            if st.session_state.show_summary:
                self.handle_summary_generation(book)

        with qa_tab:
            if st.button("Ask Questions", key=f"ask_questions_button_{book['name']}", use_container_width=True):
                st.session_state.show_qa = True
                st.session_state.show_summary = False
            if st.session_state.show_qa:
                self.handle_qa_interface(book)
              
    def render_search_interface(self):
        with st.container():
            search_type = st.radio(
                "Search Type",
                ["Browse Books", "Search Within Books"],
                horizontal=True
            )

            if search_type == "Browse Books":
                book_list = self.load_book_list()
                selected_book_name = st.selectbox(
                    "Select a Book",
                    book_list,
                    index=None,
                    placeholder="Choose a book..."
                )

                if selected_book_name:
                    book = next((b for b in st.session_state.files if b['name'] == selected_book_name), None)
                    if book:
                        st.markdown(f"""
                            <div style="
                                padding: 1.5rem;
                                border-radius: 8px;
                                border: 1px solid #541680;
                                background-color:#4E2A84;
                                margin: 1rem 0;
                            ">
                                <h3 style="color: #FFFFFF; margin-bottom: 1rem;">📚 {book['name']}</h3>
                                <p style="color: #FFFFFF;"><strong>Category:</strong> {book['category']}</p>
                                <p style="color: #FFFFFF;"><strong>Added:</strong> {book['date_added']}</p>
                                <p style="color: #FFFFFF;"><strong>Size:</strong> {book['size']}</p>
                            </div>
                        """, unsafe_allow_html=True)

                        col1, col2, col3 = st.columns([1, 1, 1])

                        with col1:
                            if st.button("📖 Read Book", use_container_width=True):
                                self.on_read_click(book)

                        with col2:
                            if st.button("📝 Summary", use_container_width=True):
                                st.session_state.current_view = "details"
                                st.session_state.selected_book = book
                                st.session_state.show_summary = True
                                st.session_state.show_search = False
                                st.rerun()

                        with col3:
                            if st.button("❓ Q&A", use_container_width=True):
                                st.session_state.current_view = "details"
                                st.session_state.selected_book = book
                                st.session_state.show_qa = True
                                st.session_state.show_search = False
                                st.rerun()

            else:
                search_col1, search_col2 = st.columns([6, 1])

                with search_col1:
                    search_query = st.text_input(
                        "Search Query",
                        value=st.session_state.search_query,
                        placeholder="Search content within books...",
                        key="search_input",
                        label_visibility="collapsed"
                    )

                with search_col2:
                    search_clicked = st.button(
                        "🔍 Search",
                        type="primary",
                        use_container_width=True
                    )

                if search_clicked and search_query:
                    st.session_state.search_query = search_query
                    with st.spinner("Searching..."):
                        try:
                            results = SnowparkManager.semantic_search_with_llm(
                                query=search_query,
                                filename=None,
                                operation_type="SEARCH",
                                limit=10,
                                similarity_threshold=0.3
                            )

                            if results and results.get('sources'):
                                st.markdown("### 📄 Content Results")
                                st.session_state.search_results = results['sources']

                                for idx, result in enumerate(results['sources']):
                                    self.render_search_result(result, idx)

                        except Exception as e:
                            st.error(f"Search error: {str(e)}")
                            print(f"Search error details: {str(e)}")
                            
    # def on_read_click(self,book):
    #     """Handle click events for reading a book"""
    #     if not book:
    #         st.error("No book selected")
    #         return
            
    #     # Update session state
    #     st.session_state.selected_book = book
    #     st.session_state.current_view = "details"
        
    #     # Store book details for reference
    #     if 'current_book_details' not in st.session_state:
    #         st.session_state.current_book_details = {}
            
    #     st.session_state.current_book_details = {
    #         'name': book.get('name', ''),
    #         'category': book.get('category', ''),
    #         'date_added': book.get('date_added', ''),
    #         'size': book.get('size', '')
    #     }
        
    def display_content_block(self, content):
            """Helper method to display content block with enhanced HTML formatting"""
            # Create the container div with improved styling and header/footer handling
            container_style = (
                "background-color: #593163;"
                "color: #FFFFFF;"
                "padding: 2rem 3rem;" # Adjusted padding
                "border-radius: 8px;"
                "border: 1px solid #541680;"
                "position: relative;" # Added for header/footer positioning
                "box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);"
                "font-family: Georgia, 'Times New Roman', serif;"
                "font-size: 16px;"
                "height: 800px;"
                "width: 90%;"
                "margin: 2rem auto;"
                "position: relative;"
                "min-height: 600px;"
                "letter-spacing: 0.5px;"
            )
            
            # Content container with improved structure
            content_container_style = (
                "padding: 1rem 2rem;"
                "height: calc(100% - 4rem);" # Account for padding
                "overflow-y: auto;"
                "position: relative;"
                "z-index: 1;"
                "margin: 0 auto;" # Center content
                "max-width: 100%;" # Prevent overflow
                "scrollbar-width: thin;" # Thin scrollbar
                "scrollbar-color: #541680 #593163;" # Styled scrollbar
            )
            
            # Shadow effects for better visual hierarchy
            shadow_styles = {
                'right': (
                    "position: absolute;"
                    "top: 0;"
                    "right: 0;"
                    "width: 30px;"
                    "height: 100%;"
                    "background: linear-gradient(to left, rgba(89, 49, 99, 0.8), transparent);"
                    "pointer-events: none;"
                    "z-index: 2;"
                ),
                'bottom': (
                    "position: absolute;"
                    "bottom: 0;"
                    "left: 0;"
                    "right: 0;"
                    "height: 30px;"
                    "background: linear-gradient(to top, rgba(89, 49, 99, 0.8), transparent);"
                    "pointer-events: none;"
                    "z-index: 2;"
                )
            }

            # Format the content with proper HTML structure
            formatted_content = self.format_content_html(content)
            
            # Combine everything into the final HTML structure
            html_content = """
            <div style="{}">
                <div style="{}">
                    {}
                </div>
                <div style="{}"></div>
                <div style="{}"></div>
            </div>
            """.format(
                container_style,
                content_container_style,
                formatted_content,
                shadow_styles['right'],
                shadow_styles['bottom']
            )
            
            # Render HTML content
            st.markdown(html_content, unsafe_allow_html=True)
            
            # Add read aloud controls
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                accent = st.selectbox(
                    "Voice Accent",
                    ["co.uk", "com", "com.au", "co.in", "ca"],
                    help="Select voice accent for text-to-speech",
                    key=f"accent_{hash(content)}"
                )
                
                if st.button("🔊 Read Content", use_container_width=True, key=f"read_{hash(content)}"):
                    try:
                        with st.spinner("Generating audio..."):
                            temp_dir = tempfile.gettempdir()
                            temp_file = os.path.join(temp_dir, f'content_{uuid.uuid4().hex}.mp3')
                            
                            try:
                                # Clean content for text-to-speech
                                clean_content = self.clean_content_for_tts(content)
                                
                                tts = gTTS(text=clean_content, lang='en', slow=False, tld=accent)
                                tts.save(temp_file)
                                
                                with open(temp_file, 'rb') as audio_file:
                                    audio_bytes = audio_file.read()
                                st.audio(audio_bytes)
                                
                            finally:
                                try:
                                    time.sleep(1)
                                    if os.path.exists(temp_file):
                                        os.remove(temp_file)
                                except Exception:
                                    pass
                                    
                    except Exception as e:
                        st.error(f"Error generating audio: {str(e)}")

    def format_content_html(self, content: str) -> str:
            """Convert markdown content to formatted HTML with enhanced document structure"""
            if not content:
                return ""
                
            # Create a dictionary of document sections
            document_sections = {
                'header': [],
                'content': [],
                'footer': []
            }
            
            # Split content into lines for processing
            lines = content.split('\n')
            section = 'content'  # Default section
            
            for line in lines:
                # Skip empty lines
                if not line.strip():
                    continue
                    
                # Skip header/footer lines that contain document title or page numbers
                if any(marker in line.lower() for marker in ['business plan', 'page', 'confidential']):
                    continue
                
            try:
                # Parse content structure
                paragraphs = content.split('\n')
                formatted_paragraphs = []
                
                # Track current context
                in_list = False
                list_items = []
                in_code_block = False
                code_lines = []
                
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    
                    # Handle headings
                    if para.startswith('#'):
                        level = len(para.split()[0])  # Count # symbols
                        text = ' '.join(para.split()[1:])
                        formatted_paragraphs.append(
                            f'<h{level} style="color: #DFB6FF; font-size: {2.0-level*0.2}em; '
                            f'margin: 1em 0; font-weight: bold;">{text}</h{level}>'
                        )
                        continue
                    
                    # Handle lists
                    if para.startswith(('-', '*', '•')) or para.strip().startswith(('1.', '2.', '3.')):
                        if not in_list:
                            in_list = True
                            list_items = []
                        
                        item_text = para.lstrip('- *•').strip()
                        if para[0].isdigit():
                            item_text = ' '.join(para.split()[1:])
                        
                        list_items.append(
                            f'<li style="margin-bottom: 0.5em; line-height: 1.6;">{item_text}</li>'
                        )
                        continue
                    
                    # Close list if we're not in a list item anymore
                    if in_list and not (para.startswith(('-', '*', '•')) or para[0].isdigit()):
                        formatted_paragraphs.append(
                            f'<ul style="margin-left: 2em; margin-bottom: 1em; list-style-type: disc;">'
                            f'{"".join(list_items)}</ul>'
                        )
                        in_list = False
                        list_items = []
                    
                    # Handle code blocks
                    if para.startswith('```') or para.startswith('    '):
                        if not in_code_block:
                            in_code_block = True
                            code_lines = []
                        else:
                            in_code_block = False
                            code_content = '\n'.join(code_lines)
                            formatted_paragraphs.append(
                                f'<pre style="background-color: #2d1934; padding: 1em; '
                                f'border-radius: 4px; overflow-x: auto; margin: 1em 0;">'
                                f'<code>{code_content}</code></pre>'
                            )
                            code_lines = []
                        continue
                    
                    if in_code_block:
                        code_lines.append(para)
                        continue
                    
                    # Regular paragraphs
                    formatted_paragraphs.append(
                        f'<p style="margin-bottom: 1em; text-align: justify; '
                        f'line-height: 1.8; padding: 0.2em 0;">{para}</p>'
                    )
                
                # Close any open structures
                if in_list and list_items:
                    formatted_paragraphs.append(
                        f'<ul style="margin-left: 2em; margin-bottom: 1em; list-style-type: disc;">'
                        f'{"".join(list_items)}</ul>'
                    )
                
                if in_code_block and code_lines:
                    code_content = '\n'.join(code_lines)
                    formatted_paragraphs.append(
                        f'<pre style="background-color: #2d1934; padding: 1em; '
                        f'border-radius: 4px; overflow-x: auto; margin: 1em 0;">'
                        f'<code>{code_content}</code></pre>'
                    )
                
                return '\n'.join(formatted_paragraphs)
                
            except Exception as e:
                st.error(f"Error formatting content: {str(e)}")
                return f'<p style="color: red;">Error formatting content: {str(e)}</p>'

    
    def clean_content_for_tts(self, content: str) -> str:
        """Clean content for text-to-speech by removing HTML tags and normalizing text"""
        import re
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', ' ', content)
        
        # Normalize whitespace
        clean_text = ' '.join(clean_text.split())
        
        # Convert common symbols to words
        replacements = {
            '-': 'dash',
            '*': 'bullet',
            '•': 'bullet',
            '|': 'separator',
            '>': 'greater than',
            '<': 'less than',
            '=': 'equals',
        }
        
        for symbol, word in replacements.items():
            clean_text = clean_text.replace(symbol, f' {word} ')
        
        return clean_text

    def handle_qa_interface(self, book):
        """Q&A interface with optimized layout and controls"""
        from back import SnowparkManager

        # Style and format preferences first
        col1, col2 = st.columns(2)
        with col1:
            style = st.selectbox(
                "Response Style", 
                ["Concise", "Detailed", "Technical", "Simple"],
                help="Choose the style of the answer"
            )
            format_type = st.selectbox(
                "Format", 
                ["Paragraph", "Bullet Points", "Step by Step"],
                help="Choose how the answer is formatted"
            )
        with col2:
            max_tokens = st.slider(
                "Maximum Length", 
                100, 400, 250,
                help="Control the length of the response"
            )
            include_quotes = st.checkbox(
                "Include Source Quotes", 
                value=True,
                help="Include relevant quotes from the document"
            )

        # Question input with better styling
        question = st.text_area(
            "Enter your question about the document:",
            height=100,
            placeholder="Type your question here...",
            help="Ask anything about the document content"
        )

        # Ask button with clear visual hierarchy
        if st.button("🔍 Ask Question", type="primary", use_container_width=True):
            if not question:
                st.warning("Please enter a question first.")
                return

            with st.spinner("Searching for answer..."):
                try:
                    qa_results = SnowparkManager.semantic_search_with_llm(
                        query=question,
                        filename=book['name'],
                        operation_type="QA",
                        temperature=0.3,
                        style=style,
                        format_type=format_type,
                        include_quotes=include_quotes,
                        max_tokens=max_tokens
                    )
                    
                    if qa_results and qa_results.get('answer'):
                        # Display answer in a card-like container
                        st.markdown("### 💡 Answer")
                        st.markdown(f"""
                            <div style="
                                background-color: #4E2A84;
                                padding: 20px;
                                border-radius: 8px;
                                border: 1px solid #541680;
                                margin: 10px 0;">
                                {qa_results['answer']}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Display sources if available
                        if qa_results.get('sources'):
                            with st.expander("📚 View Sources", expanded=False):
                                st.markdown("#### Source References")
                                for idx, source in enumerate(qa_results.get('sources', []), 1):
                                    filename = source.get('filename', 'Unknown')
                                    page = source.get('page', 'N/A')
                                    
                                    # Extract content snippet if available
                                    content_snippet = source.get('content', '')
                                    if content_snippet:
                                        content_snippet = content_snippet[:200] + '...' if len(content_snippet) > 200 else content_snippet
                                        
                                    st.markdown(f"""
                                        <div style='
                                            background-color: #4E2A84;
                                            padding: 10px;
                                            border-radius: 5px;
                                            margin: 5px 0;
                                            border: 1px solid #541680;'>
                                            <strong>Source {idx}</strong><br/>
                                            📄 <strong>File</strong>: {filename}<br/>
                                            📑 <strong>Page</strong>: {page}<br/>
                                            {f"💡 <strong>Excerpt</strong>: <i>{content_snippet}</i>" if content_snippet else ""}
                                        </div>
                                    """, unsafe_allow_html=True)
                        
                        # TruLens evaluation
                        # try:
                        #     if (hasattr(st.session_state, 'trulens_evaluator') and 
                        #         st.session_state.trulens_evaluator and 
                        #         st.session_state.trulens_evaluator.initialized):
                                
                        #         raw_results = qa_results.get('raw_results', [])
                        #         contexts = [{"CONTENT": result['CONTENT']} 
                        #                 for result in raw_results if 'CONTENT' in result]
                                
                        #         print(" Inside handlqa before calling evaluate_rag_pipeline")     
                        #         eval_results = st.session_state.trulens_evaluator.evaluate_rag_pipeline(
                        #             query=question,
                        #             response=qa_results['answer'],
                        #             contexts=contexts,
                        #             operation_type="QA",
                        #             style=style,
                        #             format_type=format_type,
                        #             output_token_count=max_tokens
                        #         )
                        #         print(" Inside handlqa after calling evaluate_rag_pipeline")                                
                                                                
                             # GroundTruthAgreement(ground_truth_df, provider=provider).precision_at_k(query, response)          

                                                    
                        # except Exception as e:
                        #     print(f"Error in quality evaluation: {str(e)}")

                except Exception as e:
                    st.error(f"Error generating answer: {str(e)}")

# Main execution        
if __name__ == "__main__":
    app = PDFLibraryApp()
    app.run()
