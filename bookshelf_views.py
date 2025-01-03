import streamlit as st
from datetime import datetime
import uuid
import random
import json


def truncate_text(text, length=20):
    return text[:length] + '...' if len(text) > length else text
def get_category_color(category):
    colors = {
        "Book": "#2ecc71",
        "PDF": "#e74c3c",
        "Research Paper": "#3498db", 
        "Article": "#9b59b6",
        "Other": "#95a5a6"
    }
    return colors.get(category, "#95a5a6")

def handle_book_click(book):
    st.session_state.selected_book = book
    st.session_state.current_view = "details"
    st.rerun()
    
@st.fragment
def book_spine_fragment(book, category, idx):
    category_color = get_category_color(category)
    book_key = f"book_{book['name']}_{category}_{idx}"
    
    style = f"""
    height: 200px;
    width: 50px;
    padding: 10px;
    border-radius: 3px;
    box-shadow: -2px 2px 5px rgba(0,0,0,0.2);
    background-color: {category_color};
    border-left: 2px solid rgba(255,255,255,0.3);
    cursor: pointer;
    display: flex;
    justify-content: center;
    align-items: center;
    """
    
    container = st.empty()
    with container.container():
        st.markdown(f"""
            <div style="{style}" title="{book['name']}">
                <span style="writing-mode: vertical-rl; text-orientation: mixed; font-weight: bold; font-size: 12px;">{truncate_text(book['name'])}</span>
            </div>
        """, unsafe_allow_html=True)
        clicked = st.button("View", key=book_key, type="primary")
        if clicked:
            handle_book_click(book)
def render_traditional_view(files):
    categories = set(file["category"] for file in files)
    
    for category in categories:
        with st.container():
            st.markdown(f"### {category} ({len([f for f in files if f['category'] == category])})")
            
            # Top wooden bar
            st.markdown("""
                <div style="
                    height: 20px;
                    background-color: #452B1F;
                    margin-bottom: 10px;
                    border-radius: 5px 5px 0 0;
                "></div>
            """, unsafe_allow_html=True)
            
            books = [f for f in files if f["category"] == category]
            
            cols = st.columns(len(books))
            
            for idx, (col, book) in enumerate(zip(cols, books)):
                with col:
                    book_spine_fragment(book, category, idx)
            
            # Bottom wooden bar
            st.markdown("""
                <div style="
                    height: 20px;
                    background-color: #452B1F;
                    margin-top: 10px;
                    border-radius: 0 0 5px 5px;
                "></div>
            """, unsafe_allow_html=True)

        
# def render_traditional_view(files):
#     with st.container():
#         st.markdown(
#                     """
#                     <div style='background-color: #f5f5dc; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
#                     </div>
#                     """,
#                     unsafe_allow_html=True
#                 )
#         def handle_book_click(book):
#             st.session_state.selected_book = book
#             st.session_state.current_view = "details"
#             st.rerun()

#         categories = set(file["category"] for file in files)
        
#         for category in categories:
#             with st.container():
#                 st.markdown(f"### 📚 {category} ({len([f for f in files if f['category'] == category])})")
                
#                 books = [f for f in files if f["category"] == category]
#                 category_color = get_category_color(category)
                
#                 st.markdown("""
#                     <style>
#                         .stContainer {
#                             background-color: #f5f5dc;
#                             padding: 20px;
#                             border-radius: 10px;
#                             box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
#                         }
#                     </style>
#                 """, unsafe_allow_html=True)
                
#                 cols = st.columns(len(books)) if books else st.columns(1)
                
#                 for idx, (col, book) in enumerate(zip(cols, books)):
#                     with col:
#                         book_session_key = f"trad_book_data_{category}_{idx}"
#                         if book_session_key not in st.session_state:
#                             st.session_state[book_session_key] = book
                            
#                         book_key = f"book_{book['name']}_{book['category']}_{idx}"
                        
