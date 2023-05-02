import can
import sys
import time

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QLabel, QComboBox, QSpinBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QSize, QThread
from can.interfaces.ixxat import get_ixxat_hwids

# Por defecto inicia a 150V (tensión mínima)
Consigna_mV = [0x00, 0x02, 0x49, 0xF0]
# Por defecto inicia a 0A (corriente mínima)
Consigna_mA = [0x00, 0x00, 0x00, 0x00]

bus = can.interface.Bus(bustype='ixxat', channel=0, bitrate=500000)


# IXXAT CAN
def Descubre_Dispositivo():
    for hwid in get_ixxat_hwids():
        return hwid


def Envio_CAN(id, datos):
    global bus
    msg = can.Message(arbitration_id=id, data=bytearray(datos), is_extended_id=False)
    bus.send(msg, timeout=None)
    time.sleep(0.1)


def Envio_CAN_idext(id, datos):
    global bus
    msg = can.Message(arbitration_id=id, data=bytearray(datos), is_extended_id=True)
    bus.send(msg, timeout=None)
    time.sleep(0.1)


def Recepcion_CAN(datos_CAN):

    #Obtiene ID
    ID = ((datos_CAN.arbitration_id >> 16) & 0xFFFF)

    # Obtiene información según ID
    if(ID == 0x281):
        #TENSION
        MS_Byte1 = format(datos_CAN.data[0], '08b')
        MS_Byte2 = format(datos_CAN.data[1], '08b')
        MS_Byte3 = format(datos_CAN.data[2], '08b')
        MS_Byte4 = format(datos_CAN.data[3], '08b')

        # Obtiene Signo
        if (MS_Byte1[0] == '1'):
            Signo = -1
        else:
            Signo = 1

        # Obtiene E
        bin_string = (MS_Byte1[1] + MS_Byte1[2] + MS_Byte1[3] + MS_Byte1[4] + MS_Byte1[5] + MS_Byte1[6] + MS_Byte1[7] + MS_Byte2[0])
        E = int(bin_string, 2)

        # Obtiene M
        bin_string = (MS_Byte2[1] + MS_Byte2[2] + MS_Byte2[3] + MS_Byte2[4] + MS_Byte2[5] + MS_Byte2[6] + MS_Byte2[7] + MS_Byte3 + MS_Byte4)
        M = int(bin_string, 2)

        # Obtiene Valor Tensión Salida
        Tension_Salida = (1 + M * 2 ** (-23)) * 2 ** (E - 127)
        Tension_Salida = (Signo)*(Tension_Salida)
        print((Tension_Salida))





    elif(ID == 0x282):
        print("ID 282")




