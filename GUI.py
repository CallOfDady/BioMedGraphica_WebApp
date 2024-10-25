# GUI.py

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from itertools import cycle
from tabs.import_tab import ImportTab
from tabs.read_tab import ReadTab, read_file
from tabs.process_tab import ProcessTab
from tabs.export_tab import ExportTab
import traceback
from data_pipeline.entity_process.soft_match.entity_match import EntityMatcher
import time
import os

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class MedGraphica(QMainWindow):
    def __init__(self, matcher, phenotype_embeddings, disease_embeddings, drug_embeddings):
        super().__init__()

        self.matcher = matcher
        self.phenotype_embeddings = phenotype_embeddings
        self.disease_embeddings = disease_embeddings
        self.drug_embeddings = drug_embeddings

        # Set main window properties
        self.setWindowTitle("MedGraphica")
        self.setWindowIcon(QIcon("assets/icons/logo.png"))
        self.resize(2000, 800)

        # Center the window on the screen
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Create the central widget and layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create the tab widget
        self.tab_widget = QTabWidget(self)
        self.main_layout.addWidget(self.tab_widget)

        # Create tabs with initial content
        self.import_tab = ImportTab()
        self.read_tab = self.create_default_read_tab()  # Start with a default ReadTab
        self.process_tab = ProcessTab([])  # Empty data initialization for ProcessTab
        self.export_tab = ExportTab()

        # Add tabs to the tab widget
        self.tab_widget.addTab(self.import_tab, "Import")
        self.tab_widget.addTab(self.read_tab, "Read")
        self.tab_widget.addTab(self.process_tab, "Process")
        self.tab_widget.addTab(self.export_tab, "Export")

        # Create the bottom button area
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)

        # Create navigation buttons
        self.previous_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.button_layout.addWidget(self.previous_button)
        self.button_layout.addWidget(self.next_button)

        # Connect button signals to slots
        self.previous_button.clicked.connect(self.go_to_previous_tab)
        self.next_button.clicked.connect(self.go_to_next_tab)

        # Initialize button states
        self.update_buttons()

        # Thread pool
        self.threadpool = QThreadPool()
        print(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

    def create_default_read_tab(self):
        """Create the ReadTab with a default message if no files are uploaded."""
        default_read_tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("No files uploaded. Please return to Import Tab and upload files to proceed."))
        default_read_tab.setLayout(layout)
        return default_read_tab

    def go_to_previous_tab(self):
        """Go to the previous tab"""
        current_index = self.tab_widget.currentIndex()
        if current_index > 0:
            self.tab_widget.setCurrentIndex(current_index - 1)
        self.update_buttons()

    def go_to_next_tab(self):
        """Go to the next tab based on the current tab"""
        current_index = self.tab_widget.currentIndex()
        print(f"Current Tab Index: {current_index}")  # Debug info

        if current_index == 0:
            # Handle Import tab logic
            worker = Worker(self.handle_import_next)
            worker.signals.result.connect(self.update_read_tab_data)
        elif current_index == 1:
            # Handle Read tab logic
            if isinstance(self.read_tab, ReadTab):  # Only proceed if ReadTab has data
                worker = Worker(self.handle_read_next)
                worker.signals.result.connect(self.update_process_tab_data)
            else:
                QMessageBox.warning(self, "No Data", "Please return to Import Tab and upload files to proceed.")
                return  # Prevent advancing if no data is loaded
        elif current_index == 2:
            # ProcessTab to ExportTab transition
            worker = Worker(self.handle_process_next)
            worker.signals.result.connect(self.update_export_tab)
        else:
            return

        worker.signals.finished.connect(self.on_thread_complete)
        worker.signals.error.connect(self.on_thread_error)

        # Execute the worker
        self.threadpool.start(worker)

    def on_thread_complete(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < self.tab_widget.count() - 1:
            self.tab_widget.setCurrentIndex(current_index + 1)
            print(f"Switched to Tab Index: {self.tab_widget.currentIndex()}")  # Debug info
        self.update_buttons()

    def on_thread_error(self, error):
        exctype, value, traceback_str = error
        QMessageBox.critical(self, "Error", f"An error occurred: {value}\n{traceback_str}")

    def handle_import_next(self):
        """Handle the Next button in the Import tab"""
        file_info_list, error_message = self.import_tab.get_all_file_info()
        if error_message:
            raise Exception(error_message)
        
        # Return file_info_list, which will be used to create the ReadTab in the main thread
        return file_info_list

    def update_read_tab_data(self, file_info_list):
        """Update the Read tab data by creating a ReadTab in the main thread when data is provided."""
        if file_info_list:
            # Replace the current ReadTab with a new instance, enabling file reading functionality
            self.read_tab = ReadTab(file_info_list)
            self.tab_widget.removeTab(1)
            self.tab_widget.insertTab(1, self.read_tab, "Read")

            # Start reading files and extracting columns in the background
            for i, (feature_label, entity_type, id_type, file_path) in enumerate(file_info_list):
                worker = Worker(self.read_file_columns, file_path, id_type)
                worker.signals.result.connect(lambda columns, index=i: self.update_read_tab_columns(index, columns))
                self.threadpool.start(worker)
        else:
            # Reset to default message if no files were uploaded
            self.read_tab = self.create_default_read_tab()
            self.tab_widget.removeTab(1)
            self.tab_widget.insertTab(1, self.read_tab, "Read")

    def read_file_columns(self, file_path, id_type, **kwargs):
        """Read the file and extract columns based on id_type"""
        return read_file(file_path, id_type)

    def update_read_tab_columns(self, index, columns):
        """Update the ReadTab with the columns extracted from the file"""
        self.read_tab.update_row_columns(index, columns)

    def handle_read_next(self):
        """Handle the Next button in the Read tab"""
        print("Reading the data...")
        read_info = self.read_tab.get_read_info()
        print(f"Selected Columns: {read_info}")
        
        # Return read_info, which will be used to create the ProcessTab in the main thread
        return read_info
    
    def update_process_tab_data(self, read_info):
        """Update the Process tab data by creating ProcessTab in the main thread"""
        # Delay the creation of ProcessTab to minimize GUI update time
        self.process_tab = ProcessTab(read_info, matcher=self.matcher,
                                    phenotype_embeddings=self.phenotype_embeddings, 
                                    disease_embeddings=self.disease_embeddings, 
                                    drug_embeddings=self.drug_embeddings)
        self.tab_widget.removeTab(2)
        self.tab_widget.insertTab(2, self.process_tab, "Process")
    
    def handle_process_next(self):
        """Handle the Next button in the Process tab"""
        print("Finished processing the data, switching to export tab...")
        # # Get the process info in the background thread
        # process_info = self.process_tab.get_read_info()
        # return process_info

    def update_export_tab(self, process_info):
        """Update the Export tab content based on the data from ProcessTab"""
        print("Preparing to export the data...")
        self.export_tab = ExportTab()
        self.tab_widget.removeTab(3)
        self.tab_widget.insertTab(3, self.export_tab, "Export")

    def exit_program(self):
        """Finish the read and close the application"""
        self.close()

    def update_buttons(self):
        """Update the states of the navigation buttons"""
        current_index = self.tab_widget.currentIndex()
        self.previous_button.setEnabled(current_index > 0)
        
        # Check if the current tab is the last tab
        if current_index == self.tab_widget.count() - 1:
            self.next_button.setText("Exit")
            self.next_button.clicked.disconnect() 
            self.next_button.clicked.connect(self.exit_program)
        else:
            self.next_button.setText("Next")
            self.next_button.clicked.disconnect()
            self.next_button.clicked.connect(self.go_to_next_tab)

class LoadingDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Initializing")
        self.setModal(True)

        layout = QVBoxLayout(self)
        label = QLabel(message)
        layout.addWidget(label)
        self.setWindowIcon(QIcon("assets/icons/logo.png"))

        self.setFixedSize(600, 300)

        self.loading_label = QLabel()
        layout.addWidget(self.loading_label)

        self.animation_chars = cycle(["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"])
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loading_animation)
        self.timer.start(100)  # Update every 100ms

    def update_loading_animation(self):
        char = next(self.animation_chars)
        self.loading_label.setText(f"Loading... {char}")

