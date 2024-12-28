import streamlit as st
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import time
import statistics
from datetime import datetime
from trulens_eval import Feedback, TruLlama

@dataclass
class MetricsTracker:
    """Tracks various performance metrics for the PDF Library application"""
    
    def __init__(self):
        # Initialize metric storage
        self.relevance_metrics = {
            'keyword_match_scores': [],
            'response_lengths': [],
            'context_usage_rates': []
        }
        
        self.performance_metrics = {
            'response_times': [],
            'memory_usage': [],
            'tokens_processed': []
        }
        
        self.search_metrics = {
            'precision_at_k': [],
            'first_relevant_positions': [],
            'results_count': []
        }
        
        self.user_metrics = {
            'time_to_first_click': [],
            'session_durations': [],
            'query_lengths': []
        }
        
        self.rag_metrics = {
            'context_lengths': [],
            'context_response_ratios': [],
            'source_counts': []
        }
        
        self.business_metrics = {
            'cost_per_query': [],
            'success_rates': [],
            'sla_compliance': []
        }

    def track_relevance_metrics(self, query: str, response: str, context: str) -> Dict[str, float]:
        """Track relevance-related metrics"""
        try:
            metrics = {
                'keyword_match': len(set(query.split()) & set(response.split())) / max(len(query.split()), 1),
                'response_length': len(response.split()),
                'context_usage': len(set(context.split()) & set(response.split())) / max(len(context.split()), 1)
            }
            
            self.relevance_metrics['keyword_match_scores'].append(metrics['keyword_match'])
            self.relevance_metrics['response_lengths'].append(metrics['response_length'])
            self.relevance_metrics['context_usage_rates'].append(metrics['context_usage'])
            
            return metrics
        except Exception as e:
            st.error(f"Error tracking relevance metrics: {str(e)}")
            return {}

    def track_performance_metrics(self, start_time: float, end_time: float, 
                                memory_used: int, tokens: int) -> Dict[str, float]:
        """Track performance-related metrics"""
        try:
            metrics = {
                'response_time': end_time - start_time,
                'memory_used_mb': memory_used / (1024 * 1024),
                'tokens_processed': tokens
            }
            
            self.performance_metrics['response_times'].append(metrics['response_time'])
            self.performance_metrics['memory_usage'].append(metrics['memory_used_mb'])
            self.performance_metrics['tokens_processed'].append(metrics['tokens_processed'])
            
            return metrics
        except Exception as e:
            st.error(f"Error tracking performance metrics: {str(e)}")
            return {}

    def track_search_metrics(self, results: List[Dict], clicked_position: Optional[int] = None) -> Dict[str, float]:
        """Track search-related metrics"""
        try:
            metrics = {
                'precision_at_3': len([r for r in results[:3] if r.get('relevant', False)]) / 3,
                'first_relevant_position': next((i for i, r in enumerate(results) if r.get('relevant', False)), -1),
                'results_count': len(results)
            }
            
            self.search_metrics['precision_at_k'].append(metrics['precision_at_3'])
            self.search_metrics['first_relevant_positions'].append(metrics['first_relevant_position'])
            self.search_metrics['results_count'].append(metrics['results_count'])
            
            return metrics
        except Exception as e:
            st.error(f"Error tracking search metrics: {str(e)}")
            return {}

    def track_user_metrics(self, start_time: float, first_click_time: float, 
                          end_time: float, query: str) -> Dict[str, float]:
        """Track user interaction metrics"""
        try:
            metrics = {
                'time_to_first_click': first_click_time - start_time,
                'session_duration': end_time - start_time,
                'query_length': len(query.split())
            }
            
            self.user_metrics['time_to_first_click'].append(metrics['time_to_first_click'])
            self.user_metrics['session_durations'].append(metrics['session_duration'])
            self.user_metrics['query_lengths'].append(metrics['query_length'])
            
            return metrics
        except Exception as e:
            st.error(f"Error tracking user metrics: {str(e)}")
            return {}

    def get_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics for all tracked metrics"""
        try:
            return {
                'Relevance & Quality': {
                    'Keyword Match': f"{self._safe_mean(self.relevance_metrics['keyword_match_scores']):.2%}",
                    'Response Length': f"{self._safe_mean(self.relevance_metrics['response_lengths']):.0f} words",
                    'Context Usage': f"{self._safe_mean(self.relevance_metrics['context_usage_rates']):.2%}"
                },
                'Performance': {
                    'Response Time': f"{self._safe_mean(self.performance_metrics['response_times']) /1000:.1f}s",
                    'Memory Usage': f"{self._safe_mean(self.performance_metrics['memory_usage']):.1f}MB",
                    'Tokens/Query': f"{self._safe_mean(self.performance_metrics['tokens_processed']):.0f}"
                },
                'Search Quality': {
                    'Precision@3': f"{self._safe_mean(self.search_metrics['precision_at_k']):.2%}",
                    'First Relevant': f"Position {self._safe_mean(self.search_metrics['first_relevant_positions']):.1f}",
                    'Results/Query': f"{self._safe_mean(self.search_metrics['results_count']):.1f}"
                }
            }
        except Exception as e:
            st.error(f"Error generating metrics summary: {str(e)}")
            return {}

    def _safe_mean(self, values: List[float]) -> float:
        """Safely calculate mean of a list of values"""
        try:
            return statistics.mean(values) if values else 0
        except Exception:
            return 0
        
        
        
        
        

class MetricsDashboard:
    """Handles the rendering of metrics in Streamlit"""
    
    @staticmethod
    def render_dashboard(metrics_tracker: MetricsTracker):
        """Render metrics dashboard in Streamlit"""
        st.title("📊 Performance Metrics Dashboard")
        
        # Get metrics summary
        metrics = metrics_tracker.get_metrics_summary()
        
        # Display metrics in tabs
        tabs = st.tabs(['Relevance & Quality', 'Performance', 'Search Quality'])
        
        for tab, (category, category_metrics) in zip(tabs, metrics.items()):
            with tab:
                st.header(category)
                
                # Create columns for metrics
                cols = st.columns(len(category_metrics))
                
                # Display each metric in a card
                for col, (metric_name, metric_value) in zip(cols, category_metrics.items()):
                    with col:
                        st.markdown(
                            f"""
                            <div style="
                                padding: 1rem;
                                border-radius: 0.5rem;
                                background: white;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                margin-bottom: 1rem;
                            ">
                                <h3 style="margin: 0; color: #666; font-size: 0.9rem;">{metric_name}</h3>
                                <p style="margin: 0.5rem 0 0 0; font-size: 1.5rem; font-weight: bold;">{metric_value}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    @staticmethod
    def render_export_section():
        """Render export options for metrics"""
        st.header("📊 Export Metrics")
        if st.button("Export to CSV"):
            # Add export functionality here
            st.info("Export functionality to be implemented")
            
            
    def show_system_health():
        # Initialize metrics in session state if not exists
        if 'system_metrics' not in st.session_state:
            st.session_state.system_metrics = {
                'total_files': len(st.session_state.files),
                'upload_count': 0,
                'search_count': 0,
                'memory_usage': psutil.Process().memory_info().rss / (1024 * 1024),  # MB
                'last_operation_time': 0
            }

        # Update current metrics
        current_metrics = {
            'total_files': len(st.session_state.files),
            'memory_usage': psutil.Process().memory_info().rss / (1024 * 1024),
        }

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
                <div style="padding: 20px; background: #374151; border-radius: 10px; text-align: center;">
                    <h3 style="color: #f9fafb; margin-bottom: 10px; font-size: 1em;">Total Documents</h3>
                    <p style="font-size: 1.8em; font-weight: bold; color: #60a5fa;">{}</p>
                </div>
            """.format(current_metrics['total_files']), unsafe_allow_html=True)

        with col2:
            st.markdown("""
                <div style="padding: 20px; background: #374151; border-radius: 10px; text-align: center;">
                    <h3 style="color: #f9fafb; margin-bottom: 10px; font-size: 1em;">Memory Usage</h3>
                    <p style="font-size: 1.8em; font-weight: bold; color: #60a5fa;">{:.1f} MB</p>
                </div>
            """.format(current_metrics['memory_usage']), unsafe_allow_html=True)

        with col3:
            st.markdown("""
                <div style="padding: 20px; background: #374151; border-radius: 10px; text-align: center;">
                    <h3 style="color: #f9fafb; margin-bottom: 10px; font-size: 1em;">Upload Count</h3>
                    <p style="font-size: 1.8em; font-weight: bold; color: #60a5fa;">{}</p>
                </div>
            """.format(st.session_state.system_metrics['upload_count']), unsafe_allow_html=True)

        with col4:
            st.markdown("""
                <div style="padding: 20px; background: #374151; border-radius: 10px; text-align: center;">
                    <h3 style="color: #f9fafb; margin-bottom: 10px; font-size: 1em;">Search Count</h3>
                    <p style="font-size: 1.8em; font-weight: bold; color: #60a5fa;">{}</p>
                </div>
            """.format(st.session_state.system_metrics['search_count']), unsafe_allow_html=True)

        # Document type distribution
        if st.session_state.files:
            st.markdown("### Document Distribution")
            doc_types = {}
            for file in st.session_state.files:
                category = file.get('category', 'Other')
                doc_types[category] = doc_types.get(category, 0) + 1

            fig = go.Figure(data=[
                go.Bar(
                    x=list(doc_types.keys()),
                    y=list(doc_types.values()),
                    marker_color='#60a5fa'
                )
            ])
            fig.update_layout(
                plot_bgcolor='#1E0935',
                paper_bgcolor='#11001C',
                font=dict(color='#FFFFFF'),
                margin=dict(t=30, l=30, r=30, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)

        return current_metrics