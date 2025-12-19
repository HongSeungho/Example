import sys
from random import randint
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QLabel, QPushButton, QGridLayout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("무작위 번호 생성기")
        self.setGeometry(100, 100, 400, 150) # 창 위치와 크기 설정

        self.layout = QGridLayout()
        self.labels = [] # 생성된 모든 QLabel 객체를 저장할 리스트

        # --- 레이블 생성 및 배치 (2행 6열) ---
        for row in range(2):
            for col in range(6):
                # QLabel 객체를 생성하고 초기 텍스트를 설정합니다.
                label = QLabel(f"0", self)
                label.setAlignment(Qt.AlignCenter)
                # 폰트 크기를 키워서 더 잘 보이게 설정합니다.
                label.setStyleSheet("font-size: 16px; border: 1px solid black; padding: 5px;")
                
                self.layout.addWidget(label, row, col) # 레이아웃에 추가
                self.labels.append(label)             # 리스트에 객체 저장

        # --- 버튼 생성 및 배치 ---
        self.btn = QPushButton("무작위 번호 생성")
        self.btn.clicked.connect(self.random_number)
        # 버튼을 2행 0열부터 6열까지 걸쳐서 배치 (가운데 정렬 효과)
        self.layout.addWidget(self.btn, 2, 0, 1, 6) 

        # --- 메인 위젯 설정 ---
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

    def random_number(self):
        """저장된 모든 레이블에 1부터 45 사이의 무작위 숫자를 설정합니다."""
        for label in self.labels:
            number = randint(1, 45)
            label.setText(f"{number}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
