import sys
from PySide2.QtWidgets import QWidget, QApplication, QLabel, QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, QFrame
from PySide2.QtGui import QIcon, QPixmap


class QPulsar(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open('Styles/QPulsar.qss') as stylefile:
            self.setStyleSheet(stylefile.read())

        self.laserstatus = QLaserStatus()
        hbox = QHBoxLayout()
        hbox.addWidget(self.laserstatus, stretch=1)
        hbox.setSpacing(0)
        hbox.setContentsMargins(0, 0, 0, 0)

        self.setLayout(hbox)
        self.show()


class QLaserStatus(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open('Styles/QPulsarPanel.qss') as stylefile:
            self.setStyleSheet(stylefile.read())

        labels = {label: QLabel(label) for label in ['Shots', 'Remaining', 'Start', 'Stop']}
        self.label_values = {key: QLabel(text=('-----/-----' if key == 'Shots' else '--:--:--')) for key in labels}
        grid = QGridLayout()
        for idx, control in enumerate(labels):
            grid.addWidget(labels[control], idx // 2, 2*(idx % 2))
            grid.addWidget(self.label_values[control], idx // 2, 1 + 2*(idx % 2))
        grid.setSpacing(15)

        self.label = QLabel()
        self.label.setPixmap(QPixmap('../Icons/Laser_Red.png'))
        box = QHBoxLayout()
        box.addItem(grid)
        box.addWidget(self.label)

        self.setLayout(box)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pulsar = QPulsar(parent=None)
    sys.exit(app.exec_())
