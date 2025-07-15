# BioMedGraphica Web UI - File Management System

## Overview

This application now supports a multi-user, multi-task file management system capable of safely handling concurrent users and multiple processing tasks.

## File Structure

```
project_root/
├── biomedgraphica_app_core.py
├── temp/                     ← All temporary files are stored here
│   ├── job_20250714_14h23m45s_ab12cd/
│   │   ├── promoter.csv
│   │   ├── gene.csv
│   │   ├── transcript.csv
│   │   └── t2ds.csv         ← Label file
│   ├── job_20250714_15h12m33s_xy89ef/
│   │   └── ...
│   └── ...
├── cache/                    ← Processed data
│   └── processed_data/
│       ├── xAll.npy
│       └── ...
└── utils/
    ├── temp_manager.py       ← Temporary file manager
    └── app_init.py           ← Application initialization
```

## Key Features

### 1. Isolated Task Directories
- Each user session gets a unique task directory
- Format: `job_<timestamp>_<uuid>`
- Example: `job_20250714_14h23m45s_ab12cd`

### 2. Session Management
- **Page refresh**: Considered the same job, uses the same task directory
- **New browser tab/window**: Creates a new job directory
- **Reopen browser after closing**: Creates a new job directory

### 3. Auto-Cleanup Mechanism
- **On startup**: Clears the entire temp directory when the app starts
- **Scheduled cleanup**: Background thread cleans expired job directories every 30 minutes
- **On shutdown**: Clears the temp directory when the app shuts down
- **Manual cleanup**: A "Force Cleanup" button is provided in the UI

### 4. File Management
- **Entity files**: Saved as `<entity_label>.<extension>`
- **Label files**: Original file names are preserved
- **Path storage**: Full file paths are stored in session state

## Usage

### Basic Usage
```python
from utils.temp_manager import get_temp_manager

# Get the temporary file manager
temp_manager = get_temp_manager()

# Save an uploaded file
saved_path = temp_manager.save_uploaded_file(uploaded_file, "promoter")

# Save a label file
label_path = temp_manager.save_label_file(uploaded_label_file)

# Delete an entity file
deleted = temp_manager.delete_uploaded_file("promoter")

# Delete a label file
deleted = temp_manager.delete_label_file("filename.csv")
```

### Retrieve Job Info
```python
# Get current job info
job_info = temp_manager.get_current_job_info()
print(f"Job ID: {job_info['job_id']}")
print(f"Created: {job_info['created_at']}")
print(f"Files: {len(job_info['files'])}")
```

### Cleanup Operations
```python
# Force cleanup of all temporary files
temp_manager.force_cleanup_all()

# Get temporary file statistics
stats = temp_manager.get_temp_stats()
print(f"Total jobs: {stats['total_jobs']}")
print(f"Total files: {stats['total_files']}")
```

## Configuration Options

### TempFileManager Parameters
- `project_root`: Project root directory (default: `"."`)
- `temp_dir`: Temporary file directory name (default: `"temp"`)
- `cleanup_interval_minutes`: Cleanup interval in minutes (default: `30`)

### Custom Configuration
```python
from utils.temp_manager import TempFileManager

# Create a manager with custom configuration
custom_manager = TempFileManager(
    project_root="/path/to/project",
    temp_dir="custom_temp",
    cleanup_interval_minutes=60  # Cleanup every hour
)
```

## Security Considerations

1. **File isolation**: Files from each session are completely isolated
2. **Auto cleanup**: Prevents accumulation of temporary files
3. **Path safety**: Uses secure path generation
4. **Concurrency safe**: Supports concurrent access from multiple users
5. **Resource management**: Automatically cleans up expired resources

## Monitoring and Debugging

### Log Information
- Initialization info is shown on app startup
- File save operations log detailed messages
- Cleanup operations log cleanup results

### Status Panel
- UI displays the current task status
- Includes job ID, creation time, file count, etc.
- Manual cleanup button provided

### Statistics
```python
stats = temp_manager.get_temp_stats()
# Returns: total_jobs, total_files, total_size_mb, job details
```

## Best Practices

1. **Regular monitoring**: Keep track of temp file usage
2. **Proper configuration**: Adjust cleanup intervals based on usage patterns
3. **Clean up during development**: Regularly clean temp files during debugging
4. **Path management**: Use the full path returned, do not assume file locations

## Troubleshooting

### Common Issues
1. **Permission errors**: Ensure the app has read/write access to the temp directory
2. **Disk space**: Regularly check disk usage
3. **Cleanup failures**: Manually delete the temp directory and restart the app

### Debugging Methods
```python
# Get detailed job info
job_info = temp_manager.get_current_job_info()
print(f"Job directory: {job_info['job_dir']}")
print(f"Files: {[str(f) for f in job_info['files']]}")

# Get system statistics
stats = temp_manager.get_temp_stats()
for job in stats['jobs']:
    print(f"Job: {job['name']}, Age: {job['age_minutes']:.1f}min")
```

## 新功能更新

### 文件删除功能
- **删除实体文件**：用户可以通过UI中的🗑️按钮删除已上传的实体文件
- **删除标签文件**：支持删除已上传的标签文件
- **自动清理**：删除实体时自动清理关联的文件
- **状态显示**：UI中显示已上传文件的状态

### Job Status面板改进
- **始终显示**：Job Status面板现在始终显示，即使在提前设置entity label的情况下
- **详细信息**：显示job目录中的所有文件及其大小
- **控制按钮**：提供强制清理和手动清理按钮

### 使用示例
```python
# 删除实体文件
temp_manager.delete_uploaded_file("promoter")

# 删除标签文件
temp_manager.delete_label_file("t2ds.csv")

# 获取清理线程状态
status = temp_manager.get_cleanup_thread_status()
print(f"Thread alive: {status['thread_alive']}")
```

### UI改进
- 上传文件后显示✅状态和文件名
- 每个文件旁边都有🗑️删除按钮
- 删除操作后自动刷新页面
- 控制台日志显示文件操作历史
