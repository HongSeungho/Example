import sys, os
import json
import qdarktheme
from typing import Dict, List, Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QComboBox, QLabel, QLineEdit, QTableWidget,
                               QGridLayout, QVBoxLayout, QTabWidget,
                               QSpacerItem, QSizePolicy, QTableWidgetItem,
                               QHeaderView, QAbstractItemView,
                               QStackedLayout, QHBoxLayout, QFrame,
                               QScrollArea)

# --- [중요] PyInstaller 리소스 경로 해결 함수 ---
def resource_path(relative_path):
    """ 실행 파일 내부의 임시 폴더나 현재 폴더에서 파일을 찾음 """
    try:
        base_path = sys._MEIPASS
    except EXception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- 1. 상수 데이터 정의 (데이터와 로직 분리) ---
UNIT_DATA = {
        "길이": {
            "mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0, "in": 0.0254,
            "ft": 0.3048, "yd": 0.9144, "mi": 1609.344
            },
        "넓이": {
            "mm²": 1e-6, "cm²": 0.0001, "m²": 1.0, "km²": 1e6,
            "in²": 0.00064516, "ft²": 0.09290304,
            "yd²": 0.83612736, "mi²": 2589988.110336
            },
        "부피": {
            "Milliliter": 1e-6, "Liter": 0.001, "m³": 1.0, "mm³": 1e-9,
            "cm³": 1e-6, "Barrel(oil)": 0.1589872949, "CC": 1e-6,
            "in³": 0.0000163871, "ft³": 0.0283168466,
            "yd³": 0.764554858, "US Gallon": 0.0037854118,
            },
        "무게": {
            "Milligram": 1e-6, "Gram": 0.001, "Kilogram": 1.0,
            "Ton": 1000.0, "Ounce": 0.0283495231, "Pound": 0.45359237
            },
        "압력": {
            "Kilopascal": 0.001, "bar": 0.1, "Megapascal": 1.0,
            "psi": 0.0068947573, "Standard Atmosphere": 0.101325,
            "Newton/m²": 1e-6, "Newton/cm²": 0.01, "Newton/mm²": 1.0,
            "kgf/m²": 0.00000980665, "kgf/cm²": 0.0980665, "kgf/mm²": 9.80665,
            "Torr": 0.0001333224
            },
        "동적 유속": {
            "mN·s/m²": 1.0, "Centipoise": 1.0, "mPa·s": 1.0
            },
        "정적 유속": {
            "mm²/s": 1.0, "Centistokes": 1.0
            },
        "부피 유량": {
            "cm³/s": 0.0036, "cm³/min": 0.00006, "cm³/hr": 1e-6,
            "m³/s": 3600.0, "m³/min": 60.0, "m³/hr": 1.0,
            "L/s": 3.6, "L/min": 0.06, "L/hr": 0.001,
            "gal(US)/s": 13.627482, "gal(US)/min": 0.227124, "gal(US)/hr": 0.003785,
            "barrel/s": 572.35426, "barrel/min": 9.539237, "barrel/hr": 0.158987
            },
        "질량 유량": {
            "g/s": 3.6, "g/min": 0.06, "g/hr": 0.001,
            "kg/s": 3600.0, "kg/min": 60.0, "kg/hr": 1.0,
            "lb/s": 1632.9325, "lb/min": 27.21554, "lb/hr": 0.453592
            }
        }

# --- 2. 커스텀 UI 위젯 ---
class UnitLabel(QLabel):
    def __init__(self, text: str = " ", parent=None, bold: bool=False, font_size: int=0):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.setContentsMargins(5, 0, 5, 0)
        if bold:
            style = "font-weight: bold;"
            if font_size > 0:
                style += f" font-size: {font_size}pt;"
            self.setStyleSheet(style)

