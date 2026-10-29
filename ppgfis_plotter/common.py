# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import re
import sys
import webbrowser
import shutil
import csv
import json
import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QLineEdit, QFileDialog, QMessageBox,
    QColorDialog, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QScrollArea,
    QSplitter, QStackedWidget, QFrame, QSizePolicy, QToolBar, QComboBox,
    QDialog, QListWidget, QDialogButtonBox, QTreeWidget, QTreeWidgetItem,
)

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.ticker import MultipleLocator, AutoMinorLocator, FuncFormatter, ScalarFormatter

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_DIR = os.path.join(APP_DIR, "logos")

URLS_INSTITUCIONAIS = {
    "UFAM": "https://ufam.edu.br/",
    "PPGFIS": "https://www.ppgfis.ufam.edu.br/",
    "DFMat": "https://dfmat.ufam.edu.br/",
    "CAPES": "https://www.gov.br/capes/pt-br",
}

LATTES_URL = "http://lattes.cnpq.br/4998528514801080"
BRILLOUIN_URL = "https://en.wikipedia.org/wiki/Brillouin_zone"

UI_FONT = "DejaVu Sans"