#                         # Make the entire book spine clickable using a button
#                         if col.button(
#                             truncate_text(book['name']),
#                             key=book_key,
#                             help=book['name'],
#                             use_container_width=True,
#                             # Style the button to look like a book spine
#                             args=tuple(),
#                             kwargs={
#                                 "style": """
#                                 height: 200px;
#                                 width: 50px;
#                                 padding: 10px;
#                                 border-radius: 3px;
#                                 writing-mode: vertical-rl;
#                                 text-orientation: mixed;
#                                 font-weight: bold;
#                                 font-size: 12px;
#                                 box-shadow: -2px 2px 5px rgba(0,0,0,0.2);
#                                 background-color: {category_color};
#                                 border-left: 2px solid rgba(255,255,255,0.3);
#                                 """
#                             }
#                         ):
#                             handle_book_click(st.session_state[book_session_key])

#                 st.markdown("""
#                     <div style="
#                         height: 20px;
#                         background-color: #653005;
#                         margin-top: 10px;
#                         border-radius: 0 0 5px 5px;
#                     "></div>
#                 """, unsafe_allow_html=True)

#                 st.markdown("<br>", unsafe_allow_html=True)

def render_column_view(files):
    def handle_book_click(book):
        st.session_state.selected_book = book
        st.session_state.current_view = "details"
        st.rerun()
        
    categories = ["Book", "PDF", "Research Paper", "Article", "Other"]
    
    cols = st.columns(len(categories))
    for idx, (category, col) in enumerate(zip(categories, cols)):
        with col:
            
            category_books = [book for book in files if book["category"] == category]
            category_color = get_category_color(category)
            # st.write(f"Debug: Category: {category}")
            # st.write(f"Debug: Number of books in category: {len(category_books)}")
            
            col.markdown(f"""
                <div style="
                    background-color: {category_color};
                    color: white;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-bottom: 5px;
                ">
                    {category}
                </div>
            """, unsafe_allow_html=True)
            
            for book_idx, book in enumerate(category_books):
                book_session_key = f"col_book_data_{category}_{book_idx}"
                if book_session_key not in st.session_state:
                    st.session_state[book_session_key] = book
                    
                book_key = f"book_{book['name']}_{category}_{book_idx}"
                
                # Make the entire book spine clickable
                if col.button(
                    truncate_text(book['name'], length=40),
                    key=book_key,
                    use_container_width=True,
                    help=book['name']
                ):
                    handle_book_click(st.session_state[book_session_key])
                
                col.markdown(f"""
                    <div style="
                        height: 3px;
                        width: 100%;
                        background-color: {category_color};
                        margin: 2px 0 8px 0;
                        border-radius: 2px;
                    "></div>
                """, unsafe_allow_html=True)
            
            col.markdown(f"""
                <div style="
                    height: 10px;
                    width: 100%;
                    background-color: {category_color};
                    margin-top: 5px;
                    border-radius: 0 0 5px 5px;
                "></div>
            """, unsafe_allow_html=True)