class UnitLine(QLineEdit):
    def __init__(self, default_text: str = "", parent=None):
        super().__init__(default_text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

class UnitCombobox(QComboBox):
    def __init__(self, units: List[str], parent=None):
        super().__init__(parent)
        self.addItems(units)

# --- 3. 단위 변환기 로직 ---
class BaseConverterWidget(QWidget):
    """모든 단위 변환 위젯의 기본이 되는 클래스"""
    def __init__(self, title: str, units: List[str], parent=None):
        super().__init__(parent)
        self.title = title
        self.unit_list = units
        self.setup_ui()
        self.signal_connections()
        self.input_lineedit.setText("1")

    def setup_ui(self):
        # 메인 레이아웃 (여백 조절)
            self.main_layout = QVBoxLayout(self)
            self.main_layout.setContentsMargins(5, 5, 5, 5)

            # --- 카드 스타일 프레임 생성 ---
            self.card_frame = QFrame()
            self.card_frame.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border-radius: 10px;
                    border: 1px solid #dee2e6;
                }
                QLabel { border: none; }
                QLineEdit { border: 1px solid #ced4da; border-radius: 4px; padding: 2px; }
                QComboBox { border: 1px solid #ced4da; border-radius: 4px; }
            """)

            # 프레임 내부용 그리드 레이아웃
            self.glayout = QGridLayout(self.card_frame)
            self.glayout.setContentsMargins(15, 15, 15, 15)
            self.glayout.setHorizontalSpacing(15)

            # 구성 요소 생성
            self.label = UnitLabel(self.title, bold=True)
            self.label.setMinimumWidth(80)

            self.input_lineedit = UnitLine("1")
            self.input_combobox = UnitCombobox(self.unit_list)

            self.output_label = UnitLabel("-")
            self.output_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            self.output_label.setStyleSheet("font-weight: bold; color: #d35400; font-size: 11pt; border: none;")
            self.output_label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse | 
                    Qt.TextInteractionFlag.TextSelectableByKeyboard
                    )

            self.output_combobox = UnitCombobox(self.unit_list)
            if len(self.unit_list) > 1:
                self.output_combobox.setCurrentIndex(1)

            # 위젯 배치 (카드 프레임 내부 그리드에 배치)
            self.glayout.addWidget(self.label, 0, 0)
            self.glayout.addWidget(self.input_lineedit, 0, 1)
            self.glayout.addWidget(self.input_combobox, 0, 2)

            # 화살표나 구분 기호 역할을 하는 라벨 추가 (선택 사항)
            self.arrow_label = QLabel("▶")
            self.arrow_label.setStyleSheet("color: #95a5a6; border: none;")
            self.arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.glayout.addWidget(self.arrow_label, 0, 3)

            self.glayout.addWidget(self.output_label, 0, 4)
            self.glayout.addWidget(self.output_combobox, 0, 5)

            # 열 비율 조정 (입력창과 결과창이 유연하게 늘어나도록)
            self.glayout.setColumnStretch(1, 2)
            self.glayout.setColumnStretch(2, 1)
            self.glayout.setColumnStretch(4, 2)
            self.glayout.setColumnStretch(5, 1)

            self.glayout.setColumnMinimumWidth(0, 70)
            self.glayout.setColumnMinimumWidth(1, 210)
            self.glayout.setColumnMinimumWidth(2, 268)
            self.glayout.setColumnMinimumWidth(4, 240)
            self.glayout.setColumnMinimumWidth(5, 268)

            # 카드 프레임을 메인 레이아웃에 추가
            self.main_layout.addWidget(self.card_frame)

    def signal_connections(self):
        self.input_lineedit.textChanged.connect(self.update_conversion)
        self.input_combobox.currentTextChanged.connect(self.update_conversion)
        self.output_combobox.currentTextChanged.connect(self.update_conversion)

    def update_conversion(self):
        """UI 입력을 읽어 변환 로직을 수행하고 결과를 출력"""
        input_text = self.input_lineedit.text()

        if not input_text or input_text in ["-", "."]:
            self.output_label.setText("-")
            return

        try:
            val = float(input_text)
            in_unit = self.input_combobox.currentText()
            out_unit = self.output_combobox.currentText()

            # 자식 클래스에서 구현할 구체적인 계산 로직 호출
            result = self.calculate(val, in_unit, out_unit)

            self.output_label.setText(f"{result:.11g}")
        except ValueError:
            self.output_label.setText("Error")

    def calculate(self, value: float, in_unit: str, out_unit: str) -> float:
        """자식 클래스에서 반드시 오버라이딩 해야 함"""
        raise NotImplementedError("Subclasses must implement convert_logic")

# --- 4. 비율 변환기 (길이, 넓이, 부피, 무게, 압력, 유속, 유량) ---
class RatioConverterWidget(BaseConverterWidget):
    """단순 비율(Factor)로 변환하는 위젯"""
    def __init__(self, title: str, unit_dict: Dict[str, float], parent=None):
        self.unit_dict = unit_dict
        # 부모 클래스 초기화 (키 값만 리스트로 전달)
        super().__init__(title, list(unit_dict.keys()), parent)

    def calculate(self, value: float, in_unit: str, out_unit: str) -> float:
        # Base 단위로 변환 후 목표 단위로 변환
        return (value * self.unit_dict[in_unit]) / self.unit_dict[out_unit]

# --- 5. 온도 변환기 (공식 필요) ---
class TemperatureConverterWidget(BaseConverterWidget):
    """온도 변환 위젯 (공식 사용)"""
    def __init__(self, parent=None):
        super().__init__("온도", ["Celsius", "Fahrenheit", "Kelvin"], parent)
        self.input_lineedit.setText("0") # 온도는 0도부터 시작하는게 자연스러움

    def to_celsius(self, value: float, unit: str) -> float:
        if unit == "Celsius": return value
        elif unit == "Fahrenheit": return (value - 32) * 5 / 9
        elif unit == "Kelvin": return value - 273.15
        return value

    def from_celsius(self, value: float, unit: str) -> float:
        if unit == "Celsius": return value
        elif unit == "Fahrenheit": return (value * 9 / 5) + 32
        elif unit == "Kelvin": return value + 273.15
        return value

    def calculate(self, value: float, in_unit: str, out_unit: str) -> float:
        # 섭씨로 변환
        celsius = value
        if in_unit == "Fahrenheit":
            celsius = (value -32) * 5 / 9
        elif in_unit == "Kelvin":
            celsius = value - 273.15

        # 목표 단위로 변환
        if out_unit == "Celsius":
            return celsius
        elif out_unit == "Fahrenheit":
            return (celsius * 9 / 5) + 32
        elif out_unit == "Kelvin":
            return celsius + 273.15
        return celsius


class PipeThicknessWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inputs = {}
        self.setup_ui()
        self.load_reference_data()
        
    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # --- 왼쪽: 입력 영역 (카드 스타일) ---
        input_group = QFrame()
        input_group.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 10px;
                border: 1px solid #dee2e6;
            }
            QLabel { border: none; }
            QLineEdit { border: 1px solid #ced4da; border-radius: 4px; padding: 5px; }
        """)

        # 입력 카드 내부 레이아웃
        input_vbox = QVBoxLayout(input_group)
        input_vbox.setContentsMargins(20, 20, 20, 20)

        title_lbl = QLabel("Pipe Thickness Calculation")
        title_lbl.setMinimumHeight(75)
        title_lbl.setStyleSheet("font-size: 13pt; font-weight: bold; color: #d35400; margin-bottom: 10px;")
        input_vbox.addWidget(title_lbl)

        # 필드들을 담을 그리드
        fields_grid = QGridLayout()
        fields_grid.setVerticalSpacing(30) # 필드 간 간격 확보
        fields_grid.setHorizontalSpacing(25) 

        fields = [
            ("pressure", "Design Pressure (P)", "MPa"),
            ("diameter", "Outside Diameter (D)", "mm"),
            ("stress", "Allowable Stress (S)", "MPa"),
            ("quality", "Quality Factor (E)", ""),
            ("weld", "Weld Joint Factor (W)", ""),
            ("coeff", "Coefficient (Y)", ""),
            ("corrosion", "Corrosion (C)", "mm")
        ]

        for i, (key, label, unit) in enumerate(fields):
            lbl = QLabel(label)
            lbl.setFont(QFont("Malgun Gothic", 11))
            edit = UnitLine()
            edit.setFixedHeight(30) # 입력창 높이 고정
            edit.textChanged.connect(self.calculate)
            self.inputs[key] = edit

            fields_grid.addWidget(lbl, i, 0)
            fields_grid.addWidget(edit, i, 1)
            fields_grid.addWidget(QLabel(unit), i, 2)

        input_vbox.addLayout(fields_grid)

        # 결과 영역 (하단 고정 및 강조)
        input_vbox.addStretch(1) # 입력 필드와 결과 사이 공간을 늘려줌

        result_frame = QFrame()
        result_frame.setStyleSheet("background-color: transparent; border-radius: 5px; border: 1px solid #e9ecef;")
        res_layout = QHBoxLayout(result_frame)

        min_thick = QLabel("Required Min. Thickness (t):")
        min_thick.setStyleSheet("font: Malgun Gothic; font-weight: bold; font-size: 11; border:noe;")
        self.res_label = QLabel("-")
        self.res_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #d35400; border:none;")

        res_layout.addWidget(min_thick)
        res_layout.addStretch()
        res_layout.addWidget(self.res_label)

        input_vbox.addWidget(result_frame)

        # --- 오른쪽: 참조 테이블 (시인성 개선) ---
        self.table = QTableWidget()
        self.table.setMinimumSize(150, 550)
        self.table.setAlternatingRowColors(True) # 행 색상 교차
        self.table.setStyleSheet("""
            QTableWidget { 
                gridline-color: #ecf0f1; 
                background-color: transparent;
                alternate-background-color: transparent;
            }
            QHeaderView::section { 
                background-color: #34495e; 
                color: white; 
                padding: 5px;
                font-weight: bold;
            }
        """)

        self.selector = QComboBox()
        self.selector.addItems(["Allowable Stress (S)", "Casting Quality (Ec)", "Longitudinal Weld Joints (Ej)", "Weld Joint (W)", "Coefficient (Y)"])
        self.selector.currentIndexChanged.connect(self.update_table_view)

        ref_data_sele = QLabel("Reference Data Selection:")
        ref_data_sele.setStyleSheet("font-size: 11;")
        ref_data_sele.setMinimumHeight(50)

        right_layout = QVBoxLayout()
        right_layout.addWidget(ref_data_sele)
        right_layout.addWidget(self.selector)
        right_layout.addWidget(self.table)

        layout.addWidget(input_group, 0, 0)
        layout.addLayout(right_layout, 0, 1)
        layout.setColumnStretch(1, 2)
        layout.setHorizontalSpacing(50)

    def load_reference_data(self):
        """JSON 파일에서 데이터를 한 번에 로드"""
        # 파일이 없을 경우를 대비한 기본 데이터 구조
        self.db = {"stress_data": [], "casting_data": [], "longitu_data": [], "weld_data": [], "coefficient_data": []}

        # [중요] resource_path 적용
        json_path = resource_path("piping_data.json")        

        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                self.db = json.load(f)
        self.update_table_view()

    def update_table_view(self):
        """콤보박스 선택에 따라 테이블 갱신 (리팩토링 핵심)"""
        key_map = ["stress_data", "casting_data", "longitu_data", "weld_data", "coefficient_data"]
        data = self.db.get(key_map[self.selector.currentIndex()], [])
        
        if not data:
            self.table.setRowCount(0)
            return

        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(data[0]))
        
        for r, row_data in enumerate(data):
            for c, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if r == 0: # 첫 줄 헤더 강조
                    item.setBackground(QColor("#2c3e50"))
                    item.setForeground(QColor("white"))
                self.table.setItem(r, c, item)
        
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def calculate(self):
        # 기존 계산 로직과 동일하되, 시각적 피드백 추가
        try:
            P = float(self.inputs['pressure'].text() or 0)
            D = float(self.inputs['diameter'].text() or 0)
            S = float(self.inputs['stress'].text() or 0)
            E = float(self.inputs['quality'].text() or 0)
            W = float(self.inputs['weld'].text() or 0)
            Y = float(self.inputs['coeff'].text() or 0)
            C = float(self.inputs['corrosion'].text() or 0)

            denominator = 2 * (S * E * W + P * Y)
            if denominator <= 0: return

            t = (P * D / denominator) + C
            self.res_label.setText(f"{t:.4f} mm")
        except:
            self.res_label.setText("-")

