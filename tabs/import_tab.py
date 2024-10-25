# import_tab.py

import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class UploadRow(QWidget):
    def __init__(self, parent=None, remove_callback=None, insert_callback=None):
        super().__init__(parent)

        # Layout for the row
        self.layout = QHBoxLayout(self)
        
        # Add and remove buttons
        self.add_button = QPushButton("+")
        self.remove_button = QPushButton("-")

        # Set fixed size for add and remove buttons to be square
        self.add_button.setFixedSize(30, 30)
        self.remove_button.setFixedSize(30, 30)

        # Omics Feature Label input
        self.feature_label = QLineEdit()
        self.feature_label.setFixedWidth(300)
        self.feature_label.setPlaceholderText("Omics Feature Label")

        # Entity type dropdown
        self.entity_type = QComboBox()
        self.entity_type.setFixedWidth(300)
        self.entity_type.addItems(["Gene", "Transcript", "Protein", "Promoter", "Drug", "Disease", "Phenotype", "MicroBiome"])
        self.entity_type.setEditable(True)
        self.entity_type.lineEdit().setPlaceholderText("Entity Type")
        self.entity_type.setCurrentIndex(-1)  # Ensure no item is selected by default

        # Entity id type dropdown
        self.id_types_dict = {
            "Gene": ["Ensembl_Gene_ID", "Locus-based ID", "HGNC_Symbol", "Ensembl_Gene_ID_Version", "HGNC_ID", "OMIM_ID", "NCBI_ID", "RefSeq_ID", "GO_ID"],
            "Transcript": ["Ensembl_Transcript_ID", "Ensembl_Transcript_ID_Version", "Ensembl_Gene_ID", "Reactome_ID", "RefSeq_ID", "RNACentral_ID"],
            "Protein": ["Ensembl_Protein_ID", "Ensembl_Protein_ID_Version", "RefSeq_ID", "Uniprot_ID"],
            "Promoter": ["Ensembl_Gene_ID", "HGNC_Symbol", "Ensembl_Gene_ID_Version", "HGNC_ID", "OMIM_ID", "NCBI_ID", "RefSeq_ID", "GO_ID"],
            "Drug": ["PubChem_CID_ID", "PubChem_SID_ID", "CAS_ID", "NDC_ID", "UNII_ID", "InChI_ID", "ChEBI_ID", "DrugBank_ID"],
            "Disease": ["OMIM_ID", "ICD11_ID", "ICD10_ID", "DO_ID", "SnomedCT_ID", "UMLS_ID", "MeSHID", "Mondo_ID"],
            "Phenotype": ["Phenotype_Name", "HPO_ID", "OMIM_ID", "Orpha_ID", "UMLS_ID"], 
            "MicroBiome": ["NCBI_ID", "SILVA_ID", "Greengenes_ID", "RDP_ID", "RNACentral_ID", "GTDB_ID"],
        }

        self.id_type = QComboBox()
        self.id_type.setFixedWidth(400)
        self.id_type.setEditable(True)
        self.id_type.lineEdit().setPlaceholderText("ID Type")
        self.id_type.setEnabled(False)  # Initially disabled

        # Path display
        self.path_display = QLineEdit()
        self.path_display.setReadOnly(True)
        self.path_display.setPlaceholderText("File Path")

        # Upload and clear buttons (also square)
        self.upload_button = QPushButton()
        self.upload_button.setFixedSize(30, 30)
        self.upload_button.setIcon(QIcon("assets/icons/upload.png"))

        self.clear_button = QPushButton()
        self.clear_button.setFixedSize(30, 30)
        self.clear_button.setIcon(QIcon("assets/icons/clear.png"))
    
        # Add widgets to the layout
        self.layout.addWidget(self.add_button)
        self.layout.addWidget(self.remove_button)
        self.layout.addWidget(self.feature_label)  # Add Omics Feature Label input before Entity Type
        self.layout.addWidget(self.entity_type)
        self.layout.addWidget(self.id_type)
        self.layout.addWidget(self.path_display)
        self.layout.addWidget(self.upload_button)
        self.layout.addWidget(self.clear_button)

        # Set callbacks
        self.entity_type.currentTextChanged.connect(self.update_id_type)
        self.remove_callback = remove_callback
        self.insert_callback = insert_callback
        self.remove_button.clicked.connect(self.remove_row)
        self.add_button.clicked.connect(self.insert_row)
        self.upload_button.clicked.connect(self.upload_file)
        self.clear_button.clicked.connect(self.clear_path)

    def update_id_type(self):
        """Update the id_type dropdown based on the selected entity_type"""
        entity = self.entity_type.currentText()
        self.id_type.clear()

        if entity in self.id_types_dict:
            id_types = self.id_types_dict[entity]
            if id_types:
                self.id_type.addItems(id_types)
                self.id_type.setEnabled(True)
            else:
                self.id_type.setEnabled(False)
        else:
            self.id_type.setEnabled(False)

    def upload_file(self):
        """Open a file dialog to select a file"""
        options = QFileDialog.Options()
        
        # Set a default directory path (you can change this to any directory you prefer)
        default_dir = f"./input_data"  # Default path, modify as needed
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select a text-based file", 
            default_dir,  # This sets the default directory
            "Text-based Files (*.txt *.csv *.tsv);;All Files (*)", 
            options=options
        )
        if file_path:
            self.path_display.setText(file_path)

    def clear_path(self):
        """Clear the file path"""
        self.path_display.clear()

    def remove_row(self):
        """Remove the current row"""
        if self.remove_callback:
            self.remove_callback(self)

    def insert_row(self):
        """Insert a new row below the current one"""
        if self.insert_callback:
            self.insert_callback(self)

    def get_file_info(self):
        """Get feature label, entity type, id type, file path"""
        return (self.feature_label.text(), 
                self.entity_type.currentText(), 
                self.id_type.currentText(), 
                self.path_display.text())

    def set_file_info(self, feature_label, entity_type, id_type, file_path):
        """Set feature label, entity type, id type, file path"""
        self.feature_label.setText(feature_label)
        self.entity_type.setCurrentText(entity_type)
        self.id_type.setCurrentText(id_type)
        self.path_display.setText(file_path)

class ImportTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        
        # Config file label and buttons at the top
        self.setup_config_controls()

        # Upload rows
        self.upload_rows = []
        self.upload_rows_layout = QVBoxLayout()

        # Scroll area for upload rows
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(self.upload_rows_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

        # Initial N upload rows
        for _ in range(4):
            self.add_row()

    def setup_config_controls(self):
        """Setup config file label and buttons at the top of the layout."""
        # Config file label layout
        config_label_layout = QHBoxLayout()
        config_label = QLabel("Config File:")

        # Set a smaller font for the label
        small_font = QFont()
        small_font.setPointSize(12)
        config_label.setFont(small_font)

        config_label.setFixedSize(150, 40)
        config_label_layout.addWidget(config_label)
        config_label_layout.addStretch()

        # Config buttons layout (smaller buttons)
        config_buttons_layout = QHBoxLayout()
        self.import_button = QPushButton("Import")
        self.import_button.setFixedSize(100, 40)
        self.import_button.setFont(small_font)
        self.import_button.clicked.connect(self.import_config_file)

        self.export_button = QPushButton("Export")
        self.export_button.setFixedSize(100, 40)
        self.export_button.setFont(small_font)
        self.export_button.clicked.connect(self.export_config_file)

        config_buttons_layout.addWidget(self.import_button)
        config_buttons_layout.addWidget(self.export_button)
        config_buttons_layout.addStretch()  # Ensure buttons are left-aligned

        # Add the layouts to the main layout
        self.main_layout.addLayout(config_label_layout)
        self.main_layout.addLayout(config_buttons_layout)

    def add_row(self, after_row=None):
        """Add a new row to the upload area"""
        row = UploadRow(self, remove_callback=self.remove_row, insert_callback=self.add_row)

        # Insert the row after the specified row
        if after_row:
            index = self.upload_rows.index(after_row) + 1
            self.upload_rows.insert(index, row)
            self.upload_rows_layout.insertWidget(index, row)  # Insert at the specified index
        else:
            # Append the row at the end
            self.upload_rows.append(row)
            self.upload_rows_layout.addWidget(row)

    def remove_row(self, row):
        """Remove a row from the upload area"""
        if len(self.upload_rows) > 1:
            self.upload_rows.remove(row)
            self.upload_rows_layout.removeWidget(row)
            row.deleteLater()

    def get_all_file_info(self):
        """Get file info from all rows, including feature label"""
        file_info_list = []
        for row in self.upload_rows:
            feature_label, entity_type, id_type, file_path = row.get_file_info()
            if not feature_label:
                return None, "Missing Omics Feature Label"
            if not entity_type:
                return None, "Invalid Entity Type"
            if not id_type:
                return None, "Invalid ID Type"
            if not file_path or not os.path.exists(file_path):
                return None, "Invalid File Path"
            file_info_list.append((feature_label, entity_type, id_type, file_path))
        return file_info_list, None

    def set_all_file_info(self, file_info_list):
        """Set file info into rows and adjust rows based on the list size"""
        # Clear existing rows
        for row in self.upload_rows:
            self.upload_rows_layout.removeWidget(row)
            row.deleteLater()
        self.upload_rows.clear()

        # Add new rows based on file_info_list
        for file_info in file_info_list:
            self.add_row()  # Add a new row
            self.upload_rows[-1].set_file_info(*file_info)  # Set file info for the last row

    def import_config_file(self):
        """Import a CSV config file and populate the fields"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Import Config File", 
            "", 
            "CSV Files (*.csv);;All Files (*)", 
            options=options
        )
        if file_path:
            # Read the CSV and populate the rows
            try:
                df = pd.read_csv(file_path)
                if set(['Feature Label', 'Entity Type', 'ID Type', 'File Path']).issubset(df.columns):
                    file_info_list = df[['Feature Label', 'Entity Type', 'ID Type', 'File Path']].values.tolist()
                    self.set_all_file_info(file_info_list)
                    print(f"Config file '{file_path}' imported successfully.")
                else:
                    print("CSV file does not have the required columns.")
            except Exception as e:
                print(f"Failed to import config file: {e}")

    def export_config_file(self):
        """Export the current form to a CSV config file"""
        file_info_list, error = self.get_all_file_info()
        if error:
            print(f"Error: {error}")
            return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Config File", 
            "Config.csv", 
            "CSV Files (*.csv);;All Files (*)", 
            options=options
        )
        if file_path:
            # Export the file_info_list to CSV
            try:
                df = pd.DataFrame(file_info_list, columns=['Feature Label', 'Entity Type', 'ID Type', 'File Path'])
                df.to_csv(file_path, index=False)
                print(f"Config file '{file_path}' exported successfully.")
            except Exception as e:
                print(f"Failed to export config file: {e}")
