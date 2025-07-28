import streamlit as st
from pathlib import Path


def render_job_status_panel(job_manager):

    job_info = job_manager.get_job_info()

    with st.expander("📊 Current Job Status", expanded=False):
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
