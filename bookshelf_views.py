import streamlit as st
from datetime import datetime
import uuid
import random
import json
from back import SnowparkManager
from typing import List, Dict, Optional
import os
from st_clickable_images import clickable_images


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
    

def book_spine_fragment(book, category, idx):
    category_color = get_category_color(category)
    book_key = f"book_{book['name']}_{category}_{idx}"
    
    spine_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
    <svg width="25" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="25" height="200" fill="{category_color}" rx="3"/>
        <rect x="0" y="0" width="2" height="200" fill="rgba(255,255,255,0.3)"/>
        <g transform="rotate(90 12.5 100)">
            <text 
                x="18.5" 
                y="100" 
                text-anchor="middle" 
                fill="white"
                font-weight="bold"
                font-size="10px"
                font-family="Arial, sans-serif"
                dominant-baseline="middle">{truncate_text(book['name'])}</text>
        </g>
    </svg>'''
    
    encoded_svg = spine_svg.replace('\n', ' ').replace('    ', '')
    encoded_svg = encoded_svg.replace('"', "'")
    encoded_svg = encoded_svg.replace('#', '%23')
    
    container_style = {
        'width': '35px',
        'height': '200px',
        'margin': '0 auto',  # Center in column
        'padding': '0',
        'box-shadow': '-2px 2px 5px rgba(0,0,0,0.2)',
        'border-radius': '3px',
        'cursor': 'pointer',
        'display': 'block'  # Changed to block for column layout
    }
    
    img_style = {
        'width': '100%',
        'height': '100%',
        'margin': '0',
        'padding': '0',
        'display': 'block'
    }
    
    clicked = clickable_images(
        paths=[f"data:image/svg+xml;utf8,{encoded_svg}"],
        titles=[book['name']],
        div_style=container_style,
        img_style=img_style,
        key=book_key
    )
    
    if clicked != -1:
        handle_book_click(book)

def render_traditional_view(files):
    categories = set(file["category"] for file in files)
    COLS_PER_ROW = 20
    
    for category in categories:
        st.markdown(f"### {category} ({len([f for f in files if f['category'] == category])})")
        
        # Top wooden bar
        st.markdown("""
            <div style="
                height: 20px;
                background-color: #452B1F;
                margin-bottom: -12px;
                border-radius: 5px 5px 0 0;
            "></div>
        """, unsafe_allow_html=True)
        
        books = [f for f in files if f["category"] == category]
        
        # Calculate number of rows needed
        num_rows = (len(books) + COLS_PER_ROW - 1) // COLS_PER_ROW
        
        # Render books row by row
        for row in range(num_rows):
            start_idx = row * COLS_PER_ROW
            end_idx = min(start_idx + COLS_PER_ROW, len(books))
            row_books = books[start_idx:end_idx]
            
            # Create columns for this row
            cols = st.columns(COLS_PER_ROW)
            
            # Fill the columns with books
            for col_idx in range(COLS_PER_ROW):
                with cols[col_idx]:
                    if col_idx < len(row_books):
                        book_spine_fragment(row_books[col_idx], category, start_idx + col_idx)
        
        # Bottom wooden bar
        st.markdown("""
            <div style="
                height: 20px;
                background-color: #452B1F;
                margin-top: -23px;
                border-radius: 0 0 5px 5px;
            "></div>
        """, unsafe_allow_html=True)

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

# def render_hybrid_view(files):
#     # Initialize session state if not already done
#     if 'selected_book' not in st.session_state:
#         st.session_state.selected_book = None
#     if 'current_view' not in st.session_state:
#         st.session_state.current_view = "bookshelf"

#     def handle_book_click(book):
#         """Helper function to handle book selection"""
#         st.session_state.selected_book = book
#         st.session_state.current_view = "details"
#         st.rerun()
    
#     # Category selection at the top
#     categories = ["All"] + ["Book", "PDF", "Research Paper", "Article", "Other"]
#     st.selectbox("Filter by Category", categories, key="active_category")
    
#     if st.session_state.active_category == "All":
#         category_books = {
#             cat: [b for b in files if b['category'] == cat]
#             for cat in ["Book", "PDF", "Research Paper", "Article", "Other"]
#             if any(b['category'] == cat for b in files)
#         }
#     else:
#         category_books = {
#             st.session_state.active_category: [
#                 b for b in files 
#                 if b['category'] == st.session_state.active_category
#             ]
#         }

#     ROWS_PER_CATEGORY = 2
    
#     for cat_idx, (category, books) in enumerate(category_books.items()):
#         if books:
#             category_color = get_category_color(category)
            
#             st.markdown(f"""
#                 <div style="
#                     background-color: {category_color};
#                     color: white;
#                     padding: 5px 10px;
#                     border-radius: 5px;
#                     margin: 10px 0;
#                 ">
#                     {category} ({len(books)} items)
#                 </div>
#             """, unsafe_allow_html=True)
            
#             for row_idx in range(ROWS_PER_CATEGORY):
#                 cols = st.columns(3)
                
#                 for col_idx, col in enumerate(cols):
#                     book_idx = row_idx * 3 + col_idx
                    
#                     if book_idx < len(books):
#                         book = books[book_idx]
#                         with col:
#                             # Store book in session state with a unique key
#                             book_session_key = f"book_data_{cat_idx}_{row_idx}_{col_idx}"
#                             if book_session_key not in st.session_state:
#                                 st.session_state[book_session_key] = book
                                
#                             unique_key = f"book_{book['name']}_{category}_{cat_idx}_{row_idx}_{col_idx}"
                            
#                             if col.button(
#                                 f"📖 {truncate_text(book['name'], length=30)}",
#                                 key=unique_key,
#                                 use_container_width=True,
#                             ):
#                                 handle_book_click(st.session_state[book_session_key])
                            
#                             # Separator line
#                             st.markdown(f"""
#                                 <div style="
#                                     height: 2px;
#                                     background: linear-gradient(to right, {category_color}20, {category_color}, {category_color}20);
#                                     margin: 0 0 10px 0;
#                                 "></div>
#                             """, unsafe_allow_html=True)
            
#             st.markdown("---")

def get_thumbnail(filename: str) -> str:
    """Retrieve thumbnail from database."""
    session = SnowparkManager.get_session()
    if not session:
        return None
        
    try:
        query = f"""
        SELECT THUMBNAIL
        FROM TESTDB.MYSCHEMA.BOOK_METADATA
        WHERE FILENAME = '{filename.replace("'", "''")}'
        """
        result = session.sql(query).collect()
        return result[0]['THUMBNAIL'] if result and len(result) > 0 else None
    finally:
        session.close()

import io
import docx

def get_first_page_content(filename: str) -> Optional[str]:
    """Get first page content from the document for fallback display."""
    session = SnowparkManager.get_session()
    if not session:
        return None
        
    try:
        query = f"""
        SELECT BINARY_CONTENT, METADATA, FILE_TYPE
        FROM {SnowparkManager.RAG_TABLE}
        WHERE FILENAME = '{filename.replace("'", "''")}'
        ORDER BY METADATA:chunk_number
        LIMIT 1
        """
        result = session.sql(query).collect()
        if result and len(result) > 0:
            binary_content = result[0]['BINARY_CONTENT']
            file_type = result[0]['FILE_TYPE']
            
            if file_type == 'text/plain':
                content = binary_content.decode('utf-8')
            elif file_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                doc = docx.Document(io.BytesIO(binary_content))
                content = '\n'.join([para.text for para in doc.paragraphs])
            else:
                return None
            
            # Take first 100 characters for preview
            return content[:100] + '...' if len(content) > 100 else content
        return None
    finally:
        session.close()

def truncate_filename(filename: str, max_length: int = 25) -> str:
    """Truncate filename to specified length while preserving file extension."""
    name, ext = os.path.splitext(filename)
    if len(filename) <= max_length:
        return filename
    
    # Calculate available length for name considering extension and ellipsis
    available_length = max_length - len(ext) - 3  # 3 for '...'
    if available_length < 1:
        return filename  # Return original if too short to truncate
        
    truncated_name = name[:available_length] + '...' + ext
    return truncated_name



def render_book_thumbnail(book: Dict, category_color: str, cat_idx: int, row_idx: int, col_idx: int):
    """Render an individual book thumbnail with library-style appearance."""
    thumbnail = get_thumbnail(book['name'])
    unique_key = f"book_{book['name']}_{category_color}_{cat_idx}_{row_idx}_{col_idx}"
    truncated_name = truncate_filename(book['name'])
    
    # Define consistent dimensions for all displays
    img_width = "200px"
    img_height = "200px"
    
    # Fallback image path (if no thumbnail is available)
    cover_icon = {
        "Book": "📚",
        "PDF": "📄",
        "Research Paper": "📋",
        "Article": "📰",
        "Other": "📎"
    }.get(book['category'], "📚")
    
    cursor_style = {"cursor": "pointer"}  # This will add the hand (pointer) cursor on hover
    
    # Ensure both the div and image are the same size
    container_style = {
        'width': img_width,
        'height': img_height,
        'display': 'flex',
        'justify-content': 'center',
        'align-items': 'center',
        'overflow': 'hidden',
        'background': 'transparent',
        'border': 'none',
        'box-shadow': 'none',
        'border-radius': '4px'
    }
    
    img_style = {
        'width': '100%',
        'height': '100%',
        'object-fit': 'contain',  # Ensures the image fills the container properly without distortion
        **cursor_style,
        "margin": "0px"
    }
    
    if thumbnail:
        # If thumbnail exists, use clickable_images for clickable thumbnail
        clicked = clickable_images(
            paths=[f"data:image/png;base64,{thumbnail}"], 
            titles=[book['name']],
            div_style=container_style,
            img_style=img_style,
            key=unique_key
        )
        if clicked != -1:
            st.session_state.selected_book = book
            st.session_state.current_view = "details"
            st.rerun()
    else:
        # If no thumbnail, fallback to category-based cover icon
        clicked = clickable_images(
            paths=[f"data:image/svg+xml;utf8,<svg width='100%' height='100%' xmlns='http://www.w3.org/2000/svg'><text x='50%' y='50%' font-size='80' text-anchor='middle' dy='.3em'>{cover_icon}</text></svg>"], 
            titles=[book['category']],
            div_style={**container_style, 'background': f'linear-gradient(145deg, {category_color}12, {category_color}34)'},
            img_style=img_style,
            key=unique_key
        )
        if clicked != -1:
            st.session_state.selected_book = book
            st.session_state.current_view = "details"
            st.rerun()
    
    # Display the book title below the thumbnail
    st.markdown(f"""
        <div style="
            width: {img_width};
            text-align: center;
            margin-top: 8px;
            color: white;
            font-size: 12px;
            overflow: hidden;
            text-overflow: ellipsis;get
            white-space: nowrap;
            padding: 0 5px;
            title="{book['name']}"
        ">{truncated_name}</div>
    """, unsafe_allow_html=True)






def render_hybrid_view(files: List[Dict]):
    """Enhanced hybrid view with realistic library-style display."""
    # Initialize session state
    if 'selected_book' not in st.session_state:
        st.session_state.selected_book = None
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "bookshelf"

    # Category filter
    categories = ["All"] + sorted(list(set(f["category"] for f in files)))
    st.selectbox("Filter by Category", categories, key="active_category")
    
    # Filter and group books
    if st.session_state.active_category == "All":
        category_books = {}
        for book in files:
            if book["category"] not in category_books:
                category_books[book["category"]] = []
            category_books[book["category"]].append(book)
    else:
        category_books = {
            st.session_state.active_category: [
                b for b in files if b['category'] == st.session_state.active_category
            ]
        }

    # Display books by category
    for cat_idx, (category, books) in enumerate(category_books.items()):
        if books:
            category_color = get_category_color(category)
            
            # Category header with shelf styling
            st.markdown(f"""
                <div style="
                    position: relative;
                    margin: 30px 0 15px 0;
                ">
                    <div style="
                        background-color: {category_color};
                        color: white;
                        padding: 10px 15px;
                        border-radius: 5px 5px 0 0;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        <span style="font-weight: bold;">{category}</span>
                        <span style="font-size: 0.9em;">({len(books)} items)</span>
                    </div>
                    <div style="
                        height: 15px;
                        background: linear-gradient(180deg, #2c1810 0%, #452B1F 100%);
                        border-radius: 0 0 5px 5px;
                    "></div>
                </div>
            """, unsafe_allow_html=True)
            
            # Display books in a 5-column grid
            cols_per_row = 5
            for row_idx in range(0, len(books), cols_per_row):
                cols = st.columns(cols_per_row)
                for col_idx, col in enumerate(cols):
                    if row_idx + col_idx < len(books):
                        with col:
                            render_book_thumbnail(
                                books[row_idx + col_idx],
                                category_color,
                                cat_idx,
                                row_idx,
                                col_idx
                            )
            
            # Add wooden shelf at the bottom
            st.markdown(f"""
                <div style="
                    height: 20px;
                    background: linear-gradient(180deg, #452B1F 0%, #2c1810 100%);
                    border-radius: 5px;
                    margin-bottom: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                "></div>
            """, unsafe_allow_html=True)

def get_category_color(category: str) -> str:
    """Get color for category."""
    colors = {
        "Book": "#2ecc71",
        "PDF": "#e74c3c",
        "Research Paper": "#3498db",
        "Article": "#9b59b6",
        "Other": "#95a5a6"
    }
    return colors.get(category, "#95a5a6")

__all__ = [
    'truncate_text',
    'get_category_color',
    'render_traditional_view',
    'render_column_view',
    'render_hybrid_view',
]