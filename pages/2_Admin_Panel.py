import streamlit as st
from back import SnowparkManager
import time
import uuid
from datetime import datetime
import json
import pandas as pd

class AdminPanel:
    def __init__(self):
        self.setup_page()
        self.initialize_session_state()
     
    def add_bg_image(self):
        """Add a background image to the app."""
        st.markdown(
            f"""
            <style>
                .stApp {{
                    background-image: url("https://i.postimg.cc/qM6yd5mJ/Picture117.png");
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
        """Configure page settings"""
        st.set_page_config(
            page_title="Library Admin Panel",
            layout="wide"
        )
        
        self.add_bg_image()
        # Create elegant header with logo and title
        header_cols = st.columns([0.8, 4, 3])  # Adjusted ratios for better spacing
        
        with header_cols[0]:
            st.markdown(
                """
                <div style="margin-top: -10px; text-align: left;">
                    <img src="https://i.postimg.cc/cJrXGrxd/PALicon.png" width="100">
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
                    font-weight: 800;
                    color: #FFFFFF;
                    background: linear-gradient(45deg, #9b4dca, #6772e5);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;'>
                    Admin Panel
                </h1>
                """, 
                unsafe_allow_html=True
            )
           
        #with header_cols[2]:
                # st.image("https://i.postimg.cc/wMhnbwVn/Banner-Image.png", width=300, use_container_width=True)        
   
        
        #st.sidebar.image("https://i.postimg.cc/BXSNChRp/robot-dashboard.png", width=100, use_container_width=True)
        st.markdown("""
            <style>
            [data-testid="stSidebar"] {
                background-color: #72245C;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Custom styling
        st.markdown("""
            <style>
                .stApp {
                    background-color: #220135;
                    color: #FFFFFF;
                }
                .info-box {
                    background-color: #1a0d27;
                    border: 1px solid #9b4dca;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .notification-box {
                    background-color: #311847;
                    border: 1px solid #6772e5;
                    padding: 20px;
                    border-radius: 5px;
                }
            </style>
        """, unsafe_allow_html=True)
        
    def clean_filename(self, filename: str) -> str:
        """Clean up file name by removing duplicate extensions"""
        if filename.lower().endswith('.pdf.pdf'):
            return filename[:-4]
        return filename
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'upload_queue' not in st.session_state:
            st.session_state.upload_queue = []
        if 'queue_processing' not in st.session_state:
            st.session_state.queue_processing = False
        if 'files' not in st.session_state:
            st.session_state.files = []
            
    def render_upload_interface(self):
        st.header("📚 Library Management")
        
        try:
            session = SnowparkManager.get_session()
            if not session:
                st.error("Failed to establish database connection")
                return
        except Exception as e:
            st.error(f"Database connection error: {str(e)}")
            return
        
        col1, col2 = st.columns([2, 1], gap="large")
        
        with col1:
            upload_tab, delete_tab = st.tabs(["📥 Upload Documents", "🗑️ Delete Document"])
            
            with upload_tab:
                uploaded_files = st.file_uploader(
                    "Choose files to Upload",
                    type=["pdf", "doc", "docx", "txt"],
                    accept_multiple_files=True,
                    help="Upload multiple documents (Max size per file: 10MB)"
                )
                
                category = st.selectbox(
                    "Category",
                    ["Book", "PDF", "Research Paper", "Article", "Other"]
                )
                
                if uploaded_files:
                    if st.button("Add to Queue", type="primary"):
                        for file in uploaded_files:
                            if not any(q['file'].name == file.name for q in st.session_state.upload_queue):
                                st.session_state.upload_queue.append({
                                    'id': str(uuid.uuid4()),
                                    'file': file,
                                    'category': category,
                                    'status': 'queued',
                                    'progress': 0,
                                    'message': 'Waiting in queue'
                                })
                                
                                new_file = {
                                    "name": file.name,
                                    "category": category,
                                    "date_added": datetime.now().strftime("%Y-%m-%d"),
                                    "size": f"{file.size / 1024:.1f} KB",
                                    "usage_stats": {
                                        "queries": 0,
                                        "summaries": 0
                                    }
                                }
                                
                                st.session_state.files = [f for f in st.session_state.files if f['name'] != file.name]
                                st.session_state.files.append(new_file)
                        
                        st.success("Files added to queue!")
                
                if st.session_state.upload_queue:
                    st.markdown("---")
                    st.subheader("📋 Upload Queue")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if not st.session_state.queue_processing:
                            if st.button("Add to Library", type="primary", key="process_queue"):
                                st.session_state.queue_processing = True
                    with col2:
                        if st.button("Clear Queue", type="secondary", key="clear_queue"):
                            st.session_state.upload_queue = []
                            st.session_state.queue_processing = False
                    
                    queue_status_container = st.container()
                    with queue_status_container:
                        for idx, item in enumerate(st.session_state.upload_queue):
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                            with col1:
                                st.write(f"📄 {item['file'].name}")
                            with col2:
                                st.write(f"Category: {item['category']}")
                            with col3:
                                st.write(f"Status: {item['status']}")
                            with col4:
                                if item['status'] not in ['completed', 'processing']:
                                    if st.button("🗑️", key=f"remove_{item['id']}"):
                                        st.session_state.upload_queue.pop(idx)
                            
                            if item['status'] != 'queued':
                                st.progress(item['progress'], text=item['message'])
                    
                    if st.session_state.queue_processing:
                        processing_complete = True
                        
                        for item in st.session_state.upload_queue:
                            if item['status'] == 'queued':
                                processing_complete = False
                                status_placeholder = st.empty()
                                status_placeholder.info(f"Processing {item['file'].name}...")
                                
                                try:
                                    item['status'] = 'processing'
                                    success, error_msg, documents = SnowparkManager.process_pdf(
                                        item['file'].read(),
                                        item['file'].name,
                                        item['file'].type
                                    )

                                    if success and documents:
                                        if SnowparkManager.upload_documents(
                                            session=session,
                                            documents=documents,
                                            filename=item['file'].name,
                                            file_type=item['file'].type,
                                            api_key=st.session_state.mistral_api_key
                                        ):
                                            status_placeholder.success(f"✅ {item['file'].name} successfully added!")
                                            item['status'] = 'completed'
                                            item['progress'] = 100
                                            st.rerun() 
                                        else:
                                            status_placeholder.error(f"Failed to upload {item['file'].name}")
                                            item['status'] = 'failed'
                                    else:
                                        status_placeholder.error(f"Failed to process {item['file'].name}: {error_msg}")
                                        item['status'] = 'failed'
                                    
                                except Exception as e:
                                    st.error(f"Error processing {item['file'].name}: {str(e)}")
                                    item['status'] = 'failed'
                        
                        if processing_complete:
                            st.session_state.queue_processing = False
                            st.success("✅ All files processed!")
                            
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
                            progress_placeholder = st.empty()
                            progress_placeholder.progress(0, text="Starting deletion...")
                            
                            selected_filename = book_to_delete.split(" (")[0]
                            
                            try:
                                progress_placeholder.progress(0.33, text="Removing metadata...")
                                delete_metadata_sql = f"""
                                DELETE FROM TESTDB.MYSCHEMA.BOOK_METADATA 
                                WHERE FILENAME = '{selected_filename.replace("'", "''")}'
                                """
                                session.sql(delete_metadata_sql).collect()
                                
                                progress_placeholder.progress(0.66, text="Removing document content...")
                                delete_rag_sql = f"""
                                DELETE FROM {SnowparkManager.RAG_TABLE}
                                WHERE FILENAME = '{selected_filename.replace("'", "''")}'
                                """
                                session.sql(delete_rag_sql).collect()
                                
                                progress_placeholder.progress(1.0, text="Finalizing...")
                                st.session_state.files = [
                                    f for f in st.session_state.files 
                                    if f['name'] != selected_filename
                                ]
                                
                                progress_placeholder.empty()
                                st.success(f"✅ Document '{selected_filename}' deleted successfully!")
                                time.sleep(1)
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Failed to delete from database: {str(e)}")
                                
                        except Exception as e:
                            st.error(f"Error during deletion: {str(e)}")
                else:
                    st.info("No documents available to delete")
        
        with col2:
            self.render_admin_trivia()
            self.render_notifications()
            
            
        collapsible_container = st.container()

        with collapsible_container:
            collapsible = st.expander("📂 Uploaded Files")
            with collapsible:
                files_dataframe_placeholder = st.empty()
                
        if st.session_state.files:
            files_df = pd.DataFrame(st.session_state.files)
            with files_dataframe_placeholder:
                st.dataframe(files_df)
        
        session.close()
    
    def render_admin_trivia(self):
        with st.container():
            st.markdown(
                """
                <div class="info-box">
                    <h3>📌 Admin Trivia</h3>
                    <ul>
                        <li>Did you know? The Library of Congress is the largest library in the world, with more than 170 million items!</li>
                        <li>Fun fact: The most expensive book ever sold at auction was Leonardo da Vinci's "Codex Leicester," which sold for $30.8 million in 1994.</li>
                        <li>Interesting statistic: The average person reads about 12 books per year.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    def render_notifications(self):
        with st.container():
            st.markdown(
                """
                <div class="notification-box">
                    <h3>🔔 Notifications</h3>
                    <div id="notifications"></div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        notification_container = st.empty()
        
        notifications = []
        
        def display_notification(message, notification_type="info"):
            if notification_type == "info":
                st.info(message)
            elif notification_type == "warning":
                st.warning(message)
            elif notification_type == "error":
                st.error(message)
            elif notification_type == "success":
                st.success(message)
        
        def trigger_notification(message, notification_type="info"):
            notifications.append({"message": message, "type": notification_type})
            
            top_notifications = notifications[-5:]
            
            with notification_container:
                for notification in top_notifications:
                    display_notification(notification["message"], notification["type"])
        
        trigger_notification("Document uploaded successfully!", "success")
        trigger_notification("User logged in.", "info")
        trigger_notification("System error occurred.", "error")
        trigger_notification("Backup completed.", "success")
        trigger_notification("User accessed a document.", "info")
        trigger_notification("Another notification.", "info")
        
        
        
    
    def run(self):
        self.render_upload_interface()

if __name__ == "__main__":
    admin = AdminPanel()
    admin.run()