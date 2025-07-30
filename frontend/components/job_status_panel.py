import streamlit as st
import time
from pathlib import Path
from frontend.api.client import check_backend_config


def check_backend_with_cache():
    """
    Check backend status and return (status, message, database_path)
    """
    if "backend_initial_check" not in st.session_state:
        try:
            config_status = check_backend_config()
            st.session_state["backend_status"] = config_status
            st.session_state["backend_initial_check"] = True
            st.session_state["last_backend_check"] = time.time()
        except Exception as e:
            st.session_state["backend_status"] = {
                "status": "error",
                "message": str(e),
                "database_path": "Unknown",
            }
            st.session_state["backend_initial_check"] = True
            st.session_state["last_backend_check"] = time.time()

    status = st.session_state.get("backend_status", {})
    return status


def safe_api_call(api_func, *args, **kwargs):
    """
    Safe API call wrapper with automatic error recovery.
    Re-checks backend status when connection errors occur.
    """
    try:
        return api_func(*args, **kwargs)
    except Exception as e:
        # Check if it's a connection error
        if "connection" in str(e).lower() or "refused" in str(e).lower():
            # 3. Error-time re-check - verify backend status when errors occur
            st.warning("⚠️ Connection lost, rechecking backend status...")
            try:
                config_status = check_backend_config()
                st.session_state["backend_status"] = config_status
                st.session_state["last_backend_check"] = time.time()

                if config_status["status"] == "ok":
                    st.info("✅ Backend is available, please retry your request")
                else:
                    st.error("❌ Backend is unavailable")
                    st.stop()
            except Exception as recheck_error:
                st.error(f"❌ Cannot reach backend: {recheck_error}")
                st.stop()
        # Re-raise the original error for the caller to handle
        raise e


def render_job_status_panel(job_manager):
    job_info = job_manager.get_job_info()

    # Get backend status
    backend_status = check_backend_with_cache()
    backend_ok = backend_status.get("status") == "ok"

    # Expand based on backend error status
    with st.expander("📊 Current Job Panel", expanded=(not backend_ok)):
        # Job information
        if job_info:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Job ID", job_info["job_id"])
                st.metric("Created", job_info["created_at"])
            with col2:
                st.metric("Age (minutes)", f"{job_info['age_minutes']:.1f}")
                st.metric("Files", len(job_info["files"]))

            if job_info["files"]:
                st.write("**Files in job directory:**")
                for file_path in job_info["files"]:
                    file_size = file_path.stat().st_size / (1024 * 1024)
                    st.write(f"  📄 {file_path.name} ({file_size:.1f} MB)")
            
            st.divider()

        else:
            st.write("No job information available")

        # Backend status
        if backend_ok:
            last_check = st.session_state.get("last_backend_check", 0)
            check_time = time.strftime("%H:%M:%S", time.localtime(last_check))

            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(
                    f"✅ Backend ready. Database: `{backend_status.get('database_path')}` (checked at {check_time})"
                )
            with col2:
                if st.button("🔄 Re-Check Backend Status", key="refresh_backend"):
                    del st.session_state["backend_initial_check"]
                    st.rerun()
        else:
            st.error(f"❌ Backend error: {backend_status.get('message', 'Unknown error')}")
            st.info("💡 Please check backend configuration and restart the service")