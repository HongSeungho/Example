import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QComboBox, QLabel, QLineEdit,
                               QGridLayout, QVBoxLayout, QTabWidget,
                               QSpacerItem, QSizePolicy)

# --- 커스텀 위젯 (기존 유지) ---
class UnitLabel(QLabel):
    def __init__(self, text: str = " ", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.setContentsMargins(5, 0, 5, 0)

class UnitLine(QLineEdit):
    def __init__(self, default_text: str = "1", parent=None):
        super().__init__(default_text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

class UnitCombobox(QComboBox):
    def __init__(self, units: list[str], parent=None):
        super().__init__(parent)
        self.addItems(units)

# --- 핵심: 모든 변환기의 부모 클래스 ---
class BaseConverter(QWidget):
    """모든 단위 변환 위젯의 기본이 되는 클래스"""
    def __init__(self, title: str, units: list[str], parent=None):
        super().__init__(parent)
        self.title = title
        self.unit_list = units
        
        self.setup_ui()
        self.signal_connections()
        
        # 초기값 설정 시 로직 실행을 위해 강제 호출 하지 않고,
        # LineEdit에 값을 넣어서 트리거 유도
        self.input_lineedit.setText("1") 

    def setup_ui(self):
        self.glayout = QGridLayout(self)
        
        self.label = UnitLabel(self.title)
        self.input_lineedit = UnitLine()
        self.input_combobox = UnitCombobox(self.unit_list)
        
        self.output_label = UnitLabel("-")
        self.output_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.output_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | 
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        
        self.output_combobox = UnitCombobox(self.unit_list)
        # 출력 콤보박스의 기본값을 리스트의 두 번째 항목으로 설정 (사용자 편의)
        if len(self.unit_list) > 1:
            self.output_combobox.setCurrentIndex(1)

        self.glayout.addWidget(self.label, 0, 0)
        self.glayout.addWidget(self.input_lineedit, 0, 1)
        self.glayout.addWidget(self.input_combobox, 0, 2)
        self.glayout.addWidget(self.output_label, 0, 3)
        self.glayout.addWidget(self.output_combobox, 0, 4)

        self.glayout.setColumnMinimumWidth(0, 70)
        self.glayout.setColumnMinimumWidth(1, 210)
        self.glayout.setColumnMinimumWidth(2, 268)
        self.glayout.setColumnMinimumWidth(3, 240)
        self.glayout.setColumnMinimumWidth(4, 268)

    def signal_connections(self):
        self.input_lineedit.textChanged.connect(self.update_conversion)
        self.input_combobox.currentTextChanged.connect(self.update_conversion)
        self.output_combobox.currentTextChanged.connect(self.update_conversion)

    def update_conversion(self):
        """UI 입력을 읽어 변환 로직을 수행하고 결과를 출력"""
        input_text = self.input_lineedit.text()
        
        if not input_text or input_text == "-" or input_text == ".":
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

    def calculate(self, value, in_unit, out_unit):
        """자식 클래스에서 반드시 오버라이딩 해야 함"""
        raise NotImplementedError("Subclasses must implement convert_logic")

# --- 1. 비율 변환기 (길이, 넓이, 부피, 무게, 압력, 유속, 유량) ---
class RatioConverter(BaseConverter):
    """단순 비율(Factor)로 변환하는 위젯"""
    def __init__(self, title: str, unit_dict: dict, parent=None):
        self.unit_dict = unit_dict
        # 부모 클래스 초기화 (키 값만 리스트로 전달)
        super().__init__(title, list(unit_dict.keys()), parent)

    def calculate(self, value, in_unit, out_unit):
        input_ratio = self.unit_dict[in_unit]
        output_ratio = self.unit_dict[out_unit]
        
        # Base 단위로 변환 후 목표 단위로 변환
        return (value * input_ratio) / output_ratio

# --- 2. 온도 변환기 (공식 필요) ---
class TemperatureConverter(BaseConverter):
    """온도 변환 위젯 (공식 사용)"""
    def __init__(self, parent=None):
        units = ["Celsius", "Fahrenheit", "Kelvin"]
        super().__init__("온도", units, parent)
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

    def calculate(self, value, in_unit, out_unit):
        val_in_c = self.to_celsius(value, in_unit)
        return self.from_celsius(val_in_c, out_unit)

# --- 3. 파이프 두께 계산 (공식 필요) ---
class Thickness(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.signal_connections()

    def setup_ui(self):
        self.glayout = QGridLayout(self)
        self.rowspacer = QSpacerItem(60, 20,
                                  QSizePolicy.Policy.Expanding,
                                  QSizePolicy.Policy.Minimum)
        self.colspacer = QSpacerItem(520, 20,
                                  QSizePolicy.Policy.Expanding,
                                  QSizePolicy.Policy.Minimum)

        self.label = UnitLabel("내부 압력 하의 직선 파이프 - t < D/6")
        font = self.label.font()
        font.setPointSize(14)
        self.label.setFont(font)
        self.glayout.addWidget(self.label, 0, 0)
        self.glayout.addItem(self.rowspacer, 1, 0)
        self.pressure_label = UnitLabel(
                                "Internal Design Gage Pressure")
        self.pressure_line = UnitLine()
        self.pressure_unit = UnitLabel("MPa")
        self.outdiameter_label = UnitLabel(
                                "Outside Diameter of Pipe")
        self.outdiameter_line = UnitLine()
        self.outdiameter_unit = UnitLabel("Millimeter")
        self.stress_label = UnitLabel(
                                "Stress Value for Material")
        self.stress_line = UnitLine()
        self.stress_unit = UnitLabel("MPa")
        self.quality_label = UnitLabel(
                                "Quality Factor")
        self.quality_line = UnitLine()
        self.weld_label = UnitLabel(
                                "Weld Joint Strength Reduction Factor")
        self.weld_line = UnitLine()
        self.coefficient_label = UnitLabel(
                                "Coefficient")
        self.coefficient_line = UnitLine()

        self.glayout.addWidget(self.pressure_label, 2, 0)
        self.glayout.addWidget(self.pressure_line, 2, 1)
        self.glayout.addWidget(self.pressure_unit, 2, 2)
        self.glayout.addWidget(self.outdiameter_label, 3, 0)
        self.glayout.addWidget(self.outdiameter_line, 3, 1)
        self.glayout.addWidget(self.outdiameter_unit, 3, 2)
        self.glayout.addWidget(self.stress_label, 4, 0)
        self.glayout.addWidget(self.stress_line, 4, 1)
        self.glayout.addWidget(self.stress_unit, 4, 2)
        self.glayout.addWidget(self.quality_label, 5, 0)
        self.glayout.addWidget(self.quality_line, 5, 1)
        self.glayout.addWidget(self.weld_label, 6, 0)
        self.glayout.addWidget(self.weld_line, 6, 1)
        self.glayout.addWidget(self.coefficient_label, 7, 0)
        self.glayout.addWidget(self.coefficient_line, 7, 1)
        self.glayout.addItem(self.colspacer, 0, 3)

        # self.glayout.setColumnMinimumWidth(0, 240)
        # self.glayout.setColumnMinimumWidth(1, 140)
        # self.glayout.setColumnMinimumWidth(2, 160)
        
    def signal_connections(self):
        pass

# --- 메인 윈도우 ---
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("배관 및 계장 계산 도구")
        
        # 데이터 정의
        length_units = {
            "Millimeter": 0.001, "Centimeter": 0.01, "Meter": 1.0,
            "Kilometer": 1000.0, "Inch": 0.0254, "Foot": 0.3048,
            "Yard": 0.9144, "Mile": 1609.344
        }
        area_units = {
            "Square Millimeter": 0.000001, "Square Centimeter": 0.0001,
            "Square Meter": 1.0, "Square Kilometer": 1000000.0,
            "Square Inch": 0.00064516, "Square Foot": 0.09290304,
            "Square Yard": 0.83612736, "Square Mile": 2589988.110336
        }
        volume_units = {
            "Milliliter": 0.000001, "Liter": 0.001, "Cubic Meter": 1.0,
            "Cubic Millimeter": 0.000000001, "Cubic Centimeter": 0.000001,
            "Barrel(oil)": 0.1589872949, "CC": 0.000001, 
            "Cubic Inch": 0.0000163871, "Cubic Foot": 0.0283168466,
            "Cubic Yard": 0.764554858, "US Gallon": 0.0037854118,
        }
        weight_units = {
            "Milligram": 0.000001, "Gram": 0.001, "Kilogram": 1.0,
            "Ton": 1000.0, "Ounce": 0.0283495231, "Pound": 0.45359237
        }
        pressure_units = {
                "Kilopascal": 0.001, "bar": 0.1, "Megapascal": 1.0,
                "psi": 0.0068947573, "Standard Atmosphere": 0.101325,
                "Newton/Square Meter": 0.000001,
                "Newton/Square Centimeter": 0.01,
                "Newton/Square Millimeter": 1.0,
                "Kilogram-Force/Square Meter": 0.00000980665,
                "Kilogram-Force/Square Centimeter": 0.0980665,
                "Kilogram-Force/Square Millimeter": 9.80665,
                "Torr": 0.0001333224
        }
        viscosity_d_units = {
                "Millinewton Second/Square Meter": 1.0,
                "Centipoise": 1.0,
                "Millipascal Second": 1.0
        }
        viscosity_k_units = {
                "Square Millimeter/Second": 1.0,
                "Centistokes": 1.0
        }
        flow_v_units = {
                "Cubic Centimeter/Second": 0.0036,
                "Cubic Centimeter/Minute": 0.00006,
                "Cubic Centimeter/Hour": 0.000001,
                "Cubic Meter/Second": 3600.0,
                "Cubic Meter/Minute": 60.0,
                "Cubic Meter/Hour": 1.0,
                "Liter/Second": 3.6,
                "Liter/Minute": 0.06,
                "Liter/Hour": 0.001,
                "Gallon(US)/Second": 13.627482422,
                "Gallon(US)/Minute": 0.227124707,
                "Gallon(US)/Hour": 0.0037854118,
                "Barrel/Second": 572.35426174,
                "Barrel/Minute": 9.5392376957,
                "Barrel/Hour": 0.1589872949
        }
        flow_m_units = {
                "Gram/Second": 3.6, "Gram/Minute": 0.06,
                "Gram/Hour": 0.001, "Kilogram/Second": 3600.0,
                "Kilogram/Minute": 60.0, "Kilogram/Hour": 1.0,
                "Pound/Second": 1632.932532, "Pound/Minute": 27.2155422,
                "Pound/Hour": 0.45359237
        }

        # 메인 레이아웃 구성
        self.unit_container = QWidget()
        self.unit_layout = QVBoxLayout(self.unit_container)
        
        # 변환기 인스턴스 추가 (RatioConverter 재사용)
        self.unit_layout.addWidget(RatioConverter("길이", length_units))
        self.unit_layout.addWidget(RatioConverter("넓이", area_units))
        self.unit_layout.addWidget(RatioConverter("부피", volume_units))
        self.unit_layout.addWidget(RatioConverter("무게", weight_units))
        self.unit_layout.addWidget(TemperatureConverter()) # 온도는 별도 클래스 사용
        self.unit_layout.addWidget(RatioConverter("압력", pressure_units))
        self.unit_layout.addWidget(RatioConverter("동적 유속", viscosity_d_units))
        self.unit_layout.addWidget(RatioConverter("정적 유속", viscosity_k_units))
        self.unit_layout.addWidget(RatioConverter("부피 유량", flow_v_units))
        self.unit_layout.addWidget(RatioConverter("질량 유량", flow_m_units))
        
        # UI 마무리
        self.unit_layout.addStretch() # 아래 공간 채우기
        
        self.thickness_container = QWidget()
        self.thickness_unit_layout = QVBoxLayout(self.thickness_container)
        self.thickness_unit_layout.addWidget(Thickness())

        self.thickness_unit_layout.addStretch()

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.South)
        self.tab_widget.addTab(self.unit_container, "단위 환산")
        self.tab_widget.addTab(self.thickness_container, "배관 두께 계산")
        
        self.setCentralWidget(self.tab_widget)
        # 창 크기 자동 조절 (내용물에 맞게)
        self.resize(800, 600)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
