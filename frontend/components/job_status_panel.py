import streamlit as st
import time
from pathlib import Path
from frontend.api.client import check_backend_config


def check_backend_with_cache():
    """
    Smart backend status checking with caching and error recovery.
    Combines startup check, session caching, and error-time re-checking.
    """

    # 1. Startup check - ensure backend is available on first load
    if "backend_initial_check" not in st.session_state:
        with st.spinner("🔍 Checking backend status..."):
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

    # 2. Use cached results - avoid repeated requests
    status = st.session_state.get("backend_status", {})
    if status.get("status") == "ok":
        last_check = st.session_state.get("last_backend_check", 0)
        check_time = time.strftime("%H:%M:%S", time.localtime(last_check))

        # Display success status with timestamp
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(
                f"✅ Backend ready. Database: `{status.get('database_path')}` (checked at {check_time})"
            )
        with col2:
            # Optional: manual refresh button
            if st.button(
                "🔄 Recheck Backend Status",
                key="refresh_backend",
                help="Manually refresh backend status",
            ):
                del st.session_state["backend_initial_check"]
                st.rerun()
    else:
        st.error(f"❌ Backend error: {status.get('message', 'Unknown error')}")
        st.info("💡 Please check your backend configuration and restart the service.")
        st.stop()


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

    with st.expander("📊 Current Job Panel", expanded=False):
        if job_info:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Job ID", job_info["job_id"])
                st.metric("Created", job_info["created_at"])
            with col2:
                st.metric("Age (minutes)", f"{job_info['age_minutes']:.1f}")
                st.metric("Files", len(job_info["files"]))

            # File list
            if job_info["files"]:
                st.write("**Files in job directory:**")
                for file_path in job_info["files"]:
                    file_size = file_path.stat().st_size / (1024 * 1024)  # MB
                    st.write(f"  📄 {file_path.name} ({file_size:.1f} MB)")
            st.divider()
            check_backend_with_cache()
        else:
            st.write("No job information available")

        # # Control buttons
        # col1, col2 = st.columns(2)
        # with col1:
        #     if st.button("🧹 Force Clean All job Files"):
        #         job_manager.force_cleanup_all()
        #         st.rerun()
        # with col2:
        #     if st.button("🔄 Manual Cleanup Old Jobs"):
        #         job_manager.manual_cleanup_old_jobs()
        #         st.rerun()
