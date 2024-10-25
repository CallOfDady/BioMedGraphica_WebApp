# export_tab.py

import os
import shutil
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class ExportTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up the main layout for the tab
        self.layout = QVBoxLayout(self)

        # Create the tree widget to display the cache folder structure
        self.cache_tree = QTreeWidget()
        self.cache_tree.setHeaderLabel("Cache Folder Structure")
        self.layout.addWidget(self.cache_tree)

        # Populate the tree widget with the cache folder structure
        self.populate_cache_tree()

        # Export Path Label and Controls
        export_layout = QVBoxLayout()

        # Export Path Label
        export_path_label = QLabel("Export Path:")
        export_layout.addWidget(export_path_label)

        # Horizontal layout for the path input and browse button
        path_layout = QHBoxLayout()

        # Text field for the export path, default is "./output"
        self.export_path_input = QLineEdit("./output")
        path_layout.addWidget(self.export_path_input)

        # Browse button to select the export path
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_export_path)
        path_layout.addWidget(self.browse_button)

        # Add the path layout to the export layout
        export_layout.addLayout(path_layout)

        # Export button to trigger the export logic
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_cache_data)
        export_layout.addWidget(self.export_button)

        # Add the export layout to the main layout
        self.layout.addLayout(export_layout)

    def populate_cache_tree(self):
        """Populate the tree widget with the contents of the ./cache directory."""
        cache_dir = "./cache"
        self.cache_tree.clear()  # Clear existing items

        if not os.path.exists(cache_dir):
            QMessageBox.warning(self, "Warning", "Cache directory does not exist.")
            return

        # Add the folders and files in cache_dir to the tree widget
        for item in os.listdir(cache_dir):
            item_path = os.path.join(cache_dir, item)
            if os.path.isdir(item_path):  # Only display directories
                folder_item = QTreeWidgetItem(self.cache_tree, [item])
                self.add_files_to_tree(folder_item, item_path)

        self.cache_tree.expandAll()  # Expand all items by default

    def add_files_to_tree(self, parent_item, folder_path):
        """Recursively add files and subfolders to the tree widget."""
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                subfolder_item = QTreeWidgetItem(parent_item, [item])
                self.add_files_to_tree(subfolder_item, item_path)  # Recursive call for subfolders
            else:
                QTreeWidgetItem(parent_item, [item])  # Add files directly

    def browse_export_path(self):
        """Open a dialog to select the export directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Export Directory", "./")
        if directory:
            self.export_path_input.setText(directory)

    def export_cache_data(self):
        """Copy the contents of ./cache subfolders to the selected export path."""
        cache_dir = "./cache"
        export_dir = self.export_path_input.text()

        if not os.path.exists(cache_dir):
            QMessageBox.warning(self, "Error", "Cache directory does not exist.")
            return

        if not os.path.exists(export_dir):
            try:
                os.makedirs(export_dir)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create export directory: {e}")
                return

        # Loop through cache directory to find and copy subdirectories
        try:
            for item in os.listdir(cache_dir):
                item_path = os.path.join(cache_dir, item)
                if os.path.isdir(item_path):  # Only copy subdirectories
                    shutil.copytree(item_path, os.path.join(export_dir, item))
            
            QMessageBox.information(self, "Success", f"Export completed successfully to {export_dir}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data: {e}")



