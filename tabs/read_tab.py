# read_tab.py

import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from itertools import cycle

def read_file(file_path, id_type):
    """Read a file and return a DataFrame with appropriate columns based on id_type."""
    _, file_extension = os.path.splitext(file_path)
    
    if file_extension == ".csv":
        df = pd.read_csv(file_path, nrows=0)
    elif file_extension in [".txt", ".tsv"]:
        df = pd.read_csv(file_path, delimiter='\t', nrows=0)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")
    first_5_columns = df.columns[:5]
    last_5_columns = df.columns[-5:]
    target_columns = list(first_5_columns) + list(last_5_columns)

    valid_columns = [col for col in target_columns if "id" in col.lower() or "name" in col.lower()]
    
    return valid_columns

class ReadRow(QWidget):
    def __init__(self, feature_label, entity_type, id_type, file_path, columns=None, parent=None):
        super().__init__(parent)

        # Layout for the row
        self.layout = QVBoxLayout(self)
        
        # Display feature label, entity type, and file path
        entity_layout = QHBoxLayout()
        feature_label_display = QLabel(f"Label: {feature_label}")
        entity_label = QLabel(f"Entity Type: {entity_type}")
        self.column_select = QComboBox()
        self.column_select.setFixedWidth(300)
        
        # Add widgets to the layout
        entity_layout.addWidget(feature_label_display)
        entity_layout.addWidget(entity_label)
        entity_layout.addWidget(self.column_select)
        
        # File path display
        path_label = QLabel(file_path)
        path_label.setStyleSheet("color: gray; font-size: 12px;")
        
        self.layout.addLayout(entity_layout)
        self.layout.addWidget(path_label)

        # Populate the column dropdown if columns are provided
        if columns:
            self.update_columns(columns)

    def update_columns(self, columns):
        """Update the column dropdown with the provided columns."""
        self.column_select.clear()
        self.column_select.addItems(columns)

    def get_selected_column(self):
        """Get the selected column from the dropdown."""
        return self.column_select.currentText()

class ReadTab(QWidget):
    def __init__(self, file_info_list, parent=None):
        super().__init__(parent)

        self.file_info_list = file_info_list
        self.layout = QVBoxLayout(self)
        self.read_rows = []
        self.files_loaded = 0  # Counter for files loaded

        # Add loading label
        self.loading_label = QLabel("Loading columns...")
        self.layout.addWidget(self.loading_label)
        self.animation_chars = cycle(["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"])
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loading_animation)
        self.timer.start(100)

        # Create a ReadRow for each entry in file_info_list without columns initially
        for feature_label, entity_type, id_type, file_path in file_info_list:
            row = ReadRow(feature_label, entity_type, id_type, file_path)
            self.read_rows.append(row)
            self.layout.addWidget(row)

        # Add some spacing at the bottom
        self.layout.addStretch()

    def update_loading_animation(self):
        """Update the loading label with the next animation character."""
        char = next(self.animation_chars)
        self.loading_label.setText(f"Loading... {char}")

    def update_row_columns(self, index, columns):
        """Update the columns for a specific row."""
        if 0 <= index < len(self.read_rows):
            self.read_rows[index].update_columns(columns)
        
        # Increase the count of loaded files
        self.files_loaded += 1

        # Stop the loading animation once all rows are updated
        if self.files_loaded == len(self.read_rows):
            self.timer.stop()
            self.loading_label.setText("Columns loaded.")

    def get_read_info(self):
        """Get selected columns from all rows, including file_info_list content."""
        read_info_list = []
        for (feature_label, entity_type, id_type, file_path), row in zip(self.file_info_list, self.read_rows):
            selected_column = row.get_selected_column()
            read_info_list.append((feature_label, entity_type, id_type, file_path, selected_column))
        return read_info_list
