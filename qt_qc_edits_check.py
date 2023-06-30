
#standard library imports
import os
import re 
import sys
import random 
from itertools import cycle
from time import sleep
from pathlib import Path


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from matplotlib.patheffects import withSimplePatchShadow
#from mplcursors import cursor
import mplcursors                                          #<== Uncomment for the cursor function!!!!

#Qt imports
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QLabel, QDialog,\
                            QLineEdit, QGridLayout,QPushButton, QComboBox, QFileDialog

#local imports
from aux_functions import source_sps_to_df, th_sps_to_df, get_flags_counts
from extra_functions import get_all_sps, get_sequence_by_nb, name_to_numbers
from qc_edits_check import read_shots_edits

__version__ = "beta 0.0.3"
 
#colors
raw_color = "#A9A9A9"
clean_color = "#00FF00"
missed_color = "#FF0000"
faulty_color = "#B22222"

#missed points comments
missed = [' Missing SP.', 'missed shot, no trigger']

class MainWindow(QDialog):
    def __init__(self,parent = None):
        super(MainWindow,self).__init__(parent, flags = Qt.WindowMinimizeButtonHint|Qt.WindowCloseButtonHint)
        #self.setGeometry(400,400,900,900)
        
        #buttons 
        self.browseLabel = QLabel("Sequence folder:")
        self.browseLine = QLineEdit()
        self.openButton = QPushButton("Browse")
        self.infoLabel = QLabel(f"<b><font color = {raw_color}>Select sequence to plot</font></b>")
        self.figure = plt.figure(figsize = (10,6))
        self.canvas = FigureCanvas(self.figure)     #!!!
        toolbar = NavigationToolbar(self.canvas, self)
        
        #b&w settings
        self.browseLine.setReadOnly(True)
        self.infoLabel.setStyleSheet("border: 1px solid black;")
        self.infoLabel.setAlignment(Qt.AlignCenter)
        
        #icon
        icon = QIcon()
        icon.addFile("Resources\wrench.png")
        
        #layout
        grid = QGridLayout()
        grid.addWidget(self.browseLabel, 0, 0)
        grid.addWidget(self.browseLine, 0, 1)
        grid.addWidget(self.openButton,0, 2)
        grid.addWidget(self.infoLabel, 1, 0, 1, 3)
        grid.addWidget(toolbar,2,0,1,3)
        grid.addWidget(self.canvas, 3, 0,1,3)

        self.setLayout(grid)
        self.setMinimumSize(1200,800)
        self.setMaximumSize(1201,801)
        
        #main window
        self.setWindowIcon(icon)
        self.setWindowTitle(f"QC edit check {__version__}")
        
        #slots and signals
        self.openButton.clicked.connect(self.getSpsDir)
        
    def getSpsDir(self):
        dir_name = QFileDialog.getExistingDirectory(self,"Select sequence directory", r"X:\Projects\07_BR001522_ARAM_Petrobras\05_QC\03_GUNS\05_Sequences\01_Artemis_Odyssey", options = QFileDialog.DontUseNativeDialog)
        if dir_name:
            #clear figure if there is a plot already
            self.figure.clear()
            path = Path(dir_name)
            self.browseLine.setText(str(path))
            seq_paths = get_all_sps(path)
            seq_line = name_to_numbers(os.path.basename(seq_paths[0]))['line']
            seq_type = name_to_numbers(os.path.split(seq_paths[0])[1])['type']
            seq_index = name_to_numbers(os.path.split(seq_paths[0])[1])['index']
            seq_number = name_to_numbers(os.path.basename(seq_paths[0]))['sequence']
            #first work with NTBP sequences block
            if seq_type == "N":
                dir_opened_msg = f"<b>Line number from {os.path.basename(seq_paths[0])}: {seq_line}<br>Sequence {seq_number} is NTBP</b>"
                self.infoLabel.setText(dir_opened_msg)
                #read available SPS
                theo_sps = th_sps_to_df(path_to_theo_sps)
                raw_df = source_sps_to_df(seq_paths[0])
                
                thline_df = theo_sps.query(f"line == {seq_line}")
                theo_points = len(thline_df.point)
                
                #raw stats
                raw_sp_range = f"{raw_df.point[0]} - {raw_df.point[len(raw_df.point)-1]}"
                raw_sp_counts = len(raw_df)
                
                stats = f"<b>Theoretical SP range<b>: {thline_df.point.min()}-{thline_df.point.max()} <b>Total SP:<b> {theo_points} \
                <b>Raw sps SP range:</b> {raw_sp_range} <b>Total SP: </b>{raw_sp_counts}; \
                <b>SP difference:</b> 0"
                self.infoLabel.setText(stats)
                
                #update the raw_df
                raw_df = raw_df[['line','point','sequence','easting','northing']]
                
                #read QC edited shots file
                edits_df = read_shots_edits(path_to_qc_edit)
                seq_df = edits_df.query(f"sequence == {seq_number}")
                seq_df = seq_df.drop_duplicates(subset = ['point'])
                seq_df = seq_df[['line','point','sequence','code','comment']]
                #update the QC edited shots dataframe with coordinates
                seq_df = seq_df.merge(raw_df, how = "left", on = "point")
                seq_df = seq_df[['line_x','point','sequence_x','easting','northing','comment']]
                seq_df.rename(columns = {'line_x':'line','sequence_x':'sequence'}, inplace = True)
                
                
                faulty_df = seq_df.query("comment != @missed")
                missed_df = seq_df.query("comment == @missed")
                missed_df = missed_df.merge(thline_df, how = "left", on = "point")
                missed_df.rename(columns = {'easting_y':'easting','northing_y':'northing','line_x':'line'}, inplace = True)
                missed_df = missed_df[['line','point','sequence','easting','northing','comment']]
                
                hover_df = pd.concat([missed_df, faulty_df], axis = 0)
                hover_df.sort_values(by=['point'], inplace = True)
                hover_df.reset_index(inplace = True, drop = True)
                
                ax = self.figure.add_subplot(111)
                
                raw_df.plot(kind='scatter',x = 'easting', y = 'northing', color = raw_color, s = 5, label = f'Sps raw: {len(raw_df)}', ax = ax)
                #clean_df.plot(kind='scatter',x = 'easting', y = 'northing', color = clean_color, s = 6, label = f'Sps clean: {len(clean_df)}', alpha = 0.3, ax = ax)
                faulty_df.plot(kind='scatter',x = 'easting', y = 'northing', color = faulty_color, s = 24, marker = '.',label = f"Faulty shots: {len(faulty_df)}", ax = ax)
                missed_df.plot(kind='scatter',x = 'easting', y = 'northing', color = missed_color, s = 24, marker = 'x', label = f"Missed shots: {len(missed_df)}", ax = ax)
                
                hover_df.plot(kind='scatter',x = 'easting', y = 'northing', color = faulty_color, s = 34, alpha = 0, ax = ax)
                
            else:
                dir_opened_msg = f"Line number from {os.path.basename(seq_paths[0])}: {seq_line}"
                self.infoLabel.setText(dir_opened_msg)
                
                #read available SPS
                theo_sps = th_sps_to_df(path_to_theo_sps)
                raw_df = source_sps_to_df(seq_paths[0])
                clean_df = source_sps_to_df(seq_paths[1])
                
                #theo sps line
                thline_df = theo_sps.query(f"line == {seq_line}")
                theo_points = len(thline_df.point)
                thline_df = theo_sps.query(f"line == {seq_line}")
                theo_points = len(thline_df.point)
                
                #points statistics goes here
                raw_sp_range = f"{raw_df.point[0]} - {raw_df.point[len(raw_df.point)-1]}"
                clean_sps_range = f"{clean_df.point[0]} - {clean_df.point[len(clean_df.point)-1]}"
                
                raw_sp_counts = len(raw_df)
                clean_sp_counts = len(clean_df)
                sp_diff = raw_sp_counts - clean_sp_counts
                
                #stats = f"<b>Theoretical SP range<b>: {thline_df.point.min()}-{thline_df.point.max()} <b>Total SP:<b> {theo_points} \
                #<b>Raw sps SP range:</b> {raw_sp_range} <b>Total SP: </b>{raw_sp_counts}; \
                #<b>Clean sps SP range:</b> {clean_sps_range} <b>Total SP:</b> {clean_sp_counts}<br> \
                #<b>SP difference:</b> {sp_diff}"
                #self.infoLabel.setText(stats)
                
                #update the raw_df
                raw_df = raw_df[['line','point','sequence','easting','northing']]
                
                #update the clean df
                clean_df = clean_df[['line','point','sequence','easting','northing']]
                comment = pd.Series(['Valid point' for i in range(len(clean_df))])
                clean_df = clean_df.assign(comment = comment.values) # assign helps to avoid the SettingWithCopyWarning
                
                edits_df = read_shots_edits(path_to_qc_edit)
                seq_df = edits_df.query(f"sequence == {seq_number}")
                seq_df = seq_df.drop_duplicates(subset = ['point'])
                seq_df = seq_df[['line','point','sequence','code','comment']]
                
                #in case we have points in edit get coords for this points
                seq_df = seq_df.merge(raw_df, how = "left", on = "point")
                seq_df = seq_df[['line_x','point','sequence_x','easting','northing','comment']]
                seq_df.rename(columns = {'line_x':'line','sequence_x':'sequence'}, inplace = True)
                
                
                faulty_df = seq_df.query("comment != @missed")
                missed_df = seq_df.query("comment == @missed")
                missed_df = missed_df.merge(thline_df, how = "left", on = "point")
                missed_df.rename(columns = {'easting_y':'easting','northing_y':'northing','line_x':'line'}, inplace = True)
                missed_df = missed_df[['line','point','sequence','easting','northing','comment']]
                
                print("Missing shots df")
                print(missed_df)
                
                stats = f"<b>Theoretical SP range</b>: {int(thline_df.point.min())}-{int(thline_df.point.max())} <b>Total SP:</b> {theo_points}<br> \
                <b>Raw sps SP range:</b> {raw_sp_range} <b>Total SP: </b>{raw_sp_counts}<br><b>Clean sps SP range:</b> {clean_sps_range} <b>Total SP:</b> {clean_sp_counts}<br> \
                <b>SP difference:</b> {sp_diff} <b>Number of edited shots:</b> {len(seq_df)}"
                self.infoLabel.setText(stats)
                
                
                #the special data frame for comments
                hover_df = pd.concat([clean_df,missed_df, faulty_df], axis = 0)
                hover_df.sort_values(by=['point'], inplace = True)
                hover_df.reset_index(inplace = True, drop = True)
                
                print(hover_df.head(), '\n-----------\n', hover_df.tail())
                
                #The plotting should be done iwth the UpdateUI function
                #create the raw vs clean sps scatter
                
                ax = self.figure.add_subplot(111)    #!!!
                
                hover_df.plot(kind='scatter',x = 'easting', y = 'northing', color = faulty_color, s = 34, alpha = 0, ax = ax)
                #thline_df.plot(kind='scatter',x = 'easting', y = 'northing', color='gray', s = 1, ax = ax)
                raw_df.plot(kind='scatter',x = 'easting', y = 'northing', color = raw_color, s = 5, label = f'Sps raw: {len(raw_df)}', ax = ax)
                clean_df.plot(kind='scatter',x = 'easting', y = 'northing', color = clean_color, s = 6, label = f'Sps clean: {len(clean_df)}', alpha = 0.3, ax = ax)
                faulty_df.plot(kind='scatter',x = 'easting', y = 'northing', color = faulty_color, s = 24, marker = '.',label = f"Faulty shots: {len(faulty_df)}", ax = ax)
                missed_df.plot(kind='scatter',x = 'easting', y = 'northing', color = missed_color, s = 24, marker = 'x', label = f"Missed shots: {len(missed_df)}", ax = ax)
            
            ax.set_axisbelow(True)
            ax.grid()
            ax.legend()
            
            #below functionality is copy-pasted, so hard to tell how it actually works
            def show_hover_panel(get_text_func=None):
                cursor = mplcursors.cursor(
                    hover=2,  # Transient
                    annotation_kwargs=dict(
                        bbox=dict(
                            boxstyle="square,pad=0.5",
                            facecolor="white",
                            edgecolor="#ddd",
                            linewidth=0.5,
                            path_effects=[withSimplePatchShadow(offset=(1.5, -1.5))],
                        ),
                        linespacing=1.5,
                        arrowprops=None,
                    ),
                    highlight=True, highlight_kwargs=dict(linewidth=2),)
                if get_text_func:
                    cursor.connect(
                        event="add",
                        func = lambda sel: sel.annotation.set_text(get_text_func(sel.index)),
                    )
                return cursor
            def on_add(index):
                item = hover_df.iloc[index]
                parts = [
                    f"Line: {item.line}",
                    f"Point: {item.point}",
                    f"Comment: {item.comment}",
                ]
                return "\n".join(parts)
                
            show_hover_panel(on_add)
            self.canvas.draw()                  #plot here
            
        else:                                   #in case no directory was selected
            message = "No directory selected"
            self.infoLabel.setText(message)
        
if __name__ == "__main__":
    path_to_theo_sps = r"Q:\06-ARAM\nav\preplot.s01"
    path_to_qc_edit = r"X:\Projects\07_BR001522_ARAM_Petrobras\05_QC\03_GUNS\05_Sequences\01_Artemis_Odyssey\0256-QC_edited_shots.csv"
    app = QApplication(sys.argv)
    dialog = MainWindow()
    dialog.show()
    app.exec_()