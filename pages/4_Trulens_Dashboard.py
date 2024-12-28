import streamlit as st
from back import SnowparkManager

class Trulens_Dashboard:
    def __init__(self):
        self.setup_page()

        if 'dashboard_url' not in st.session_state:
          st.session_state.dashboard_url = None
          
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


    def render_dashboard_ui(self):
        st.title("TruLens Dashboard")
        st.markdown("""### 📊 TruLens Analytics Dashboard""")
    
        st.markdown("""
            <style>
            [data-testid="stSidebar"] {
                background-color: #72245C;
            }
            </style>
        """, unsafe_allow_html=True)
        
    
        url = st.session_state.get('dashboard_url')
        if url:
            st.markdown(f"""
                <div style="padding: 20px; border-radius: 8px; 
                    background-color: #1E0935; border: 1px solid #541680; 
                    margin: 10px 0; text-align: center;">
                    <a href="{url}" target="_blank" style="color: #FFFFFF; 
                        text-decoration: none; font-size: 18px;">
                        🔗 Open TruLens Dashboard
                    </a>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Processing... Dashboard URL will appear here once generated.")
            
            
    def run(self):
        """Run the main application."""
        self.render_dashboard_ui()


if __name__ == "__main__":
    dashboard = Trulens_Dashboard()
    dashboard.run()
    