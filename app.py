#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py
------
Main entry point for BiomedGraphica Streamlit application.

To run the app, use the command:
    streamlit run app.py
"""

import streamlit as st
from frontend.core import build_app

if __name__ == "__main__":
    # Build and run the Streamlit app
    build_app()
