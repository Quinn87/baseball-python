#!/bin/bash
# Helper script to run Streamlit with the correct virtual environment

# Activate venv
source .venv-baseball/bin/activate

# Run streamlit
streamlit run app.py
