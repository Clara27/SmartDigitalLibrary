import streamlit as st
import json
from back import SnowparkManager
from truelens_utils import TruLensEvaluator

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
                    background-image: url("https://i.postimg.cc/bwT8wrQM/backpal.png");
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
        #st.set_page_config(page_title="PAL - Personal AI Library", layout="wide", initial_sidebar_state="collapsed")
        st.set_page_config(page_title="PAL - Personal AI Library", layout="wide")
        self.add_bg_image()
        
        st.markdown("""
        <style>
            /* Your existing styles... */
                        
            div.stChatMessage {
                background-color: #B768A2 !important;
                color: white !important;
                border-radius: 15px !important;
                padding: 15px !important;
                border: 1px solid rgba(155, 77, 202, 0.3) !important;
            }

            /* Assistant messages */
            div.stChatMessage.assistant {
                background-color: #CEA2FD !important;
                color: white !important;
                border-radius: 15px !important;
                padding: 15px !important;
                border: 1px solid rgba(213, 130, 181, 0.3) !important;
            }
            
                    /* User message - purple background */
            div.stChatMessage[data-testid="stChatMessageContent-user"] {
                background-color: rgba(155, 77, 202, 0.4) !important;
            }

           
            /* Style for usernames in chat */
            .stChatMessage .username {
                color: #E5B8F4 !important;
                font-weight: bold !important;
            }
            
            /* Add glow effect on hover */
            [data-testid="stChatMessageContent-user"]:hover,
            [data-testid="stChatMessageContent-assistant"]:hover {
                box-shadow: 0 0 15px rgba(155, 77, 202, 0.3) !important;
                transition: box-shadow 0.3s ease !important;
            }
            
            /* Make text more readable */
            .stChatMessage p {
                margin: 0 !important;
                line-height: 1.5 !important;
                font-size: 16px !important;
            }
        </style>
    """, unsafe_allow_html=True)
        
        # Add space at top of page
        #st.markdown('<div style="padding-top: 1rem;"></div>', unsafe_allow_html=True)
        
        # Create elegant header with logo and title
        header_cols = st.columns([0.8, 4, 3])  # Adjusted ratios for better spacing
        
        with header_cols[0]:
            st.markdown(
                """
                <div style="margin-top: -60px; text-align: left;">
                    <img src="https://i.postimg.cc/cJrXGrxd/PALicon.png" width="150">
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with header_cols[1]:
            st.markdown("""
                <h1 style='
                    margin: 0;
                    padding: 8px 0 0 0;
                    font-size: 49px;
                    margin-top: -30px;
                    font-weight: 800;
                    background: linear-gradient(45deg, #E5B8F4, #C147E9);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;'>
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
                    background-color: #D982B5 !important;
                    color: #FFFFFF !important;
                    border-radius: 8px !important;
                    border: 1px solid rgba(155, 77, 202, 0.2) !important;
                    padding: 0.75rem !important;
                    transition: all 0.3s ease !important;
                }
                
                .stTextInput input:focus, .stSelectbox select:focus {
                    border-color: #D982B5 !important;
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
        
        

    def get_chatbot_response(self, user_input: str, book_name: str) -> str:
        """Generate a response using Snowflake session with improved error handling."""
        try:
            session = SnowparkManager.get_session()
            if not session:
                return "I'm having trouble accessing the document. Please try again."
                
            # Get relevant document content
            safe_book_name = book_name.replace("'", "''")
            content_query = f"""
            SELECT CONTENT, METADATA:page_number::INTEGER as PAGE_NUM
            FROM RAG_DOCUMENTS_TMP
            WHERE FILENAME = '{safe_book_name}'
            ORDER BY PAGE_NUM
            """
            results = session.sql(content_query).collect()
            
            if not results:
                return f"I couldn't find any content in the document '{book_name}'. Please make sure the document is properly loaded."
                
            # Combine content from all pages with page numbers
            document_content = "\n".join([
                f"[Page {row['PAGE_NUM']}]: {row['CONTENT']}"
                for row in results
            ])
            
            # Create a focused system prompt
            system_prompt = f"""You are an AI assistant specifically analyzing the document '{book_name}'.
            
            Instructions:
            1. Base your answers ONLY on the document content provided below
            2. If you can't find the information in the document, say "I cannot find information about [topic] in this document"
            3. If you find the information, cite the page number in your response
            4. Be precise and accurate - don't make assumptions
            5. If the question is unclear, ask for clarification
            
            Current document content:
            {document_content}
            """
            
            # Clean and escape the prompts
            safe_user_input = user_input.replace("'", "''")
            safe_system_prompt = system_prompt.replace("'", "''")
            
            # Generate response
            query = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large',
                ARRAY_CONSTRUCT(
                    OBJECT_CONSTRUCT('role', 'system', 'content', '{safe_system_prompt}'),
                    OBJECT_CONSTRUCT('role', 'user', 'content', 'Based on the document content provided, {safe_user_input}')
                ),
                OBJECT_CONSTRUCT(
                    'temperature', 0.3,
                    'max_tokens', 500
                )
            ) as response;
            """
            
            result = session.sql(query).collect()
            
            if result and result[0]['RESPONSE']:
                try:
                    response_data = json.loads(result[0]['RESPONSE'])
                    if 'choices' in response_data and response_data['choices']:
                        if isinstance(response_data['choices'][0], dict):
                            if 'message' in response_data['choices'][0]:
                                return response_data['choices'][0]['message'].get('content', '').strip()
                            elif 'messages' in response_data['choices'][0]:
                                return response_data['choices'][0]['messages'].strip()
                        return str(response_data['choices'][0]).strip()
                    
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {str(e)}")
                    # Try to use raw response if JSON parsing fails
                    return str(result[0]['RESPONSE']).strip()
                    
            return "I cannot generate a proper response from the document content. Please try rephrasing your question."
                
        except Exception as e:
            print(f"Error in get_chatbot_response: {str(e)}")
            return "I encountered an error while analyzing the document. Please try again."
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
        """Display recommendations and tips in the right panel."""
        if st.session_state["selected_book"]:
            # Initialize states if not exists
            if 'show_recommendations' not in st.session_state:
                st.session_state.show_recommendations = False
            if 'recommendations_cache' not in st.session_state:
                st.session_state.recommendations_cache = None
                
            # Recommendations in Expander
            with st.expander("🔍 Find Similar Books", expanded=st.session_state.show_recommendations):
                if st.button("PAL's Recommendations", 
                            key=f"rec_button_{st.session_state['selected_book']['name']}",
                            type="primary",
                            use_container_width=True):
                    st.session_state.show_recommendations = True
                    with st.spinner("Finding recommendations..."):
                        recommendations = SnowparkManager.get_book_recommendations(
                            st.session_state["selected_book"]["name"],
                            recommendation_type="hybrid",
                            limit=3
                        )
                        st.session_state.recommendations_cache = recommendations
                
                # Show cached recommendations if available
                if st.session_state.show_recommendations and st.session_state.recommendations_cache:
                    recommendations = st.session_state.recommendations_cache
                    if recommendations:
                        for idx, rec in enumerate(recommendations):
                            similarity_percentage = f"{rec['similarity_score']*100:.1f}%"
                            st.markdown(f'''
                                <div style="
                                    background-color: #4A0A67;
                                    padding: 15px;
                                    border-radius: 10px;
                                    margin-bottom: 10px;
                                    border: 2px solid #9b4dca;
                                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                                ">
                                    <div style="
                                        display: flex;
                                        justify-content: space-between;
                                        align-items: center;
                                        border-bottom: 1px solid #9b4dca;
                                        padding-bottom: 8px;
                                        margin-bottom: 8px;
                                    ">
                                        <span style="
                                            color: #E5B8F4;
                                            font-size: 16px;
                                            font-weight: bold;
                                        ">📚 {rec['name']}</span>
                                    </div>
                                    <div style="
                                        display: flex;
                                        justify-content: space-between;
                                        align-items: center;
                                    ">
                                        <div style="
                                            background-color: #9b4dca;
                                            padding: 4px 8px;
                                            border-radius: 15px;
                                            color: white;
                                            font-size: 14px;
                                        ">{rec['category']}</div>
                                        <div style="
                                            background-color: #6A0DAD;
                                            padding: 4px 12px;
                                            border-radius: 15px;
                                            color: white;
                                            font-size: 14px;
                                        ">Match: {similarity_percentage}</div>
                                    </div>
                                </div>
                            ''', unsafe_allow_html=True)
                        
                        # Add a reset button
                        if st.button("Clear Recommendations", 
                                    key="clear_recs",
                                    type="secondary",
                                    use_container_width=True):
                            st.session_state.show_recommendations = False
                            st.session_state.recommendations_cache = None
                            st.rerun()
                    else:
                        st.info("Looking for recommendations in your library...")

        # Tips Section
        st.markdown('''
        <div class="info-card" style="background-color: #743089; padding: 20px; border-radius: 10px; margin-top: 20px;">
            <p class="section-header" style="color: #E5B8F4; font-size: 18px; font-weight: bold;">💡 Ask PAL</p>
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="margin-bottom: 10px; color: #FFF;">1. What are the main themes?</li>
                <li style="margin-bottom: 10px; color: #FFF;">2. Summarize the key points</li>
                <li style="margin-bottom: 10px; color: #FFF;">3. What's unique about this book?</li>
                <li style="margin-bottom: 10px; color: #FFF;">4. How does it compare to others?</li>
                <li style="margin-bottom: 10px; color: #FFF;">5. What are its strengths?</li>
            </ul>
        </div>
        ''', unsafe_allow_html=True)

        # Quick Stats
        if st.session_state["selected_book"]:
            book = st.session_state["selected_book"]
            st.markdown(f'''
            <div class="info-card" style="background-color: #743089; padding: 20px; border-radius: 10px; margin-top: 20px;">
                <p class="section-header" style="color: #E5B8F4; font-size: 18px; font-weight: bold;">📊 Quick Stats</p>
                <ul style="list-style: none; padding: 0; margin: 0;">
                    <li style="margin-bottom: 10px; color: #FFF;">Category: {book["category"]}</li>
                    <li style="margin-bottom: 10px; color: #FFF;">Added: {book["date_added"]}</li>
                    <li style="margin-bottom: 10px; color: #FFF;">Size: {book["size"]}</li>
                </ul>
            </div>
            ''', unsafe_allow_html=True)

    def seamless_chat_interface(self):
        """Unified interface with two-column layout."""
        col1, col2 = st.columns([2, 1])
        
        st.markdown("""
            <style>
            /* Target specifically the selectbox label text */
            .stSelectbox > label {
                font-size: 48px !important;
                color: #0066CC !important;
                font-weight: bold !important;
            }
            
            /* Target the select box options */
            .stSelectbox > div > div > div {
                font-size: 18px !important;  /* Size for dropdown options */
            }
            </style>
        """, unsafe_allow_html=True)

        with col1:
            books = self.fetch_books()

            if books:
                book_names = [book['name'] for book in books]
                selected_book_name = st.selectbox(
                    label="📚 Choose a book",  # Empty label since we're using custom label above
                    options=book_names,
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
                        
                        
                        st.empty()
                        
                        print("\n=== TruLens Evaluator Status Check ===")
                        #if 'trulens_evaluator' not in st.session_state:
                        st.session_state.trulens_evaluator = TruLensEvaluator()
                    
                        # Check 1: Does the attribute exist?
                        has_attr = hasattr(st.session_state, 'trulens_evaluator')
                        #print(f"1. Has trulens_evaluator attribute: {has_attr}")
                        
                        # Check 2: Is the evaluator object not None?
                        evaluator_exists = bool(st.session_state.get('trulens_evaluator'))
                        #print(f"2. Evaluator object exists: {evaluator_exists}")
                        
                       
                        
                        # Check 3: Is it initialized?
                        if evaluator_exists:
                            is_initialized = getattr(st.session_state.trulens_evaluator, 'initialized', False)
                            print(f"3. Evaluator initialized: {is_initialized}")
                            #print(f"4. Evaluator type: {type(st.session_state.trulens_evaluator)}")
                            #print(f"5. Evaluator attributes: {dir(st.session_state.trulens_evaluator)}")
                        else:
                            print("3. Can't check initialization - evaluator doesn't exist")

                        # TruLens evaluation in the background
                        if (hasattr(st.session_state, 'trulens_evaluator') and 
                            st.session_state.trulens_evaluator and 
                            st.session_state.trulens_evaluator.initialized):

                            try:
                                eval_results = st.session_state.trulens_evaluator.evaluate_pal_chat(
                                    query=user_input,
                                    filename = current_book,
                                    response=bot_response,
                                    operation_type="CHAT",
                                    style="Normal",
                                    format_type="Conversation",
                                    output_token_count=len(bot_response.split())
                                )

                                # Display evaluation results
                                if eval_results and eval_results.get('status') == 'success':
                                    st.info("TruLens Evaluation:")
                                    st.write(eval_results.get('summary'))

                            except Exception as e:
                                print(f"Error in TruLens evaluation: {str(e)}")
                        
                        
                        
                        
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