def render_hybrid_view(files):
    # Initialize session state if not already done
    if 'selected_book' not in st.session_state:
        st.session_state.selected_book = None
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "bookshelf"

    def handle_book_click(book):
        """Helper function to handle book selection"""
        st.session_state.selected_book = book
        st.session_state.current_view = "details"
        st.rerun()
    
    # Category selection at the top
    categories = ["All"] + ["Book", "PDF", "Research Paper", "Article", "Other"]
    st.selectbox("Filter by Category", categories, key="active_category")
    
    if st.session_state.active_category == "All":
        category_books = {
            cat: [b for b in files if b['category'] == cat]
            for cat in ["Book", "PDF", "Research Paper", "Article", "Other"]
            if any(b['category'] == cat for b in files)
        }
    else:
        category_books = {
            st.session_state.active_category: [
                b for b in files 
                if b['category'] == st.session_state.active_category
            ]
        }

    ROWS_PER_CATEGORY = 2
    
    for cat_idx, (category, books) in enumerate(category_books.items()):
        if books:
            category_color = get_category_color(category)
            
            st.markdown(f"""
                <div style="
                    background-color: {category_color};
                    color: white;
                    padding: 5px 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                ">
                    {category} ({len(books)} items)
                </div>
            """, unsafe_allow_html=True)
            
            for row_idx in range(ROWS_PER_CATEGORY):
                cols = st.columns(3)
                
                for col_idx, col in enumerate(cols):
                    book_idx = row_idx * 3 + col_idx
                    
                    if book_idx < len(books):
                        book = books[book_idx]
                        with col:
                            # Store book in session state with a unique key
                            book_session_key = f"book_data_{cat_idx}_{row_idx}_{col_idx}"
                            if book_session_key not in st.session_state:
                                st.session_state[book_session_key] = book
                                
                            unique_key = f"book_{book['name']}_{category}_{cat_idx}_{row_idx}_{col_idx}"
                            
                            if col.button(
                                f"📖 {truncate_text(book['name'], length=30)}",
                                key=unique_key,
                                use_container_width=True,
                            ):
                                handle_book_click(st.session_state[book_session_key])
                            
                            # Separator line
                            st.markdown(f"""
                                <div style="
                                    height: 2px;
                                    background: linear-gradient(to right, {category_color}20, {category_color}, {category_color}20);
                                    margin: 0 0 10px 0;
                                "></div>
                            """, unsafe_allow_html=True)
            
            st.markdown("---")

# # Also update the traditional and column views to use the same state management
# def render_traditional_view(files):
#     def handle_book_click(book):
#         st.session_state.selected_book = book
#         st.session_state.current_view = "details"
#         st.rerun()

#     categories = set(file["category"] for file in files)
    
#     for category in categories:
#         with st.container():
#             st.markdown(f"### 📚 {category} ({len([f for f in files if f['category'] == category])})")
            
#             books = [f for f in files if f["category"] == category]
#             category_color = get_category_color(category)
            
#             st.markdown("""
#                 <div style="
#                     background-color: #8b4513;
#                     padding: 20px;
#                     border-radius: 5px;
#                     margin: 10px 0;
#                 "></div>
#             """, unsafe_allow_html=True)
            
#             cols = st.columns(len(books)) if books else st.columns(1)
            
#             for idx, (col, book) in enumerate(zip(cols, books)):
#                 with col:
#                     book_session_key = f"trad_book_data_{category}_{idx}"
#                     if book_session_key not in st.session_state:
#                         st.session_state[book_session_key] = book
                        
#                     book_key = f"book_{book['name']}_{book['category']}_{idx}"
#                     col.markdown(
#                         f"""
#                         <div style="
#                             background-color: {category_color};
#                             height: 200px;
#                             width: 50px;
#                             margin: auto;
#                             padding: 10px;
#                             border-radius: 3px;
#                             color: white;
#                             writing-mode: vertical-rl;
#                             text-orientation: mixed;
#                             display: flex;
#                             align-items: center;
#                             justify-content: center;
#                             text-align: center;
#                             font-weight: bold;
#                             font-size: 12px;
#                             box-shadow: -2px 2px 5px rgba(0,0,0,0.2);
#                             border-left: 2px solid rgba(255,255,255,0.3);
#                         ">
#                             {truncate_text(book['name'])}
#                         </div>
#                         """,
#                         unsafe_allow_html=True
#                     )
                    
#                     if col.button("📖", key=book_key, help=book['name']):
#                         handle_book_click(st.session_state[book_session_key])

#             st.markdown("""
#                 <div style="
#                     height: 20px;
#                     background-color: #653005;
#                     margin-top: 10px;
#                     border-radius: 0 0 5px 5px;
#                 "></div>
#             """, unsafe_allow_html=True)

#             st.markdown("<br>", unsafe_allow_html=True)
# # Export the functions
__all__ = [
    'truncate_text',
    'get_category_color',
    'render_traditional_view',
    'render_column_view',
    'render_hybrid_view',
]