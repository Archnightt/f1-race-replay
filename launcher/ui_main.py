import sys
import os
import subprocess
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QComboBox, QScrollArea, 
                               QGridLayout, QFrame)
from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QFont, QColor, QPalette, QFontDatabase

# Ensure we can import from the launcher module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from launcher.data_handler import SeasonSchedule

class RaceCard(QFrame):
    def __init__(self, year, round_num, country, date, location, official_name, flag, parent=None):
        super().__init__(parent)
        self.year = year
        self.round_num = round_num
        self.country = country
        self.date = date
        self.location = location
        self.official_name = official_name
        self.flag = flag
        
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(140) # Increased height to fit subtitle
        
        # Style
        self.setStyleSheet("""
            RaceCard {
                background-color: #000000;
                border-radius: 10px;
                border: 1px solid #000000;
            }
            RaceCard:hover {
                border: 1px solid #ff1801;
            }
            QLabel {
                border: none;
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(2) # Tighter spacing
        
        # Round Number
        self.lbl_round = QLabel(f"ROUND {round_num}")
        self.lbl_round.setStyleSheet("color: #aaaaaa; font-size: 12px; font-family: 'Formula1'; font-weight: bold;")
        layout.addWidget(self.lbl_round)
        
        # Header: Flag + Country
        self.lbl_header = QLabel(f"{flag}  {country}")
        self.lbl_header.setStyleSheet("color: white; font-size: 24px; font-family: 'Formula1';")
        layout.addWidget(self.lbl_header)
        
        # Subtitle: Official Name
        self.lbl_subtitle = QLabel(official_name)
        self.lbl_subtitle.setStyleSheet("color: #999; font-size: 12px;")
        self.lbl_subtitle.setWordWrap(True) # Handle long names
        layout.addWidget(self.lbl_subtitle)
        
        # Spacer
        layout.addStretch()
        
        # Date
        self.lbl_date = QLabel(date)
        self.lbl_date.setStyleSheet("color: #e0e0e0; font-size: 14px; font-family: 'Formula1';")
        layout.addWidget(self.lbl_date)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.launch_race()
            
    def launch_race(self):
        print(f"Launching race: Year {self.year}, Round {self.round_num}")
        
        # Close the launcher window
        # Find the top level window
        window = self.window()
        window.close()
        
        # Run the command
        cmd = [sys.executable, 'main.py', '--year', str(self.year), '--round', str(self.round_num)]
        subprocess.Popen(cmd)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("F1 Race Replay Launcher")
        self.resize(1000, 700) # Slightly larger default size
        
        self.schedule_loader = SeasonSchedule()
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("FIA FORMULA ONE WORLD CHAMPIONSHIP™ RACE CALENDAR")
        title_label.setStyleSheet("font-size: 24px; color: white; font-family: 'Formula1';")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.year_combo = QComboBox()
        
        # Dynamic Year List
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year + 1, 2017, -1)]
        self.year_combo.addItems(years)
        
        # Set default selection
        default_year = "2025"
        if default_year in years:
            self.year_combo.setCurrentText(default_year)
        else:
            self.year_combo.setCurrentText(str(current_year))

        self.year_combo.setStyleSheet("""
            QComboBox {
                background-color: #333;
                color: white;
                padding: 5px;
                border-radius: 5px;
                min-width: 80px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #333;
                color: white;
                selection-background-color: #555;
            }
        """)
        self.year_combo.currentTextChanged.connect(self.load_season)
        header_layout.addWidget(self.year_combo)
        
        main_layout.addLayout(header_layout)
        
        # Scroll Area for Grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #121212;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #333;
                min-height: 20px;
                border-radius: 5px;
            }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
        # Load initial data
        self.load_season(self.year_combo.currentText())
        
    def load_season(self, year):
        # Clear existing items
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        print(f"Loading schedule for {year}...")
        
        try:
            year_int = int(year)
            events = self.schedule_loader.get_schedule(year_int)
        except ValueError:
            print(f"Invalid year: {year}")
            return
            
        if not events:
            lbl = QLabel("No data found or error loading schedule.")
            lbl.setStyleSheet("color: gray; font-size: 16px;")
            self.grid_layout.addWidget(lbl, 0, 0)
            return
            
        # Populate Grid
        columns = 3
        for i, event in enumerate(events):
            card = RaceCard(
                year=year_int,
                round_num=event['RoundNumber'],
                country=event['Country'],
                date=event['EventDate'],
                location=event['Location'],
                official_name=event['OfficialName'],
                flag=event['Flag']
            )
            
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(card, row, col)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Load Fonts
    launcher_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(launcher_dir, "..", "fonts")
    
    font_files = [
        "Formula1-Regular-1.ttf",
        "Formula1-Bold_web.ttf",
        "Formula1-Wide.ttf"
    ]
    
    for font_file in font_files:
        font_path = os.path.join(font_dir, font_file)
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            print(f"Loaded font '{font_file}': {families}")
        else:
            print(f"Failed to load font: {font_path}")

    # Global stylesheet
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #15151E;
            color: white;
            font-family: 'Formula1';
        }
    """)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())