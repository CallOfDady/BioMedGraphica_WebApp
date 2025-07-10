# BiomedGraphica Server Setup and Run Instructions

## Prerequisites
Make sure you have the following installed:
- Python 3.8 or higher
- Streamlit
- Required dependencies (see requirements.txt)

## Installation

1. Install required packages:
```bash
pip install streamlit pandas numpy
```

## Running the Application

### Method 1: Using the main app file
```bash
streamlit run app.py
```

### Method 2: Direct command
```bash
python -m streamlit run app.py
```

### Method 3: Custom port
```bash
streamlit run app.py --server.port 8501
```

### Method 4: Open in browser automatically
```bash
streamlit run app.py --server.headless false
```

## Accessing the Application
- Local URL: http://localhost:8501
- Network URL: http://your-ip:8501

## Features
- 🧬 BiomedGraphica Data Integration
- Upload and configure biomedical entity files
- Process graph data with custom parameters
- Export/Import configuration files
- Real-time status tracking

## Troubleshooting
- Make sure all required Python packages are installed
- Check that the backend processors module is available
- Verify file paths are correct for your system
- Ensure ports are not blocked by firewall

## Project Structure
- `app.py` - Main entry point
- `biomedgraphica_core.py` - Core UI components
- `biomedgraphica_app_constants.py` - Application constants
- `backend/` - Processing modules
- `cache/` - Data cache directory
