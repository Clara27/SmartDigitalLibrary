import streamlit as st
from typing import Dict, List, Any, Optional
import requests
import re
import uuid
from collections import Counter
import pandas as pd
import plotly.graph_objects as go 
import json
import numpy as np
from back import SnowparkManager
import traceback
from trulens.apps.custom import instrument
from trulens.core import TruSession
from trulens.connectors.snowflake import SnowflakeConnector
from snowflake.snowpark.context import get_active_session
from trulens.providers.cortex import Cortex
from trulens.core import Feedback, Select
from trulens.core.guardrails.base import context_filter
from back import SnowparkManager
from datetime import datetime
import uuid
from typing import Dict, Any
from trulens_eval import Select
from trulens.feedback import GroundTruthAgreement
from trulens.apps.basic import TruBasicApp
from trulens.apps.custom import TruCustomApp
from snowflake.core import Root
from typing import List
from snowflake.snowpark import Session
from trulens_eval import TruChain, Feedback, Tru, feedback, Select
import io
import logging
import threading
import subprocess
import re
from trulens_eval.tru_chain import TruChain
from io import StringIO
import contextlib
import sys
from io import StringIO
from functools import wraps




tru = Tru()



class CortexSearchRetriever:
   
 
    def __init__(self, session: Session, limit_to_retrieve: int = 4):
        try:
            session = SnowparkManager.get_session()
            if not session:
                print("ERROR: Failed to get Snowpark session")
                return
          
        
            self._session = session
            self._limit_to_retrieve = limit_to_retrieve
          
        
        except Exception as e:
            print(f"ERROR during evaluator initialization: {str(e)}")
        traceback.print_exc()

 

    def retrieve(self, query: str) -> List[str]:
        #print(f"Searching for query: {query} in file: {filename}")
        root = Root(self._session)
        cortex_search_service = (
            root.databases["TESTDB"]
            .schemas["MYSCHEMA"]
            .cortex_search_services["MY_RAG_SEARCH_SERVICE"]
        )
        print("Calling cortex_search_service.search")
        resp = cortex_search_service.search(
            query=query,
            columns=["CONTENT"],
            limit=self._limit_to_retrieve,
        )
        print(f"Search query: {query}")
        print(f"Search response: {resp}")

        if resp.results:
            print(f"Found {len(resp.results)} results")
            return [curr["CONTENT"] for curr in resp.results]
        else:
            print("No results found")
            return []
        
