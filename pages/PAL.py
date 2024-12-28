import streamlit as st
import json
from back import SnowparkManager

class PAL:
    def __init__(self):
        self.setup_page()
        self.initialize_session_state()

    def add_bg_image(self):
        """Add a background image to the app."""
        st.markdown(
            f"""
            <style>
                .stApp {{
                    background-image: url("https://i.postimg.cc/zB4sY92Y/Picture114.png");
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

  
        
    def setup_page(self):
        """Configure the Streamlit page and apply custom styling."""
        st.set_page_config(page_title="PAL - Personal AI Library", layout="wide", initial_sidebar_state="collapsed")
        self.add_bg_image()
        
        # Add space at top of page
        #st.markdown('<div style="padding-top: 1rem;"></div>', unsafe_allow_html=True)
        
        # Create elegant header with logo and title
        header_cols = st.columns([0.8, 4, 3])  # Adjusted ratios for better spacing
        
        with header_cols[0]:
            st.image("https://i.postimg.cc/cJrXGrxd/PALicon.png", width=100)
        
        with header_cols[1]:
                st.markdown("""
                    <h1 style='
                        margin: 0;
                        padding: 8px 0 0 0;
                        font-size: 49px;
                        font-weight: 800;
                        color: #FFFFFF;
                        background: linear-gradient(45deg, #9b4dca, #6772e5);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;'>
                        Personal AI Librarian
                    </h1>
                    """, 
                    unsafe_allow_html=True
                )
            
        #with header_cols[2]:
                 #st.image("https://i.postimg.cc/wMhnbwVn/Banner-Image.png", width=300, use_container_width=True)
        
        st.markdown("""
            <style>
            [data-testid="stSidebar"] {
                background-color: #4E2A84;
            }
            </style>
        """, unsafe_allow_html=True)
            
        #st.sidebar.image("https://i.postimg.cc/BXSNChRp/robot-dashboard.png", width=100, use_container_width=True)
        # Update existing styles for more elegance
        st.markdown("""
            <style>
                /* Refined container styling */
                .css-1d391kg {
                    background-color: rgba(30, 9, 53, 0.85) !important;
                    backdrop-filter: blur(12px) !important;
                    border-radius: 12px !important;
                    border: 1px solid rgba(155, 77, 202, 0.1) !important;
                    padding: 1.5rem !important;
                }
                
                /* Enhanced input field styling */
                .stTextInput input, .stSelectbox select {
                    background-color: rgba(30, 9, 53, 0.7) !important;
                    color: #FFFFFF !important;
                    border-radius: 8px !important;
                    border: 1px solid rgba(155, 77, 202, 0.2) !important;
                    padding: 0.75rem !important;
                    transition: all 0.3s ease !important;
                }
                
                .stTextInput input:focus, .stSelectbox select:focus {
                    border-color: rgba(155, 77, 202, 0.5) !important;
                    box-shadow: 0 0 0 2px rgba(155, 77, 202, 0.2) !important;
                }
                
                /* Refined chat message styling */
                .stChatMessage {
                    background-color: rgba(30, 9, 53, 0.75) !important;
                    border-radius: 12px !important;
                    backdrop-filter: blur(12px) !important;
                    border: 1px solid rgba(155, 77, 202, 0.1) !important;
                    padding: 1rem !important;
                    margin: 0.5rem 0 !important;
                }
                
                /* Enhanced info card styling */
                .info-card {
                    background-color: rgba(30, 9, 53, 0.75);
                    border-radius: 12px;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                    border: 1px solid rgba(155, 77, 202, 0.1);
                    backdrop-filter: blur(12px);
                    transition: transform 0.3s ease;
                }
                
                .info-card:hover {
                    transform: translateY(-2px);
                }
                
                /* Refined section headers */
                .section-header {
                    color: #9b4dca;
                    font-size: 1.1em;
                    font-weight: 500;
                    margin-bottom: 1rem;
                    letter-spacing: 0.5px;
                }
                
                /* Enhanced button styling */
                .stButton button {
                    background-color: rgba(155, 77, 202, 0.7) !important;
                    color: white !important;
                    border-radius: 8px !important;
                    border: 1px solid rgba(155, 77, 202, 0.2) !important;
                    padding: 0.75rem 1.5rem !important;
                    transition: all 0.3s ease !important;
                    font-weight: 500 !important;
                    letter-spacing: 0.5px !important;
                }
                
                .stButton button:hover {
                    background-color: rgba(155, 77, 202, 0.9) !important;
                    transform: translateY(-2px) !important;
                    box-shadow: 0 4px 12px rgba(155, 77, 202, 0.2) !important;
                }
                
                /* Chat input label styling */
                .chat-label {
                    color: #9b4dca;
                    font-size: 1.1em;
                    font-weight: 500;
                    margin: 1rem 0 0.5rem 0;
                    letter-spacing: 0.5px;
                }
            </style>
        """, unsafe_allow_html=True)
    
    def initialize_session_state(self):
        """Initialize session state variables."""
        if "history" not in st.session_state:
            st.session_state["history"] = []
        if "selected_book" not in st.session_state:
            st.session_state["selected_book"] = None
        if "previous_book" not in st.session_state:
            st.session_state["previous_book"] = None

    def clear_chat_history(self):
        """Clear the chat history."""
        st.session_state["history"] = []
        st.rerun()
        
        

    def get_chatbot_response(self, user_input, book_name):
        """Generate a response using Snowflake session."""
        try:
            session = SnowparkManager.get_session()
            safe_book_name = book_name.replace("'", "''")
            safe_user_input = user_input.replace("'", "''")
            
            query = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large',
                ARRAY_CONSTRUCT(
                    OBJECT_CONSTRUCT('role', 'system', 'content', 'You are discussing book: {safe_book_name}. Provide clear, concise responses under 300 words.'),
                    OBJECT_CONSTRUCT('role', 'user', 'content', '{safe_user_input}')
                ),
                OBJECT_CONSTRUCT(
                    'temperature', 0.7,
                    'max_tokens', 400
                )
            ) as response;
            """
            
            result = session.sql(query).collect()
            
            if result and result[0]['RESPONSE']:
                response_data = json.loads(result[0]['RESPONSE'])
                if 'choices' in response_data and response_data['choices']:
                    if 'messages' in response_data['choices'][0]:
                        return response_data['choices'][0]['messages']
                
            return "I apologize, but I couldn't generate a response."
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return "I'm sorry, I couldn't process your request."
        finally:
            if session:
                session.close()

    def fetch_books(self):
        """Fetch books from the database using the SnowparkManager."""
        try:
            session = SnowparkManager.get_session()
            query = "SELECT * FROM TESTDB.MYSCHEMA.BOOK_METADATA"
            results = session.sql(query).collect()

            books = [
                {
                    "name": row["FILENAME"],
                    "category": row["CATEGORY"],
                    "date_added": row["DATE_ADDED"].strftime("%Y-%m-%d"),
                    "size": row["SIZE"],
                    "usage_stats": json.loads(row["USAGE_STATS"])
                }
                for row in results
            ]
            return books

        except Exception as e:
            st.error(f"Failed to fetch books: {str(e)}")
            return []

    def display_info_panel(self):
        """Display the information panel with tips and suggested questions."""
        st.markdown('''
        <div class="info-card" style="background-color: #743089; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
            <p class="section-header" style="color: #3498db; font-size: 18px; font-weight: bold;">💡 Suggested Questions</p>
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="margin-bottom: 10px;">1. Can you summarize the main plot?</li>
                <li style="margin-bottom: 10px;">2. Who are the key characters?</li>
                <li style="margin-bottom: 10px;">3. What themes are explored?</li>
                <li style="margin-bottom: 10px;">4. What's the historical context?</li>
                <li style="margin-bottom: 10px;">5. How does this compare to similar works?</li>
            </ul>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('''
        <div class="info-card" style="background-color: #743089; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
            <p class="section-header" style="color: #3498db; font-size: 18px; font-weight: bold;">📖 Book Trivia </p>
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="margin-bottom: 10px;">• E-book adoption: About 25% of personal library owners have adopted e-books, while 75% still prefer physical books.</li>
                <li style="margin-bottom: 10px;">• The smallest personal library: The smallest library in the world is located in a phone booth in Somerset, England, and contains about 100 books.</li>
            </ul>
        </div>
        ''', unsafe_allow_html=True)

    def seamless_chat_interface(self):
        """Unified interface with two-column layout."""
        col1, col2 = st.columns([2, 1])

        with col1:
            books = self.fetch_books()

            if books:
                book_names = [book['name'] for book in books]
                selected_book_name = st.selectbox(
                    "📚 Choose a book",
                    book_names,
                    key="book_select",
                    index=0 if not st.session_state["selected_book"] else book_names.index(st.session_state["selected_book"]["name"])
                )
                
                if selected_book_name:
                    # Get the selected book
                    current_book = next(book for book in books if book['name'] == selected_book_name)
                    
                    # Clear chat if book selection changes
                    if (st.session_state["previous_book"] is None or 
                        st.session_state["previous_book"]["name"] != current_book["name"]):
                        st.session_state["history"] = []
                        st.session_state["previous_book"] = current_book
                    
                    st.session_state["selected_book"] = current_book
                    
                    # Keep the clear chat button for manual clearing
                    if st.button("🗑️ Clear Chat"):
                        self.clear_chat_history()

                if st.session_state["selected_book"]:
                    # Display chat history
                    for user_message, bot_message in st.session_state["history"]:
                        st.chat_message("user").markdown(user_message)
                        st.chat_message("assistant").markdown(bot_message)
                        
                        
                    st.markdown("""
                        <div style="
                            margin-bottom: 10px;
                            color: #9b4dca;
                            font-size: 1.1em;
                            font-weight: bold;
                        ">
                            💬 Ask PAL
                        </div>
                    """, unsafe_allow_html=True)

                    # Chat input
                    user_input = st.chat_input("Ask about the book or chat with PAL...")
                    if user_input:
                        bot_response = self.get_chatbot_response(user_input, st.session_state["selected_book"]["name"])
                        st.session_state["history"].append((user_input, bot_response))
                        st.chat_message("user").markdown(user_input)
                        st.chat_message("assistant").markdown(bot_response)
            else:
                st.warning("No books available.")

        with col2:
            self.display_info_panel()

    def run(self):
        """Run the main application."""
        self.seamless_chat_interface()

if __name__ == "__main__":
    pal = PAL()
    pal.run()
