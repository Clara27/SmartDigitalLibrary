# SmartDigitalLibrary
Uncover AI Insights
PAL (Personal AI Librarian)
Project Overview
PAL is a modern, AI-powered library management system that combines document library management, interactive chat, analytics, and evaluation capabilities. The system is built using Streamlit for the frontend and integrates with Snowflake for backend operations and data storage and Mistral AI for Insights. 

Features
Interactive Library Views
 •	Traditional View: Classic bookshelf layout with book spines
 •	Column View: Organized columnar display of documents by category
 •	Hybrid View: Combined view with enhanced sorting and filtering options

AI-Powered Reading Experience
 •	Read: Access and read documents directly in the interface
 •	Listen: Text-to-speech functionality for audio playback
 •	Ask Questions: Interactive chat with your documents using natural language
 •	Get Summaries: Generate comprehensive document summaries
 •	Smart Recommendations: Receive personalized book recommendations based on your reading history

 Book Management
 •	Easy Upload: Add books in multiple formats (PDF, DOCX, TXT)
 •	Category Organization: Assign and manage book categories
 •	Quick Delete: Remove books from your library when needed
 •	Usage Tracking: Monitor reading history and interactions
 •	Metadata Management: Track and update book information

Interactive Chat
•	 Intelligent Analysis: Get insights about book themes and content
•	 Contextual Memory: AI remembers your previous conversations about each book
•	 Real-time Answers: Get immediate responses to your questions about any book
•	 Citation Support: Answers include page references and relevant quotes
•	 Customizable Interaction: Choose how you want to interact with your books

Analytics and Monitoring
  •	Real-time performance metrics
  •	Usage statistics
  •	Document analytics
  •	System health monitoring
  •	Interactive visualizations

Quality Evaluation
  •	TruLens integration
  •	Response quality metrics
  •	Performance evaluation
  •	Automated feedback

Admin Controls
  •	User management
  •	Document upload/management
  •	System configuration
  •	Performance monitoring

Core Components
1. PAL.py
The main application interface that provides:
  •	Interactive chat with PAL AI
  •	Intelligent book recommendations
  •	Real-time chat history
  •	Custom styling and user interface
  •	Integration with TruLens for evaluation
2. Admin_Panel.py
Administrative interface for:
  •	Document upload and management
  •	Category management
  •	Document metadata tracking
  •	Usage statistics
  •	Notification – Enhancement placeholder
3. Dashboard.py
Comprehensive analytics dashboard featuring:
  •	System performance metrics
  •	Document usage analytics
  •	Interactive visualizations
  •	Real-time monitoring
  •	Performance trends
  •	AI-powered presentation system
4. Trulens_Dashboard.py
Evaluation and monitoring dashboard that provides:
  •	Integration with TruLens evaluation framework
5. back.py (Backend Manager)
Core backend functionality including:
  •	Snowflake session management
  •	Document processing
  •	File handling
  •	Database operations
  •	Analytics tracking
  •	Search functionality
  •	Recommendation engine
  6. truelens_utils.py
Evaluation and metrics utility that handles:
  •	Response evaluation
  •	Quality metrics
  •	Performance tracking
  •	Integration with Snowflake
  •	Custom feedback mechanisms
7. bookshelf_views.py
View components for document display:
  •	Traditional bookshelf view
  •	Column view
  •	Hybrid view
  •	Custom styling and interactions
Technical Requirements
Please refer to requirements.txt for a complete list of dependencies. Key components include:
  •	Streamlit for web interface
  •	Snowflake for data management
  •	TruLens for evaluation
  •	Various Python packages for document processing and analysis
Setup and Installation
1.	Clone the repository
2.	Install required dependencies:
bash
Copy
pip install -r requirements3.txt
3.	Configure Snowflake credentials in your environment:
python
Copy
# Required Snowflake configurations
snowflake_account = "your_account"
snowflake_user = "your_user"
snowflake_password = "your_password"
snowflake_warehouse = "your_warehouse"
snowflake_database = "TESTDB"
snowflake_schema = "MYSCHEMA"
snowflake_role = "AccountAdmin"
4.	Run the application:
bash
Copy
streamlit run PAL.py
Usage
Document Management
1.	Use Admin Panel to upload documents
2.	Assign categories and metadata
3.	Monitor processing status
Chat Interface
1.	Select a document from the library
2.	Use natural language to ask questions
3.	View chat history and responses
Analytics
1.	Access Dashboard for system metrics
2.	Monitor performance and usage
3.	Generate AI-powered presentations
Evaluation
1.	Use TruLens Dashboard for quality metrics
2.	Monitor response quality
3.	Track system performance
Architecture
The system uses a modular architecture with:
•	Streamlit for frontend
•	Snowflake for data storage and processing
•	TruLens for evaluation
•	Custom utilities for specialized operations
Security and Performance
•	Secure Snowflake integration
•	Optimized document processing
•	Efficient memory management
•	Real-time monitoring
•	Error handling and logging