# HILOS
class Hilo_TX(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.seguir_ejecutando = True

    def run(self):
        while self.seguir_ejecutando:
            Set_Tension_Corriente_Salida_Modulo_0()
            ON_Todos_Modulos_Sistema()
            Tension_Corriente_Salida_Sistema()
            Numero_Modulos_Sistema()
            Status_Modulo_0()


class Hilo_RX(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.seguir_ejecutando = True

    def run(self):
        while self.seguir_ejecutando:
            msg = bus.recv(timeout=0)
            if msg is not None:
                Recepcion_CAN(msg)


# COMANDOS COMUNICACION MODULO POTENCIA
def Tension_Corriente_Salida_Sistema():
    id = 0x02813FF0
    datos = [0, 0, 0, 0, 0, 0, 0, 0]
    Envio_CAN_idext(id, datos)


def Numero_Modulos_Sistema():
    id = 0x02823FF0
    datos = [0, 0, 0, 0, 0, 0, 0, 0]
    Envio_CAN_idext(id, datos)


def Status_Modulo_0():
    id = 0x028400F0
    datos = [0, 0, 0, 0, 0, 0, 0, 0]
    Envio_CAN_idext(id, datos)


def Tension_AC_Entrada_Modulo_0():
    id = 0x028600F0
    datos = [0, 0, 0, 0, 0, 0, 0, 0]
    Envio_CAN_idext(id, datos)


def ON_Todos_Modulos_Sistema():
    id = 0x029A3FF0
    datos = [0, 0, 0, 0, 0, 0, 0, 0]
    Envio_CAN_idext(id, datos)


def OFF_Todos_Modulos_Sistema():
    id = 0x029A3FF0
    datos = [1, 0, 0, 0, 0, 0, 0, 0]
    Envio_CAN_idext(id, datos)


def Set_Tension_Corriente_Salida_Modulo_0():
    global Consigna_mV, Consigna_mA
    id = 0x029C3FF0
    datos = [Consigna_mV[0], Consigna_mV[1], Consigna_mV[2], Consigna_mV[3], Consigna_mA[0], Consigna_mA[1],
             Consigna_mA[2], Consigna_mA[3]]
    Envio_CAN_idext(id, datos)


# INTERFAZ USUARIO
class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        self.hilo_tx = Hilo_TX()
        self.hilo_rx = Hilo_RX()

        self.setMinimumSize(QSize(600, 300))
        self.setWindowTitle("CHARX 30kW")

        # BOTON descubrir dispositivo ixxat
        self.boton_desc_disp = QPushButton('Búsqueda IXXAT', self)
        self.boton_desc_disp.clicked.connect(self.metodo_click_boton_desc_disp)
        self.boton_desc_disp.move(10, 20)

        # ETIQUETA descubrir dispositivo ixxat
        self.label_desc_disp = QLabel('', self)
        self.label_desc_disp.move(130, 20)

        # ETIQUETA velocidad bus can
        self.label_vel_can = QLabel('Velocidad CAN (kbit/s)', self)
        self.label_vel_can.move(12, 60)

        # DESPLEGABLE velocidades bus can
        self.desp_vel_can = QComboBox(self)
        self.desp_vel_can.move(130, 60)
        self.desp_vel_can.addItem("10")
        self.desp_vel_can.addItem("20")
        self.desp_vel_can.addItem("50")
        self.desp_vel_can.addItem("100")
        self.desp_vel_can.addItem("125")
        self.desp_vel_can.addItem("250")
        self.desp_vel_can.addItem("500")
        self.desp_vel_can.addItem("800")
        self.desp_vel_can.addItem("1000")
        self.desp_vel_can.setCurrentIndex(6)
        self.desp_vel_can.currentTextChanged.connect(self.metodo_cambio_desp_vel_can)
        self.desp_vel_can.setDisabled(True)

        # ETIQUETA tension salida modulo
        self.label_tension_salida = QLabel('Tensión Salida (Vo DC)', self)
        self.label_tension_salida.move(12, 120)

        # SPINBOX tension salida modulo
        self.tension_salida = QSpinBox(self)
        self.tension_salida.move(130, 120)
        self.tension_salida.setMinimum(150)
        self.tension_salida.setMaximum(1000)
        self.tension_salida.setDisabled(True)
        self.tension_salida.valueChanged.connect(self.metodo_cambio_spin_box_tension_salida)

        # ETIQUETA corriente salida modulo
        self.label_corriente_salida = QLabel('Corriente Salida (Io DC)', self)
        self.label_corriente_salida.move(12, 180)

        # SPINBOX corriente salida modulo
        self.corriente_salida = QSpinBox(self)
        self.corriente_salida.move(130, 180)
        self.corriente_salida.setMinimum(0)
        self.corriente_salida.setMaximum(100)
        self.corriente_salida.setDisabled(True)
        self.corriente_salida.valueChanged.connect(self.metodo_cambio_spin_box_corriente_salida)

        # BOTON inicio control
        self.boton_init_ctrl = QPushButton('INICIO Control', self)
        self.boton_init_ctrl.clicked.connect(self.metodo_click_boton_init_ctrl)
        self.boton_init_ctrl.move(130, 250)
        self.boton_init_ctrl.setDisabled(True)
        self.boton_init_ctrl.setStyleSheet("background-color:rgb(198,255,198)")

        # BOTON stop control
        self.boton_parada_ctrl = QPushButton('STOP Control', self)
        self.boton_parada_ctrl.clicked.connect(self.metodo_click_boton_parada_ctrl)
        self.boton_parada_ctrl.move(320, 250)
        self.boton_parada_ctrl.setDisabled(True)
        self.boton_parada_ctrl.setStyleSheet("background-color:rgb(249,172,174)")

    def metodo_click_boton_desc_disp(self):
        self.label_desc_disp.setText(Descubre_Dispositivo())
        if len(Descubre_Dispositivo()) >= 1:
            can.rc['bitrate'] = (self.desp_vel_can.currentText())
            can.rc['bitrate'] = (int(can.rc['bitrate'])) * (1000)
            can.rc['bitrate'] = str(can.rc['bitrate'])
            self.desp_vel_can.setDisabled(False)
            self.tension_salida.setDisabled(False)
            self.corriente_salida.setDisabled(False)
            self.boton_init_ctrl.setDisabled(False)
            self.boton_parada_ctrl.setDisabled(False)
        else:
            self.desp_vel_can.setDisabled(True)
            self.tension_salida.setDisabled(True)
            self.corriente_salida.setDisabled(True)
            self.boton_init_ctrl.setDisabled(True)
            self.boton_parada_ctrl.setDisabled(True)

    def metodo_cambio_desp_vel_can(self):
        can.rc['bitrate'] = (self.desp_vel_can.currentText())
        can.rc['bitrate'] = (int(can.rc['bitrate'])) * (1000)
        can.rc['bitrate'] = str(can.rc['bitrate'])

    def metodo_cambio_spin_box_tension_salida(self):
        global Consigna_mV
        aux_mV = self.tension_salida.value() * 1000
        Consigna_mV = [((aux_mV >> 24) & 0xFF), ((aux_mV >> 16) & 0xFF), ((aux_mV >> 8) & 0xFF), (aux_mV & 0xFF)]

    def metodo_cambio_spin_box_corriente_salida(self):
        global Consigna_mA
        aux_mA = self.corriente_salida.value() * 1000
        Consigna_mA = [((aux_mA >> 24) & 0xFF), ((aux_mA >> 16) & 0xFF), ((aux_mA >> 8) & 0xFF), (aux_mA & 0xFF)]

    def metodo_click_boton_init_ctrl(self):
        ON_Todos_Modulos_Sistema()

        self.hilo_tx.seguir_ejecutando = True
        self.hilo_tx.start()
        self.hilo_rx.seguir_ejecutando = True
        self.hilo_rx.start()

    def metodo_click_boton_parada_ctrl(self):
        OFF_Todos_Modulos_Sistema()

        self.hilo_tx.seguir_ejecutando = False
        self.hilo_tx.wait()
        self.hilo_rx.seguir_ejecutando = False
        self.hilo_rx.wait()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())