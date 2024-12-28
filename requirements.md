# Core Web Framework
streamlit>=1.31.0

# Snowflake Dependencies
snowflake-snowpark-python==1.26.0
snowflake-connector-python==3.12.3
snowflake.core==1.0.2

# Document Processing
PyPDF2>=3.0.0
python-docx>=0.8.10

# Data Processing and Visualization
pandas==2.2.3
plotly==5.24.1
numpy==1.26.4

# TruLens and Evaluation
trulens_eval==1.2.8
trulens-core==1.2.8
trulens-feedback==1.2.8

# API Interaction
requests>=2.31.0

# System Utilities
python-uuid>=1.30
psutil>=5.9.0
uuid>=1.30

# Audio Processing
pydub>=0.25.1
gtts>=2.3.0
psutil>=5.9.0
ffmpeg-python=0.2.0


# Vector Operations (used by TruLens)
scikit-learn==1.5.2
scipy==1.14.1

# Note: This project requires Python 3.11

# If audio processing fails in production, run:
# sudo apt-get update && sudo apt-get install -y ffmpeg