class RAGPipeline:
    def __init__(self):
        session = SnowparkManager.get_session()
        self.session =session
        self.retriever = CortexSearchRetriever(
            session, 
            limit_to_retrieve=3
        )
        
    
        
    @instrument
    def retrieve_context(self, query: str) -> list:
        """Retrieve relevant text from vector store."""
        try:
            contexts = self.retriever.retrieve(query)
            return contexts if contexts else []
        except Exception as e:
            print(f"Error in retrieve_context: {str(e)}")
            return []
            
    @instrument
    def generate_completion(self, query: str, contexts: list) -> str:
        """Generate answer from context."""
        try:
            # Format contexts into a string
            context_str = "\n\n".join([f"Context {i+1}:\n{ctx}" for i, ctx in enumerate(contexts)])
            
            prompt = f"""You are an expert assistant extracting information from context provided.
            Answer the question based on the context. Be concise and do not hallucinate.
            If you don't have the information just say so.

            Context:
            {context_str}

            Question: {query}
            Answer:"""
            
            llm_query = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large2',
                ARRAY_CONSTRUCT(
                    OBJECT_CONSTRUCT('role', 'system', 'content', '{prompt.replace("'", "''")}'),
                    OBJECT_CONSTRUCT('role', 'user', 'content', 'Question: {query}\\n\\nContext:\\n{context_str.replace("'", "''")}')
                ),
                OBJECT_CONSTRUCT(
                    'temperature', 0.3,
                    'max_tokens', 100
                )
            ) as response
            """
            llm_response = self.session.sql(llm_query).collect()
            synthesized_answer = SnowparkManager.process_llm_response(llm_response)
            
            return synthesized_answer
        
        except Exception as e:
            print(f"Error in generate_completion: {str(e)}")
            return "Error generating response"
        
        


    @instrument
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query and return response with contexts
        Args:
            query (str): The user's query
        Returns:
            Dict containing response and contexts
        """
        try:
            # Get relevant contexts
            contexts = self.retrieve_context(query)
            session = self.session
            
            # Generate completion using contexts
            response = self.generate_completion(query, contexts)
            
            return {
                "response": response,
                "contexts": contexts,
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error processing query: {str(e)}")
            return {
                "response": "Error processing query",
                "contexts": [],
                "query": query,
                "error": str(e)
            }


class TruLensEvaluator:
    def __init__(self):
        print("\n=== Starting TruLens Evaluator Initialization ===")
        self.initialized = False
        self.dashboard_url = None
        
        try:
            session = SnowparkManager.get_session()
            
           
            
            if not session:
                print("ERROR: Failed to get Snowpark session")
                return

            print("Initializing Cortex provider...")
            try:
                self.provider = Cortex(
                    snowpark_session=session,
                    model="mistral-large2"
                )
                print("✓ Cortex provider initialized")

                # Initialize feedback functions
                print("Setting up feedback functions...")
                self.rag = RAGPipeline() 
                self.retriever = CortexSearchRetriever(session, limit_to_retrieve=4)
                #self.get_document_summary = self.rag.get_document_summary


                self.f_answer_relevance = (
                    Feedback(self.provider.relevance_with_cot_reasons, name="Answer Relevance")
                    .on_input()
                    .on_output()
                )
                self.f_context_relevance = (
                    Feedback(self.provider.context_relevance_with_cot_reasons, name="Context Relevance")
                    .on_input()
                    .on(Select.RecordCalls.retrieve_context.rets[:])
                    .aggregate(np.mean)
                )
                self.f_groundedness = (
                    Feedback(self.provider.relevance_with_cot_reasons, name="Groundedness")
                    .on(Select.RecordCalls.retrieve_context.rets.collect())
                    .on_output()
                )
                
                
                self.f_controversiality = (
                    Feedback(self.provider.controversiality_with_cot_reasons,name="Controversiality")
                    .on_output()
                )
                self.f_insensitivity = (
                    Feedback(self.provider.insensitivity_with_cot_reasons,name="Insensitivity")
                    .on_output()
                )
  
                self.f_coherence = (
                    Feedback(self.provider.coherence_with_cot_reasons, name="Coherence")
                    .on_output()
                )
                
               

                    
                self.all_feedbacks = [           
                    self.f_answer_relevance,
                    self.f_context_relevance,
                    self.f_groundedness,
                    self.f_controversiality,
                    self.f_insensitivity,
                    self.f_coherence,
                               
                ]
                
                
                
                self.initialized = True
                print("✓ TruLens evaluator fully initialized")

            except Exception as e:
                print(f"ERROR during Cortex initialization: {str(e)}")
                traceback.print_exc()

        except Exception as e:
            print(f"ERROR during evaluator initialization: {str(e)}")
            traceback.print_exc()
    

        
        
        
    def debug_metrics(self, eval_results: Dict[str, float]) -> None:
        """Debug helper to print metric values"""
        print("\n=== TruLens Metrics Debug ===")
        for metric, value in eval_results.items():
            print(f"{metric}: {value}")
        print("============================\n")    
            
    def save_metrics_to_db(self, metrics: Dict[str, Any], operation_type: str) -> bool:
        """Save TruLens metrics to database with improved error handling"""
        print("\n=== Starting save_metrics_to_db ===")
        print(f"Operation Type: {operation_type}")
        print(f"Input Metrics: {metrics}")
        
        session = None
        try:
            session = SnowparkManager.get_session()
            if not session:
                print("Failed to get database session")
                return False

            # Generate metric ID
            metric_id = str(uuid.uuid4())
            print(f"Debug: Generated metric ID: {metric_id}")

            # Format metric values with proper NULL handling
            formatted_metrics = {
                key: ('NULL' if value is None else 
                    f"'{value}'" if isinstance(value, str) else 
                    float(value)) 
                for key, value in metrics.items()
            }

            # Construct query mapping feedback scores to TRULENS_METRICS columns
            insert_query = f"""
            INSERT INTO TESTDB.MYSCHEMA.TRULENS_METRICS (
                METRIC_ID,
                TIMESTAMP,
                RELEVANCE_SCORE,
                GROUNDEDNESS_SCORE,
                COHERENCE_SCORE,
                STYLE,
                FORMAT_TYPE,
                OUTPUT_TOKEN_COUNT,
                OPERATION_TYPE
            ) VALUES (
                '{metric_id}',
                CURRENT_TIMESTAMP(),
                {formatted_metrics.get('relevance_score', 'NULL')},
                {formatted_metrics.get('groundedness_score', 'NULL')},
                {formatted_metrics.get('coherence_score', 'NULL')},
                {formatted_metrics.get('style', "'default'")},
                {formatted_metrics.get('format_type', "'default'")},
                {formatted_metrics.get('output_token_count', 0)},
                '{operation_type}'
            )
            """
            
            print(f"Debug: Executing query:\n{insert_query}")
            session.sql(insert_query).collect()
            print(f"Debug: Successfully saved metrics with ID: {metric_id}")
            
            # Verify insertion
            verify_query = f"""
            SELECT COUNT(*) as count 
            FROM TESTDB.MYSCHEMA.TRULENS_METRICS 
            WHERE METRIC_ID = '{metric_id}'
            """
            verify_result = session.sql(verify_query).collect()
            inserted = verify_result[0]['COUNT'] > 0
            print(f"Debug: Verification result - Record {'found' if inserted else 'not found'}")
            
            return inserted

        except Exception as e:
            print(f"Error in save_metrics_to_db: {str(e)}")
            traceback.print_exc()
            return False
            
        finally:
            if session:
                session.close()
                print("Debug: Database session closed")
            

    def evaluate_relevance(self, query: str, response: str) -> float:
        """Calculate relevance score based on keyword matching and semantic similarity"""
        try:
            # Tokenize query and response
            query_tokens = set(query.lower().split())
            response_tokens = set(response.lower().split())
            
            # Calculate keyword overlap
            overlap = query_tokens.intersection(response_tokens)
            relevance_score = len(overlap) / len(query_tokens) if query_tokens else 0
            
            # Normalize score to 0-1 range
            return min(max(relevance_score, 0), 1)
        except Exception:
            return 0.0

    def evaluate_groundedness(self, response: str, contexts: List[Dict[str, Any]]) -> float:
        """Evaluate if response is grounded in the provided contexts"""
        try:
            if not contexts or not response:
                return 0.0
                
            # Extract all context content
            all_context = " ".join([ctx.get('CONTENT', '') for ctx in contexts])
            context_tokens = set(all_context.lower().split())
            response_tokens = set(response.lower().split())
            
            # Calculate what percentage of response tokens appear in context
            overlap = response_tokens.intersection(context_tokens)
            groundedness = len(overlap) / len(response_tokens) if response_tokens else 0
            
            return min(max(groundedness, 0), 1)
        except Exception:
            return 0.0
        
    @instrument
    def evaluate_pal_chat(self, query: str, filename, operation_type: str, **kwargs):
        if not self.initialized:
            return None
        stdout_backup = sys.stdout
        try:
            print("Starting evaluate_pal_chat")
            self.rag = RAGPipeline()
            
            # print ("before calling self.rag = Ragpipeline()")
            # self.rag = RAGPipeline()
            
               
            print ("before self.tru_rag")
            # Initialize your TruCustomApp with the configuration
            self.tru_rag = TruCustomApp(
                app=self.rag,
                app_name="RAG Pipeline",
                app_version="base2",
                app_id="rag_pipeline",
                feedbacks=self.all_feedbacks,
             )
                
                           
            
            with self.tru_rag as recording:  
                print("Inside tru_rag context")
                resp = self.rag.process_query(query)
                #print(f"Got response: {resp[:100]}...")
                
                              
            print("Capturing dashboard output")
            sys.stdout = StringIO()
            
            tru.run_dashboard()
            output = sys.stdout.getvalue()
            print(f"Captured output: {output}")
            
            sys.stdout = stdout_backup
            
            network_url = re.search(r'Network URL: (http://[\d\.:]+)', output)
            dashboard_url = network_url.group(1) if network_url else None
            st.session_state.dashboard_url = dashboard_url
            print(f"Extracted URL: {dashboard_url}")
            
            return {
                'response': resp,
                'dashboard_url': dashboard_url
            }
        except Exception as e:
            print(f"Error in RAG pipeline evaluation: {str(e)}")
            traceback.print_exc()
            sys.stdout = stdout_backup
            return None
            
        
        
    @instrument
    def evaluate_rag_pipeline(self, query: str, filename, operation_type: str, **kwargs):
        if not self.initialized:
            return None
        stdout_backup = sys.stdout
        try:
            print("Starting evaluate_rag_pipeline")
            self.rag = RAGPipeline()
            
            # print ("before calling self.rag = Ragpipeline()")
            # self.rag = RAGPipeline()
            
               
            print ("before self.tru_rag")
            # Initialize your TruCustomApp with the configuration
            self.tru_rag = TruCustomApp(
                app=self.rag,
                app_name="RAG Pipeline",
                app_version="base1",
                app_id="rag_pipeline",
                feedbacks=self.all_feedbacks,
            )
                
                           
            
            with self.tru_rag as recording:  
                print("Inside tru_rag context")
                resp = self.rag.process_query(query)
                #print(f"Got response: {resp[:100]}...")
                
                              
            print("Capturing dashboard output")
            sys.stdout = StringIO()
            
            tru.run_dashboard()
            output = sys.stdout.getvalue()
            print(f"Captured output: {output}")
            
            sys.stdout = stdout_backup
            
            network_url = re.search(r'Network URL: (http://[\d\.:]+)', output)
            dashboard_url = network_url.group(1) if network_url else None
            st.session_state.dashboard_url = dashboard_url
            print(f"Extracted URL: {dashboard_url}")
            
            return {
                'response': resp,
                'dashboard_url': dashboard_url
            }
        except Exception as e:
            print(f"Error in RAG pipeline evaluation: {str(e)}")
            traceback.print_exc()
            sys.stdout = stdout_backup
            return None
            
    def calculate_metrics(self, record: Dict) -> Dict[str, float]:
            """Calculate metrics using TruLens app"""
            try:
                print("\n=== Starting Metrics Calculation ===")
                print(f"Input record: {record}")
                
                if not self.initialized:
                    print("Error: TruLens evaluator not initialized")
                    return {}
                
                try:
                    # Run the app and collect metrics
                    metrics = self.tru_rag.app(record)
                    print(f"Debug: Collected metrics: {metrics}")
                    return metrics
                    
                except Exception as e:
                    print(f"Error calculating metrics: {str(e)}")
                    traceback.print_exc()
                    return {}
                    
            except Exception as e:
                print(f"Error in calculate_metrics: {str(e)}")
                traceback.print_exc()
                return {}
          
    

    def analyze_response_statistics(self, response: str) -> Dict[str, Any]:
        """Generate additional response statistics"""
        try:
            if not response:
                return {}
                
            words = response.split()
            sentences = re.split(r'[.!?]+', response)
            
            return {
                "word_count": len(words),
                "sentence_count": len(sentences),
                "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
                "unique_words": len(set(words)),
                "vocabulary_richness": len(set(words)) / len(words) if words else 0
            }
        except Exception:
            return {}


    
    def evaluate_search(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Evaluate search results using precision and recall metrics"""
        try:
            # Get documents marked as relevant for this query from metadata
            relevant_query = f"""
            SELECT FILENAME
            FROM TESTDB.MYSCHEMA.BOOK_METADATA
            WHERE SEARCH_GROUND_TRUTH:relevant_queries ? '{query.replace("'", "''")}'
            """
            relevant_docs = set(row['FILENAME'] for row in self.session.sql(relevant_query).collect())
            
            # If no ground truth exists, use relevance scores as proxy
            if not relevant_docs:
                relevant_docs = {r['filename'] for r in results if r['score'] >= 0.7}
            
            # Calculate metrics
            retrieved_docs = {r['filename'] for r in results}
            
            if not retrieved_docs:
                return {'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0}
                
            relevant_retrieved = len(relevant_docs.intersection(retrieved_docs))
            precision = relevant_retrieved / len(retrieved_docs) if retrieved_docs else 0
            recall = relevant_retrieved / len(relevant_docs) if relevant_docs else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            # Update search metrics in metadata
            self.update_search_metrics(query, results, precision, recall, f1_score)
            
            return {
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score
            }
            
        except Exception as e:
            print(f"Error evaluating search: {str(e)}")
            return {'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0}
        
    def update_search_metrics(self, query: str, results: List[Dict[str, Any]], 
                            precision: float, recall: float, f1_score: float):
        """Update search metrics in book metadata"""
        try:
            timestamp = datetime.now().isoformat()
            
            for result in results:
                # Get existing metadata
                metadata_query = f"""
                SELECT SEARCH_METADATA
                FROM TESTDB.MYSCHEMA.BOOK_METADATA
                WHERE FILENAME = '{result['filename'].replace("'", "''")}'
                """
                
                existing = self.session.sql(metadata_query).collect()
                
                if existing:
                    # Parse existing metadata or create new
                    current_metadata = json.loads(existing[0]['SEARCH_METADATA']) if existing[0]['SEARCH_METADATA'] else {
                        'search_history': [],
                        'avg_metrics': {
                            'precision': 0.0,
                            'recall': 0.0,
                            'f1_score': 0.0
                        }
                    }
                    
                    # Add new search record
                    search_record = {
                        'query': query,
                        'timestamp': timestamp,
                        'relevance_score': result['score'],
                        'precision': precision,
                        'recall': recall,
                        'f1_score': f1_score
                    }
                    
                    # Update search history
                    current_metadata['search_history'].append(search_record)
                    
                    # Keep only last 100 searches
                    current_metadata['search_history'] = current_metadata['search_history'][-100:]
                    
                    # Update average metrics
                    history = current_metadata['search_history']
                    if history:
                        current_metadata['avg_metrics'] = {
                            'precision': sum(h['precision'] for h in history) / len(history),
                            'recall': sum(h['recall'] for h in history) / len(history),
                            'f1_score': sum(h['f1_score'] for h in history) / len(history)
                        }
                    
                    # Update metadata in database
                    update_query = f"""
                    UPDATE TESTDB.MYSCHEMA.BOOK_METADATA
                    SET SEARCH_METADATA = PARSE_JSON('{json.dumps(current_metadata).replace("'", "''")}')
                    WHERE FILENAME = '{result['filename'].replace("'", "''")}'
                    """
                    self.session.sql(update_query).collect()
                    
        except Exception as e:
            print(f"Error updating search metrics: {str(e)}")

    def render_search_metrics(self, st_container, current_metrics: Optional[Dict[str, float]] = None):
        """Render search metrics visualization in Streamlit"""
        try:
            with st_container:
                if current_metrics:
                    st.markdown("### 📊 Search Quality Metrics")
                    
                    # Display current search metrics
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric(
                            "Precision",
                            f"{current_metrics['precision']:.2%}",
                            help="Percentage of retrieved documents that are relevant"
                        )
                    with cols[1]:
                        st.metric(
                            "Recall",
                            f"{current_metrics['recall']:.2%}",
                            help="Percentage of relevant documents that were retrieved"
                        )
                    with cols[2]:
                        st.metric(
                            "F1 Score",
                            f"{current_metrics['f1_score']:.2%}",
                            help="Harmonic mean of precision and recall"
                        )
                        
                    # Add a horizontal line for visual separation
                    st.markdown("---")
                        
        except Exception as e:
            print(f"Error rendering search metrics: {str(e)}")
    
    
    
    
 