# --- 메인 윈도우 ---
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
           super().__init__(parent)
           self.setWindowTitle("배관 및 계장 계산 도구 - 베타")
           self.resize(1050, 700)
           self.setup_ui()

    def setup_ui(self):
        self.tab_widget = QTabWidget()

        # --- 탭 헬퍼 함수 ---
        def create_scroll_tab(widget, min_w=1050):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            # 가로 스크롤이 필요할 때 나타나도록 설정
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # 내부 컨테이너 위젯 생성
            container = QWidget()
            container.setMinimumWidth(min_w)
            layout = QVBoxLayout(container)
            layout.addWidget(widget)
            layout.addStretch()
            
            scroll.setWidget(container)
            return scroll

        # 1. 단위 환산 위젯 그룹화
        unit_group = QWidget()
        unit_vbox = QVBoxLayout(unit_group)
        for title, units in UNIT_DATA.items():
            unit_vbox.addWidget(RatioConverterWidget(title, units))
        unit_vbox.addWidget(TemperatureConverterWidget())

        # 2. 배관 두께 위젯
        thickness_group = PipeThicknessWidget()

        # 스크롤 적용하여 탭 추가
        self.tab_widget.addTab(create_scroll_tab(unit_group), "단위 환산")
        self.tab_widget.addTab(create_scroll_tab(thickness_group), "배관 두께 계산")
        
        self.setCentralWidget(self.tab_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        qdarktheme.setup_theme("dark")
    except AttributeError:
        app.setStyleSheet(qdarktheme.load_stylesheet())

    #app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
