from tempfile import NamedTemporaryFile
from snowflake.snowpark import Session
import snowflake.snowpark.types as T
import snowflake.snowpark.functions as F
from snowflake.snowpark.context import get_active_session
import PyPDF2
import docx
import textwrap 
import io
import uuid
import json
import time
import psutil
from psutil import Process
from datetime import datetime
import streamlit as st
from typing import Optional, List, Dict, Any, Tuple
import requests
import time
from gtts import gTTS
import os
from tempfile import NamedTemporaryFile
from pydub import AudioSegment
from trulens.core import TruSession
from trulens.connectors.snowflake import SnowflakeConnector
from snowflake.snowpark.context import get_active_session
from trulens.apps.custom import instrument
from trulens_eval.feedback import Feedback
from trulens_eval.feedback.provider import OpenAI
from trulens.core.guardrails.base import context_filter
from trulens.providers.cortex import Cortex
import numpy as np
from snowflake.core import Root



class SnowparkManager:
    CHUNK_SIZE_OPTIONS = {
        "Small": 1000,
        "Medium": 1500,
        "Large": 2000
    }
    
    MISTRAL_API_ENDPOINT = "https://api.mistral.ai/v1/embeddings"
    RAG_TABLE = "RAG_DOCUMENTS_TMP"

    SEARCH_SYSTEM_PROMPT = """You are a helpful AI assistant that synthesizes search results to provide accurate, concise answers.
Your task is to:
1. Analyze the provided search results and their relevance scores
2. Extract the most relevant information that answers the user's query
3. Provide a clear, comprehensive answer based on the most relevant content
4. If the search results don't contain relevant information, acknowledge this
5. Always cite the specific documents/pages you reference in your answer

Original Query: {query}"""

    SUMMARY_SYSTEM_PROMPT = """You are an expert document analyst and summarizer. Your task is to create clear, structured summaries that help readers quickly understand documents. Focus on extracting and organizing key information in a professional format.

Key Requirements:
1. Maintain factual accuracy
2. Preserve important details and context
3. Present information in clear sections
4. Use consistent formatting
5. Keep the business context in mind"""

    SUMMARY_USER_PROMPT = """Please provide a comprehensive summary of this document using the following structure:

📌 Executive Overview
- Core purpose of the document
- Key takeaways (2-3 bullet points)

📊 Main Points
- Key findings and ideas
- Critical data points
- Important statements

🔍 Detailed Analysis
- Significant sections breakdown
- Notable specifics
- Important relationships or dependencies

💡 Insights & Implications
- Key recommendations
- Action items
- Strategic considerations

Document to summarize:
{content}

Please format the response with clear section headers and bullet points for readability."""

    STYLE_INSTRUCTIONS = {
        "Concise": "Provide brief, focused answers that get straight to the point.",
        "Detailed": "Provide comprehensive answers with supporting details and explanations.",
        "Technical": "Use technical language and provide in-depth, precise explanations.",
        "Simple": "Use simple language and explain concepts in an easy-to-understand way."
    }

    FORMAT_INSTRUCTIONS = {
        "Paragraph": "Format the response as coherent paragraphs.",
        "Bullet Points": "Format the response as clear bullet points.",
        "Step by Step": "Break down the response into numbered steps.",
        "Structured": "Organize the response with clear headings and sections."
    }


    @staticmethod
    def cleanup_documents(filenames: List[str]) -> bool:
        """Clean up documents from database when session ends"""
        session = SnowparkManager.get_session()
        if not session:
            return False

        try:
            filenames_str = "', '".join([f.replace("'", "''") for f in filenames])
            
            cleanup_query = f"""
            DELETE FROM {SnowparkManager.RAG_TABLE}
            WHERE FILENAME IN ('{filenames_str}')
            """
            session.sql(cleanup_query).collect()
            return True

        except Exception as e:
            st.error(f"Failed to cleanup documents: {str(e)}")
            return False

        finally:
            session.close()
    

    @staticmethod
    def _debug_print(title: str, content: str, max_length: int = 200):
        """Helper to print debug info in a clean format"""
        if st.session_state.get('debug_mode', False):
            st.expander(f"🔍 Debug: {title}").write(content[:max_length] + ("..." if len(content) > max_length else ""))


    @staticmethod
    def get_session() -> Optional[Session]:
        """Create Snowpark session using credentials from secrets"""
        try:
            # Create a new Session using configs
            session = Session.builder.configs({
                "account": st.secrets["snowflake_account"],
                "user": st.secrets["snowflake_user"],
                "password": st.secrets["snowflake_password"],
                "warehouse": st.secrets["snowflake_warehouse"],
                "database": st.secrets["snowflake_database"],
                "schema": st.secrets["snowflake_schema"],
                "role":st.secrets["snowflake_role"]
            }).create()
            
            return session
        except Exception as e:
            print(f"Session creation error: {str(e)}")
            st.error(f"❌ Connection Error: {str(e)}")
            return None

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate Mistral API key"""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                SnowparkManager.MISTRAL_API_ENDPOINT,
                headers=headers,
                json={
                    "model": "mistral-embed",
                    "input": "test"
                }
            )
            #st.write("Inside after response {response} ")
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def setup_snowflake_context(session: Session) -> bool:
        """Set up Snowflake context with required roles and warehouses"""
        try:
            session.sql("USE ROLE ACCOUNTADMIN").collect()
            session.sql("USE DATABASE TestDB").collect()
            session.sql("USE SCHEMA MySchema").collect()
            session.sql("USE WAREHOUSE Compute_WH").collect()
            return True
        except Exception as e:
            st.error(f"❌ Failed to set up Snowflake context: {str(e)}")
            return False


    @staticmethod
    def ensure_table_exists(session: Session) -> bool:
        """Ensure both RAG documents and metadata tables exist"""
        try:
            session.sql("USE ROLE ACCOUNTADMIN").collect()
            
            # Create RAG documents table for text chunks
            rag_table_exists = session.sql(f"SHOW TABLES LIKE '{SnowparkManager.RAG_TABLE}'").collect()
            if not rag_table_exists:
                create_rag_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {SnowparkManager.RAG_TABLE} (
                    DOC_ID VARCHAR NOT NULL,
                    FILENAME VARCHAR,
                    FILE_TYPE VARCHAR,
                    CONTENT TEXT,
                    EMBEDDING VECTOR(FLOAT, 768),
                    METADATA VARIANT,
                    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
                ENABLE SEARCH OPTIMIZATION;
                """
                session.sql(create_rag_table_sql).collect()
                print(f"Created table {SnowparkManager.RAG_TABLE}")
                
            # Create metadata table for binary content
            create_metadata_table_sql = """
            CREATE TABLE IF NOT EXISTS RAG_METADATA (
                DOC_ID VARCHAR PRIMARY KEY,
                FILENAME VARCHAR,
                FILE_TYPE VARCHAR,
                BINARY_CONTENT BINARY,
                METADATA VARIANT,
                CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            );
            """
            session.sql(create_metadata_table_sql).collect()
            print("Created RAG_METADATA table")
            
            return True
                
        except Exception as e:
            st.error(f"❌ Failed to verify/create tables: {str(e)}")
            return False
          
    @staticmethod
    def debug_print_metrics(prefix: str, message: str, data: Any = None):
        """Helper method to print debug information"""
        print(f"[TRULENS DEBUG] {prefix}: {message}")
        if data is not None:
            print(f"[TRULENS DEBUG] Data: {str(data)}")    

    @staticmethod
    def insert_trulens_metrics(
        session,
        metric_id: str,
        operation_type: str,
        style: str,
        format_type: str,
        output_token_count: int,
        eval_results: dict
    ) -> bool:
        """Insert metrics with debug logging"""
        try:
            SnowparkManager.debug_print_metrics(
                "INSERT_METRICS", 
                f"Attempting to insert metrics for operation: {operation_type}",
                eval_results
            )
            
            insert_query = f"""
            INSERT INTO TESTDB.MYSCHEMA.TRULENS_METRICS (
                METRIC_ID,
                TIMESTAMP,
                OPERATION_TYPE,
                STYLE,
                FORMAT_TYPE,
                OUTPUT_TOKEN_COUNT,
                CONTEXT_RELEVANCE,
                GROUNDEDNESS_SCORE,
                COHERENCE_SCORE,
                SOURCE_DIVERSITY_SCORE,
                FLUENCY_SCORE,
                TOKEN_EFFICIENCY
            ) VALUES (
                '{metric_id}',
                CURRENT_TIMESTAMP(),
                '{operation_type}',
                '{style.replace("'", "''")}',
                '{format_type.replace("'", "''")}',
                {output_token_count},
                {eval_results.get('context_relevance', 0)},
                {eval_results.get('groundedness', 0)},
                {eval_results.get('coherence', 0)},
                {eval_results.get('source_diversity', 0)},
                {eval_results.get('fluency', 0)},
                {eval_results.get('token_efficiency', 0)}
            )
            """
            SnowparkManager.debug_print_metrics("INSERT_QUERY", insert_query)
            
            session.sql(insert_query).collect()
            SnowparkManager.debug_print_metrics("INSERT_METRICS", "Successfully inserted metrics")
            return True
            
        except Exception as e:
            SnowparkManager.debug_print_metrics("INSERT_METRICS_ERROR", str(e))
            return False
            
    @staticmethod
    def setup_streaming_infrastructure(session: Session) -> bool:
        """Set up streaming infrastructure for document processing"""
        try:
            # Create file format for documents with correct type
            session.sql("""
            CREATE FILE FORMAT IF NOT EXISTS doc_format
                TYPE = 'CSV'  -- Using CSV as base format
                COMPRESSION = 'AUTO'
                FIELD_DELIMITER = 'none'
                RECORD_DELIMITER = 'none'
                BINARY_FORMAT = 'HEX'
            """).collect()

            # Create stage if not exists
            session.sql("""
            CREATE STAGE IF NOT EXISTS docs_stage
                FILE_FORMAT = doc_format
                DIRECTORY = (ENABLE = TRUE)
            """).collect()

            # Create stream on stage
            session.sql("""
            CREATE OR REPLACE STREAM docs_stream 
                ON STAGE docs_stage
            """).collect()

            # Create task for processing documents
            session.sql("""
            CREATE OR REPLACE TASK process_documents_task
                WAREHOUSE = COMPUTE_WH
                SCHEDULE = '1 MINUTE'
                WHEN SYSTEM$STREAM_HAS_DATA('docs_stream')
            AS
            MERGE INTO RAG_DOCUMENTS_TMP t
            USING (
                SELECT 
                    UUID_STRING() as DOC_ID,
                    METADATA$FILENAME as FILENAME,
                    METADATA$FILE_CONTENT_TYPE as FILE_TYPE,
                    TO_VARCHAR(SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
                        build_scoped_file_url(@docs_stage, METADATA$FILENAME),
                        'PDF'
                    )) as raw_content,
                    CAST(SNOWFLAKE.CORTEX.EMBED_TEXT_768(
                        'snowflake-arctic-embed-m-v1.5',
                        raw_content
                    ) AS VECTOR(FLOAT, 768)) as EMBEDDING,
                    OBJECT_CONSTRUCT(
                        'source_type', 'pdf',
                        'page_number', ROW_NUMBER() OVER (PARTITION BY METADATA$FILENAME ORDER BY METADATA$FILE_ROW_NUMBER),
                        'upload_timestamp', CURRENT_TIMESTAMP()
                    ) as METADATA
                FROM docs_stream
            ) s
            ON t.DOC_ID = s.DOC_ID
            WHEN NOT MATCHED THEN INSERT
                (DOC_ID, FILENAME, FILE_TYPE, CONTENT, EMBEDDING, METADATA)
            VALUES
                (s.DOC_ID, s.FILENAME, s.FILE_TYPE, s.raw_content, s.EMBEDDING, s.METADATA)
            """).collect()

            # Resume task
            session.sql("""
            ALTER TASK process_documents_task RESUME
            """).collect()

            # Add metrics table for monitoring if it doesn't exist
            session.sql("""
            CREATE TABLE IF NOT EXISTS STREAM_METRICS (
                METRIC_ID VARCHAR NOT NULL,
                TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                METRIC_TYPE VARCHAR,
                METRIC_VALUE FLOAT,
                METADATA VARIANT
            )
            """).collect()

            return True

        except Exception as e:
            st.error(f"Failed to set up streaming infrastructure: {str(e)}")
            st.write("Error details:", str(e))  # Additional error details for debugging
            return False

    @staticmethod
    def check_streaming_status(session: Session) -> dict:
        """Check if streaming infrastructure is properly set up"""
        try:
            status = {
                'file_format': False,
                'stage': False,
                'stream': False,
                'task': False
            }
            
            # Check file format
            ff_result = session.sql("SHOW FILE FORMATS LIKE 'doc_format'").collect()
            status['file_format'] = len(ff_result) > 0
            
            # Check stage
            stage_result = session.sql("SHOW STAGES LIKE 'docs_stage'").collect()
            status['stage'] = len(stage_result) > 0
            
            # Check stream
            stream_result = session.sql("SHOW STREAMS LIKE 'docs_stream'").collect()
            status['stream'] = len(stream_result) > 0
            
            # Check task
            task_result = session.sql("SHOW TASKS LIKE 'process_documents_task'").collect()
            status['task'] = len(task_result) > 0
            
            return status
            
        except Exception as e:
            st.error(f"Error checking streaming status: {str(e)}")
            return {}

    @staticmethod
    def upload_documents_streaming(
        session: Session,
        file_content: bytes,
        filename: str,
        file_type: str
    ) -> bool:
        """Upload document to stage for streaming processing"""
        try:
            st.write("Debug: Starting upload process...")
            
            # First, verify the stage exists
            st.write("Debug: Checking stage exists...")
            stage_check = session.sql("SHOW STAGES LIKE 'docs_stage'").collect()
            if not stage_check:
                st.error("Stage 'docs_stage' not found. Please initialize streaming infrastructure first.")
                return False
            
            # Write file content to a temporary local file
            st.write("Debug: Creating temporary file...")
            with NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
                st.write(f"Debug: Temporary file created at: {temp_file_path}")
                st.write(f"Debug: File size: {len(file_content)} bytes")

            try:
                # Put file directly to docs_stage with more detailed output
                st.write("Debug: Uploading to stage...")
                put_result = session.file.put(
                    temp_file_path,
                    f"@docs_stage/{filename}",
                    auto_compress=False,
                    overwrite=True,
                    #show_progress_bar=True
                )
                st.write(f"Debug: Put operation result: {put_result}")

                # Show stage contents for debugging
                st.write("Debug: Listing stage contents...")
                list_result = session.sql("LIST @docs_stage").collect()
                st.write("Files in stage:")
                for file in list_result:
                    st.write(f"- {file['name']} ({file['size']} bytes)")

                # Verify file was staged with explicit pattern matching
                st.write(f"Debug: Verifying upload for file: {filename}")
                verify_query = f"""
                LIST @docs_stage
                PATTERN = '.*{filename}.*'
                """
                verification = session.sql(verify_query).collect()
                
                if verification and len(verification) > 0:
                    st.write("Debug: File successfully staged")
                    st.write(f"Debug: Found {len(verification)} matching files:")
                    for v in verification:
                        st.write(f"- {v['name']} ({v['size']} bytes)")
                    
                    # Insert initial metadata
                    st.write("Debug: Inserting metadata...")
                    metadata_sql = f"""
                    INSERT INTO
                    BOOK_METADATA (
                        BOOK_ID,
                        FILENAME,
                        CATEGORY,
                        DATE_ADDED,
                        SIZE,
                        USAGE_STATS
                    )
                    SELECT
                    UUID_STRING(),
                    '{filename.replace("' ", " '' ")}',
                        'Document',
                        CURRENT_TIMESTAMP(),
                        LENGTH(file_content),
                        parse_json('{" queries ": 0, " summaries ": 0}')
                    FROM
                        (SELECT '{file_content}' AS file_content)
                    """  
                else:
                    st.write(f"Debug: File not found in stage after upload")
                    st.write(f"Debug: Verification query: {verify_query}")
                    return False

            except Exception as e:
                st.error(f"Error during staging operation: {str(e)}")
                return False
            finally:
                # Clean up temporary file
                try:
                    st.write("Debug: Cleaning up temporary file...")
                   # os.unlink(temp_file_path)
                    st.write("Debug: Temporary file cleaned up successfully")
                except Exception as e:
                    st.write(f"Debug: Error cleaning up temporary file: {str(e)}")

        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
            st.write(f"Error details: {str(e)}")
            return False
    


    @staticmethod
    def process_pdf(
        file_content: bytes,
        filename: str,
        file_type: str,
        chunk_size: int
    ) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Process PDF content into chunks for storage and extract binary content.
        Returns:
            Tuple containing (success, error_message, documents)
        """
        try:
            documents = []
            
            if file_type == "application/pdf":
                # Process PDF using PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                total_pages = len(pdf_reader.pages)

                for page_num in range(total_pages):
                    text = pdf_reader.pages[page_num].extract_text()
                    # Format PDF content with page numbers
                    formatted_text = f"## Page {page_num + 1}\n\n{text}"
                    documents.append({
                        "page_num": page_num + 1,
                        "text": formatted_text
                    })

            elif file_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                # Process Word document
                doc = docx.Document(io.BytesIO(file_content))
                current_chunk = []
                current_length = 0
                chunk_number = 1

                for paragraph in doc.paragraphs:
                    if not paragraph.text.strip():
                        continue
                    
                    text = paragraph.text.strip()
                    style_name = paragraph.style.name.lower()

                    if 'heading' in style_name:
                        level = style_name[-1] if style_name[-1].isdigit() else '2'
                        formatted_text = f"{'#' * int(level)} {text}"
                    elif style_name == 'list paragraph':
                        formatted_text = f"* {text}"
                    else:
                        formatted_text = text

                    if current_length + len(formatted_text) >= chunk_size:
                        if current_chunk:
                            documents.append({
                                "page_num": chunk_number,
                                "text": "\n\n".join(current_chunk)
                            })
                            chunk_number += 1
                            current_chunk = []
                            current_length = 0

                    current_chunk.append(formatted_text)
                    current_length += len(formatted_text)

                if current_chunk:
                    documents.append({
                        "page_num": chunk_number,
                        "text": "\n\n".join(current_chunk)
                    })

            elif file_type == "text/plain":
                text_content = file_content.decode("utf-8")
                lines = text_content.split('\n')
                current_chunk = []
                current_length = 0
                chunk_number = 1

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith('#'):
                        formatted_text = line
                    elif line.startswith('-') or line.startswith('*'):
                        formatted_text = line
                    elif ':' in line and len(line.split(':')[0].split()) <= 3:
                        section, content = line.split(':', 1)
                        formatted_text = f"### {section.strip()}\n{content.strip()}"
                    else:
                        formatted_text = line

                    if current_length + len(formatted_text) >= chunk_size:
                        if current_chunk:
                            documents.append({
                                "page_num": chunk_number,
                                "text": "\n\n".join(current_chunk)
                            })
                            chunk_number += 1
                            current_chunk = []
                            current_length = 0

                    current_chunk.append(formatted_text)
                    current_length += len(formatted_text)

                if current_chunk:
                    documents.append({
                        "page_num": chunk_number,
                        "text": "\n\n".join(current_chunk)
                    })

            else:
                return False, f"Unsupported file type: {file_type}", None

            print(f"Processed {len(documents)} chunks from document")
            return True, "", documents

        except Exception as e:
            return False, f"Error processing document: {str(e)}", None
    
    @staticmethod
    def check_document_exists(session: Session, filename: str) -> bool:
        """Check if document already exists in database"""
        try:
            escaped_filename = filename.replace("'", "''")
            check_query = f"""
            SELECT COUNT(*) as count
            FROM {SnowparkManager.RAG_TABLE}
            WHERE FILENAME = '{escaped_filename}'
            """
            result = session.sql(check_query).collect()
            return result[0]['COUNT'] > 0
        except Exception as e:
            st.error(f"Error checking document existence: {str(e)}")
            return False

    @staticmethod
    def cleanup_duplicate_documents(session: Session, filename: str) -> bool:
        """Remove duplicate documents from database"""
        try:
            escaped_filename = filename.replace("'", "''")
            cleanup_query = f"""
            DELETE FROM {SnowparkManager.RAG_TABLE}
            WHERE DOC_ID IN (
                SELECT DOC_ID
                FROM (
                    SELECT DOC_ID,
                        ROW_NUMBER() OVER (PARTITION BY FILENAME ORDER BY CREATED_AT DESC) as rn
                    FROM {SnowparkManager.RAG_TABLE}
                    WHERE FILENAME = '{escaped_filename}'
                )
                WHERE rn > 1
            )
            """
            session.sql(cleanup_query).collect()
            return True
        except Exception as e:
            st.error(f"Error cleaning up duplicates: {str(e)}")
            return False



    def upload_documents_streaming(
        session: Session,
        file_content: bytes,
        filename: str,
        file_type: str
    ) -> bool:
        """Upload document to stage for streaming processing with improved metadata handling"""
        try:
            st.write("Debug: Starting upload process...")
            
            # First, verify the stage exists
            st.write("Debug: Checking stage exists...")
            stage_check = session.sql("SHOW STAGES LIKE 'docs_stage'").collect()
            if not stage_check:
                st.error("Stage 'docs_stage' not found. Please initialize streaming infrastructure first.")
                return False
            
            # Write file content to a temporary local file
            st.write("Debug: Creating temporary file...")
            with NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
                st.write(f"Debug: Temporary file created at: {temp_file_path}")
                st.write(f"Debug: File size: {len(file_content)} bytes")

            try:
                # Put file directly to docs_stage
                st.write("Debug: Uploading to stage...")
                put_result = session.file.put(
                    temp_file_path,
                    f"@docs_stage/{filename}",
                    auto_compress=False,
                    overwrite=True
                )
                st.write(f"Debug: Put operation result: {put_result}")

                # Verify file was staged
                st.write(f"Debug: Verifying upload for file: {filename}")
                verify_query = f"""
                LIST @docs_stage
                PATTERN = '.*{filename}.*'
                """
                verification = session.sql(verify_query).collect()
                
                if verification and len(verification) > 0:
                    st.write("Debug: File successfully staged")
                    
                    # Create properly escaped JSON string for usage stats
                    usage_stats = json.dumps({
                        "queries": 0,
                        "summaries": 0
                    }).replace("'", "''")  # Properly escape single quotes for SQL
                    
                    # Get the file size from the staged file
                    file_size = verification[0]['size']
                    
                    # Insert metadata with properly formatted JSON
                    st.write("Debug: Inserting metadata...")
                    metadata_sql = f"""
                    INSERT INTO TESTDB.MYSCHEMA.BOOK_METADATA (
                        BOOK_ID,
                        FILENAME,
                        CATEGORY,
                        DATE_ADDED,
                        SIZE,
                        USAGE_STATS
                    )
                    SELECT 
                        UUID_STRING(),           -- Generate unique ID
                        '{filename.replace("'", "''")}',  -- Escaped filename
                        'Document',              -- Default category
                        CURRENT_TIMESTAMP(),     -- Current timestamp
                        {file_size},             -- Size from staged file
                        PARSE_JSON('{usage_stats}')  -- Parsed JSON object
                    FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))  -- Use result of last query
                    LIMIT 1
                    """
                    
                    session.sql(metadata_sql).collect()
                    
                    # Insert metrics for upload
                    metrics_sql = f"""
                    INSERT INTO ANALYTICS_METRICS (
                        METRIC_ID,
                        TIMESTAMP,
                        DOCUMENT_NAME,
                        ACTION_TYPE,
                        STATUS,
                        MEMORY_USAGE_MB,
                        TOKEN_COUNT
                    ) VALUES (
                        '{str(uuid.uuid4())}',
                        CURRENT_TIMESTAMP(),
                        '{filename.replace("'", "''")}',
                        'FILE_UPLOAD',
                        'success',
                        {len(file_content) / (1024 * 1024)},  # Convert bytes to MB
                        0
                    )
                    """
                    try:
                        session.sql(metrics_sql).collect()
                        st.write("Debug: Upload metrics recorded")
                    except Exception as e:
                        st.write(f"Debug: Error recording metrics: {str(e)}")
                    
                    
                    from thumbnail_generator import ThumbnailGenerator

                    # After processing the uploaded file
                    thumbnail = ThumbnailGenerator.generate_thumbnail(
                        file_content=uploaded_file.read(),
                        file_type=uploaded_file.type,
                        filename=uploaded_file.name
                    )

                    if thumbnail:
                        file_details["thumbnail"] = thumbnail
                    
                    return True
                else:
                    st.write(f"Debug: File not found in stage after upload")
                    return False
                             

            except Exception as e:
                st.error(f"Error during staging operation: {str(e)}")
                return False
            finally:
                # Clean up temporary file
                try:
                    st.write("Debug: Cleaning up temporary file...")
                    os.unlink(temp_file_path)
                    st.write("Debug: Temporary file cleaned up successfully")
                except Exception as e:
                    st.write(f"Debug: Error cleaning up temporary file: {str(e)}")

        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
            st.write(f"Error details: {str(e)}")
            return False
    




    @staticmethod
    def upload_documents(
        session: Session,
        documents: List[Dict],
        filename: str,
        file_type: str,
        api_key: str,
        file_content: bytes = None
    ) -> bool:
        """Upload processed documents with embeddings and PDF binary content if applicable"""
        try:
            start_time = time.time()
            file_details = next((f for f in st.session_state.files if f['name'] == filename), None)
            thumbnail = None
            
            if file_details:
                print("🔍 File details found")
                filename_escaped = filename.replace("'", "''")
                
                # Delete existing entries from RAG table
                delete_rag_sql = f"DELETE FROM {SnowparkManager.RAG_TABLE} WHERE FILENAME = '{filename_escaped}'"
                session.sql(delete_rag_sql).collect()
                
                # Only handle RAG_METADATA for PDFs
                if file_type == "application/pdf" and file_content:
                    # Delete existing PDF metadata
                    delete_metadata_sql = f"DELETE FROM RAG_METADATA WHERE FILENAME = '{filename_escaped}'"
                    session.sql(delete_metadata_sql).collect()
                    
                    # Store binary content for PDFs
                    metadata_doc_id = str(uuid.uuid4())
                    metadata = {
                        'upload_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'file_size': len(file_content)
                    }
                    
                    metadata_insert_sql = f"""
                    INSERT INTO RAG_METADATA (
                        DOC_ID, 
                        FILENAME, 
                        FILE_TYPE, 
                        BINARY_CONTENT, 
                        METADATA
                    ) 
                    SELECT
                        '{metadata_doc_id}',
                        '{filename_escaped}',
                        '{file_type}',
                        TO_BINARY(HEX_ENCODE(?)),
                        PARSE_JSON('{json.dumps(metadata)}')
                    """
                    session.sql(metadata_insert_sql, params=[file_content]).collect()
                    print(f"Inserted binary content into RAG_METADATA for PDF, doc_id: {metadata_doc_id}")
                
                # Update BOOK_METADATA
                delete_book_sql = f"""
                DELETE FROM TESTDB.MYSCHEMA.BOOK_METADATA 
                WHERE FILENAME = '{filename_escaped}'
                """
                session.sql(delete_book_sql).collect()
                
                # Insert into BOOK_METADATA
                book_id = str(uuid.uuid4())
                file_size = f"{len(file_content) if file_content else 0 / 1024:.1f} KB"

                # Thumbnail generation

                if file_content:
                    
                    try:
                        # Create a copy of file_content for thumbnail generation
                        file_content_copy = file_content[:]
                 
                        # Generate thumbnail using the copy
                        from thumbnail_generator import ThumbnailGenerator
                        thumbnail = ThumbnailGenerator.generate_thumbnail(
                            file_content=file_content_copy,
                            file_type=file_type,
                            filename=filename
                        )
                       
                        # Store thumbnail status in session state
                        if 'thumbnails_status' not in st.session_state:
                            st.session_state.thumbnails_status = {}
                            
                        st.session_state.thumbnails_status[filename] = {
                            'generated': thumbnail is not None,
                            'timestamp': datetime.now().isoformat(),
                            'file_type': file_type
                        }
                        
                        print(f"Thumbnail generated for {filename}: {'Success' if thumbnail else 'Failed'}")

                    except Exception as e:
                        print(f"Error generating thumbnail: {str(e)}")
                        if 'thumbnails_status' not in st.session_state:
                            st.session_state.thumbnails_status = {}
                        st.session_state.thumbnails_status[filename] = {
                            'generated': False,
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        }
                       

                # Construct SQL based on whether we have a thumbnail
                print("🔍 Before calling book_metadata_sql")
                if thumbnail:
                    book_metadata_sql = f"""
                    INSERT INTO TESTDB.MYSCHEMA.BOOK_METADATA (
                        BOOK_ID,
                        FILENAME,
                        CATEGORY,
                        DATE_ADDED,
                        SIZE,
                        USAGE_STATS,
                        THUMBNAIL
                    )
                    SELECT
                        '{book_id}',
                        '{filename_escaped}',
                        '{file_details['category'].replace("'", "''")}',
                        CURRENT_TIMESTAMP(),
                        '{file_size}',
                        TO_VARIANT(PARSE_JSON('{{ "queries": 0, "summaries": 0 }}')),
                        {f", '{thumbnail}'" if thumbnail else ''} 
                    """
                else:
                    book_metadata_sql = f"""
                    INSERT INTO TESTDB.MYSCHEMA.BOOK_METADATA (
                        BOOK_ID,
                        FILENAME,
                        CATEGORY,
                        DATE_ADDED,
                        SIZE,
                        USAGE_STATS
                    )
                    SELECT
                        '{book_id}',
                        '{filename_escaped}',
                        '{file_details['category'].replace("'", "''")}',
                        CURRENT_TIMESTAMP(),
                        '{file_size}',
                        TO_VARIANT(PARSE_JSON('{{ "queries": 0, "summaries": 0 }}'))
                    """
                print("🔍 After calling book_metadata_sql")
                session.sql(book_metadata_sql).collect()
                print("🔍 After calling book_metadata_sql collect")
                # Process documents for RAG table
                temp_table = f"TEMP_{uuid.uuid4().hex[:8]}"
                create_temp_table_sql = f"""
                CREATE TEMPORARY TABLE {temp_table} (
                    DOC_ID VARCHAR,
                    FILENAME VARCHAR,
                    FILE_TYPE VARCHAR,
                    CONTENT TEXT,
                    METADATA VARIANT
                )
                """
                session.sql(create_temp_table_sql).collect()

                # Prepare document data
                rows = []
                for idx, doc in enumerate(documents, 1):
                    chunk_metadata = {
                        'page_number': doc.get('page_num', idx),
                        'total_pages': len(documents),
                        'chunk_number': idx,
                        'file_type': file_type  # Store file type in metadata
                    }
                    
                    rows.append([
                        str(uuid.uuid4()),                  # DOC_ID
                        filename,                           # FILENAME
                        file_type,                         # FILE_TYPE
                        doc['text'],                       # CONTENT
                        json.dumps(chunk_metadata)         # METADATA
                    ])

                if not rows:
                    st.error("No valid documents to upload")
                    return False

                # Create dataframe and save to temporary table
                df = session.create_dataframe(
                    rows,
                    schema=["DOC_ID", "FILENAME", "FILE_TYPE", "CONTENT", "METADATA"]
                )
                df.write.save_as_table(temp_table, mode="overwrite", table_type="temporary")

                # Insert into final table with embeddings
                insert_sql = f"""
                INSERT INTO {SnowparkManager.RAG_TABLE} (
                    DOC_ID, FILENAME, FILE_TYPE, CONTENT, EMBEDDING, METADATA, CREATED_AT
                )
                SELECT 
                    t.DOC_ID,
                    t.FILENAME,
                    t.FILE_TYPE,
                    t.CONTENT,
                    CAST(SNOWFLAKE.CORTEX.EMBED_TEXT_768(
                        'snowflake-arctic-embed-m-v1.5',
                        t.CONTENT
                    ) AS VECTOR(FLOAT, 768)),
                    PARSE_JSON(t.METADATA),
                    CURRENT_TIMESTAMP()
                FROM {temp_table} t
                """
                
                session.sql(insert_sql).collect()
                session.sql(f"DROP TABLE IF EXISTS {temp_table}").collect()
                
                return True
            else:
                st.error(f"File details not found for {filename}")
                return False

        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
            print(f"Error details: {str(e)}")
            return False
    
    # @staticmethod
    # def upload_documents(
    #     session: Session,
    #     documents: List[Dict],
    #     filename: str,
    #     file_type: str,
    #     api_key: str
    # ) -> bool:
    #     """Upload processed documents with embeddings to Snowflake"""
    #     try:
    #         start_time = time.time()
    #         file_details = next((f for f in st.session_state.files if f['name'] == filename), None)
            
    #         if file_details:
    #             st.write("🔍 File details found")
                
    #             # Delete existing entries
    #             delete_sql = f"""
    #             DELETE FROM TESTDB.MYSCHEMA.BOOK_METADATA 
    #             WHERE FILENAME = '{filename.replace("'", "''")}'
    #             """
    #             session.sql(delete_sql).collect()
                
    #             # Single metadata insertion
    #             book_id = str(uuid.uuid4())
    #             file_size = f"{len(json.dumps(documents)) / 1024:.1f} KB"
                
    #             metadata_sql = f"""
    #             INSERT INTO TESTDB.MYSCHEMA.BOOK_METADATA 
    #                 (BOOK_ID, FILENAME, CATEGORY, DATE_ADDED, SIZE, USAGE_STATS)
    #             SELECT
    #                 '{book_id}',
    #                 '{filename.replace("'", "''")}',
    #                 '{file_details['category'].replace("'", "''")}',
    #                 CURRENT_TIMESTAMP(),
    #                 '{file_size}',
    #                 TO_VARIANT(PARSE_JSON('{{ "queries": 0, "summaries": 0 }}'))
    #             """
    #             session.sql(metadata_sql).collect()
                
    #             # Process documents for RAG table
    #             temp_table = f"TEMP_{uuid.uuid4().hex[:8]}"
    #             create_temp_table_sql = f"""
    #             CREATE TEMPORARY TABLE {temp_table} (
    #                 DOC_ID VARCHAR,
    #                 FILENAME VARCHAR,
    #                 FILE_TYPE VARCHAR,
    #                 CONTENT TEXT,
    #                 METADATA VARIANT
    #             )
    #             """
    #             session.sql(create_temp_table_sql).collect()

    #             # Prepare document data
    #             rows = []
    #             metadata_rows = []
    #             for idx, doc in enumerate(documents, 1):
    #                 doc_id = str(uuid.uuid4())
    #                 metadata = {
    #                     'source_type': 'pdf' if file_type == 'application/pdf' else 'doc',
    #                     'page_number': doc.get('page_num', idx),
    #                     'total_pages': len(documents),
    #                     'upload_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #                 }
                    
    #                 rows.append([
    #                     doc_id,                             # DOC_ID
    #                     filename,                           # FILENAME
    #                     file_type,                          # FILE_TYPE
    #                     doc['text'],                        # CONTENT
    #                     json.dumps(metadata)                # METADATA
    #                 ])

    #                 if idx == 1:
    #                     metadata_rows.append([
    #                         doc_id,                        # DOC_ID
    #                         filename,                      # FILENAME
    #                         file_type,                     # FILE_TYPE
    #                         st.session_state.uploaded_file.getvalue(),  # BINARY_CONTENT
    #                         json.dumps(metadata)           # METADATA
    #                     ])

    #             if not rows:
    #                 st.error("No valid documents to upload")
    #                 return False

    #             # Create dataframe with schema
    #             df = session.create_dataframe(
    #                 rows,
    #                 schema=["DOC_ID", "FILENAME", "FILE_TYPE", "CONTENT", "METADATA"]
    #             )
    #             df.write.save_as_table(temp_table, mode="overwrite", table_type="temporary")

    #             # Insert into RAG_METADATA table
    #             metadata_df = session.create_dataframe(
    #                 metadata_rows,
    #                 schema=["DOC_ID", "FILENAME", "FILE_TYPE", "BINARY_CONTENT", "METADATA"]
    #             )
    #             metadata_df.write.save_as_table("RAG_METADATA", mode="append")

    #             # Insert RAG documents
    #             insert_sql = f"""
    #             INSERT INTO {SnowparkManager.RAG_TABLE} (
    #                 DOC_ID, FILENAME, FILE_TYPE, CONTENT, EMBEDDING, METADATA, CREATED_AT
    #             )
    #             SELECT 
    #                 t.DOC_ID,
    #                 t.FILENAME,
    #                 t.FILE_TYPE,
    #                 t.CONTENT,
    #                 CAST(SNOWFLAKE.CORTEX.EMBED_TEXT_768(
    #                     'snowflake-arctic-embed-m-v1.5',
    #                     t.CONTENT
    #                 ) AS VECTOR(FLOAT, 768)),
    #                 PARSE_JSON(t.METADATA),
    #                 CURRENT_TIMESTAMP()
    #             FROM {temp_table} t
    #             """
                
    #             session.sql(insert_sql).collect()
    #             session.sql(f"DROP TABLE IF EXISTS {temp_table}").collect()
                
    #             end_time = time.time()
    #             processing_time = int((end_time - start_time) * 1000)  # Calculate time in milliseconds
    #             metrics_query = f"""
    #             INSERT INTO ANALYTICS_METRICS (
    #                 METRIC_ID,
    #                 TIMESTAMP,
    #                 DOCUMENT_NAME,
    #                 ACTION_TYPE,
    #                 STATUS,
    #                 MEMORY_USAGE_MB,
    #                 TOKEN_COUNT,
    #                 RESPONSE_TIME_MS
    #             ) VALUES (
    #                 '{str(uuid.uuid4())}',
    #                 CURRENT_TIMESTAMP(),
    #                 '{filename.replace("'", "''")}',
    #                 'FILE_UPLOAD',
    #                 'success',
    #                 {len(json.dumps(documents)) / (1024 * 1024)},
    #                 0,
    #                 {processing_time}
    #             )
    #             """
                
    #             try:
    #                 session.sql(metrics_query).collect()
    #                 st.write("Debug: Upload metrics recorded")
    #             except Exception as e:
    #                 st.write(f"Debug: Error recording metrics: {str(e)}")
                
    #             return True
            
    #         else:
    #             st.error(f"File details not found for {filename}")
    #             return False

    #     except Exception as e:
    #         st.error(f"Upload failed: {str(e)}")
    #         st.write(f"Error details: {str(e)}")
    #         return False

    #     finally:
    #         try:
    #             session.sql("ALTER WAREHOUSE Compute_WH SET WAREHOUSE_SIZE = 'XSMALL'").collect()
    #         except Exception as e:
    #             st.warning(f"Note: Could not scale down warehouse: {str(e)}")
        
    
    
    
    @staticmethod
    @instrument
    def process_llm_response(response):
        """Process LLM response and extract answer"""
        if not response or not response[0][0]:
            return "Failed to generate response"
            
        try:
            response_data = json.loads(response[0][0])
            if isinstance(response_data, dict) and 'choices' in response_data:
                if response_data['choices'] and isinstance(response_data['choices'][0], dict):
                    if 'messages' in response_data['choices'][0]:
                        return response_data['choices'][0]['messages'].strip()
                    elif 'message' in response_data['choices'][0]:
                        return response_data['choices'][0]['message'].get('content', '').strip()
            return str(response_data)
        except json.JSONDecodeError:
            return response[0][0].strip()
   



    @staticmethod
    def semantic_search_with_llm(
            query: str,
            filename: Optional[str] = None,
            limit: int = 4,
            similarity_threshold: float = 0.1,
            max_tokens_per_context: int = 500,
            temperature: float = 0.3,
            style: str = "Detailed",
            format_type: str = "Paragraph",
            include_quotes: bool = True,
            max_tokens: int = 500,
            model: str = 'mistral-large2',
            operation_type: str = "SEARCH"
        ) -> Optional[Dict[str, Any]]:
        """
        Semantic search using Cortex Search Service with LLM response generation.
        """
        session = SnowparkManager.get_session()
        if not session:
            return None

        try:
            start_time = time.time()
            if not query or not query.strip():
                return {'answer': 'Please provide a valid search query.', 'sources': [], 'raw_results': []}

            # Set proper context first
            session.sql("USE DATABASE TESTDB").collect()
            session.sql("USE SCHEMA MYSCHEMA").collect()
            session.sql("USE WAREHOUSE COMPUTE_WH").collect()

            # Get page mapping if filename is provided
            page_map = {}
            if filename:
                safe_filename = filename.replace("'", "''")
                content_query = """
                SELECT CONTENT, METADATA:page_number::INTEGER as PAGE_NUM
                FROM RAG_DOCUMENTS_TMP
                WHERE FILENAME = '{}'
                ORDER BY PAGE_NUM
                """.format(safe_filename)
                all_pages = session.sql(content_query).collect()
                page_map = {row['PAGE_NUM']: row['CONTENT'] for row in all_pages}

            # Initialize cortex search service
            root = Root(session)
            search_service = root.databases["TESTDB"].schemas["MYSCHEMA"].cortex_search_services["MY_RAG_SEARCH_SERVICE"]
            
            filters = None
            # Build simple search parameters focusing on basic search functionality
            search_params = {
                "query": query,
                "columns": ["CONTENT", "FILENAME", "METADATA"],
                "limit": limit,
                "similarity_threshold": 0.5  # Lower threshold for better recall
            }
            
            if filename:
                #search_params["filters"] = "FILENAME = '{}'".format(safe_filename)
                filters = "FILENAME = '{}'".format(safe_filename)
                
            print(f"Debug - Executing search with query: {query}")
            print(f"Debug - Search parameters: {search_params}")
            print(f"Debug - Filters: {filters}")
            
            # Execute search
            resp = search_service.search(**search_params, filters=filters)
            
            # Debug search results
            if resp.results:
                print(f"Debug - Found {len(resp.results)} results")
                for idx, result in enumerate(resp.results):
                    print(f"Debug - Result {idx + 1} preview: {result['CONTENT'][:100]}...")
                
            # Execute search using cortex service
            #resp = search_service.search(**search_params)

            if not resp.results:
                return {'answer': 'No relevant results found.', 'sources': [], 'raw_results': []}

            # Process results
            processed_results = []
            for idx, result in enumerate(resp.results):
                try:
                    content = result['CONTENT'].strip() if result['CONTENT'] is not None else ""
                    result_filename = result.get('FILENAME', 'Unknown')
                    
                    # Get page number from metadata
                    page_num = None
                    if result['METADATA']:
                        try:
                            metadata = result['METADATA']
                            if isinstance(metadata, str):
                                metadata = json.loads(metadata)
                            page_num = metadata.get('page_number')
                        except:
                            pass
                    
                    processed_results.append({
                        'FILENAME': result_filename,
                        'CONTENT': content,
                        'PAGE_NUMBER': page_num or 1,
                        'SIMILARITY_SCORE': float(result['_SCORE']) if '_SCORE' in result else 0.0
                    })
                    
                except Exception as e:
                    print(f"Error processing result {idx}: {str(e)}")
                    continue

            # Prepare context with length management
            context_sections = []
            total_length = 0
            max_context_length = 32000  # Conservative limit
            
            for i, r in enumerate(processed_results):
                section_header = f"Section {i+1} (Source: {r['FILENAME']}, Page {r['PAGE_NUMBER']})"
                section_content = r['CONTENT']
                
                # Truncate long sections
                if len(section_content) > 4000:
                    section_content = section_content[:4000] + "..."
                
                section_text = f"{section_header}\n{section_content}"
                
                if total_length + len(section_text) > max_context_length:
                    break
                    
                context_sections.append(section_text)
                total_length += len(section_text)
            
            context = "\n\n".join(context_sections)

            # Get style and format instructions
            style_instr = SnowparkManager.STYLE_INSTRUCTIONS.get(style, "Provide detailed answers with supporting details.")
            format_instr = SnowparkManager.FORMAT_INSTRUCTIONS.get(format_type, "Format the response as paragraphs.")

            # Prepare system prompt
            system_prompt = f"""You are an AI assistant analyzing documents. Based on the context provided, answer the user's question.
            If you cannot find the relevant information in the context, clearly state that.
            Style: {style_instr}
            Format: {format_instr}

            Context:
            {context}
            """

            # Generate LLM response
            llm_query = """
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large2',
                ARRAY_CONSTRUCT(
                    OBJECT_CONSTRUCT('role', 'system', 'content', '{system_prompt}'),
                    OBJECT_CONSTRUCT('role', 'user', 'content', '{user_query}')
                ),
                OBJECT_CONSTRUCT(
                    'temperature', {temperature},
                    'max_tokens', {max_tokens}
                )
            ) as response
            """.format(
                system_prompt=system_prompt.replace("'", "''"),
                user_query=query.replace("'", "''"),
                temperature=temperature,
                max_tokens=max_tokens
            )

            llm_response = session.sql(llm_query).collect()
            synthesized_answer = SnowparkManager.process_llm_response(llm_response)

            # Record metrics
            end_time = time.time()
            output_token_count = len(synthesized_answer.split()) if synthesized_answer else 0
            memory_mb = Process().memory_info().rss / (1024 * 1024)
            processing_time = int((end_time - start_time) * 1000)

            metrics_sql = f"""
            INSERT INTO ANALYTICS_METRICS (
                METRIC_ID,
                TIMESTAMP,
                DOCUMENT_NAME,
                ACTION_TYPE,
                USER_QUERY,
                STATUS,
                TOKEN_COUNT,
                MEMORY_USAGE_MB,
                RESPONSE_TIME_MS
            ) VALUES (
                '{str(uuid.uuid4())}',
                CURRENT_TIMESTAMP(),
                '{(filename or "multiple_docs").replace("'", "''")}',
                'SEARCH',
                '{query.replace("'", "''")}',
                'success',
                {output_token_count},
                {memory_mb},
                {processing_time}
            )
            """
            session.sql(metrics_sql).collect()

            return {
                'answer': synthesized_answer,
                'sources': [{
                    'filename': r['FILENAME'],
                    'page': r['PAGE_NUMBER'],
                    'score': r['SIMILARITY_SCORE'],
                    'content': r['CONTENT'][:200] + '...' if len(r['CONTENT']) > 200 else r['CONTENT']
                } for r in processed_results],
                'raw_results': processed_results
            }

        except Exception as e:
            st.error(f"❌ Search failed: {str(e)}")
            return None
        finally:
            if session:
                session.close()
            
    @staticmethod
    def get_book_recommendations(current_book: str, recommendation_type: str = "content", limit: int = 3) -> List[Dict]:
        """
        Get book recommendations based on the current book using content similarity.
        """
        try:
            print(f"Starting recommendation generation for book: {current_book}")
            session = SnowparkManager.get_session()
            if not session:
                print("Failed to establish database session")
                return []

            # Get current book's metadata and find similar books
            safe_book_name = current_book.replace("'", "''")
            similar_books_query = f"""
            WITH current_book AS (
                SELECT 
                    m.FILENAME,
                    m.CATEGORY,
                    r.EMBEDDING
                FROM TESTDB.MYSCHEMA.BOOK_METADATA m
                JOIN TESTDB.MYSCHEMA.RAG_DOCUMENTS_TMP r ON m.FILENAME = r.FILENAME
                WHERE m.FILENAME = '{safe_book_name}'
                LIMIT 1
            ),
            similarity_scores AS (
                SELECT DISTINCT  -- Add DISTINCT to remove duplicates
                    FIRST_VALUE(m.FILENAME) OVER (PARTITION BY m.FILENAME ORDER BY r.CREATED_AT DESC) as FILENAME,
                    FIRST_VALUE(m.CATEGORY) OVER (PARTITION BY m.FILENAME ORDER BY r.CREATED_AT DESC) as CATEGORY,
                    FIRST_VALUE(m.DATE_ADDED) OVER (PARTITION BY m.FILENAME ORDER BY r.CREATED_AT DESC) as DATE_ADDED,
                    FIRST_VALUE(m.SIZE) OVER (PARTITION BY m.FILENAME ORDER BY r.CREATED_AT DESC) as SIZE,
                    CASE 
                        WHEN m.CATEGORY = (SELECT CATEGORY FROM current_book) THEN 0.2
                        ELSE 0
                    END as category_boost,
                    VECTOR_COSINE_SIMILARITY(
                        r.EMBEDDING,
                        (SELECT EMBEDDING FROM current_book)
                    ) as content_similarity
                FROM TESTDB.MYSCHEMA.BOOK_METADATA m
                JOIN TESTDB.MYSCHEMA.RAG_DOCUMENTS_TMP r ON m.FILENAME = r.FILENAME
                WHERE m.FILENAME != '{safe_book_name}'
            )
            SELECT DISTINCT  -- Additional DISTINCT for safety
                FILENAME,
                CATEGORY,
                DATE_ADDED,
                SIZE,
                MAX(content_similarity + category_boost) as total_score
            FROM similarity_scores
            GROUP BY FILENAME, CATEGORY, DATE_ADDED, SIZE
            ORDER BY total_score DESC
            LIMIT {limit}
            """
            
            print("Executing similar books query...")
            similar_books = session.sql(similar_books_query).collect()

            if not similar_books:
                print("No similar books found")
                return []

            # Generate recommendations list with deduplication
            seen_books = set()
            recommendations = []
            for book in similar_books:
                if book['FILENAME'] not in seen_books:
                    seen_books.add(book['FILENAME'])
                    recommendations.append({
                        'name': book['FILENAME'],
                        'category': book['CATEGORY'],
                        'similarity_score': min(1.0, float(book['TOTAL_SCORE'])),
                        'date_added': book['DATE_ADDED'].strftime('%Y-%m-%d') if book['DATE_ADDED'] else 'Unknown',
                        'size': book['SIZE']
                    })
                
            print(f"Generated {len(recommendations)} unique recommendations")
            return recommendations

        except Exception as e:
            print(f"Error in get_book_recommendations: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if session:
                session.close()
         
         
                
    @instrument 
    def get_document_summary(
        filename: str,
        style: str = "Concise",
        format_type: str = "Structured",
        max_tokens: int = 1000,
        include_key_points: bool = True,
        operation_type: str = "SUMMARY"  # Add operation type parameter
    ) -> Optional[Dict[str, Any]]:
        """Generate a comprehensive summary of a specific document with customizable options"""
        print("\n=== Debug: Starting Document Summary Generation ===")
        print(f"Filename: {filename}")
        print(f"Style: {style}")
        print(f"Format: {format_type}")
        session = SnowparkManager.get_session()
        if not session:
            return None

        try:
            start_time = time.time()
            escaped_filename = filename.replace("'", "''")
            count_query = f"""
            SELECT COUNT(*) as total_pages
            FROM {SnowparkManager.RAG_TABLE}
            WHERE FILENAME = '{escaped_filename}'  
            """
            page_count = session.sql(count_query).collect()[0]['TOTAL_PAGES']

            if page_count == 0:
                return {
                    'summary': 'Document not found.',
                    'filename': filename,
                    'page_count': 0,
                    'status': 'error'
                }

            # Style instructions for different summary types
            style_instructions = {
                "Concise": "Create a brief, focused summary highlighting only the most important points.",
                "Detailed": "Provide a comprehensive summary covering all major aspects of the document.",
                "Academic": "Generate a scholarly summary with formal language and structured analysis."
            }

            # Format instructions for different presentation styles
            format_instructions = {
                "Structured": """
                Organize the summary in clear sections:
                1. Overview
                2. Main Findings
                3. Conclusions
                """,
                "Bullet Points": "Present the summary as concise bullet points for each major topic.",
                "Narrative": "Present the summary as a flowing narrative with clear paragraph transitions."
            }

            batch_size = 5
            num_batches = (page_count + batch_size - 1) // batch_size
            all_summaries = []

            for batch in range(num_batches):
                start_page = batch * batch_size
                
                batch_query = f"""
                SELECT 
                    CONTENT,
                    METADATA:page_number::INTEGER as PAGE_NUMBER
                FROM {SnowparkManager.RAG_TABLE}
                WHERE FILENAME = '{escaped_filename}'  
                ORDER BY PAGE_NUMBER
                LIMIT {batch_size} OFFSET {start_page}
                """

                batch_results = session.sql(batch_query).collect()
                if not batch_results:
                    continue

                batch_content = ""
                for row in batch_results:
                    page_num = row['PAGE_NUMBER'] or 'N/A'
                    batch_content += f"[Page {page_num}]\n{row['CONTENT']}\n\n"

                system_prompt = f"""
                You are an expert document analyzer creating summaries.
                {style_instructions[style]}
                {format_instructions[format_type]}
                {"Extract and highlight key points in a separate section." if include_key_points else ""}
                Focus on maintaining accuracy and coherence.
                """

                llm_query = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'mistral-large',
                    ARRAY_CONSTRUCT(
                        OBJECT_CONSTRUCT(
                            'role', 'system',
                            'content', '{system_prompt}'
                        ),
                        OBJECT_CONSTRUCT(
                            'role', 'user',
                            'content', 'Summarize this section:\n{batch_content.replace("'", "''")}'
                        )
                    ),
                    OBJECT_CONSTRUCT(
                        'temperature', 0.3,
                        'max_tokens', {max_tokens // num_batches}
                    )
                )::string as RESPONSE;
                """

                batch_response = session.sql(llm_query).collect()
                
                if batch_response and batch_response[0]['RESPONSE']:
                    try:
                        response_data = json.loads(batch_response[0]['RESPONSE'])
                        if isinstance(response_data, dict) and 'choices' in response_data:
                            if isinstance(response_data['choices'][0], dict):
                                if 'messages' in response_data['choices'][0]:
                                    batch_summary = response_data['choices'][0]['messages']
                                elif 'message' in response_data['choices'][0]:
                                    batch_summary = response_data['choices'][0]['message'].get('content', '')
                                else:
                                    batch_summary = str(response_data['choices'][0])
                            else:
                                batch_summary = str(response_data['choices'][0])
                        else:
                            batch_summary = str(response_data)
                    except json.JSONDecodeError:
                        batch_summary = batch_response[0]['RESPONSE'].strip()
                    
                    if batch_summary:
                        all_summaries.append(batch_summary)
                        
            print("before if all_summaries")
            if all_summaries:
                combined_summaries = "\n\n".join(all_summaries)
                
                final_prompt = f"""
                Create a {style.lower()} final summary of this document.
                {format_instructions[format_type]}
                {"Include a 'Key Points' section highlighting the most important findings." if include_key_points else ""}
                
                Content to summarize:
                {combined_summaries}
                """

                final_query = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'mistral-large',
                    ARRAY_CONSTRUCT(
                        OBJECT_CONSTRUCT(
                            'role', 'system',
                            'content', '{style_instructions[style]}'
                        ),
                        OBJECT_CONSTRUCT(
                            'role', 'user',
                            'content', '{final_prompt.replace("'", "''")}'
                        )
                    ),
                    OBJECT_CONSTRUCT(
                        'temperature', 0.3,
                        'max_tokens', {max_tokens}
                    )
                )::string as RESPONSE;
                """
                print("before final_response")
                final_response = session.sql(final_query).collect()

                if final_response and final_response[0]['RESPONSE']:
                    try:
                        response_data = json.loads(final_response[0]['RESPONSE'])
                        if isinstance(response_data, dict) and 'choices' in response_data:
                            if isinstance(response_data['choices'][0], dict):
                                if 'messages' in response_data['choices'][0]:
                                    generated_summary = response_data['choices'][0]['messages']
                                elif 'message' in response_data['choices'][0]:
                                    generated_summary = response_data['choices'][0]['message'].get('content', '')
                                else:
                                    generated_summary = str(response_data['choices'][0])
                            else:
                                generated_summary = str(response_data['choices'][0])
                        else:
                            generated_summary = str(response_data)
                    except json.JSONDecodeError:
                        generated_summary = final_response[0]['RESPONSE'].strip()
                    
                    # Initialize the summary dictionary
                    summary = {
                        'summary': generated_summary,
                        'filename': filename,
                        'page_count': page_count,
                        'status': 'success'
                    }
                    
                    # After getting the query results
                    query = f"""
                    SELECT CONTENT, METADATA:page_number::INTEGER as PAGE_NUM
                    FROM RAG_DOCUMENTS_TMP
                    WHERE FILENAME = '{filename.replace("'", "''")}' 
                    ORDER BY PAGE_NUM
                    """
                    results = session.sql(query).collect()
                    
                     # Record metrics for summary generation
                    token_count = len(generated_summary.split())  # Estimate token count
                    print("token_count: {Token_count}")
                    
                    # Record metrics for summary generation
                    #token_count = len(generated_summary.split())  # Estimate token count
                    end_time = time.time()
                    memory_mb = psutil.Process().memory_info().rss / (1024 * 1024)  # Calculate memory in MB
                    processing_time = int((end_time - start_time) * 1000)  # Calculate time in ms
                    
                    metrics_sql = f"""
                    INSERT INTO ANALYTICS_METRICS (
                        METRIC_ID,
                        TIMESTAMP,
                        DOCUMENT_NAME,
                        ACTION_TYPE,
                        STATUS,
                        TOKEN_COUNT,
                        MEMORY_USAGE_MB,
                        RESPONSE_TIME_MS
                    ) VALUES (
                        '{str(uuid.uuid4())}',
                        CURRENT_TIMESTAMP(),
                        '{filename.replace("'", "''")}',
                        'SUMMARY',
                        'success',
                        {token_count},
                        {memory_mb},
                        {processing_time}
                    )
                    """
                    session.sql(metrics_sql).collect() 
                 
                    # Store results before processing
                    # document_results = results
                    print("Debug: Summary generated, proceeding to evaluation")
                    
                    from truelens_utils import TruLensEvaluator
                
                    st.session_state.trulens_evaluator = TruLensEvaluator()
                    print("Debug: Created new TruLens evaluator")
                    
                     # Debug TruLens evaluator status
                    print("\n=== Debug: Checking TruLens Evaluator Status ===")
                    print(f"Has trulens_evaluator attribute: {hasattr(st.session_state, 'trulens_evaluator')}")
                    print(f"Evaluator object exists: {bool(st.session_state.get('trulens_evaluator'))}")
                    if hasattr(st.session_state, 'trulens_evaluator'):
                        print(f"Evaluator initialized: {getattr(st.session_state.trulens_evaluator, 'initialized', False)}")
                    
                    # TruLens evaluation
                    # Debug TruLens evaluator status in detail
                    print("\n=== TruLens Evaluator Status Check ===")
                    
                    # Check 1: Does the attribute exist?
                    has_attr = hasattr(st.session_state, 'trulens_evaluator')
                    print(f"1. Has trulens_evaluator attribute: {has_attr}")
                    
                    # Check 2: Is the evaluator object not None?
                    evaluator_exists = bool(st.session_state.get('trulens_evaluator'))
                    print(f"2. Evaluator object exists: {evaluator_exists}")
                    
                    # Check 3: Is it initialized?
                    if evaluator_exists:
                        is_initialized = getattr(st.session_state.trulens_evaluator, 'initialized', False)
                        print(f"3. Evaluator initialized: {is_initialized}")
                        print(f"4. Evaluator type: {type(st.session_state.trulens_evaluator)}")
                        print(f"5. Evaluator attributes: {dir(st.session_state.trulens_evaluator)}")
                    else:
                        print("3. Can't check initialization - evaluator doesn't exist")
        
                    # Now do TruLens evaluation
                    if (hasattr(st.session_state, 'trulens_evaluator') and 
                        st.session_state.trulens_evaluator and 
                        st.session_state.trulens_evaluator.initialized):
                        
                        #contexts = [{"CONTENT": row['CONTENT']} for row in results] if results else []
                           
                        eval_results = st.session_state.trulens_evaluator.evaluate_rag_pipeline(
                            query="Generate a summary of this document",
                            filename = filename,
                            response=generated_summary,
                            operation_type="SUMMARY",
                            style=style,
                            format_type=format_type,
                            output_token_count=max_tokens
                        )
                        
                        # Handle the new return format
                        if eval_results and eval_results.get('status') == 'success':
                            summary['dashboard_url'] = eval_results.get('dashboard_url')
                    
                    print("Debug: Returning final summary with evaluation")
                    return summary
                    
            
        except Exception as e:
            st.error(f"❌ Summary generation failed: {str(e)}")
            return {
                'summary': str(e),
                'filename': filename,
                'page_count': 0,
                'status': 'error'
            }
        finally:
            session.close()          
        


    @staticmethod
    def delete_document(filename: str) -> bool:
        """Delete a document and its associated data"""
        session = SnowparkManager.get_session()
        if not session:
            return False

        try:
            delete_query = f"""
            DELETE FROM {SnowparkManager.RAG_TABLE}
            WHERE FILENAME = '{filename.replace("'", "''")}'
            """
            session.sql(delete_query).collect()
            return True
            
            
            delete_metadata_query = f"""
            DELETE FROM BOOK_METADATA
            WHERE FILENAME = '{filename.replace("'", "''")}'
            """
            session.sql(delete_metadata_query).collect()
            

        except Exception as e:
            st.error(f"Failed to delete document: {str(e)}")
            return False

        finally:
            session.close()
