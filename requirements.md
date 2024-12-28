# Core Web Framework
streamlit

# Snowflake Dependencies
snowflake-snowpark-python
snowflake-connector-python
snowflake.core==1.0.2

# Document Processing
PyPDF2
python-docx

# Data Processing and Visualization
pandas==2.2.3
plotly
numpy==1.26.4

# TruLens and Evaluation
trulens_eval
trulens-core
trulens-feedback
trulens.connectors.snowflake
trulens.providers.cortex

# API Interaction
requests>=2.31.0

# System Utilities
python-uuid>=1.30
psutil>=5.9.0
uuid>=1.30

# Audio Processing
pydub
gtts
psutil
ffmpeg-python


# Vector Operations (used by TruLens)
scikit-learn==1.5.2
scipy==1.14.1

# Note: This project requires Python 3.11

# If audio processing fails in production, run:
# sudo apt-get update && sudo apt-get install -y ffmpeg