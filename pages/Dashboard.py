import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid
from front import SnowparkManager
import time
import psutil
import json
from typing import Dict, Any, Optional
from gtts import gTTS
import tempfile
import os
import re
import traceback
from truelens_utils import WindowSizeAnalyzer  
from truelens_utils import TruLensEvaluator

class DashboardPage:
    def __init__(self):
        """Initialize the dashboard"""
        self.setup_styling()
        self.add_bg_image()
        self.session = None
        
        # Initialize presentation state
        if 'last_presentation' not in st.session_state:
            st.session_state.last_presentation = None
        if 'presentation_settings' not in st.session_state:
            st.session_state.presentation_settings = {
                'duration': 1,
                'audience': 'Business Managers',
                'tech_level': 'Moderate',
                'style': 'Professional'
            }
            
        # Initialize TruLens evaluator
        if ('mistral_api_key' in st.session_state and 
            st.session_state.get('api_key_valid', False)):
            try:
                if 'trulens_evaluator' not in st.session_state:
                    st.session_state.trulens_evaluator = TruLensEvaluator()
                    if not st.session_state.trulens_evaluator.initialized:
                        print("TruLens evaluator failed to initialize properly")
            except Exception as e:
                print(f"Error initializing TruLens evaluator: {str(e)}")
                st.session_state.trulens_evaluator = None
            
    def add_bg_image(self):
        """Add a background image to the app."""
        st.markdown(
            f"""
            <style>
                .stApp {{
                    background-image: url("https://i.postimg.cc/28gZrzQn/Dashboard.png");
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
        
        
        st.markdown("""
            <style>
            [data-testid="stSidebar"] {
                background-color: #72245C;
            }
            </style>
        """, unsafe_allow_html=True)

    def setup_styling(self):
        
             # Create elegant header with logo and title
        header_cols = st.columns([0.8, 4, 3])  # Adjusted ratios for better spacing
        
        with header_cols[0]:
            st.image("https://i.postimg.cc/cJrXGrxd/PALicon.png", width=80)
        
        with header_cols[1]:
            st.markdown("""
                <h1 style='
                    margin: 0;
                    padding: 8px 0 0 0;
                    font-size: 49px;
                    margin-top: -20px;
                    font-weight: 800;
                    background: linear-gradient(45deg, #E5B8F4, #C147E9);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;'>
                    Analytics Dashboard
                </h1>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("""
            <style>
            body {
                background-color: #11001C;
                color: #FFFFFF;
            }
            .stPlotlyChart {
                background-color: #461257;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .streamlit-expanderHeader {
                background-color: #1E0935;
                border-radius: 10px;
            }
            div[data-testid="stMetricValue"] {
                font-size: 24px;
                color: #541680;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 24px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: pre-wrap;
                background-color: #1E0935;
                border-radius: 5px;
                padding: 10px 20px;
                color: #FFFFFF;
            }
            .metric-card {
                background: #11001C;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .section-header {
                color: #FFFFFF;
                padding: 10px 0;
                font-size: 1.2em;
                font-weight: bold;
            }
            </style>
        """, unsafe_allow_html=True)
        
        
        st.markdown("""
        <style>
        .tooltip {{
            position: absolute;
            top: 5px;
            right: 5px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 12px;
            font-weight: bold;
            cursor: pointer;
        }}

        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 200px;
            background-color: rgba(0, 0, 0, 0.8);
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            opacity: 0;
            transition: opacity 0.3s;
        }}

        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
        </style>
    """, unsafe_allow_html=True)
        
        
        st.markdown("""
        <style>
            .presenter-container {
                background-color: #1E0935;
                padding: 2rem;
                border-radius: 10px;
                border: 1px solid #541680;
                margin: 1rem 0;
            }
            .presenter-controls {
                background-color: #252f3e;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
            }
            .presentation-content {
                font-size: 1.1rem;
                line-height: 1.6;
                color: #FFFFFF;
            }
        </style>
    """, unsafe_allow_html=True)
        
    


    # def render_operation_metrics(self, operation_type: str):
    #     """Render metrics for specific operation type with enhanced visualization"""
    #     session = SnowparkManager.get_session()
    #     if not session:
    #         st.error("Could not connect to database")
    #         return
            
    #     try:
    #         # Query metrics for specific operation with additional computed columns
    #         metrics_query = f"""
    #         SELECT 
    #             TIMESTAMP,
    #             CONTEXT_RELEVANCE,
    #             GROUNDEDNESS_SCORE,
    #             COHERENCE_SCORE,
    #             SOURCE_DIVERSITY_SCORE,
    #             FLUENCY_SCORE,
    #             TOKEN_EFFICIENCY,
    #             LAG(CONTEXT_RELEVANCE) OVER (ORDER BY TIMESTAMP) as PREV_RELEVANCE,
    #             LAG(GROUNDEDNESS_SCORE) OVER (ORDER BY TIMESTAMP) as PREV_GROUNDEDNESS,
    #             LAG(COHERENCE_SCORE) OVER (ORDER BY TIMESTAMP) as PREV_COHERENCE
    #         FROM TESTDB.MYSCHEMA.TRULENS_METRICS
    #         WHERE OPERATION_TYPE = '{operation_type}'
    #         ORDER BY TIMESTAMP DESC
    #         """
            
    #         results = session.sql(metrics_query).collect()
            
    #         if results:
    #             metrics_df = pd.DataFrame(results)
                
    #             # Create header with operation type
    #             st.markdown(f"""
    #                 <div style="
    #                     padding: 10px;
    #                     background-color: #1E0935;
    #                     border-radius: 10px;
    #                     margin-bottom: 20px;
    #                     border: 1px solid #541680;
    #                 ">
    #                     <h2 style="color: #f9fafb; margin: 0; text-align: center;">
    #                         {operation_type.title()} Performance Analytics
    #                     </h2>
    #                 </div>
    #             """, unsafe_allow_html=True)

    #             # Calculate trends and display primary metrics using metric cards
    #             metrics_cols = st.columns(4)
                
    #             # Source Diversity
    #             with metrics_cols[0]:
    #                 avg_diversity = metrics_df['SOURCE_DIVERSITY_SCORE'].mean()
    #                 prev_diversity = metrics_df['SOURCE_DIVERSITY_SCORE'].iloc[1:].mean() if len(metrics_df) > 1 else avg_diversity
    #                 trend = ((avg_diversity - prev_diversity) / prev_diversity * 100) if prev_diversity else 0
                    
    #                 col1, col2 = st.columns([5, 1])
    #                 with col1:
    #                     st.markdown(f"""
    #                         <div style="
    #                             padding: 20px;
    #                             background: #374151;
    #                             border-radius: 10px;
    #                             text-align: center;
    #                             height: 100%;
    #                             position: relative;
    #                         ">
    #                             <h3 style="color: #f9fafb; margin-bottom: 10px; font-size: 1em;">Source Diversity</h3>
    #                             <p style="font-size: 1.8em; font-weight: bold; color: #60a5fa; margin: 0;">{avg_diversity:.2%}</p>
    #                             <p style="font-size: 0.9em; color: {'#10b981' if trend > 0 else '#ef4444'}; margin-top: 5px;">
    #                                 {trend > 0 and '↑' or '↓'} {abs(trend):.1f}%
    #                             </p>
    #                         </div>
    #                     """, unsafe_allow_html=True)
    #                 with col2:
    #                     st.button("ℹ️", key=f"info_diversity_{operation_type}", 
    #                             help="Measures the variety and breadth of sources used in responses")

    #             # Groundedness Score
    #             with metrics_cols[1]:
    #                 avg_groundedness = metrics_df['GROUNDEDNESS_SCORE'].mean()
    #                 prev_groundedness = metrics_df['PREV_GROUNDEDNESS'].iloc[0]
    #                 trend = ((avg_groundedness - prev_groundedness) / prev_groundedness * 100) if prev_groundedness else 0
                    
    #                 col1, col2 = st.columns([5, 1])
    #                 with col1:
    #                     st.markdown(f"""
    #                         <div style="
    #                             padding: 20px;
    #                             background: #374151;
    #                             border-radius: 10px;
    #                             text-align: center;
    #                             height: 100%;
    #                             position: relative;
    #                         ">
    #                             <h3 style="color: #f9fafb; margin-bottom: 10px; font-size: 1em;">Groundedness</h3>
    #                             <p style="font-size: 1.8em; font-weight: bold; color: #60a5fa; margin: 0;">{avg_groundedness:.2%}</p>
    #                             <p style="font-size: 0.9em; color: {'#10b981' if trend > 0 else '#ef4444'}; margin-top: 5px;">
    #                                 {trend > 0 and '↑' or '↓'} {abs(trend):.1f}%
    #                             </p>
    #                         </div>
    #                     """, unsafe_allow_html=True)
    #                 with col2:
    #                     st.button("ℹ️", key=f"info_groundedness_{operation_type}", 
    #                             help="Measures factual accuracy and evidence support")

    #             # Coherence Score
    #             with metrics_cols[2]:
    #                 avg_coherence = metrics_df['COHERENCE_SCORE'].mean()
    #                 prev_coherence = metrics_df['PREV_COHERENCE'].iloc[0]
    #                 trend = ((avg_coherence - prev_coherence) / prev_coherence * 100) if prev_coherence else 0
                    
    #                 col1, col2 = st.columns([5, 1])
    #                 with col1:
    #                     st.markdown(f"""
    #                         <div style="
    #                             padding: 20px;
    #                             background: #374151;
    #                             border-radius: 10px;
    #                             text-align: center;
    #                             height: 100%;
    #                             position: relative;
    #                         ">
    #                             <h3 style="color: #f9fafb; margin-bottom: 10px; font-size: 1em;">Coherence</h3>
    #                             <p style="font-size: 1.8em; font-weight: bold; color: #60a5fa; margin: 0;">{avg_coherence:.2%}</p>
    #                             <p style="font-size: 0.9em; color: {'#10b981' if trend > 0 else '#ef4444'}; margin-top: 5px;">
    #                                 {trend > 0 and '↑' or '↓'} {abs(trend):.1f}%
    #                             </p>
    #                         </div>
    #                     """, unsafe_allow_html=True)
    #                 with col2:
    #                     st.button("ℹ️", key=f"info_coherence_{operation_type}", 
    #                             help="Measures logical flow and structure of responses")

    #             # Token Efficiency
    #             with metrics_cols[3]:
    #                 avg_efficiency = metrics_df['TOKEN_EFFICIENCY'].mean()
                    
    #                 col1, col2 = st.columns([5, 1])
    #                 with col1:
    #                     st.markdown(f"""
    #                         <div style="
    #                             padding: 20px;
    #                             background: #374151;
    #                             border-radius: 10px;
    #                             text-align: center;
    #                             height: 100%;
    #                             position: relative;
    #                         ">
    #                             <h3 style="color: #f9fafb; margin-bottom: 10px; font-size: 1em;">Token Efficiency</h3>
    #                             <p style="font-size: 1.8em; font-weight: bold; color: #60a5fa; margin: 0;">{avg_efficiency:.2f}</p>
    #                         </div>
    #                     """, unsafe_allow_html=True)
    #                 with col2:
    #                     st.button("ℹ️", key=f"info_efficiency_{operation_type}", 
    #                             help="Measures effective use of tokens in responses")

    #             # Performance Trends Visualization
    #             st.markdown("""
    #                 <div style="
    #                     margin-top: 30px;
    #                     margin-bottom: 10px;
    #                     padding: 10px;
    #                     background-color: #1E0935;
    #                     border-radius: 10px;
    #                     border: 1px solid #541680;
    #                 ">
    #                     <h3 style="color: #f9fafb; margin: 0;">📈 Performance Trends</h3>
    #                 </div>
    #             """, unsafe_allow_html=True)

    #             fig = go.Figure()
                
    #             metrics_to_plot = {
    #                 'Context Relevance': 'CONTEXT_RELEVANCE',
    #                 'Groundedness': 'GROUNDEDNESS_SCORE',
    #                 'Coherence': 'COHERENCE_SCORE',
    #                 'Source Diversity': 'SOURCE_DIVERSITY_SCORE'
    #             }
                
    #             colors = ['#60a5fa', '#34d399', '#f472b6', '#a78bfa']
                
    #             for (label, column), color in zip(metrics_to_plot.items(), colors):
    #                 fig.add_trace(go.Scatter(
    #                     x=metrics_df['TIMESTAMP'],
    #                     y=metrics_df[column],
    #                     name=label,
    #                     line=dict(color=color, width=2),
    #                     mode='lines+markers',
    #                     marker=dict(size=6)
    #                 ))
                
    #             fig = self.apply_modern_clean_style(
    #                 fig, 
    #                 f'{operation_type.title()} Metrics Over Time'
    #             )
                
    #             # Additional layout improvements
    #             fig.update_layout(
    #                 legend=dict(
    #                     orientation="h",
    #                     yanchor="bottom",
    #                     y=1.02,
    #                     xanchor="right",
    #                     x=1,
    #                     bgcolor='rgba(0,0,0,0.1)',
    #                     bordercolor='#541680'
    #                 ),
    #                 hovermode='x unified'
    #             )
                
    #             st.plotly_chart(fig, use_container_width=True)

    #             # Additional Metrics Section
    #             #if operation_type == 'SEARCH':
    #                 #self.render_search_specific_metrics(metrics_df)
    #             #elif operation_type == 'SUMMARY':
    #                 #self.render_summary_specific_metrics(metrics_df)
    #             #else:  # QA
    #                 #self.render_qa_specific_metrics(metrics_df)
                
    #             # Display detailed metrics table in an expander
    #             with st.expander("📋 View Detailed Metrics", expanded=False):
    #                 display_df = metrics_df[[
    #                     'TIMESTAMP', 
    #                     'CONTEXT_RELEVANCE', 
    #                     'GROUNDEDNESS_SCORE',
    #                     'COHERENCE_SCORE',
    #                     'SOURCE_DIVERSITY_SCORE',
    #                     'TOKEN_EFFICIENCY'
    #                 ]].copy()
                    
    #                 display_df.columns = [col.replace('_', ' ').title() for col in display_df.columns]
    #                 st.dataframe(
    #                     display_df,
    #                     hide_index=True,
    #                     use_container_width=True
    #                 )
                    
    #         else:
    #             st.info(f"No {operation_type.lower()} metrics available yet.")
                
    #     except Exception as e:
    #         st.error(f"Error loading {operation_type.lower()} metrics: {str(e)}")
    #         print(f"Detailed error: {str(e)}")
    #     finally:
    #         if session:
    #             session.close()

    def render_search_specific_metrics(self, df: pd.DataFrame):
        """Render metrics specific to search operations"""
        st.markdown("#### Search-Specific Metrics")
        
        col1, col2 = st.columns(2)
        with col1:
            avg_diversity = df['SOURCE_DIVERSITY_SCORE'].mean()
            st.metric(
                "Source Diversity",
                f"{avg_diversity:.2%}",
                help="Variety of sources in search results"
            )
        
        with col2:
            avg_efficiency = df['TOKEN_EFFICIENCY'].mean()
            st.metric(
                "Token Efficiency",
                f"{avg_efficiency:.2f}",
                help="Efficiency of token usage in responses"
            )

    def render_summary_specific_metrics(self, df: pd.DataFrame):
        """Render metrics specific to summary operations"""
        st.markdown("#### Summary-Specific Metrics")
        
        col1, col2 = st.columns(2)
        with col1:
            avg_fluency = df['FLUENCY_SCORE'].mean()
            st.metric(
                "Fluency",
                f"{avg_fluency:.2%}",
                help="Natural language quality of summaries"
            )
        
        with col2:
            avg_efficiency = df['TOKEN_EFFICIENCY'].mean()
            st.metric(
                "Compression Ratio",
                f"{avg_efficiency:.2f}",
                help="Ratio of summary length to original content"
            )

    def render_qa_specific_metrics(self, df: pd.DataFrame):
        """Render metrics specific to QA operations"""
        st.markdown("#### QA-Specific Metrics")
        
        col1, col2 = st.columns(2)
        with col1:
            avg_fluency = df['FLUENCY_SCORE'].mean()
            st.metric(
                "Answer Fluency",
                f"{avg_fluency:.2%}",
                help="Natural language quality of answers"
            )
        
        with col2:
            avg_efficiency = df['TOKEN_EFFICIENCY'].mean()
            st.metric(
                "Response Efficiency",
                f"{avg_efficiency:.2f}",
                help="Conciseness of answers"
            )    
        

    def create_metric_with_info(self, title, value, trend_value, trend_direction, info_text, key_suffix=None):
        """Create a metric card with an info button using title as part of the key"""
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"""
                <div style="
                    padding: 20px;
                    background: linear-gradient(135deg, #2D033B 0%, #810CA8 100%);
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                    text-align: center;
                    height: 180px;  /* Fixed height */
                    width: 100%;    /* Full width of column */
                    min-width: 200px; /* Minimum width */
                    position: relative;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <h3 style="
                        color: #E5B8F4;
                        margin: 0 0 10px 0;
                        font-size: 1em;
                        font-weight: bold;
                        width: 100%;
                    ">{title}</h3>
                    <p style="
                        font-size: 1.8em;
                        font-weight: bold;
                        color: #C147E9;
                        margin: 0;
                        width: 100%;
                    ">{value}</p>
                    <p style="
                        font-size: 0.9em;
                        color: {'#10b981' if trend_direction == 'up' else '#ef4444'};
                        margin: 5px 0 0 0;
                        font-weight: bold;
                        width: 100%;
                    ">
                        {trend_direction == 'up' and '↑' or '↓'} {trend_value if trend_value else ''}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            unique_key = f"info_{title.lower().replace(' ', '_')}_{uuid.uuid4().hex[:4]}"
            st.button("ℹ️", key=unique_key, help=info_text)

    def create_metric_with_hover_analysis(
        self,
        title: str,
        value: float,
        trend_value: float = None,
        trend_direction: str = None
    ):
        """Create a metric card with hover analysis"""
        
        cache_key = f"analysis_{title}_{value}_{trend_value}"
        if cache_key not in st.session_state:
            try:
                # Modified prompt to enforce brevity
                analysis_query = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'mistral-large',
                    ARRAY_CONSTRUCT(
                        OBJECT_CONSTRUCT('role', 'system', 'content', 'You are an analytics expert providing extremely concise metric analysis. Limit responses to 20-25 words maximum.'),
                        OBJECT_CONSTRUCT('role', 'user', 'content', 'Give a very brief analysis of {title}: {value:.2f} (Trend: {trend_value}%). Focus on key insight only.')
                    ),
                    OBJECT_CONSTRUCT(
                        'temperature', 0.3,
                        'max_tokens', 30
                    )
                ) as response
                """
                
                session = SnowparkManager.get_session()
                response = session.sql(analysis_query).collect()
                session.close()
                
                if response and response[0][0]:
                    parsed_response = json.loads(response[0][0])
                    analysis = parsed_response.get('choices', [])[0].get('messages', 'Analysis unavailable')
                    # Truncate and clean the analysis text
                    analysis = analysis[:100].strip()  # Limit length
                    analysis = analysis.replace('"', '&quot;').replace("'", "&#39;")
                    # Ensure the analysis ends with a complete sentence
                    if not analysis.endswith('.'):
                        analysis = '. '.join(analysis.split('.')[:-1]) + '.'
                else:
                    analysis = "Analysis unavailable"
                    
            except Exception as e:
                print("Error details:", str(e))
                analysis = "Analysis unavailable"
                
            st.session_state[cache_key] = analysis
        
        return st.markdown(
            f"""
            <div class="metric-card"
                title="{st.session_state[cache_key]}"
                style="
                    padding: 20px;
                    background: #374151;
                    border-radius: 10px;
                    text-align: center;
                    height: 100%;
                    position: relative;
                    cursor: help;
                    transition: transform 0.2s;
                ">
                <h3 style="color: #f9fafb; margin-bottom: 10px; font-size: 1em;">{title}</h3>
                <p style="font-size: 1.8em; font-weight: bold; color: #60a5fa; margin: 0;">{value}</p>
                <p style="font-size: 0.9em; color: {'#10b981' if trend_direction == 'up' else '#ef4444'}; margin-top: 5px;">
                    {trend_direction == 'up' and '↑' or '↓'} {trend_value if trend_value else ''}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    def create_metric_card_with_trend(self, title, value, trend_value=None, trend_direction=None):
        trend_color = "#10b981" if trend_direction == "up" else "#ef4444" if trend_direction == "down" else "#6b7280"
        trend_arrow = "↑" if trend_direction == "up" else "↓" if trend_direction == "down" else "→"
        
        st.markdown(
            f"""
            <div style="
                padding: 20px;
                background: linear-gradient(135deg, #2D033B 0%, #810CA8 100%);
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                text-align: center;
                height: 180px;  /* Fixed height */
                width: 100%;    /* Full width of column */
                min-width: 200px; /* Minimum width */
                color: #f9fafb;
                position: relative;
                border: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                align-items: center;
            ">
                <h3 style="
                    color: #E5B8F4;
                    margin: 0 0 10px 0;
                    font-size: 1em;
                    font-weight: bold;
                    width: 100%;
                ">{title}</h3>
                <p style="
                    font-size: 1.8em;
                    font-weight: bold;
                    color: #C147E9;
                    margin: 0;
                    width: 100%;
                ">{value}</p>
                <p style="
                    font-size: 0.9em;
                    color: {trend_color};
                    margin: 5px 0 0 0;
                    font-weight: bold;
                    width: 100%;
                ">
                    {trend_arrow} {trend_value if trend_value else ''}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    def apply_modern_clean_style(self, fig, title):
        """Apply modern clean styling to charts with #86608E theme"""
        fig.update_layout(
            plot_bgcolor='rgba(134, 96, 142, 0.2)',  # #86608E with transparency
            paper_bgcolor='rgba(134, 96, 142, 0.2)',  # #86608E with transparency
            margin=dict(t=60, l=50, r=30, b=40),
            title=dict(
                text=title,
                font=dict(
                    family="Arial",
                    size=24,
                    color="#E5B8F4"  # Light purple for title
                ),
                x=0.6,
                y=0.98,
                xanchor='right',
                yanchor='top'
            ),
            xaxis=dict(
                title_font=dict(size=14, color="#E5B8F4", family="Arial"),
                tickfont=dict(size=12, color="#E5B8F4", family="Arial"),
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(134, 96, 142, 0.3)',  # #86608E for grid
                showline=True,
                linewidth=2,
                linecolor='rgba(134, 96, 142, 0.5)',  # #86608E for axis lines
                zeroline=False
            ),
            yaxis=dict(
                title_font=dict(size=14, color="#E5B8F4", family="Arial"),
                tickfont=dict(size=12, color="#E5B8F4", family="Arial"),
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(134, 96, 142, 0.3)',  # #86608E for grid
                showline=True,
                linewidth=2,
                linecolor='rgba(134, 96, 142, 0.5)',  # #86608E for axis lines
                zeroline=False
            ),
            hoverlabel=dict(
                bgcolor="rgba(134, 96, 142, 0.95)",
                font_color="#E5B8F4",
                font_size=14,
                font_family="Arial"
            ),
            font=dict(
                family="Arial",
                color="#E5B8F4"
            ),
            legend=dict(
                font=dict(color="#E5B8F4"),
                bgcolor='rgba(134, 96, 142, 0.2)',
                bordercolor='rgba(134, 96, 142, 0.3)'
            )
        )
        
        # Add a subtle gradient effect
        fig.add_shape(
            type="rect",
            x0=0,
            y0=0,
            x1=1,
            y1=1,
            xref="paper",
            yref="paper",
            fillcolor="rgba(134, 96, 142, 0.1)",
            line_width=0,
            layer="below"
        )
        
        return fig
        
        # Add a subtle gradient effect using a shape
        fig.add_shape(
            type="rect",
            x0=0,
            y0=0,
            x1=1,
            y1=1,
            xref="paper",
            yref="paper",
            fillcolor="rgba(129, 12, 168, 0.1)",
            line_width=0,
            layer="below"
        )
        
        return fig
    

        
    def render_trulens_metrics(self):
        """Render TruLens metrics visualization"""
        
        session = SnowparkManager.get_session()
        if not session:
            st.error("Failed to establish database connection")
            return
                
        try:
            trulens_query = """
            SELECT *
            FROM TESTDB.MYSCHEMA.TRULENS_METRICS
            WHERE TIMESTAMP >= DATEADD(day, -7, CURRENT_TIMESTAMP())
            ORDER BY TIMESTAMP DESC
            """
            
            print("Executing TruLens metrics query...")
            results = session.sql(trulens_query).collect()
            
            if not results:
                st.info("No TruLens metrics data available for the selected period.")
                return
                    
            df = pd.DataFrame(results)
            print(f"Retrieved {len(df)} metrics records")
            
            st.markdown("### 📊 TruLens Metrics Overview")
            
            # Define all metrics to display with their columns and descriptions
            metrics_to_display = {
                'Relevance': {
                    'column': 'RELEVANCE_SCORE',
                    'description': 'Measures how well responses match the query intent. Higher scores indicate better answer relevance.'
                },
                'Groundedness': {
                    'column': 'GROUNDEDNESS_SCORE',
                    'description': 'Indicates how well responses are supported by source documents. Higher scores show better factual accuracy.'
                },
                'Coherence': {
                    'column': 'COHERENCE_SCORE',
                    'description': 'Measures response clarity and logical flow. Higher scores indicate better structured answers.'
                },
                'Efficiency': {
                    'column': 'EFFICIENCY_SCORE',
                    'description': 'Evaluates resource utilization efficiency. Higher scores show better system optimization.'
                },
                'Token Efficiency': {
                    'column': 'TOKEN_EFFICIENCY',
                    'description': 'Measures effective use of tokens in responses. Higher scores indicate more concise answers.'
                },
                'Source Diversity': {
                    'column': 'SOURCE_DIVERSITY_SCORE',
                    'description': 'Shows variety of sources used in responses. Higher scores indicate broader information coverage.'
                },
                'Readability': {
                    'column': 'READABILITY_SCORE',
                    'description': 'Measures how easy responses are to understand. Higher scores indicate clearer communication.'
                },
                'Fluency': {
                    'column': 'FLUENCY_SCORE',
                    'description': 'Evaluates natural language quality. Higher scores show more natural-sounding responses.'
                }
            }
            
            # Create metric cards in rows of 4
            for i in range(0, len(metrics_to_display), 4):
                metric_cols = st.columns(4)
                current_metrics = list(metrics_to_display.items())[i:i+4]
                
                for col, (metric_name, metric_info) in zip(metric_cols, current_metrics):
                    with col:
                        current_value = df[metric_info['column']].mean()
                        recent_avg = df[metric_info['column']].head(5).mean()
                        older_avg = df[metric_info['column']].iloc[5:10].mean() if len(df) > 10 else current_value
                        trend = ((recent_avg - older_avg) / older_avg * 100) if older_avg != 0 else 0
                        
                        self.create_metric_with_info(
                            metric_name,
                            f"{current_value:.2f}",
                            f"{abs(trend):.1f}%",
                            "up" if trend > 0 else "down",
                            metric_info['description']
                        )
                
                # Create time series visualization
                st.markdown("### 📈 Metrics Trends")
                
                # Prepare data for visualization
                plot_df = df.melt(
                    id_vars=['TIMESTAMP'],
                    value_vars=[col for col in df.columns if '_SCORE' in col],
                    var_name='Metric',
                    value_name='Score'
                )
            
            fig = px.line(
                plot_df,
                x='TIMESTAMP',
                y='Score',
                color='Metric',
                template='plotly'
            )
            
            fig = self.apply_modern_clean_style(fig, 'TruLens Metrics Over Time')
            st.plotly_chart(fig, use_container_width=True)
            
            # Add detailed metrics table
            st.markdown("### 📋 Detailed Metrics")
            
            # Format the dataframe for display
            display_df = df.copy()
            display_df['TIMESTAMP'] = pd.to_datetime(display_df['TIMESTAMP']).dt.strftime('%Y-%m-%d %H:%M:%S')
            display_df = display_df.round(4)
            
            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True
            )
         
            df = pd.DataFrame(results)
            
            # Move SnowparkManager session here
            st.markdown("### Window Size Comparison")
            window_analyzer = WindowSizeAnalyzer(session)  # Pass the session here
            window_analyzer.display_trulens_comparison(st)
                     
            
        except Exception as e:
            st.error(f"Error rendering TruLens metrics: {str(e)}")
            import traceback
            st.error(f"Traceback: {traceback.format_exc()}")
        
        finally:
            if session:
                session.close()
                
                    
    # def fetch_trulens_comparison(self):
    #     """Fetch TruLens metrics comparison using simplified metrics view"""
    #     try:
    #         print("Starting TruLens comparison query...")
            
    #         # Basic metrics query without complex grouping
    #         comparison_query = """
    #         SELECT 
    #             TOKEN_COUNT as window_size,
    #             AVG(RELEVANCE_SCORE) as avg_relevance,
    #             AVG(GROUNDEDNESS_SCORE) as avg_groundedness,
    #             AVG(COHERENCE_SCORE) as avg_coherence,
    #             AVG(SOURCE_DIVERSITY_SCORE) as avg_source_diversity,
    #             AVG(CONTEXT_RELEVANCE) as avg_context_relevance,
    #             COUNT(*) as total_queries
    #         FROM TESTDB.MYSCHEMA.TRULENS_METRICS
    #         WHERE OUTPUT_TOKEN_COUNT IS NOT NULL 
    #         GROUP BY OUTPUT_TOKEN_COUNT
    #         ORDER BY OUTPUT_TOKEN_COUNT
    #         """
            
    #         results = self.session.sql(comparison_query).collect()
    #         print(f"Comparison query returned {len(results)} rows")
            
    #         # If no results, try a simpler query to debug
    #         if not results:
    #             print("No results found. Checking data...")
    #             debug_query = """
    #             SELECT 
    #                 COUNT(*) as total_records,
    #                 COUNT(OUTPUT_TOKEN_COUNT) as token_count_records,
    #                 COUNT(RELEVANCE_SCORE) as relevance_records
    #             FROM TESTDB.MYSCHEMA.TRULENS_METRICS
    #             """
    #             debug_results = self.session.sql(debug_query).collect()
    #             print(f"Debug results: {debug_results}")
            
    #         return results
                
    #     except Exception as e:
    #         print(f"Error fetching TruLens comparison data: {str(e)}")
    #         st.error(f"Query error: {str(e)}")
    #         return None

    def calculate_numeric_trend(self, current_value: float, previous_value: float) -> str:
        """Calculate trend percentage change with numeric values"""
        if previous_value == 0 or pd.isna(previous_value) or pd.isna(current_value):
            return "0%"
        
        change = ((current_value - previous_value) / previous_value) * 100
        return f"{change:+.1f}%"
           
                
                

    def generate_presenter_prompt(self, metrics: Dict[str, Any], settings: Dict[str, Any]) -> str:
        """Generate a focused prompt for the AI presenter based on available metrics"""
        
        return f"""Present a {settings['duration']}-minute executive summary focused on:

        1. System Performance Metrics:
        * Response Time: {metrics['response_time']:.2f} seconds
        * Success Rate: {metrics['success_rate']:.1f}%
        * Memory Usage: {metrics['memory_usage']:.1f} MB
        * Token Usage: {metrics['token_usage']:.0f} tokens per request

        2. Document Analytics:
        * Total Documents Processed: {metrics['total_documents']}
        * Total Queries Handled: {metrics['total_queries']}
        * Document Processing Patterns
        * Usage Statistics

        Required Presentation Structure: (15 seconds)
        1. Introduction 
            - Overview of current system state
            - Highlight key metrics

        2. System Performance Analysis (15 seconds)
            - Response time trends and implications
            - Resource utilization patterns
            - Success rate analysis
            - Token usage efficiency

        3. Document Analytics (15 seconds)
            - Document processing statistics
            - Usage patterns and trends
            - Optimization opportunities

        4. Recommendations & Conclusion (30 seconds)
            - Key performance insights
            - Specific improvement recommendations

        Target Audience: {settings['audience']}
        Technical Detail Level: {settings['tech_level']}
        Presentation Style: {settings['style']}

        Note: Focus only on available metrics and provide actionable insights appropriate for the audience level."""

           
           
          
            
    def safe_float(self, value, decimals=2):
        """
        Safely convert a value to float with specified decimal places.
        """
        try:
            if value is None:
                return 0.0
            return round(float(value), decimals)
        except (TypeError, ValueError):
            return 0.0
        
        
    def render_search_metrics(self):
        """Render search metrics dashboard with actual table schema"""
        st.markdown("### 🔍 Search Performance Analytics")
        
        session = SnowparkManager.get_session()
        if not session:
            st.error("Could not connect to database")
            return
            
        try:
            # Fetch metrics using actual table columns
            metrics_query = """
            SELECT 
                TIMESTAMP,
                CONTEXT_RELEVANCE,
                RELEVANCE_SCORE,
                SOURCE_DIVERSITY_SCORE,
                COHERENCE_SCORE,
                TOKEN_EFFICIENCY,
                OUTPUT_TOKEN_COUNT
            FROM TESTDB.MYSCHEMA.TRULENS_METRICS
            ORDER BY TIMESTAMP DESC
            LIMIT 100
            """
            results = session.sql(metrics_query).collect()
            
            if results:
                metrics_df = pd.DataFrame(results)
                
                # Display key metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_relevance = metrics_df['CONTEXT_RELEVANCE'].mean()
                    st.metric(
                        "Average Context Relevance",
                        f"{avg_relevance:.2%}",
                        help="Average relevance of search results to queries"
                    )
                
                with col2:
                    avg_efficiency = metrics_df['TOKEN_EFFICIENCY'].mean()
                    st.metric(
                        "Token Efficiency",
                        f"{avg_efficiency:.2f}",
                        help="Efficiency of token usage in responses"
                    )
                
                with col3:
                    avg_coherence = metrics_df['COHERENCE_SCORE'].mean()
                    st.metric(
                        "Average Coherence",
                        f"{avg_coherence:.2%}",
                        help="Quality and coherence of search results"
                    )

                # Create trend visualization
                st.markdown("#### Performance Trends")
                fig = go.Figure()
                
                # Add multiple metrics to the chart
                fig.add_trace(go.Scatter(
                    x=metrics_df['TIMESTAMP'],
                    y=metrics_df['CONTEXT_RELEVANCE'],
                    name='Context Relevance',
                    line=dict(color='#60a5fa')
                ))
                
                fig.add_trace(go.Scatter(
                    x=metrics_df['TIMESTAMP'],
                    y=metrics_df['COHERENCE_SCORE'],
                    name='Coherence',
                    line=dict(color='#34d399')
                ))
                
                fig.add_trace(go.Scatter(
                    x=metrics_df['TIMESTAMP'],
                    y=metrics_df['SOURCE_DIVERSITY_SCORE'],
                    name='Source Diversity',
                    line=dict(color='#f472b6')
                ))
                
                fig.update_layout(
                    template='plotly_dark',
                    title='Search Performance Metrics Over Time',
                    xaxis_title='Time',
                    yaxis_title='Score',
                    plot_bgcolor='#1E0935',
                    paper_bgcolor='#11001C',
                    font=dict(color='#FFFFFF'),
                    legend=dict(
                        bgcolor='rgba(0,0,0,0.1)',
                        bordercolor='#541680'
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)

                # Token usage analysis
                st.markdown("#### Token Usage Analysis")
                token_fig = go.Figure()
                token_fig.add_trace(go.Scatter(
                    x=metrics_df['TIMESTAMP'],
                    y=metrics_df['OUTPUT_TOKEN_COUNT'],
                    name='Token Usage',
                    line=dict(color='#8b5cf6')
                ))
                
                token_fig.update_layout(
                    template='plotly_dark',
                    title='Token Usage Over Time',
                    xaxis_title='Time',
                    yaxis_title='Token Count',
                    plot_bgcolor='#1E0935',
                    paper_bgcolor='#11001C',
                    font=dict(color='#FFFFFF')
                )
                
                st.plotly_chart(token_fig, use_container_width=True)

                # Recent metrics table
                st.markdown("#### Recent Performance Metrics")
                display_df = metrics_df[[
                    'TIMESTAMP', 
                    'CONTEXT_RELEVANCE', 
                    'COHERENCE_SCORE',
                    'SOURCE_DIVERSITY_SCORE',
                    'TOKEN_EFFICIENCY'
                ]].copy()
                
                display_df.columns = [
                    'Timestamp',
                    'Context Relevance',
                    'Coherence',
                    'Source Diversity',
                    'Token Efficiency'
                ]
                
                st.dataframe(
                    display_df,
                    hide_index=True,
                    use_container_width=True
                )
                
            else:
                st.info("No search metrics data available yet. Try performing some searches to generate metrics.")
                
        except Exception as e:
            st.error(f"Error loading search metrics: {str(e)}")
            print(f"Detailed error: {str(e)}")
        finally:
            if session:
                session.close()
        
        
        
        

    def render_ai_presenter(self, metrics_data):
        """Render the AI Presenter with controls in sidebar and content in main area"""
        if metrics_data is None:
            st.warning("No metrics data available for presentation")
            return
            
        # Controls in sidebar
        with st.sidebar:
            st.markdown("""
                <style>
                [data-testid="stSidebar"] {
                    background-color: #4E2A84;
                }
                </style>
            """, unsafe_allow_html=True)
            
            #st.sidebar.image("https://i.postimg.cc/BXSNChRp/robot-dashboard.png", width=100, use_container_width=True)
            st.image(
                    "https://i.postimg.cc/4NtMsq5D/Presenter-AI.jpg",
                    caption="Your PAL",
                    use_container_width=True
                )
        
            st.markdown("### 🎙️ AI Presenter Controls")
            
            # Simplified style options
            col1, col2 = st.columns(2)
            with col1:
                duration = st.slider("Duration (min)", 
                                1, 5, 
                                st.session_state.presentation_settings['duration'])
                tech_level = st.select_slider("Detail Level",
                                            ["Basic", "Moderate", "Detailed"],
                                            st.session_state.presentation_settings['tech_level'])
            
            with col2:
                audience = st.selectbox("Audience",
                                    ["Business Managers", "Technical Team", "Executives"],
                                    index=["Business Managers", "Technical Team", "Executives"]
                                    .index(st.session_state.presentation_settings['audience']))
                style = st.selectbox("Style",
                                ["Professional", "Technical"],
                                index=["Professional", "Technical"]
                                .index(st.session_state.presentation_settings['style']))

            if st.button("🎯 Generate Presentation", use_container_width=True):
                with st.spinner("Generating presentation..."):
                    try:
                        session = SnowparkManager.get_session()
                        
                        # Get system metrics and analytics
                        metrics_query = """
                        SELECT 
                            TIMESTAMP,
                            RESPONSE_TIME_MS,
                            MEMORY_USAGE_MB,
                            TOKEN_COUNT,
                            STATUS,
                            DOCUMENT_NAME
                        FROM TESTDB.MYSCHEMA.ANALYTICS_METRICS 
                        ORDER BY TIMESTAMP DESC
                        """
                        
                        results = session.sql(metrics_query).collect()
                        metrics_df = pd.DataFrame(results)
                        
                        if not metrics_df.empty:
                            # Format metrics in the structure expected by generate_presenter_prompt
                            current_metrics = {
                                'response_time': metrics_df['RESPONSE_TIME_MS'].mean() / 1000,  # Convert to seconds
                                'memory_usage': metrics_df['MEMORY_USAGE_MB'].mean(),
                                'success_rate': (metrics_df['STATUS'] == 'success').mean() * 100,
                                'token_usage': metrics_df['TOKEN_COUNT'].mean(),
                                'total_documents': metrics_df['DOCUMENT_NAME'].nunique(),
                                'total_queries': len(metrics_df)
                            }
                            
                            settings = {
                                'duration': duration,
                                'audience': audience,
                                'tech_level': tech_level,
                                'style': style
                            }
    
                            st.session_state.presentation_settings = settings
                            
                            # Generate presentation using LLM
                            prompt = self.generate_presenter_prompt(current_metrics, settings)
                            
                            llm_query = f"""
                            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                                'mistral-large2',
                                ARRAY_CONSTRUCT(
                                    OBJECT_CONSTRUCT('role', 'system', 'content', 
                                        'You are an expert AI metrics analyst presenting system performance and document analytics. 
                                        Focus on:
                                        1. System Performance - response times, memory usage, success rates, and token usage
                                        2. Document Analytics - processing patterns, usage statistics, and access trends
                                        
                                        Provide clear insights and actionable recommendations based on the metrics.'),
                                    OBJECT_CONSTRUCT('role', 'user', 'content', '{prompt.replace("'", "''")}')
                                ),
                                OBJECT_CONSTRUCT(
                                    'temperature', 0.7,
                                    'max_tokens', 500,
                                    'top_p', 0.9
                                )
                            ) as response
                            """
                            
                            response = session.sql(llm_query).collect()
                            
                            if response and response[0]['RESPONSE']:
                                presentation = json.loads(response[0]['RESPONSE'])
                                content = None
                                
                                if isinstance(presentation, dict) and 'choices' in presentation:
                                    choices = presentation['choices']
                                    if choices and isinstance(choices, list) and len(choices) > 0:
                                        first_choice = choices[0]
                                        if isinstance(first_choice, dict):
                                            if 'messages' in first_choice:
                                                content = first_choice['messages']
                                            elif 'message' in first_choice and 'content' in first_choice['message']:
                                                content = first_choice['message']['content']
                                            elif 'content' in first_choice:
                                                content = first_choice['content']
                            
                                if content:
                                    st.session_state.last_presentation = content.strip()
                                    st.success("Presentation generated successfully!")
                                else:
                                    st.error("No content generated from LLM")
                            else:
                                st.error("Failed to get response from LLM")
                        else:
                            st.warning("No metrics data available for presentation")
                            
                    except Exception as e:
                        st.error(f"Error generating presentation: {str(e)}")
                        print(f"Detailed error: {traceback.format_exc()}")
                    finally:
                        # Only close the session when we're completely done with the tab
                        if 'session' in locals() and session is not None:
                            session.close()
                
            presenter_accent = st.selectbox(
                "🌍 Choose Presenter Accent",
                ["co.uk", "com", "com.au", "co.in", "ca"],  # List of string values
                index=0
            )
            # Voice playback button
            if 'last_presentation' in st.session_state:
                if st.button("🔊 AI Presenter", use_container_width=True):
                    try:
                        with st.spinner("Generating audio..."):
                            presentation_text = st.session_state.last_presentation
                            presentation_text = re.sub(r'\*\*|__', '', presentation_text)
                            presentation_text = re.sub(r'\*|_', '', presentation_text)
                            presentation_text = re.sub(r'#+\s', '', presentation_text)
                            presentation_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', presentation_text)
                            presentation_text = re.sub(r'•', '', presentation_text)
                            presentation_text = re.sub(r'\n+', ' ', presentation_text)
                            
                              
                            # Create temp file with a unique name
                            temp_dir = tempfile.gettempdir()
                            temp_file = os.path.join(temp_dir, f'presentation_{uuid.uuid4().hex}.mp3')
                            
                            try:
                                # Generate and save audio
                                tts = gTTS(
                                    text=presentation_text,
                                    lang='en',
                                    slow=False,
                                    tld=str(presenter_accent) 
                                )
                                tts.save(temp_file)
                                
                                # Play audio
                                with open(temp_file, 'rb') as audio_file:
                                    audio_bytes = audio_file.read()
                                st.audio(audio_bytes)
                                
                            finally:
                                # Clean up: Try to remove file after a short delay
                                try:
                                    time.sleep(1)  # Give a small delay
                                    if os.path.exists(temp_file):
                                        os.remove(temp_file)
                                except Exception:
                                    pass  # Ignore cleanup errors
                                    
                    except Exception as e:
                        st.error(f"Error generating voice presentation: {str(e)}")
                        
            st.markdown("<br>", unsafe_allow_html=True)  # Add space
           
        # Display presentation content in main area
        if 'last_presentation' in st.session_state:
            st.markdown("## 📊 AI Dashboard Presentation")
            st.markdown("""
                <div style="
                    background-color: #1E0935;
                    padding: 2rem;
                    border-radius: 10px;
                    border: 1px solid #541680;
                    margin: 1rem 0;
                ">
            """, unsafe_allow_html=True)
            st.markdown(st.session_state.last_presentation)
            st.markdown("</div>", unsafe_allow_html=True)
            
                
                
    def calculate_change(self, current: float, previous: float) -> str:
        """Calculate percentage change between two values"""
        if previous == 0 or pd.isna(previous) or pd.isna(current):
            return "+0%"
        change = ((current - previous) / previous) * 100
        return f"{'+' if change >= 0 else ''}{change:.1f}%"
            
            
            

    def get_quality_metrics(self, session):
        """Fetch comprehensive quality metrics using RAG_DOCUMENTS_TMP and ANALYTICS_METRICS tables"""
        try:
            # Check RAG_DOCUMENTS_TMP table
            docs_query = """
            SELECT 
                FILENAME,
                FILE_TYPE,
                COUNT(*) as count
            FROM RAG_DOCUMENTS_TMP
            GROUP BY FILENAME, FILE_TYPE
            """
            
            # Check ANALYTICS_METRICS table
            metrics_query = """
            SELECT 
                DOCUMENT_NAME,
                COUNT(*) as query_count,
                AVG(RESPONSE_TIME_MS) as avg_response,
                COUNT(CASE WHEN STATUS = 'success' THEN 1 END) as success_count
            FROM ANALYTICS_METRICS
            GROUP BY DOCUMENT_NAME
            """
            
            # Get results from both tables
            docs_results = session.sql(docs_query).collect()
            metrics_results = session.sql(metrics_query).collect()
            
            # Calculate performance score based on response times
            avg_response_time = sum(float(row['AVG_RESPONSE']) for row in metrics_results) / len(metrics_results) if metrics_results else 0
            performance_score = 100 - min((avg_response_time / 1000) * 10, 100) if avg_response_time > 0 else 0
            
            return {
                'summary': {
                    'total_documents': len(docs_results),
                    'accessed_documents': len(metrics_results),
                    'performance_score': performance_score,
                    'docs_with_errors': sum(1 for row in metrics_results if row['SUCCESS_COUNT'] < row['QUERY_COUNT'])
                },
                'trends': [{
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'active_docs': len(docs_results),
                    'success_rate': (sum(row['SUCCESS_COUNT'] for row in metrics_results) / 
                                sum(row['QUERY_COUNT'] for row in metrics_results) * 100)
                                if metrics_results and sum(row['QUERY_COUNT'] for row in metrics_results) > 0 else 0
                }],
                'distribution': [{
                    'type': row['FILE_TYPE'],
                    'count': row['COUNT'],
                    'queries': sum(m['QUERY_COUNT'] for m in metrics_results 
                                if m['DOCUMENT_NAME'] == row['FILENAME'])
                } for row in docs_results]
            }
                
        except Exception as e:
            st.error(f"Error checking tables: {str(e)}")
            return None
        
    def render_quality_overview(self, quality_metrics, session):
        """Render document quality overview with Combined Metrics view"""
        if not quality_metrics:
            st.warning("No quality metrics data available")
            return

        try:
            # Get metrics from Combined Metrics view
            combined_query = """
            SELECT 
                COUNT(DISTINCT m.FILENAME) as total_documents,
                COUNT(DISTINCT a.DOCUMENT_NAME) as accessed_documents,
                AVG(a.RESPONSE_TIME_MS) as avg_response_time,
                COUNT(CASE WHEN a.STATUS != 'success' THEN 1 END) as error_count
            FROM TESTDB.MYSCHEMA.BOOK_METADATA m
            LEFT JOIN TESTDB.MYSCHEMA.ANALYTICS_METRICS a 
                ON m.FILENAME = a.DOCUMENT_NAME
            """
            metrics_results = session.sql(combined_query).collect()
            
            if metrics_results:
                metrics = metrics_results[0]
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    self.create_metric_with_info(
                        "Total Documents",
                        metrics['TOTAL_DOCUMENTS'] or 0,
                        None,
                        None,
                        "Total number of documents currently stored in the system"
                    )
                
                with col2:
                    total_docs = metrics['TOTAL_DOCUMENTS'] or 0
                    accessed_docs = metrics['ACCESSED_DOCUMENTS'] or 0
                    accessed_pct = (accessed_docs / total_docs * 100) if total_docs > 0 else 0
                    self.create_metric_with_info(
                        "Documents Accessed",
                        f"{accessed_pct:.0f}%",
                        None,
                        None,
                        "Percentage of documents that have been queried at least once"
                    )
                    
                with col3:
                    avg_response = metrics['AVG_RESPONSE_TIME'] or 0
                    perf_score = 100 - min((avg_response / 1000) * 10, 100)
                    self.create_metric_with_info(
                        "Performance Score",
                        f"{perf_score:.1f}",
                        None,
                        None,
                        "Overall system performance rating based on response times and success rates"
                    )
                    
                with col4:
                    self.create_metric_with_info(
                        "Documents with Errors",
                        metrics['ERROR_COUNT'] or 0,
                        None,
                        None,
                        "Number of documents that encountered processing errors or failed queries"
                    )

            # Document Analysis Chart
            st.markdown("<h3 style='text-align: left;'>Document Interaction Analysis</h3>", unsafe_allow_html=True)
            
            doc_analysis_query = """
            SELECT 
                a.DOCUMENT_NAME as filename,
                m.CATEGORY,
                COUNT(*) as interaction_count,
                SUM(a.TOKEN_COUNT) as total_tokens,
                AVG(a.RESPONSE_TIME_MS) as avg_response_time,
                COUNT(CASE WHEN a.STATUS = 'success' THEN 1 END) as successful_interactions
            FROM TESTDB.MYSCHEMA.ANALYTICS_METRICS a
            JOIN TESTDB.MYSCHEMA.BOOK_METADATA m 
                ON a.DOCUMENT_NAME = m.FILENAME
            GROUP BY a.DOCUMENT_NAME, m.CATEGORY
            ORDER BY interaction_count DESC
            """
            doc_results = session.sql(doc_analysis_query).collect()
            
            if doc_results:
                df_docs = pd.DataFrame([{
                    'Document': row['FILENAME'],
                    'Interactions': int(row['INTERACTION_COUNT']),
                    'Total Tokens': int(row['TOTAL_TOKENS'] or 0),
                } for row in doc_results])
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_docs['Document'],
                    y=df_docs['Interactions'],
                    name='User Interactions',
                    marker_color='#60a5fa',
                    hovertemplate='<b>%{x}</b><br>Interactions: %{y}<br><extra></extra>'
                ))
                
                fig = self.apply_modern_clean_style(fig, 'Document Interaction Analysis')
                fig.update_layout(
                    yaxis=dict(title='Number of Interactions', rangemode='nonnegative', tickformat='d'),
                    xaxis=dict(title='Documents', tickangle=45, tickfont=dict(size=10)),
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("<h3 style='text-align: left;'>Quality Metrics Distribution</h3>", unsafe_allow_html=True)
                metrics_query = """
                SELECT 
                    DOCUMENT_NAME,
                    COUNT(*) as query_count,
                    AVG(RESPONSE_TIME_MS) as avg_response_time,
                    AVG(TOKEN_COUNT) as avg_tokens,
                    AVG(MEMORY_USAGE_MB) as avg_memory,
                    COUNT(CASE WHEN STATUS = 'success' THEN 1 END) * 100.0 / COUNT(*) as success_rate
                FROM TESTDB.MYSCHEMA.ANALYTICS_METRICS
                GROUP BY DOCUMENT_NAME
                """
                quality_results = session.sql(metrics_query).collect()

                if quality_results:
                    df_quality = pd.DataFrame(quality_results)
                    
                    # Melt the DataFrame to convert to long format
                    df_melted = df_quality.melt(
                        id_vars=['DOCUMENT_NAME'],
                        value_vars=['AVG_RESPONSE_TIME', 'AVG_TOKENS', 'AVG_MEMORY', 'SUCCESS_RATE'],
                        var_name='METRIC',
                        value_name='VALUE'
                    )

                    fig = px.bar(
                        df_melted,
                        x='DOCUMENT_NAME',
                        y='VALUE',
                        color='METRIC',
                        barmode='group',
                        template='plotly_dark',
                        color_discrete_sequence=['#60a5fa', '#34d399', '#f472b6', '#a78bfa'],  # Changed to use color_discrete_sequence
                        labels={
                            'DOCUMENT_NAME': 'Document',
                            'VALUE': 'Score',
                            'METRIC': 'Metric'
                        }
                    )
                    
                    fig = self.apply_modern_clean_style(fig, 'Performance Metrics by Document')
                    # Add this line to actually display the plot
                    st.plotly_chart(fig, use_container_width=True)
                  
                  
                # Document Type Distribution
                st.markdown("<h3 style='text-align: left;'>Document Type Distribution</h3>", unsafe_allow_html=True)
                doc_type_query = """
                SELECT 
                    CATEGORY,
                    COUNT(*) as doc_count
                FROM TESTDB.MYSCHEMA.BOOK_METADATA
                GROUP BY CATEGORY
                ORDER BY doc_count DESC
                """
                doc_type_results = session.sql(doc_type_query).collect()

                if doc_type_results:
                    df_doc_types = pd.DataFrame(doc_type_results)
                    
                    fig_types = px.bar(
                        df_doc_types,
                        x='CATEGORY',
                        y='DOC_COUNT',
                        template='plotly_dark',
                        color_discrete_sequence=['#9333ea'],  # Purple color to match theme
                        labels={
                            'CATEGORY': 'Document Type',
                            'DOC_COUNT': 'Number of Documents'
                        }
                    )
                    fig_types.update_yaxes(tickformat='d') 
                    fig_types = self.apply_modern_clean_style(fig_types, 'Document Type Distribution')
                    st.plotly_chart(fig_types, use_container_width=True)
                  
            
                  
                    
            else:
                st.info("No analytics metrics available yet.")
                
        except Exception as e:
            st.error(f"Error loading metrics: {str(e)}")
            print(f"Detailed error: {str(e)}")
        finally:
            if session:
                session.close()
                    
                    
    def run(self):            
        
        col1, col2 = st.columns([3, 1])  
        with col1:
            time_filter = st.selectbox(
                "Time Range",
                ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"], 
                index=0
            )
        with col2:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
        
        session = SnowparkManager.get_session()
        if session:
            try:
                metrics_data = session.sql("SELECT * FROM ANALYTICS_METRICS ORDER BY TIMESTAMP DESC").collect()
                
                if metrics_data:  
                    df = pd.DataFrame(metrics_data)
                    
                    tabs = st.tabs(["💻 System Performance", "📚 Document Analytics", "🎙️ AI Presenter"])

                    
                    with tabs[0]:
                        st.markdown("""                             
                        <div style="                                 
                            padding: 10px;                                 
                            background-color: #46125;                                 
                            border-radius: 10px;                                   
                            margin-bottom: 10px;
                            text-align: center;  /* Added this */
                        ">                             
                            <h2 style="
                                color: #f9fafb;
                                margin: 0;  /* Added this to remove default margins */
                            ">System Health Overview</h2>                             
                        </div>                         
                        """, unsafe_allow_html=True)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            avg_response = df['RESPONSE_TIME_MS'].mean()
                            prev_avg = df['RESPONSE_TIME_MS'].iloc[1:].mean() if len(df) > 1 else avg_response  
                            trend = ((avg_response - prev_avg) / prev_avg * 100) if prev_avg != 0 else 0
                            self.create_metric_with_info(
                                "Avg Response Time", 
                                f"{avg_response / 1000:.1f}s",
                                f"{abs(trend):.1f}%",
                                "up" if trend > 0 else "down",
                                "Average time taken to process queries and generate responses. Lower values indicate better performance."
                                "qa_tokens_metric"  # Added this parameter
                            )
                        
                        with col2:
                            avg_memory = df['MEMORY_USAGE_MB'].mean()
                            prev_memory = df['MEMORY_USAGE_MB'].iloc[1:].mean() if len(df) > 1 else avg_memory
                            trend = ((avg_memory - prev_memory) / prev_memory * 100) if prev_memory != 0 else 0  
                            self.create_metric_with_info(
                                "Avg Memory Usage",
                                f"{avg_memory:.1f}MB", 
                                f"{abs(trend):.1f}%",
                                "up" if trend > 0 else "down",
                                "Average RAM usage during operations. Shows system resource consumption."
                                "qa_tokens_metric"  # Added this parameter
                            )
                        
                        with col3:
                            success_rate = (df['STATUS'] == 'success').mean() * 100
                            prev_success = (df['STATUS'].iloc[1:] == 'success').mean() * 100 if len(df) > 1 else success_rate
                            trend = success_rate - prev_success
                            self.create_metric_with_info(
                                "Success Rate",
                                f"{success_rate:.1f}%",
                                f"{abs(trend):.1f}%",  
                                "up" if trend > 0 else "down",
                                "Percentage of successful operations. Higher values indicate better reliability."
                                "qa_tokens_metric"  # Added this parameter
                            )
                        
                        with col4:
                            avg_tokens = df['TOKEN_COUNT'].mean()
                            prev_tokens = df['TOKEN_COUNT'].iloc[1:].mean() if len(df) > 1 else avg_tokens  
                            trend = ((avg_tokens - prev_tokens) / prev_tokens * 100) if prev_tokens != 0 else 0
                            self.create_metric_with_info(
                                "Avg Token Usage",
                                f"{avg_tokens:.0f}",
                                f"{abs(trend):.1f}%",
                                "up" if trend > 0 else "down",
                               "Average number of tokens used per operation. Affects processing time and cost."
                               "qa_tokens_metric"  # Added this parameter
                            )
                        
                        st.markdown("### Performance Trends")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            fig = px.line(df, x='TIMESTAMP', y='RESPONSE_TIME_MS', 
                                        template='plotly_dark')
                            fig = self.apply_modern_clean_style(fig, 'Response Time Trends')
                            fig.update_traces(line_color="#60a5fa", line_width=2)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            #st.write("Debug - DataFrame:", df)
                            fig = px.line(df, x='TIMESTAMP', y='MEMORY_USAGE_MB',
                                        template='plotly_dark')
                            fig = self.apply_modern_clean_style(fig, 'Memory Usage Trends')  
                            fig.update_traces(line_color="#ef4444", line_width=2)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.markdown("### Additional Metrics")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig = px.scatter(df, x='TIMESTAMP', y='TOKEN_COUNT',
                                            template='plotly_dark', opacity=0.7,
                                            labels={'TIMESTAMP': 'Timestamp', 'TOKEN_COUNT': 'Tokens Used'})
                            fig = self.apply_modern_clean_style(fig, 'Token Usage Over Time')
                            fig.update_traces(marker=dict(size=10, color='#8b5cf6', line=dict(width=1, color='white')))
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            df['Success'] = (df['STATUS'] == 'success').astype(int)
                            success_over_time = df.groupby(pd.Grouper(key='TIMESTAMP', freq='1h'))['Success'].mean() * 100
                            fig = px.line(success_over_time, 
                                        template='plotly_dark')  
                            fig = self.apply_modern_clean_style(fig, 'Success Rate Over Time')
                            fig.update_traces(line_color="#10b981", line_width=2)
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with tabs[1]:  # Document Analytics tab
                        #st.markdown("### 📊 Document Quality Analysis")
                    
                        # Fetch quality metrics
                            quality_metrics = self.get_quality_metrics(session)
                            st.markdown("""                             
                                <div style="                                 
                                    padding: 10px;                                 
                                    background-color: #46125;                                 
                                    border-radius: 10px;                                   
                                    margin-bottom: 10px;
                                    text-align: center;  /* Added this */
                                ">                             
                                    <h2 style="
                                        color: #f9fafb;
                                        margin: 0;  /* Added this to remove default margins */
                                    ">Document Quality Overview</h2>                             
                                </div>                         
                                """, unsafe_allow_html=True)
                            
                            # Display metrics using native Streamlit components
                            self.render_quality_overview(quality_metrics, session)
                            
                            # Add explanatory text
                            st.markdown("""                                 
                                <div style="
                                    padding: 20px; 
                                    background: linear-gradient(135deg, #2D033B 0%, #810CA8 100%);
                                    border-radius: 10px; 
                                    margin-top: 20px;
                                    border: 1px solid rgba(255, 255, 255, 0.1);
                                ">
                                    <h4 style="color: #E5B8F4;">📊 Quality Metrics Explanation</h4>
                                    <ul style="color: #E5B8F4;">
                                        <li><strong style="color: #C147E9;">Total Documents:</strong> Number of documents in the system</li>
                                        <li><strong style="color: #C147E9;">Documents Accessed:</strong> Percentage of documents that have been queried</li>
                                        <li><strong style="color: #C147E9;">Performance Score:</strong> Overall system performance rating</li>
                                        <li><strong style="color: #C147E9;">Documents with Errors:</strong> Number of documents with processing issues</li>
                                    </ul>
                                </div>
                            """, unsafe_allow_html=True)
                        
                      
      
                            
                    with tabs[2]:
                        st.markdown("### 🎙️ AI Presenter")
                        # If metrics data exists, render the AI presenter
                        if metrics_data is not None:
                            self.render_ai_presenter(metrics_data)
                        else:
                            st.warning("No metrics data available for presentation")
                                                              
                                            
                        
                else:
                    st.info("No metrics data available yet")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            
            finally:
                session.close()
        else:
            st.error("Failed to establish database connection")

if __name__ == "__main__":
    dashboard = DashboardPage()
    dashboard.run()