def load_models():
    """Function to load models and embeddings"""
    matcher = EntityMatcher(model_path='dmis-lab/biobert-v1.1', device='cuda')
    matcher.load_model()
    disease_embeddings = matcher.load_embeddings("./resources/embeddings/disease_embeddings.pt")
    phenotype_embeddings = matcher.load_embeddings("./resources/embeddings/phenotype_embeddings.pt")
    drug_embeddings = matcher.load_embeddings("./resources/embeddings/drug_embeddings.pt")
    return matcher, phenotype_embeddings, disease_embeddings, drug_embeddings

def ensure_directories_exist():
    # Define the paths for the directories in a list
    directories = [
        "./input_data",
        "./cache",
        "./cache/raw_id_mapping",
        "./cache/processed_data",
        "./resources",
        "./resources/database",
        "./resources/embeddings"
    ]

    # Loop through each directory, create it if it doesn't exist
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Ensure the necessary directories exist
    ensure_directories_exist()

    # Set font properties
    font = QFont()
    font.setPointSize(14)
    app.setFont(font)

    # Create loading dialog
    loading_dialog = LoadingDialog("Loading BioBERT model, please wait...")
    loading_dialog.show()

    # Define a worker to load models and embeddings
    def on_load_complete(result):
        print("Model loading complete. Preparing to show main window...")
        matcher, phenotype_embeddings, disease_embeddings, drug_embeddings = result

        global window  # Make window a global variable to prevent it from being garbage collected
        window = MedGraphica(matcher, phenotype_embeddings, disease_embeddings, drug_embeddings)
        window.show()
        loading_dialog.close()

    def start_main_window(matcher, phenotype_embeddings, disease_embeddings, drug_embeddings):
        window = MedGraphica(matcher, phenotype_embeddings, disease_embeddings, drug_embeddings)
        window.show()

    def on_load_error(error):
        exctype, value, traceback_str = error
        print(f"Error occurred during model loading: {value}\n{traceback_str}")  # Debug print
        loading_dialog.close()
        QMessageBox.critical(None, "Error", f"Failed to load model: {value}\n{traceback_str}")
        sys.exit(1)
    
    # Load models in the background
    worker = Worker(load_models)
    worker.signals.result.connect(on_load_complete)
    worker.signals.error.connect(on_load_error)

    # Start the worker
    QThreadPool.globalInstance().start(worker)
    sys.exit(app.exec_())