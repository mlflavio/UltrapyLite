import sys
import time
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
import pyqtgraph as pg
from brping import Ping1D
import numpy as np
from PyQt5.QtGui import QPixmap
from liteWidget import Ui_ULTRApy_Lite
import pandas as pd

class SonarWidget(QWidget):
    def __init__(self):
        "Inicializa as variáveis"
        super().__init__()
        self.ui = Ui_ULTRApy_Lite()
        self.ui.setupUi(self)

        self.ping = None
        self.distance_data = []
        self.profile_data = []
        self.timestamps = []
        self.timestamp_str = []
        self.paused = False
        self.device = self.ui.lineEdit_5.text()
        self.baudrate = 115200

        # Define a faixa de leitura do sonar
        self.start = int(self.ui.lineEdit_3.text())
        self.end = int(self.ui.lineEdit_4.text())

        # Define parâmetros
        self.gain = self.ui.comboBox.currentIndex()
        self.velocity = int(self.ui.lineEdit_2.text())

        self.center()   # mantém janela ao centro da tela

        # conecta elementos do código aos seus respectivos módulos
        self.ui.pushButton.clicked.connect(self.start_acquisition)
        self.ui.pushButton2.clicked.connect(self.toggle_pause)

    def start_acquisition(self):
        # Inicializa sonar
        self.ping = Ping1D()
        self.ping.connect_serial(self.device, self.baudrate)
        self.ping.initialize()
        self.ping.set_ping_enable(True)

        # Configura parâmetros iniciais
        self.ping.set_range(self.start, self.end)
        self.ping.set_speed_of_sound(self.velocity)
        self.ping.set_gain_setting(self.ui.comboBox.currentIndex())
        aux = 100 # variável auxiliar para armazenamento dos dos dados a cada 100 aquisições
        while True:
            # Inicia aquisição
            if self.paused:
                time.sleep(0.1)
                break

            data = self.ping.get_profile()  # realiza um ping
            if data:
                self.distance_data.append(data["distance"])
                self.profile_data.append(list(data["profile_data"]))
                timestamp = time.time()
                self.timestamps.append(timestamp)
                self.update_graph()

                dt_object = datetime.fromtimestamp(timestamp)
                self.timestamp_str.append(dt_object.strftime("%Y-%m-%d %H:%M:%S"))
                to_save = dt_object.strftime("%d-%m-%Y")

                # Cria dicionário para salvar dados da envoltória e timestamp
                dict = {"timestamp_str": self.timestamp_str,
                        "profile_data": self.profile_data}
                if aux % 100 == 0:
                    pd.DataFrame(dict).to_csv(f"data/Profile_{to_save}_vs{aux}.csv", index=False)
                    dict = {}   # limpa o dicionário para receber novos dados

                aux +=1

            QApplication.processEvents()

    def center(self):

        # módulo para centralizar a janela
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def toggle_pause(self):
        # controla aquisição
        self.paused = not self.paused

    def update_graph(self):
        # atualiza o gráfico com novas aquisições
        max_display_points = 1000
        data_len = len(self.distance_data)
        if data_len > max_display_points:
            start = data_len - max_display_points
        else:
            start = 0
        self.ui.graph_widget.clear()
        self.ui.graph_widget.plot(self.timestamps[start:], self.distance_data[start:], pen='g')
        self.ui.graph_widget.setXRange(self.timestamps[-1] - 30, self.timestamps[-1])
        self.ui.lineEdit.setText(str(self.distance_data[-1]))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = SonarWidget()
    widget.show()
    sys.exit(app.exec_())