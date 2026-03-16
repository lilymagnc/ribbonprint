import sys
import json
import win32print
import win32ui
from PIL import Image, ImageWin
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QFontComboBox, QSpinBox, 
    QGroupBox, QGridLayout, QFileDialog, QMessageBox, QCheckBox, QLineEdit,
    QStatusBar, QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPixmap, QTransform, QUndoStack, 
    QUndoCommand, QPen, QFontMetrics
)
from PyQt6.QtCore import Qt, QRectF

# --- 데이터 관리 ---
PRESETS_FILE = "ribbon_presets.json"
PHRASES_FILE = "phrases.json"
DEFAULT_PRESETS = {
    "꽃다발 38x400mm": {"리본넓이": 38, "레이스": 5, "리본길이": 400, "상단여백": 80, "하단여백": 50, "인쇄여백": 53},
    "동양란 45x450mm": {"리본넓이": 45, "레이스": 7, "리본길이": 450, "상단여백": 100, "하단여백": 50, "인쇄여백": 57},
    "동양란 50x500mm": {"리본넓이": 50, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 60},
    "동/서양란 55x500mm": {"리본넓이": 55, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 62},
    "서양란 60/65x700mm": {"리본넓이": 60, "레이스": 10, "리본길이": 700, "상단여백": 150, "하단여백": 100, "인쇄여백": 65},
    "영화(을) 70x750mm": {"리본넓이": 70, "레이스": 10, "리본길이": 750, "상단여백": 150, "하단여백": 100, "인쇄여백": 70},
    "장미바구니 95x1000mm": {"리본넓이": 95, "레이스": 10, "리본길이": 1000, "상단여백": 180, "하단여백": 130, "인쇄여백": 82},
    "화분 소 105/110x1100mm": {"리본넓이": 105, "레이스": 23, "리본길이": 1100, "상단여백": 200, "하단여백": 150, "인쇄여백": 87},
    "화분 중 135x1500mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1500, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "화분 대 150x1800mm": {"리본넓이": 150, "레이스": 23, "리본길이": 1800, "상단여백": 350, "하단여백": 350, "인쇄여백": 110},
    "근조 1단 115x1200mm": {"리본넓이": 115, "레이스": 23, "리본길이": 1200, "상단여백": 250, "하단여백": 150, "인쇄여백": 102},
    "근조 2단 135x1700mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1700, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "근조 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
    "축화환 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
}
DEFAULT_PHRASES = { "경조사": {"기본": ["祝開業"]}, "보내는이": {"기본": ["OOO 올림"]} }

def load_data(filename, default_data):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data

def save_presets(presets):
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, ensure_ascii=False, indent=4)

def get_font_for_char(char, config):
    if not char: return config.get('한글', '(한)마린_견궁서B')
    if '\uac00' <= char <= '\ud7a3': return config.get('한글', '(한)마린_견궁서B')
    elif '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf': return config.get('한자', '(한)마린_견궁서B')
    elif '\u0021' <= char <= '\u007e': return config.get('영문', '(한)마린_견궁서B')
    else: return config.get('기타 (외국어)', '(한)마린_견궁서B')

class RibbonSettingsDialog(QDialog):
    def __init__(self, presets_data, parent=None):
        super().__init__(parent)
        self.presets = presets_data.copy()
        self.setWindowTitle("리본 종류 설정")
        self.setMinimumSize(800, 400)
        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("프린터 모델:"))
        printer_combo = QComboBox()
        printer_combo.addItems(["Epson-M105"])
        top_layout.addWidget(printer_combo)
        top_layout.addStretch()
        add_btn = QPushButton("리본 추가")
        del_btn = QPushButton("리스트 삭제")
        add_btn.clicked.connect(self.add_row)
        del_btn.clicked.connect(self.remove_row)
        top_layout.addWidget(add_btn)
        top_layout.addWidget(del_btn)
        layout.addLayout(top_layout)
        self.table = QTableWidget()
        self.column_headers = ["리본이름", "넓이", "레이스", "길이", "상단", "하단", "여백"]
        self.table.setColumnCount(len(self.column_headers))
        self.table.setHorizontalHeaderLabels(self.column_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.populate_table()
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        save_btn = QPushButton("저장/종료")
        cancel_btn = QPushButton("취소")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(cancel_btn)
        layout.addLayout(bottom_layout)

    def populate_table(self):
        self.table.setRowCount(len(self.presets))
        key_map = {"리본넓이": "넓이", "레이스": "레이스", "리본길이": "길이", "상단여백": "상단", "하단여백": "하단", "인쇄여백": "여백"}
        for row, (name, data) in enumerate(self.presets.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            for key, col_name in key_map.items():
                if col_name in self.column_headers:
                    col_index = self.column_headers.index(col_name)
                    self.table.setItem(row, col_index, QTableWidgetItem(str(data.get(key, ''))))

    def add_row(self):
        self.table.insertRow(self.table.rowCount())

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row > -1: self.table.removeRow(current_row)

    def accept(self):
        new_presets = {}
        key_map_inv = {"넓이": "리본넓이", "레이스": "레이스", "길이": "리본길이", "상단": "상단여백", "하단": "하단여백", "여백": "인쇄여백"}
        for row in range(self.table.rowCount()):
            try:
                name_item = self.table.item(row, 0)
                if not name_item or not name_item.text(): continue
                name = name_item.text()
                data = {}
                for col in range(1, self.table.columnCount()):
                    header = self.column_headers[col]
                    key = key_map_inv.get(header)
                    item = self.table.item(row, col)
                    if key and item and item.text(): data[key] = int(item.text())
                new_presets[name] = data
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "입력 오류", f"{row+1}행에 잘못된 숫자 형식이 있습니다.")
                return
        self.presets = new_presets
        save_presets(self.presets)
        super().accept()

class RibbonPreviewWidget(QWidget):
    def __init__(self, app_instance):
        super().__init__(app_instance)
        self.app = app_instance
        self.setMinimumSize(500, 700)
        self.padding = 15

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(220, 220, 220))
        config_right = self.app.get_config_for_side('경조사')
        config_left = self.app.get_config_for_side('보내는이')
        total_original_width = config_right.get('리본넓이', 50) + config_left.get('리본넓이', 50) + 50
        max_original_length = max(config_right.get('리본길이', 400), config_left.get('리본길이', 400))
        if max_original_length <= 0 or total_original_width <= 0: return
        view_width = self.width() - self.padding * 2
        view_height = self.height() - self.padding * 2
        scale_w = view_width / total_original_width
        scale_h = view_height / max_original_length
        scale = min(scale_w, scale_h)
        scaled_width_right = config_right.get('리본넓이', 50) * scale
        scaled_width_left = config_left.get('리본넓이', 50) * scale
        scaled_spacing = 50 * scale
        scaled_height_right = config_right.get('리본길이', 400) * scale
        scaled_height_left = config_left.get('리본길이', 400) * scale
        total_scaled_width = scaled_width_right + scaled_width_left + scaled_spacing
        start_x = (self.width() - total_scaled_width) / 2
        start_y = (self.height() - max(scaled_height_right, scaled_height_left)) / 2
        rect_right = QRectF(start_x, start_y, scaled_width_right, scaled_height_right)
        rect_left = QRectF(start_x + scaled_width_right + scaled_spacing, start_y, scaled_width_left, scaled_height_left)
        self.draw_ruler(painter, rect_right, config_right.get('리본길이', 400), scale)
        self.draw_ruler(painter, rect_left, config_left.get('리본길이', 400), scale)
        painter.fillRect(rect_right, QColor("lightgray"))
        painter.fillRect(rect_left, QColor("lightgray"))
        self.draw_guidelines(painter, rect_right, config_right, scale)
        self.draw_guidelines(painter, rect_left, config_left, scale)
        self.render_side(painter, rect_right, config_right, scale)
        self.render_side(painter, rect_left, config_left, scale)
        self.draw_margins(painter, rect_right, config_right, scale)
        self.draw_margins(painter, rect_left, config_left, scale)
        painter.end()

    def draw_guidelines(self, painter, rect, config, scale):
        painter.save()
        center_pen = QPen(QColor(0, 0, 0, 100), 1, Qt.PenStyle.DashLine)
        painter.setPen(center_pen)
        center_x = rect.center().x()
        painter.drawLine(int(center_x), int(rect.top()), int(center_x), int(rect.bottom()))
        layer_pen = QPen(QColor(0, 0, 255, 120), 1, Qt.PenStyle.DashLine)
        painter.setPen(layer_pen)
        lace_margin = config.get('레이스', 5) * scale
        left_line_x = rect.left() + lace_margin
        right_line_x = rect.right() - lace_margin
        painter.drawLine(int(left_line_x), int(rect.top()), int(left_line_x), int(rect.bottom()))
        painter.drawLine(int(right_line_x), int(rect.top()), int(right_line_x), int(rect.bottom()))
        painter.restore()

    def draw_ruler(self, painter, rect, original_length, scale):
        painter.save()
        ruler_width = 25
        ruler_rect = QRectF(rect.left() - ruler_width, rect.top(), ruler_width, rect.height())
        if ruler_rect.left() < 0 :
             ruler_rect.moveTo(rect.right(), rect.top())
        painter.fillRect(ruler_rect, QColor(14, 209, 69))
        pen = QPen(QColor("white"), 1)
        painter.setPen(pen)
        font = QFont("Arial", 8)
        painter.setFont(font)
        for y_mm in range(0, original_length + 1, 10):
            y_pos = rect.top() + y_mm * scale
            if y_pos > rect.bottom(): break
            if y_mm % 50 == 0:
                painter.drawLine(int(ruler_rect.left() + 5), int(y_pos), int(ruler_rect.right()), int(y_pos))
                if y_mm % 100 == 0: painter.drawText(int(ruler_rect.left()+2), int(y_pos + 10), str(y_mm))
            else:
                painter.drawLine(int(ruler_rect.left() + 15), int(y_pos), int(ruler_rect.right()), int(y_pos))
        painter.restore()

    def draw_margins(self, painter, rect, config, scale):
        painter.save()
        pen = QPen(QColor(255, 0, 0, 150), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        top_margin_y = rect.top() + config.get('상단여백', 80) * scale
        bottom_margin_y = rect.bottom() - config.get('하단여백', 50) * scale
        painter.drawLine(int(rect.left()), int(top_margin_y), int(rect.right()), int(top_margin_y))
        painter.drawLine(int(rect.left()), int(bottom_margin_y), int(rect.right()), int(bottom_margin_y))
        painter.restore()

    def render_side(self, painter, rect, config, scale):
        painter.save()
        text = config.get('text', '')
        if not text or rect.width() <= 0:
            painter.restore()
            return
            
        blocks = []
        i = 0
        current_normal_block = ""
        while i < len(text):
            if text[i] == '[':
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                try:
                    end_index = text.index(']', i)
                    substr = text[i+1:end_index]
                    blocks.append({'type': 'shrink', 'text': substr}); i = end_index + 1
                except ValueError: current_normal_block += text[i]; i += 1
            elif text[i] == '(' and i + 2 < len(text) and text[i+2] == ')' and text[i+1] in ['주', '유', '株']:
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'special', 'text': text[i:i+3]}); i += 3
            elif text[i] == '/' and i > 0 and i < len(text) - 1:
                # "/" 앞뒤 글자를 2열로 배치
                left_char = text[i-1]
                right_char = text[i+1]
                # 이전 글자를 현재 블록에서 제거
                if current_normal_block and current_normal_block[-1] == left_char:
                    current_normal_block = current_normal_block[:-1]
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'two_column', 'left': left_char, 'right': right_char})
                i += 2  # "/" 다음 글자까지 건너뛰기
            else:
                current_normal_block += text[i]
                i += 1
        if current_normal_block:
            blocks.append({'type': 'normal', 'text': current_normal_block})
        
        base_font_size_pt = config.get('글자크기', 40)
        if config.get('auto_font_size', True):
            printable_width_px = (config.get('리본넓이', 50) - (config.get('레이스', 5) * 2)) * scale
            target_pixel_width = printable_width_px * 0.95
            if blocks and printable_width_px > 0:
                temp_font_size_pt = 150
                while temp_font_size_pt > 5:
                    max_char_width_px = 0
                    all_chars_in_blocks = ""
                    for b in blocks:
                        if b['type'] == 'two_column':
                            all_chars_in_blocks += b['left'] + b['right']
                        else:
                            all_chars_in_blocks += b['text']
                    for char in all_chars_in_blocks:
                        font = QFont(get_font_for_char(char, config))
                        font.setPixelSize(int(temp_font_size_pt * scale))
                        fm = QFontMetrics(font)
                        char_width = fm.horizontalAdvance(char) * (config.get('가로폰트', 100) / 100.0)
                        if char_width > max_char_width_px:
                            max_char_width_px = char_width
                    if max_char_width_px <= target_pixel_width:
                        base_font_size_pt = temp_font_size_pt
                        break
                    temp_font_size_pt -= 1

        printable_height = rect.height() - (config.get('상단여백', 80) + config.get('하단여백', 50)) * scale
        base_v_scale = config.get('세로폰트', 100) / 100.0
        
        total_uncompressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * len(block['text']) * base_v_scale
        
        final_v_scale = base_v_scale
        if total_uncompressed_height > printable_height and total_uncompressed_height > 0:
            compression_ratio = printable_height / total_uncompressed_height
            final_v_scale = base_v_scale * compression_ratio
        
        total_compressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * len(block['text']) * final_v_scale
        
        # 전체 글자 수 계산 (justify 배치를 위해)
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 1  # 2열은 1줄로 취급
            elif block['type'] == 'special':
                total_char_count += 1  # special도 1줄로 취급
            else:
                total_char_count += len(block['text'])
        
        # 하단정렬: 하단여백선 위에서 전체 글자 높이만큼 위로 올라가서 시작
        bottom_margin = config.get('하단여백', 50) * scale
        
        # 전체 글자 수 계산
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 2  # 2열은 2글자
            elif block['type'] == 'special':
                total_char_count += len(block['text'])  # special도 글자수만큼
            else:
                total_char_count += len(block['text'])
        
        # 평균 글자 높이로 전체 높이 추정
        temp_font = QFont(get_font_for_char('가', config))
        temp_font.setPixelSize(int(base_font_size_pt * scale))
        temp_fm = QFontMetrics(temp_font)
        avg_char_height = temp_fm.height() * final_v_scale
        total_text_height = total_char_count * avg_char_height
        
        # 하단여백선에서 전체 텍스트 높이만큼 위로 올라간 지점에서 시작
        bottom_y = rect.bottom() - bottom_margin
        current_y = bottom_y - total_text_height
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치 처리
                left_char = block['left']
                right_char = block['right']
                
                for i, char in enumerate([left_char, right_char]):
                    size_ratio = 1.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)

                    char_width = fm.horizontalAdvance(char)
                    scaled_char_width = char_width * h_scale
                    
                    # 왼쪽 글자는 왼쪽에, 오른쪽 글자는 오른쪽에 배치
                    if i == 0:  # 왼쪽 글자
                        char_x = rect.center().x() - scaled_char_width
                    else:  # 오른쪽 글자
                        char_x = rect.center().x()
                    
                    # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    
                    painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                    # 다음 글자 위치로 이동
                    current_y += fm.height() * final_v_scale
                
            elif block['type'] == 'special':
                # (주), (유), (株) 가로 배치 처리
                special_text = block['text']  # 예: "(주)"
                size_ratio = config.get('(주)/(株)', 90) / 100.0
                scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                if scaled_font_size_px <= 0: scaled_font_size_px = 1
                
                # 전체 텍스트의 폭 계산
                total_width = 0
                char_widths = []
                for char in special_text:
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    fm = QFontMetrics(font)
                    char_width = fm.horizontalAdvance(char)
                    char_widths.append(char_width)
                    total_width += char_width
                
                h_scale = config.get('가로폰트', 100) / 100.0 * 0.8  # 80% 가로 축소
                v_scale = final_v_scale
                
                # 중앙 정렬을 위한 시작 x 좌표
                start_x = rect.center().x() - (total_width * h_scale) / 2
                
                # 각 글자를 가로로 배치
                current_x = start_x
                for i, char in enumerate(special_text):
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)
                    
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    painter.drawText(int(current_x / h_scale), int(char_y_pos / v_scale), char)
                    current_x += char_widths[i] * h_scale
                
                # special 블록 전체 처리 후 다음 위치로 이동
                current_y += fm.height() * final_v_scale
                
            else:
                # 일반 텍스트 블록 - justify 배치 적용
                block_text = block['text']
                
                for char in block_text:
                    size_ratio = 1.0
                    if block['type'] == 'shrink': size_ratio = config.get('축소폰트', 70) / 100.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)

                    char_width = fm.horizontalAdvance(char)
                    scaled_char_width = char_width * h_scale
                    
                    char_x = rect.center().x() - (scaled_char_width / 2)
                    
                    # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    
                    painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                    # 다음 글자 위치로 이동
                    current_y += fm.height() * final_v_scale
        painter.restore()

class RibbonApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RibbonMaker - Ribbon Editor (v8.9 최종판)")
        self.setGeometry(50, 50, 1200, 850)
        self.undo_stack = QUndoStack(self)
        self.controls = {'경조사': {}, '보내는이': {}}
        self.phrase_indices = {"경조사": {}, "보내는이": {}}
        self.presets = load_data(PRESETS_FILE, DEFAULT_PRESETS)
        self.phrases = load_data(PHRASES_FILE, DEFAULT_PHRASES)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        self.preview = RibbonPreviewWidget(self)
        main_layout.addWidget(self.preview)
        self.setStatusBar(QStatusBar(self))
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("프로그램 준비 완료.")
        self._connect_signals()
        self.update_ribbon_combo()
        self.update_phrase_categories()
        self._toggle_auto_font_size(True)

    def _create_control_panel(self):
        panel = QWidget()
        panel.setFixedWidth(550)
        top_layout = QVBoxLayout(panel)
        menu_layout = self._create_menu_buttons()
        top_layout.addLayout(menu_layout)
        content_group = self._create_content_inputs()
        top_layout.addWidget(content_group)
        main_grid = self._create_main_grid()
        top_layout.addLayout(main_grid)
        font_group = self._create_font_selectors()
        top_layout.addWidget(font_group)
        env_group = QGroupBox("환경설정")
        env_layout = QHBoxLayout(env_group)
        self.settings_button = QPushButton("리본 설정...")
        self.settings_button.clicked.connect(self.open_ribbon_settings)
        env_layout.addWidget(self.settings_button)
        env_group.setFixedHeight(60)
        top_layout.addWidget(env_group)
        top_layout.addStretch(1)
        return panel
    
    def _create_main_grid(self):
        main_grid = QGridLayout()
        main_grid.setSpacing(5)
        main_grid.addWidget(QLabel("리본종류"), 0, 0)
        self.ribbon_type_combo = QComboBox()
        self.ribbon_type_combo.setMaxVisibleItems(20)  # 최대 20개 항목까지 표시
        self.ribbon_type_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        main_grid.addWidget(self.ribbon_type_combo, 0, 1, 1, 2)
        self.sync_check = QCheckBox("동시적용")
        self.sync_check.setChecked(True)
        main_grid.addWidget(self.sync_check, 0, 3)
        main_grid.addWidget(QLabel("되돌리기"), 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)
        undo_btn = QPushButton("<"); undo_btn.setFixedSize(30,25)
        redo_btn = QPushButton(">"); redo_btn.setFixedSize(30,25)
        undo_btn.clicked.connect(self.undo_stack.undo)
        redo_btn.clicked.connect(self.undo_stack.redo)
        main_grid.addWidget(undo_btn, 0, 5)
        main_grid.addWidget(redo_btn, 0, 6)
        all_fields = ["리본넓이", "레이스", "리본길이", "상단여백", "하단여백", "인쇄여백", "글자크기", "가로폰트", "세로폰트", "축소폰트", "(주)/(株)", "폰트컬러"]
        main_grid.addWidget(QLabel("경조사 설정"), 1, 1, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        main_grid.addWidget(QLabel("보내는이 설정"), 1, 4, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        for i, text in enumerate(all_fields, 2):
            main_grid.addWidget(QLabel(text), i, 0, alignment=Qt.AlignmentFlag.AlignRight)
            for j, side in enumerate(["경조사", "보내는이"]):
                widget = QSpinBox()
                if text == "(주)/(株)":
                    widget.setRange(10, 100); widget.setValue(90); widget.setSuffix('%')
                elif text == "축소폰트":
                    widget.setRange(10, 100); widget.setValue(70); widget.setSuffix('%')
                else:
                    widget.setRange(0, 5000)
                    if text in ["가로폰트", "세로폰트"]: widget.setValue(100)
                    elif text == "글자크기": widget.setValue(40)
                self.controls[side][text] = widget
                main_grid.addWidget(widget, i, 1 + j*3, 1, 2)
        for j, side in enumerate(["경조사", "보내는이"]):
            main_grid.addWidget(QPushButton("그림넣기"), len(all_fields)+2, 1 + j*3)
            main_grid.addWidget(QPushButton("그림수정"), len(all_fields)+2, 2 + j*3)
        return main_grid

    def _create_font_selectors(self):
        group = QGroupBox("서체 설정")
        layout = QGridLayout(group)
        self.auto_font_size_check = QCheckBox("글자 폭 자동 맞춤")
        self.auto_font_size_check.setChecked(True)
        layout.addWidget(self.auto_font_size_check, 0, 0, 1, 2)
        font_types = ["한글", "한자", "영문", "기타 (외국어)"]
        for i, side in enumerate(["경조사", "보내는이"]):
            layout.addWidget(QLabel(f"{side} 서체"), 1, i * 2, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            for j, ftype in enumerate(font_types, 2):
                layout.addWidget(QLabel(ftype), j, i * 2)
                combo = QFontComboBox()
                self.controls[side][ftype] = combo
                layout.addWidget(combo, j, i * 2 + 1)
        return group
    
    def _create_menu_buttons(self):
        menu_layout = QHBoxLayout()
        actions = {"새리본": self.clear_all, "파일열기": self.open_file, "저장": self.save_file,"새로저장": self.save_file_as, "도움말": self.show_help, "인쇄": self.print_ribbon}
        for text, action in actions.items():
            button = QPushButton(text); button.clicked.connect(action); menu_layout.addWidget(button)
        return menu_layout

    def _create_content_inputs(self):
        group = QGroupBox("내용 입력")
        grid = QGridLayout(group)
        self.text_right_edit = QLineEdit("祝開業")
        self.text_left_edit = QLineEdit("대표이사(주)홍길동")
        self.phrase_category_right = QComboBox()
        self.phrase_category_left = QComboBox()
        for i, (side, widget, category_combo) in enumerate([("경조사", self.text_right_edit, self.phrase_category_right), ("보내는이", self.text_left_edit, self.phrase_category_left)]):
            grid.addWidget(QLabel(side), i*2, 0)
            grid.addWidget(widget, i*2, 1)
            btn_layout = QHBoxLayout()
            for btn_text in ['+', '-', 'x']:
                btn = QPushButton(btn_text); btn.setFixedSize(25, 25)
                btn.clicked.connect(lambda _, s=side, op=btn_text: self.cycle_phrase(s, op))
                btn_layout.addWidget(btn)
            grid.addLayout(btn_layout, i*2, 2)
            grid.addWidget(QLabel("샘플 선택"), i*2 + 1, 0)
            grid.addWidget(category_combo, i*2 + 1, 1)
        return group
    
    def _connect_signals(self):
        self.ribbon_type_combo.currentTextChanged.connect(self.update_spins_from_preset)
        self.phrase_category_right.currentTextChanged.connect(lambda: self.reset_phrase_index('경조사'))
        self.phrase_category_left.currentTextChanged.connect(lambda: self.reset_phrase_index('보내는이'))
        self.auto_font_size_check.toggled.connect(self._toggle_auto_font_size)
        for side in self.controls:
            for control in self.controls[side].values():
                if isinstance(control, QSpinBox): control.valueChanged.connect(self.sync_and_update)
                else: control.currentIndexChanged.connect(self.sync_and_update_combo)
        self.text_right_edit.textChanged.connect(self.preview.update)
        self.text_left_edit.textChanged.connect(self.preview.update)

    def update_ribbon_combo(self):
        current_selection = self.ribbon_type_combo.currentText()
        self.ribbon_type_combo.blockSignals(True)
        self.ribbon_type_combo.clear()
        self.ribbon_type_combo.addItems(self.presets.keys())
        index = self.ribbon_type_combo.findText(current_selection)
        if index != -1: self.ribbon_type_combo.setCurrentIndex(index)
        self.ribbon_type_combo.blockSignals(False)
        self.update_spins_from_preset(self.ribbon_type_combo.currentText())

    def update_spins_from_preset(self, ribbon_name):
        data = self.presets.get(ribbon_name)
        if data:
            for side in self.controls:
                for key, widget in self.controls[side].items():
                    if key in data:
                        if isinstance(widget, QSpinBox):
                            widget.blockSignals(True)
                            widget.setValue(data[key])
                            widget.blockSignals(False)
        self.preview.update()

    def update_phrase_categories(self):
        self.phrase_category_right.blockSignals(True)
        self.phrase_category_left.blockSignals(True)
        self.phrase_category_right.clear()
        self.phrase_category_left.clear()
        if "경조사" in self.phrases:
            self.phrase_category_right.addItems(self.phrases["경조사"].keys())
        if "보내는이" in self.phrases:
            self.phrase_category_left.addItems(self.phrases["보내는이"].keys())
        self.phrase_category_right.blockSignals(False)
        self.phrase_category_left.blockSignals(False)
        self.reset_phrase_index('경조사')
        self.reset_phrase_index('보내는이')

    def reset_phrase_index(self, side):
        category_combo = self.phrase_category_right if side == '경조사' else self.phrase_category_left
        category = category_combo.currentText()
        if category:
            self.phrase_indices[side][category] = 0

    def cycle_phrase(self, side, op):
        widget = self.text_right_edit if side == "경조사" else self.text_left_edit
        category_combo = self.phrase_category_right if side == "경조사" else self.phrase_category_left
        category = category_combo.currentText()
        if not category or side not in self.phrases or category not in self.phrases[side]: return
        phrase_list = self.phrases[side][category]
        if not phrase_list: return
        current_index = self.phrase_indices[side].get(category, 0)
        if op == '+': current_index = (current_index + 1) % len(phrase_list)
        elif op == '-': current_index = (current_index - 1 + len(phrase_list)) % len(phrase_list)
        self.phrase_indices[side][category] = current_index
        widget.setText(phrase_list[current_index])
    
    def open_ribbon_settings(self):
        dialog = RibbonSettingsDialog(self.presets, self)
        if dialog.exec():
            self.presets = dialog.presets
            self.update_ribbon_combo()
            self.status_bar.showMessage("리본 설정이 저장되었습니다.")
            
    def _toggle_auto_font_size(self, checked): 
        self.controls['경조사']['글자크기'].setEnabled(not checked)
        self.controls['보내는이']['글자크기'].setEnabled(not checked)
        self.preview.update()

    def sync_and_update(self, value):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setValue(value)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()
        
    def sync_and_update_combo(self, index):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setCurrentIndex(index)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()

    def get_config_for_side(self, side):
        config = {key: widget.value() if isinstance(widget, QSpinBox) else widget.currentText() for key, widget in self.controls[side].items()}
        config['text'] = self.text_right_edit.text() if side == "경조사" else self.text_left_edit.text()
        config['auto_font_size'] = self.auto_font_size_check.isChecked()
        return config

    def clear_all(self): self.status_bar.showMessage("새 리본 작업을 시작합니다.")
    def open_file(self): self.status_bar.showMessage("파일을 열었습니다.")
    def save_file(self): self.status_bar.showMessage("파일이 저장되었습니다.")
    def save_file_as(self): pass
    def show_help(self): QMessageBox.information(self, "도움말", "리본메이커 v8.9\n\n제작: 브릿지앱 전문가")
    def print_ribbon(self): self.status_bar.showMessage("인쇄 명령을 보냈습니다.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RibbonApp()
    window.show()
    sys.exit(app.exec())

import sys
import json
import win32print
import win32ui
from PIL import Image, ImageWin
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QFontComboBox, QSpinBox, 
    QGroupBox, QGridLayout, QFileDialog, QMessageBox, QCheckBox, QLineEdit,
    QStatusBar, QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPixmap, QTransform, QUndoStack, 
    QUndoCommand, QPen, QFontMetrics
)
from PyQt6.QtCore import Qt, QRectF

# --- 데이터 관리 ---
PRESETS_FILE = "ribbon_presets.json"
PHRASES_FILE = "phrases.json"
DEFAULT_PRESETS = {
    "꽃다발 38x400mm": {"리본넓이": 38, "레이스": 5, "리본길이": 400, "상단여백": 80, "하단여백": 50, "인쇄여백": 53},
    "동양란 45x450mm": {"리본넓이": 45, "레이스": 7, "리본길이": 450, "상단여백": 100, "하단여백": 50, "인쇄여백": 57},
    "동양란 50x500mm": {"리본넓이": 50, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 60},
    "동/서양란 55x500mm": {"리본넓이": 55, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 62},
    "서양란 60/65x700mm": {"리본넓이": 60, "레이스": 10, "리본길이": 700, "상단여백": 150, "하단여백": 100, "인쇄여백": 65},
    "영화(을) 70x750mm": {"리본넓이": 70, "레이스": 10, "리본길이": 750, "상단여백": 150, "하단여백": 100, "인쇄여백": 70},
    "장미바구니 95x1000mm": {"리본넓이": 95, "레이스": 10, "리본길이": 1000, "상단여백": 180, "하단여백": 130, "인쇄여백": 82},
    "화분 소 105/110x1100mm": {"리본넓이": 105, "레이스": 23, "리본길이": 1100, "상단여백": 200, "하단여백": 150, "인쇄여백": 87},
    "화분 중 135x1500mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1500, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "화분 대 150x1800mm": {"리본넓이": 150, "레이스": 23, "리본길이": 1800, "상단여백": 350, "하단여백": 350, "인쇄여백": 110},
    "근조 1단 115x1200mm": {"리본넓이": 115, "레이스": 23, "리본길이": 1200, "상단여백": 250, "하단여백": 150, "인쇄여백": 102},
    "근조 2단 135x1700mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1700, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "근조 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
    "축화환 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
}
DEFAULT_PHRASES = { "경조사": {"기본": ["祝開業"]}, "보내는이": {"기본": ["OOO 올림"]} }

def load_data(filename, default_data):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data

def save_presets(presets):
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, ensure_ascii=False, indent=4)

def get_font_for_char(char, config):
    if not char: return config.get('한글', '(한)마린_견궁서B')
    if '\uac00' <= char <= '\ud7a3': return config.get('한글', '(한)마린_견궁서B')
    elif '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf': return config.get('한자', '(한)마린_견궁서B')
    elif '\u0021' <= char <= '\u007e': return config.get('영문', '(한)마린_견궁서B')
    else: return config.get('기타 (외국어)', '(한)마린_견궁서B')

class RibbonSettingsDialog(QDialog):
    def __init__(self, presets_data, parent=None):
        super().__init__(parent)
        self.presets = presets_data.copy()
        self.setWindowTitle("리본 종류 설정")
        self.setMinimumSize(800, 400)
        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("프린터 모델:"))
        printer_combo = QComboBox()
        printer_combo.addItems(["Epson-M105"])
        top_layout.addWidget(printer_combo)
        top_layout.addStretch()
        add_btn = QPushButton("리본 추가")
        del_btn = QPushButton("리스트 삭제")
        add_btn.clicked.connect(self.add_row)
        del_btn.clicked.connect(self.remove_row)
        top_layout.addWidget(add_btn)
        top_layout.addWidget(del_btn)
        layout.addLayout(top_layout)
        self.table = QTableWidget()
        self.column_headers = ["리본이름", "넓이", "레이스", "길이", "상단", "하단", "여백"]
        self.table.setColumnCount(len(self.column_headers))
        self.table.setHorizontalHeaderLabels(self.column_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.populate_table()
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        save_btn = QPushButton("저장/종료")
        cancel_btn = QPushButton("취소")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(cancel_btn)
        layout.addLayout(bottom_layout)

    def populate_table(self):
        self.table.setRowCount(len(self.presets))
        key_map = {"리본넓이": "넓이", "레이스": "레이스", "리본길이": "길이", "상단여백": "상단", "하단여백": "하단", "인쇄여백": "여백"}
        for row, (name, data) in enumerate(self.presets.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            for key, col_name in key_map.items():
                if col_name in self.column_headers:
                    col_index = self.column_headers.index(col_name)
                    self.table.setItem(row, col_index, QTableWidgetItem(str(data.get(key, ''))))

    def add_row(self):
        self.table.insertRow(self.table.rowCount())

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row > -1: self.table.removeRow(current_row)

    def accept(self):
        new_presets = {}
        key_map_inv = {"넓이": "리본넓이", "레이스": "레이스", "길이": "리본길이", "상단": "상단여백", "하단": "하단여백", "여백": "인쇄여백"}
        for row in range(self.table.rowCount()):
            try:
                name_item = self.table.item(row, 0)
                if not name_item or not name_item.text(): continue
                name = name_item.text()
                data = {}
                for col in range(1, self.table.columnCount()):
                    header = self.column_headers[col]
                    key = key_map_inv.get(header)
                    item = self.table.item(row, col)
                    if key and item and item.text(): data[key] = int(item.text())
                new_presets[name] = data
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "입력 오류", f"{row+1}행에 잘못된 숫자 형식이 있습니다.")
                return
        self.presets = new_presets
        save_presets(self.presets)
        super().accept()

class RibbonPreviewWidget(QWidget):
    def __init__(self, app_instance):
        super().__init__(app_instance)
        self.app = app_instance
        self.setMinimumSize(500, 700)
        self.padding = 15

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(220, 220, 220))
        config_right = self.app.get_config_for_side('경조사')
        config_left = self.app.get_config_for_side('보내는이')
        total_original_width = config_right.get('리본넓이', 50) + config_left.get('리본넓이', 50) + 50
        max_original_length = max(config_right.get('리본길이', 400), config_left.get('리본길이', 400))
        if max_original_length <= 0 or total_original_width <= 0: return
        view_width = self.width() - self.padding * 2
        view_height = self.height() - self.padding * 2
        scale_w = view_width / total_original_width
        scale_h = view_height / max_original_length
        scale = min(scale_w, scale_h)
        scaled_width_right = config_right.get('리본넓이', 50) * scale
        scaled_width_left = config_left.get('리본넓이', 50) * scale
        scaled_spacing = 50 * scale
        scaled_height_right = config_right.get('리본길이', 400) * scale
        scaled_height_left = config_left.get('리본길이', 400) * scale
        total_scaled_width = scaled_width_right + scaled_width_left + scaled_spacing
        start_x = (self.width() - total_scaled_width) / 2
        start_y = (self.height() - max(scaled_height_right, scaled_height_left)) / 2
        rect_right = QRectF(start_x, start_y, scaled_width_right, scaled_height_right)
        rect_left = QRectF(start_x + scaled_width_right + scaled_spacing, start_y, scaled_width_left, scaled_height_left)
        self.draw_ruler(painter, rect_right, config_right.get('리본길이', 400), scale)
        self.draw_ruler(painter, rect_left, config_left.get('리본길이', 400), scale)
        painter.fillRect(rect_right, QColor("lightgray"))
        painter.fillRect(rect_left, QColor("lightgray"))
        self.draw_guidelines(painter, rect_right, config_right, scale)
        self.draw_guidelines(painter, rect_left, config_left, scale)
        self.render_side(painter, rect_right, config_right, scale)
        self.render_side(painter, rect_left, config_left, scale)
        self.draw_margins(painter, rect_right, config_right, scale)
        self.draw_margins(painter, rect_left, config_left, scale)
        painter.end()

    def draw_guidelines(self, painter, rect, config, scale):
        painter.save()
        center_pen = QPen(QColor(0, 0, 0, 100), 1, Qt.PenStyle.DashLine)
        painter.setPen(center_pen)
        center_x = rect.center().x()
        painter.drawLine(int(center_x), int(rect.top()), int(center_x), int(rect.bottom()))
        layer_pen = QPen(QColor(0, 0, 255, 120), 1, Qt.PenStyle.DashLine)
        painter.setPen(layer_pen)
        lace_margin = config.get('레이스', 5) * scale
        left_line_x = rect.left() + lace_margin
        right_line_x = rect.right() - lace_margin
        painter.drawLine(int(left_line_x), int(rect.top()), int(left_line_x), int(rect.bottom()))
        painter.drawLine(int(right_line_x), int(rect.top()), int(right_line_x), int(rect.bottom()))
        painter.restore()

    def draw_ruler(self, painter, rect, original_length, scale):
        painter.save()
        ruler_width = 25
        ruler_rect = QRectF(rect.left() - ruler_width, rect.top(), ruler_width, rect.height())
        if ruler_rect.left() < 0 :
             ruler_rect.moveTo(rect.right(), rect.top())
        painter.fillRect(ruler_rect, QColor(14, 209, 69))
        pen = QPen(QColor("white"), 1)
        painter.setPen(pen)
        font = QFont("Arial", 8)
        painter.setFont(font)
        for y_mm in range(0, original_length + 1, 10):
            y_pos = rect.top() + y_mm * scale
            if y_pos > rect.bottom(): break
            if y_mm % 50 == 0:
                painter.drawLine(int(ruler_rect.left() + 5), int(y_pos), int(ruler_rect.right()), int(y_pos))
                if y_mm % 100 == 0: painter.drawText(int(ruler_rect.left()+2), int(y_pos + 10), str(y_mm))
            else:
                painter.drawLine(int(ruler_rect.left() + 15), int(y_pos), int(ruler_rect.right()), int(y_pos))
        painter.restore()

    def draw_margins(self, painter, rect, config, scale):
        painter.save()
        pen = QPen(QColor(255, 0, 0, 150), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        top_margin_y = rect.top() + config.get('상단여백', 80) * scale
        bottom_margin_y = rect.bottom() - config.get('하단여백', 50) * scale
        painter.drawLine(int(rect.left()), int(top_margin_y), int(rect.right()), int(top_margin_y))
        painter.drawLine(int(rect.left()), int(bottom_margin_y), int(rect.right()), int(bottom_margin_y))
        painter.restore()

    def render_side(self, painter, rect, config, scale):
        painter.save()
        text = config.get('text', '')
        if not text or rect.width() <= 0:
            painter.restore()
            return
            
        blocks = []
        i = 0
        current_normal_block = ""
        while i < len(text):
            if text[i] == '[':
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                try:
                    end_index = text.index(']', i)
                    substr = text[i+1:end_index]
                    blocks.append({'type': 'shrink', 'text': substr}); i = end_index + 1
                except ValueError: current_normal_block += text[i]; i += 1
            elif text[i] == '(' and i + 2 < len(text) and text[i+2] == ')' and text[i+1] in ['주', '유', '株']:
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'special', 'text': text[i:i+3]}); i += 3
            elif text[i] == '/' and i > 0 and i < len(text) - 1:
                # "/" 앞뒤 글자를 2열로 배치
                left_char = text[i-1]
                right_char = text[i+1]
                # 이전 글자를 현재 블록에서 제거
                if current_normal_block and current_normal_block[-1] == left_char:
                    current_normal_block = current_normal_block[:-1]
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'two_column', 'left': left_char, 'right': right_char})
                i += 2  # "/" 다음 글자까지 건너뛰기
            else:
                current_normal_block += text[i]
                i += 1
        if current_normal_block:
            blocks.append({'type': 'normal', 'text': current_normal_block})
        
        base_font_size_pt = config.get('글자크기', 40)
        if config.get('auto_font_size', True):
            printable_width_px = (config.get('리본넓이', 50) - (config.get('레이스', 5) * 2)) * scale
            target_pixel_width = printable_width_px * 0.95
            if blocks and printable_width_px > 0:
                temp_font_size_pt = 150
                while temp_font_size_pt > 5:
                    max_char_width_px = 0
                    all_chars_in_blocks = ""
                    for b in blocks:
                        if b['type'] == 'two_column':
                            all_chars_in_blocks += b['left'] + b['right']
                        else:
                            all_chars_in_blocks += b['text']
                    for char in all_chars_in_blocks:
                        font = QFont(get_font_for_char(char, config))
                        font.setPixelSize(int(temp_font_size_pt * scale))
                        fm = QFontMetrics(font)
                        char_width = fm.horizontalAdvance(char) * (config.get('가로폰트', 100) / 100.0)
                        if char_width > max_char_width_px:
                            max_char_width_px = char_width
                    if max_char_width_px <= target_pixel_width:
                        base_font_size_pt = temp_font_size_pt
                        break
                    temp_font_size_pt -= 1

        printable_height = rect.height() - (config.get('상단여백', 80) + config.get('하단여백', 50)) * scale
        base_v_scale = config.get('세로폰트', 100) / 100.0
        
        total_uncompressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * len(block['text']) * base_v_scale
        
        final_v_scale = base_v_scale
        if total_uncompressed_height > printable_height and total_uncompressed_height > 0:
            compression_ratio = printable_height / total_uncompressed_height
            final_v_scale = base_v_scale * compression_ratio
        
        total_compressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * len(block['text']) * final_v_scale
        
        # 전체 글자 수 계산 (justify 배치를 위해)
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 1  # 2열은 1줄로 취급
            elif block['type'] == 'special':
                total_char_count += 1  # special도 1줄로 취급
            else:
                total_char_count += len(block['text'])
        
        # 하단정렬: 하단여백선 위에서 전체 글자 높이만큼 위로 올라가서 시작
        bottom_margin = config.get('하단여백', 50) * scale
        
        # 전체 글자 수 계산
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 2  # 2열은 2글자
            elif block['type'] == 'special':
                total_char_count += len(block['text'])  # special도 글자수만큼
            else:
                total_char_count += len(block['text'])
        
        # 평균 글자 높이로 전체 높이 추정
        temp_font = QFont(get_font_for_char('가', config))
        temp_font.setPixelSize(int(base_font_size_pt * scale))
        temp_fm = QFontMetrics(temp_font)
        avg_char_height = temp_fm.height() * final_v_scale
        total_text_height = total_char_count * avg_char_height
        
        # 하단여백선에서 전체 텍스트 높이만큼 위로 올라간 지점에서 시작
        bottom_y = rect.bottom() - bottom_margin
        current_y = bottom_y - total_text_height
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치 처리
                left_char = block['left']
                right_char = block['right']
                
                for i, char in enumerate([left_char, right_char]):
                    size_ratio = 1.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)

                    char_width = fm.horizontalAdvance(char)
                    scaled_char_width = char_width * h_scale
                    
                    # 왼쪽 글자는 왼쪽에, 오른쪽 글자는 오른쪽에 배치
                    if i == 0:  # 왼쪽 글자
                        char_x = rect.center().x() - scaled_char_width
                    else:  # 오른쪽 글자
                        char_x = rect.center().x()
                    
                    # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    
                    painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                    # 다음 글자 위치로 이동
                    current_y += fm.height() * final_v_scale
                
            elif block['type'] == 'special':
                # (주), (유), (株) 가로 배치 처리
                special_text = block['text']  # 예: "(주)"
                size_ratio = config.get('(주)/(株)', 90) / 100.0
                scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                if scaled_font_size_px <= 0: scaled_font_size_px = 1
                
                # 전체 텍스트의 폭 계산
                total_width = 0
                char_widths = []
                for char in special_text:
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    fm = QFontMetrics(font)
                    char_width = fm.horizontalAdvance(char)
                    char_widths.append(char_width)
                    total_width += char_width
                
                h_scale = config.get('가로폰트', 100) / 100.0 * 0.8  # 80% 가로 축소
                v_scale = final_v_scale
                
                # 중앙 정렬을 위한 시작 x 좌표
                start_x = rect.center().x() - (total_width * h_scale) / 2
                
                # 각 글자를 가로로 배치
                current_x = start_x
                for i, char in enumerate(special_text):
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)
                    
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    painter.drawText(int(current_x / h_scale), int(char_y_pos / v_scale), char)
                    current_x += char_widths[i] * h_scale
                
                # special 블록 전체 처리 후 다음 위치로 이동
                current_y += fm.height() * final_v_scale
                
            else:
                # 일반 텍스트 블록 - justify 배치 적용
                block_text = block['text']
                
                for char in block_text:
                    size_ratio = 1.0
                    if block['type'] == 'shrink': size_ratio = config.get('축소폰트', 70) / 100.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                
                transform = QTransform().scale(h_scale, v_scale)
                painter.setTransform(transform)

                char_width = fm.horizontalAdvance(char)
                scaled_char_width = char_width * h_scale
                
                char_x = rect.center().x() - (scaled_char_width / 2)
                
                # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                char_y_pos = current_y + fm.ascent() * final_v_scale
            
                painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                # 다음 글자 위치로 이동
                current_y += fm.height() * final_v_scale
        painter.restore()

class RibbonApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RibbonMaker - Ribbon Editor (v8.9 최종판)")
        self.setGeometry(50, 50, 1200, 850)
        self.undo_stack = QUndoStack(self)
        self.controls = {'경조사': {}, '보내는이': {}}
        self.phrase_indices = {"경조사": {}, "보내는이": {}}
        self.presets = load_data(PRESETS_FILE, DEFAULT_PRESETS)
        self.phrases = load_data(PHRASES_FILE, DEFAULT_PHRASES)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        self.preview = RibbonPreviewWidget(self)
        main_layout.addWidget(self.preview)
        self.setStatusBar(QStatusBar(self))
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("프로그램 준비 완료.")
        self._connect_signals()
        self.update_ribbon_combo()
        self.update_phrase_categories()
        self._toggle_auto_font_size(True)

    def _create_control_panel(self):
        panel = QWidget()
        panel.setFixedWidth(550)
        top_layout = QVBoxLayout(panel)
        menu_layout = self._create_menu_buttons()
        top_layout.addLayout(menu_layout)
        content_group = self._create_content_inputs()
        top_layout.addWidget(content_group)
        main_grid = self._create_main_grid()
        top_layout.addLayout(main_grid)
        font_group = self._create_font_selectors()
        top_layout.addWidget(font_group)
        env_group = QGroupBox("환경설정")
        env_layout = QHBoxLayout(env_group)
        self.settings_button = QPushButton("리본 설정...")
        self.settings_button.clicked.connect(self.open_ribbon_settings)
        env_layout.addWidget(self.settings_button)
        env_group.setFixedHeight(60)
        top_layout.addWidget(env_group)
        top_layout.addStretch(1)
        return panel
    
    def _create_main_grid(self):
        main_grid = QGridLayout()
        main_grid.setSpacing(5)
        main_grid.addWidget(QLabel("리본종류"), 0, 0)
        self.ribbon_type_combo = QComboBox()
        self.ribbon_type_combo.setMaxVisibleItems(20)  # 최대 20개 항목까지 표시
        self.ribbon_type_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        main_grid.addWidget(self.ribbon_type_combo, 0, 1, 1, 2)
        self.sync_check = QCheckBox("동시적용")
        self.sync_check.setChecked(True)
        main_grid.addWidget(self.sync_check, 0, 3)
        main_grid.addWidget(QLabel("되돌리기"), 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)
        undo_btn = QPushButton("<"); undo_btn.setFixedSize(30,25)
        redo_btn = QPushButton(">"); redo_btn.setFixedSize(30,25)
        undo_btn.clicked.connect(self.undo_stack.undo)
        redo_btn.clicked.connect(self.undo_stack.redo)
        main_grid.addWidget(undo_btn, 0, 5)
        main_grid.addWidget(redo_btn, 0, 6)
        all_fields = ["리본넓이", "레이스", "리본길이", "상단여백", "하단여백", "인쇄여백", "글자크기", "가로폰트", "세로폰트", "축소폰트", "(주)/(株)", "폰트컬러"]
        main_grid.addWidget(QLabel("경조사 설정"), 1, 1, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        main_grid.addWidget(QLabel("보내는이 설정"), 1, 4, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        for i, text in enumerate(all_fields, 2):
            main_grid.addWidget(QLabel(text), i, 0, alignment=Qt.AlignmentFlag.AlignRight)
            for j, side in enumerate(["경조사", "보내는이"]):
                widget = QSpinBox()
                if text == "(주)/(株)":
                    widget.setRange(10, 100); widget.setValue(90); widget.setSuffix('%')
                elif text == "축소폰트":
                    widget.setRange(10, 100); widget.setValue(70); widget.setSuffix('%')
                else:
                    widget.setRange(0, 5000)
                    if text in ["가로폰트", "세로폰트"]: widget.setValue(100)
                    elif text == "글자크기": widget.setValue(40)
                self.controls[side][text] = widget
                main_grid.addWidget(widget, i, 1 + j*3, 1, 2)
        for j, side in enumerate(["경조사", "보내는이"]):
            main_grid.addWidget(QPushButton("그림넣기"), len(all_fields)+2, 1 + j*3)
            main_grid.addWidget(QPushButton("그림수정"), len(all_fields)+2, 2 + j*3)
        return main_grid

    def _create_font_selectors(self):
        group = QGroupBox("서체 설정")
        layout = QGridLayout(group)
        self.auto_font_size_check = QCheckBox("글자 폭 자동 맞춤")
        self.auto_font_size_check.setChecked(True)
        layout.addWidget(self.auto_font_size_check, 0, 0, 1, 2)
        font_types = ["한글", "한자", "영문", "기타 (외국어)"]
        for i, side in enumerate(["경조사", "보내는이"]):
            layout.addWidget(QLabel(f"{side} 서체"), 1, i * 2, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            for j, ftype in enumerate(font_types, 2):
                layout.addWidget(QLabel(ftype), j, i * 2)
                combo = QFontComboBox()
                self.controls[side][ftype] = combo
                layout.addWidget(combo, j, i * 2 + 1)
        return group
    
    def _create_menu_buttons(self):
        menu_layout = QHBoxLayout()
        actions = {"새리본": self.clear_all, "파일열기": self.open_file, "저장": self.save_file,"새로저장": self.save_file_as, "도움말": self.show_help, "인쇄": self.print_ribbon}
        for text, action in actions.items():
            button = QPushButton(text); button.clicked.connect(action); menu_layout.addWidget(button)
        return menu_layout

    def _create_content_inputs(self):
        group = QGroupBox("내용 입력")
        grid = QGridLayout(group)
        self.text_right_edit = QLineEdit("祝開業")
        self.text_left_edit = QLineEdit("대표이사(주)홍길동")
        self.phrase_category_right = QComboBox()
        self.phrase_category_left = QComboBox()
        for i, (side, widget, category_combo) in enumerate([("경조사", self.text_right_edit, self.phrase_category_right), ("보내는이", self.text_left_edit, self.phrase_category_left)]):
            grid.addWidget(QLabel(side), i*2, 0)
            grid.addWidget(widget, i*2, 1)
            btn_layout = QHBoxLayout()
            for btn_text in ['+', '-', 'x']:
                btn = QPushButton(btn_text); btn.setFixedSize(25, 25)
                btn.clicked.connect(lambda _, s=side, op=btn_text: self.cycle_phrase(s, op))
                btn_layout.addWidget(btn)
            grid.addLayout(btn_layout, i*2, 2)
            grid.addWidget(QLabel("샘플 선택"), i*2 + 1, 0)
            grid.addWidget(category_combo, i*2 + 1, 1)
        return group
    
    def _connect_signals(self):
        self.ribbon_type_combo.currentTextChanged.connect(self.update_spins_from_preset)
        self.phrase_category_right.currentTextChanged.connect(lambda: self.reset_phrase_index('경조사'))
        self.phrase_category_left.currentTextChanged.connect(lambda: self.reset_phrase_index('보내는이'))
        self.auto_font_size_check.toggled.connect(self._toggle_auto_font_size)
        for side in self.controls:
            for control in self.controls[side].values():
                if isinstance(control, QSpinBox): control.valueChanged.connect(self.sync_and_update)
                else: control.currentIndexChanged.connect(self.sync_and_update_combo)
        self.text_right_edit.textChanged.connect(self.preview.update)
        self.text_left_edit.textChanged.connect(self.preview.update)

    def update_ribbon_combo(self):
        current_selection = self.ribbon_type_combo.currentText()
        self.ribbon_type_combo.blockSignals(True)
        self.ribbon_type_combo.clear()
        self.ribbon_type_combo.addItems(self.presets.keys())
        index = self.ribbon_type_combo.findText(current_selection)
        if index != -1: self.ribbon_type_combo.setCurrentIndex(index)
        self.ribbon_type_combo.blockSignals(False)
        self.update_spins_from_preset(self.ribbon_type_combo.currentText())

    def update_spins_from_preset(self, ribbon_name):
        data = self.presets.get(ribbon_name)
        if data:
            for side in self.controls:
                for key, widget in self.controls[side].items():
                    if key in data:
                        if isinstance(widget, QSpinBox):
                            widget.blockSignals(True)
                            widget.setValue(data[key])
                            widget.blockSignals(False)
        self.preview.update()

    def update_phrase_categories(self):
        self.phrase_category_right.blockSignals(True)
        self.phrase_category_left.blockSignals(True)
        self.phrase_category_right.clear()
        self.phrase_category_left.clear()
        if "경조사" in self.phrases:
            self.phrase_category_right.addItems(self.phrases["경조사"].keys())
        if "보내는이" in self.phrases:
            self.phrase_category_left.addItems(self.phrases["보내는이"].keys())
        self.phrase_category_right.blockSignals(False)
        self.phrase_category_left.blockSignals(False)
        self.reset_phrase_index('경조사')
        self.reset_phrase_index('보내는이')

    def reset_phrase_index(self, side):
        category_combo = self.phrase_category_right if side == '경조사' else self.phrase_category_left
        category = category_combo.currentText()
        if category:
            self.phrase_indices[side][category] = 0

    def cycle_phrase(self, side, op):
        widget = self.text_right_edit if side == "경조사" else self.text_left_edit
        category_combo = self.phrase_category_right if side == "경조사" else self.phrase_category_left
        category = category_combo.currentText()
        if not category or side not in self.phrases or category not in self.phrases[side]: return
        phrase_list = self.phrases[side][category]
        if not phrase_list: return
        current_index = self.phrase_indices[side].get(category, 0)
        if op == '+': current_index = (current_index + 1) % len(phrase_list)
        elif op == '-': current_index = (current_index - 1 + len(phrase_list)) % len(phrase_list)
        self.phrase_indices[side][category] = current_index
        widget.setText(phrase_list[current_index])
    
    def open_ribbon_settings(self):
        dialog = RibbonSettingsDialog(self.presets, self)
        if dialog.exec():
            self.presets = dialog.presets
            self.update_ribbon_combo()
            self.status_bar.showMessage("리본 설정이 저장되었습니다.")
            
    def _toggle_auto_font_size(self, checked): 
        self.controls['경조사']['글자크기'].setEnabled(not checked)
        self.controls['보내는이']['글자크기'].setEnabled(not checked)
        self.preview.update()

    def sync_and_update(self, value):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setValue(value)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()
        
    def sync_and_update_combo(self, index):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setCurrentIndex(index)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()

    def get_config_for_side(self, side):
        config = {key: widget.value() if isinstance(widget, QSpinBox) else widget.currentText() for key, widget in self.controls[side].items()}
        config['text'] = self.text_right_edit.text() if side == "경조사" else self.text_left_edit.text()
        config['auto_font_size'] = self.auto_font_size_check.isChecked()
        return config

    def clear_all(self): self.status_bar.showMessage("새 리본 작업을 시작합니다.")
    def open_file(self): self.status_bar.showMessage("파일을 열었습니다.")
    def save_file(self): self.status_bar.showMessage("파일이 저장되었습니다.")
    def save_file_as(self): pass
    def show_help(self): QMessageBox.information(self, "도움말", "리본메이커 v8.9\n\n제작: 브릿지앱 전문가")
    def print_ribbon(self): self.status_bar.showMessage("인쇄 명령을 보냈습니다.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RibbonApp()
    window.show()
    sys.exit(app.exec())

import sys
import json
import win32print
import win32ui
from PIL import Image, ImageWin
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QFontComboBox, QSpinBox, 
    QGroupBox, QGridLayout, QFileDialog, QMessageBox, QCheckBox, QLineEdit,
    QStatusBar, QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPixmap, QTransform, QUndoStack, 
    QUndoCommand, QPen, QFontMetrics
)
from PyQt6.QtCore import Qt, QRectF

# --- 데이터 관리 ---
PRESETS_FILE = "ribbon_presets.json"
PHRASES_FILE = "phrases.json"
DEFAULT_PRESETS = {
    "꽃다발 38x400mm": {"리본넓이": 38, "레이스": 5, "리본길이": 400, "상단여백": 80, "하단여백": 50, "인쇄여백": 53},
    "동양란 45x450mm": {"리본넓이": 45, "레이스": 7, "리본길이": 450, "상단여백": 100, "하단여백": 50, "인쇄여백": 57},
    "동양란 50x500mm": {"리본넓이": 50, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 60},
    "동/서양란 55x500mm": {"리본넓이": 55, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 62},
    "서양란 60/65x700mm": {"리본넓이": 60, "레이스": 10, "리본길이": 700, "상단여백": 150, "하단여백": 100, "인쇄여백": 65},
    "영화(을) 70x750mm": {"리본넓이": 70, "레이스": 10, "리본길이": 750, "상단여백": 150, "하단여백": 100, "인쇄여백": 70},
    "장미바구니 95x1000mm": {"리본넓이": 95, "레이스": 10, "리본길이": 1000, "상단여백": 180, "하단여백": 130, "인쇄여백": 82},
    "화분 소 105/110x1100mm": {"리본넓이": 105, "레이스": 23, "리본길이": 1100, "상단여백": 200, "하단여백": 150, "인쇄여백": 87},
    "화분 중 135x1500mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1500, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "화분 대 150x1800mm": {"리본넓이": 150, "레이스": 23, "리본길이": 1800, "상단여백": 350, "하단여백": 350, "인쇄여백": 110},
    "근조 1단 115x1200mm": {"리본넓이": 115, "레이스": 23, "리본길이": 1200, "상단여백": 250, "하단여백": 150, "인쇄여백": 102},
    "근조 2단 135x1700mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1700, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "근조 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
    "축화환 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
}
DEFAULT_PHRASES = { "경조사": {"기본": ["祝開業"]}, "보내는이": {"기본": ["OOO 올림"]} }

def load_data(filename, default_data):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data

def save_presets(presets):
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, ensure_ascii=False, indent=4)

def get_font_for_char(char, config):
    if not char: return config.get('한글', '(한)마린_견궁서B')
    if '\uac00' <= char <= '\ud7a3': return config.get('한글', '(한)마린_견궁서B')
    elif '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf': return config.get('한자', '(한)마린_견궁서B')
    elif '\u0021' <= char <= '\u007e': return config.get('영문', '(한)마린_견궁서B')
    else: return config.get('기타 (외국어)', '(한)마린_견궁서B')

class RibbonSettingsDialog(QDialog):
    def __init__(self, presets_data, parent=None):
        super().__init__(parent)
        self.presets = presets_data.copy()
        self.setWindowTitle("리본 종류 설정")
        self.setMinimumSize(800, 400)
        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("프린터 모델:"))
        printer_combo = QComboBox()
        printer_combo.addItems(["Epson-M105"])
        top_layout.addWidget(printer_combo)
        top_layout.addStretch()
        add_btn = QPushButton("리본 추가")
        del_btn = QPushButton("리스트 삭제")
        add_btn.clicked.connect(self.add_row)
        del_btn.clicked.connect(self.remove_row)
        top_layout.addWidget(add_btn)
        top_layout.addWidget(del_btn)
        layout.addLayout(top_layout)
        self.table = QTableWidget()
        self.column_headers = ["리본이름", "넓이", "레이스", "길이", "상단", "하단", "여백"]
        self.table.setColumnCount(len(self.column_headers))
        self.table.setHorizontalHeaderLabels(self.column_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.populate_table()
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        save_btn = QPushButton("저장/종료")
        cancel_btn = QPushButton("취소")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(cancel_btn)
        layout.addLayout(bottom_layout)

    def populate_table(self):
        self.table.setRowCount(len(self.presets))
        key_map = {"리본넓이": "넓이", "레이스": "레이스", "리본길이": "길이", "상단여백": "상단", "하단여백": "하단", "인쇄여백": "여백"}
        for row, (name, data) in enumerate(self.presets.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            for key, col_name in key_map.items():
                if col_name in self.column_headers:
                    col_index = self.column_headers.index(col_name)
                    self.table.setItem(row, col_index, QTableWidgetItem(str(data.get(key, ''))))

    def add_row(self):
        self.table.insertRow(self.table.rowCount())

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row > -1: self.table.removeRow(current_row)

    def accept(self):
        new_presets = {}
        key_map_inv = {"넓이": "리본넓이", "레이스": "레이스", "길이": "리본길이", "상단": "상단여백", "하단": "하단여백", "여백": "인쇄여백"}
        for row in range(self.table.rowCount()):
            try:
                name_item = self.table.item(row, 0)
                if not name_item or not name_item.text(): continue
                name = name_item.text()
                data = {}
                for col in range(1, self.table.columnCount()):
                    header = self.column_headers[col]
                    key = key_map_inv.get(header)
                    item = self.table.item(row, col)
                    if key and item and item.text(): data[key] = int(item.text())
                new_presets[name] = data
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "입력 오류", f"{row+1}행에 잘못된 숫자 형식이 있습니다.")
                return
        self.presets = new_presets
        save_presets(self.presets)
        super().accept()

class RibbonPreviewWidget(QWidget):
    def __init__(self, app_instance):
        super().__init__(app_instance)
        self.app = app_instance
        self.setMinimumSize(500, 700)
        self.padding = 15

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(220, 220, 220))
        config_right = self.app.get_config_for_side('경조사')
        config_left = self.app.get_config_for_side('보내는이')
        total_original_width = config_right.get('리본넓이', 50) + config_left.get('리본넓이', 50) + 50
        max_original_length = max(config_right.get('리본길이', 400), config_left.get('리본길이', 400))
        if max_original_length <= 0 or total_original_width <= 0: return
        view_width = self.width() - self.padding * 2
        view_height = self.height() - self.padding * 2
        scale_w = view_width / total_original_width
        scale_h = view_height / max_original_length
        scale = min(scale_w, scale_h)
        scaled_width_right = config_right.get('리본넓이', 50) * scale
        scaled_width_left = config_left.get('리본넓이', 50) * scale
        scaled_spacing = 50 * scale
        scaled_height_right = config_right.get('리본길이', 400) * scale
        scaled_height_left = config_left.get('리본길이', 400) * scale
        total_scaled_width = scaled_width_right + scaled_width_left + scaled_spacing
        start_x = (self.width() - total_scaled_width) / 2
        start_y = (self.height() - max(scaled_height_right, scaled_height_left)) / 2
        rect_right = QRectF(start_x, start_y, scaled_width_right, scaled_height_right)
        rect_left = QRectF(start_x + scaled_width_right + scaled_spacing, start_y, scaled_width_left, scaled_height_left)
        self.draw_ruler(painter, rect_right, config_right.get('리본길이', 400), scale)
        self.draw_ruler(painter, rect_left, config_left.get('리본길이', 400), scale)
        painter.fillRect(rect_right, QColor("lightgray"))
        painter.fillRect(rect_left, QColor("lightgray"))
        self.draw_guidelines(painter, rect_right, config_right, scale)
        self.draw_guidelines(painter, rect_left, config_left, scale)
        self.render_side(painter, rect_right, config_right, scale)
        self.render_side(painter, rect_left, config_left, scale)
        self.draw_margins(painter, rect_right, config_right, scale)
        self.draw_margins(painter, rect_left, config_left, scale)
        painter.end()

    def draw_guidelines(self, painter, rect, config, scale):
        painter.save()
        center_pen = QPen(QColor(0, 0, 0, 100), 1, Qt.PenStyle.DashLine)
        painter.setPen(center_pen)
        center_x = rect.center().x()
        painter.drawLine(int(center_x), int(rect.top()), int(center_x), int(rect.bottom()))
        layer_pen = QPen(QColor(0, 0, 255, 120), 1, Qt.PenStyle.DashLine)
        painter.setPen(layer_pen)
        lace_margin = config.get('레이스', 5) * scale
        left_line_x = rect.left() + lace_margin
        right_line_x = rect.right() - lace_margin
        painter.drawLine(int(left_line_x), int(rect.top()), int(left_line_x), int(rect.bottom()))
        painter.drawLine(int(right_line_x), int(rect.top()), int(right_line_x), int(rect.bottom()))
        painter.restore()

    def draw_ruler(self, painter, rect, original_length, scale):
        painter.save()
        ruler_width = 25
        ruler_rect = QRectF(rect.left() - ruler_width, rect.top(), ruler_width, rect.height())
        if ruler_rect.left() < 0 :
             ruler_rect.moveTo(rect.right(), rect.top())
        painter.fillRect(ruler_rect, QColor(14, 209, 69))
        pen = QPen(QColor("white"), 1)
        painter.setPen(pen)
        font = QFont("Arial", 8)
        painter.setFont(font)
        for y_mm in range(0, original_length + 1, 10):
            y_pos = rect.top() + y_mm * scale
            if y_pos > rect.bottom(): break
            if y_mm % 50 == 0:
                painter.drawLine(int(ruler_rect.left() + 5), int(y_pos), int(ruler_rect.right()), int(y_pos))
                if y_mm % 100 == 0: painter.drawText(int(ruler_rect.left()+2), int(y_pos + 10), str(y_mm))
            else:
                painter.drawLine(int(ruler_rect.left() + 15), int(y_pos), int(ruler_rect.right()), int(y_pos))
        painter.restore()

    def draw_margins(self, painter, rect, config, scale):
        painter.save()
        pen = QPen(QColor(255, 0, 0, 150), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        top_margin_y = rect.top() + config.get('상단여백', 80) * scale
        bottom_margin_y = rect.bottom() - config.get('하단여백', 50) * scale
        painter.drawLine(int(rect.left()), int(top_margin_y), int(rect.right()), int(top_margin_y))
        painter.drawLine(int(rect.left()), int(bottom_margin_y), int(rect.right()), int(bottom_margin_y))
        painter.restore()

    def render_side(self, painter, rect, config, scale):
        painter.save()
        text = config.get('text', '')
        if not text or rect.width() <= 0:
            painter.restore()
            return
            
        blocks = []
        i = 0
        current_normal_block = ""
        while i < len(text):
            if text[i] == '[':
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                try:
                    end_index = text.index(']', i)
                    substr = text[i+1:end_index]
                    blocks.append({'type': 'shrink', 'text': substr}); i = end_index + 1
                except ValueError: current_normal_block += text[i]; i += 1
            elif text[i] == '(' and i + 2 < len(text) and text[i+2] == ')' and text[i+1] in ['주', '유', '株']:
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'special', 'text': text[i:i+3]}); i += 3
            elif text[i] == '/' and i > 0 and i < len(text) - 1:
                # "/" 앞뒤 글자를 2열로 배치
                left_char = text[i-1]
                right_char = text[i+1]
                # 이전 글자를 현재 블록에서 제거
                if current_normal_block and current_normal_block[-1] == left_char:
                    current_normal_block = current_normal_block[:-1]
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'two_column', 'left': left_char, 'right': right_char})
                i += 2  # "/" 다음 글자까지 건너뛰기
            else:
                current_normal_block += text[i]
                i += 1
        if current_normal_block:
            blocks.append({'type': 'normal', 'text': current_normal_block})
        
        base_font_size_pt = config.get('글자크기', 40)
        if config.get('auto_font_size', True):
            printable_width_px = (config.get('리본넓이', 50) - (config.get('레이스', 5) * 2)) * scale
            target_pixel_width = printable_width_px * 0.95
            if blocks and printable_width_px > 0:
                temp_font_size_pt = 150
                while temp_font_size_pt > 5:
                    max_char_width_px = 0
                    all_chars_in_blocks = ""
                    for b in blocks:
                        if b['type'] == 'two_column':
                            all_chars_in_blocks += b['left'] + b['right']
                        else:
                            all_chars_in_blocks += b['text']
                    for char in all_chars_in_blocks:
                        font = QFont(get_font_for_char(char, config))
                        font.setPixelSize(int(temp_font_size_pt * scale))
                        fm = QFontMetrics(font)
                        char_width = fm.horizontalAdvance(char) * (config.get('가로폰트', 100) / 100.0)
                        if char_width > max_char_width_px:
                            max_char_width_px = char_width
                    if max_char_width_px <= target_pixel_width:
                        base_font_size_pt = temp_font_size_pt
                        break
                    temp_font_size_pt -= 1

        printable_height = rect.height() - (config.get('상단여백', 80) + config.get('하단여백', 50)) * scale
        base_v_scale = config.get('세로폰트', 100) / 100.0
        
        total_uncompressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * len(block['text']) * base_v_scale
        
        final_v_scale = base_v_scale
        if total_uncompressed_height > printable_height and total_uncompressed_height > 0:
            compression_ratio = printable_height / total_uncompressed_height
            final_v_scale = base_v_scale * compression_ratio
        
        total_compressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * len(block['text']) * final_v_scale
        
        # 전체 글자 수 계산 (justify 배치를 위해)
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 1  # 2열은 1줄로 취급
            elif block['type'] == 'special':
                total_char_count += 1  # special도 1줄로 취급
            else:
                total_char_count += len(block['text'])
        
        # 하단정렬: 하단여백선 위에서 전체 글자 높이만큼 위로 올라가서 시작
        bottom_margin = config.get('하단여백', 50) * scale
        
        # 전체 글자 수 계산
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 2  # 2열은 2글자
            elif block['type'] == 'special':
                total_char_count += len(block['text'])  # special도 글자수만큼
            else:
                total_char_count += len(block['text'])
        
        # 평균 글자 높이로 전체 높이 추정
        temp_font = QFont(get_font_for_char('가', config))
        temp_font.setPixelSize(int(base_font_size_pt * scale))
        temp_fm = QFontMetrics(temp_font)
        avg_char_height = temp_fm.height() * final_v_scale
        total_text_height = total_char_count * avg_char_height
        
        # 하단여백선에서 전체 텍스트 높이만큼 위로 올라간 지점에서 시작
        bottom_y = rect.bottom() - bottom_margin
        current_y = bottom_y - total_text_height
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치 처리
                left_char = block['left']
                right_char = block['right']
                
                for i, char in enumerate([left_char, right_char]):
                    size_ratio = 1.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)

                    char_width = fm.horizontalAdvance(char)
                    scaled_char_width = char_width * h_scale
                    
                    # 왼쪽 글자는 왼쪽에, 오른쪽 글자는 오른쪽에 배치
                    if i == 0:  # 왼쪽 글자
                        char_x = rect.center().x() - scaled_char_width
                    else:  # 오른쪽 글자
                        char_x = rect.center().x()
                    
                    # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    
                    painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                    # 다음 글자 위치로 이동
                    current_y += fm.height() * final_v_scale
                
            elif block['type'] == 'special':
                # (주), (유), (株) 가로 배치 처리
                special_text = block['text']  # 예: "(주)"
                size_ratio = config.get('(주)/(株)', 90) / 100.0
                scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                if scaled_font_size_px <= 0: scaled_font_size_px = 1
                
                # 전체 텍스트의 폭 계산
                total_width = 0
                char_widths = []
                for char in special_text:
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    fm = QFontMetrics(font)
                    char_width = fm.horizontalAdvance(char)
                    char_widths.append(char_width)
                    total_width += char_width
                
                h_scale = config.get('가로폰트', 100) / 100.0 * 0.8  # 80% 가로 축소
                v_scale = final_v_scale
                
                # 중앙 정렬을 위한 시작 x 좌표
                start_x = rect.center().x() - (total_width * h_scale) / 2
                
                # 각 글자를 가로로 배치
                current_x = start_x
                for i, char in enumerate(special_text):
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)
                    
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    painter.drawText(int(current_x / h_scale), int(char_y_pos / v_scale), char)
                    current_x += char_widths[i] * h_scale
                
                # special 블록 전체 처리 후 다음 위치로 이동
                current_y += fm.height() * final_v_scale
                
            else:
                # 일반 텍스트 블록 - justify 배치 적용
                block_text = block['text']
                
                for char in block_text:
                    size_ratio = 1.0
                    if block['type'] == 'shrink': size_ratio = config.get('축소폰트', 70) / 100.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                
                transform = QTransform().scale(h_scale, v_scale)
                painter.setTransform(transform)

                char_width = fm.horizontalAdvance(char)
                scaled_char_width = char_width * h_scale
                
                char_x = rect.center().x() - (scaled_char_width / 2)
                
                # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                char_y_pos = current_y + fm.ascent() * final_v_scale
            
                painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                # 다음 글자 위치로 이동
                current_y += fm.height() * final_v_scale
        painter.restore()

class RibbonApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RibbonMaker - Ribbon Editor (v8.9 최종판)")
        self.setGeometry(50, 50, 1200, 850)
        self.undo_stack = QUndoStack(self)
        self.controls = {'경조사': {}, '보내는이': {}}
        self.phrase_indices = {"경조사": {}, "보내는이": {}}
        self.presets = load_data(PRESETS_FILE, DEFAULT_PRESETS)
        self.phrases = load_data(PHRASES_FILE, DEFAULT_PHRASES)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        self.preview = RibbonPreviewWidget(self)
        main_layout.addWidget(self.preview)
        self.setStatusBar(QStatusBar(self))
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("프로그램 준비 완료.")
        self._connect_signals()
        self.update_ribbon_combo()
        self.update_phrase_categories()
        self._toggle_auto_font_size(True)

    def _create_control_panel(self):
        panel = QWidget()
        panel.setFixedWidth(550)
        top_layout = QVBoxLayout(panel)
        menu_layout = self._create_menu_buttons()
        top_layout.addLayout(menu_layout)
        content_group = self._create_content_inputs()
        top_layout.addWidget(content_group)
        main_grid = self._create_main_grid()
        top_layout.addLayout(main_grid)
        font_group = self._create_font_selectors()
        top_layout.addWidget(font_group)
        env_group = QGroupBox("환경설정")
        env_layout = QHBoxLayout(env_group)
        self.settings_button = QPushButton("리본 설정...")
        self.settings_button.clicked.connect(self.open_ribbon_settings)
        env_layout.addWidget(self.settings_button)
        env_group.setFixedHeight(60)
        top_layout.addWidget(env_group)
        top_layout.addStretch(1)
        return panel
    
    def _create_main_grid(self):
        main_grid = QGridLayout()
        main_grid.setSpacing(5)
        main_grid.addWidget(QLabel("리본종류"), 0, 0)
        self.ribbon_type_combo = QComboBox()
        self.ribbon_type_combo.setMaxVisibleItems(20)  # 최대 20개 항목까지 표시
        self.ribbon_type_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        main_grid.addWidget(self.ribbon_type_combo, 0, 1, 1, 2)
        self.sync_check = QCheckBox("동시적용")
        self.sync_check.setChecked(True)
        main_grid.addWidget(self.sync_check, 0, 3)
        main_grid.addWidget(QLabel("되돌리기"), 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)
        undo_btn = QPushButton("<"); undo_btn.setFixedSize(30,25)
        redo_btn = QPushButton(">"); redo_btn.setFixedSize(30,25)
        undo_btn.clicked.connect(self.undo_stack.undo)
        redo_btn.clicked.connect(self.undo_stack.redo)
        main_grid.addWidget(undo_btn, 0, 5)
        main_grid.addWidget(redo_btn, 0, 6)
        all_fields = ["리본넓이", "레이스", "리본길이", "상단여백", "하단여백", "인쇄여백", "글자크기", "가로폰트", "세로폰트", "축소폰트", "(주)/(株)", "폰트컬러"]
        main_grid.addWidget(QLabel("경조사 설정"), 1, 1, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        main_grid.addWidget(QLabel("보내는이 설정"), 1, 4, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        for i, text in enumerate(all_fields, 2):
            main_grid.addWidget(QLabel(text), i, 0, alignment=Qt.AlignmentFlag.AlignRight)
            for j, side in enumerate(["경조사", "보내는이"]):
                widget = QSpinBox()
                if text == "(주)/(株)":
                    widget.setRange(10, 100); widget.setValue(90); widget.setSuffix('%')
                elif text == "축소폰트":
                    widget.setRange(10, 100); widget.setValue(70); widget.setSuffix('%')
                else:
                    widget.setRange(0, 5000)
                    if text in ["가로폰트", "세로폰트"]: widget.setValue(100)
                    elif text == "글자크기": widget.setValue(40)
                self.controls[side][text] = widget
                main_grid.addWidget(widget, i, 1 + j*3, 1, 2)
        for j, side in enumerate(["경조사", "보내는이"]):
            main_grid.addWidget(QPushButton("그림넣기"), len(all_fields)+2, 1 + j*3)
            main_grid.addWidget(QPushButton("그림수정"), len(all_fields)+2, 2 + j*3)
        return main_grid

    def _create_font_selectors(self):
        group = QGroupBox("서체 설정")
        layout = QGridLayout(group)
        self.auto_font_size_check = QCheckBox("글자 폭 자동 맞춤")
        self.auto_font_size_check.setChecked(True)
        layout.addWidget(self.auto_font_size_check, 0, 0, 1, 2)
        font_types = ["한글", "한자", "영문", "기타 (외국어)"]
        for i, side in enumerate(["경조사", "보내는이"]):
            layout.addWidget(QLabel(f"{side} 서체"), 1, i * 2, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            for j, ftype in enumerate(font_types, 2):
                layout.addWidget(QLabel(ftype), j, i * 2)
                combo = QFontComboBox()
                self.controls[side][ftype] = combo
                layout.addWidget(combo, j, i * 2 + 1)
        return group
    
    def _create_menu_buttons(self):
        menu_layout = QHBoxLayout()
        actions = {"새리본": self.clear_all, "파일열기": self.open_file, "저장": self.save_file,"새로저장": self.save_file_as, "도움말": self.show_help, "인쇄": self.print_ribbon}
        for text, action in actions.items():
            button = QPushButton(text); button.clicked.connect(action); menu_layout.addWidget(button)
        return menu_layout

    def _create_content_inputs(self):
        group = QGroupBox("내용 입력")
        grid = QGridLayout(group)
        self.text_right_edit = QLineEdit("祝開業")
        self.text_left_edit = QLineEdit("대표이사(주)홍길동")
        self.phrase_category_right = QComboBox()
        self.phrase_category_left = QComboBox()
        for i, (side, widget, category_combo) in enumerate([("경조사", self.text_right_edit, self.phrase_category_right), ("보내는이", self.text_left_edit, self.phrase_category_left)]):
            grid.addWidget(QLabel(side), i*2, 0)
            grid.addWidget(widget, i*2, 1)
            btn_layout = QHBoxLayout()
            for btn_text in ['+', '-', 'x']:
                btn = QPushButton(btn_text); btn.setFixedSize(25, 25)
                btn.clicked.connect(lambda _, s=side, op=btn_text: self.cycle_phrase(s, op))
                btn_layout.addWidget(btn)
            grid.addLayout(btn_layout, i*2, 2)
            grid.addWidget(QLabel("샘플 선택"), i*2 + 1, 0)
            grid.addWidget(category_combo, i*2 + 1, 1)
        return group
    
    def _connect_signals(self):
        self.ribbon_type_combo.currentTextChanged.connect(self.update_spins_from_preset)
        self.phrase_category_right.currentTextChanged.connect(lambda: self.reset_phrase_index('경조사'))
        self.phrase_category_left.currentTextChanged.connect(lambda: self.reset_phrase_index('보내는이'))
        self.auto_font_size_check.toggled.connect(self._toggle_auto_font_size)
        for side in self.controls:
            for control in self.controls[side].values():
                if isinstance(control, QSpinBox): control.valueChanged.connect(self.sync_and_update)
                else: control.currentIndexChanged.connect(self.sync_and_update_combo)
        self.text_right_edit.textChanged.connect(self.preview.update)
        self.text_left_edit.textChanged.connect(self.preview.update)

    def update_ribbon_combo(self):
        current_selection = self.ribbon_type_combo.currentText()
        self.ribbon_type_combo.blockSignals(True)
        self.ribbon_type_combo.clear()
        self.ribbon_type_combo.addItems(self.presets.keys())
        index = self.ribbon_type_combo.findText(current_selection)
        if index != -1: self.ribbon_type_combo.setCurrentIndex(index)
        self.ribbon_type_combo.blockSignals(False)
        self.update_spins_from_preset(self.ribbon_type_combo.currentText())

    def update_spins_from_preset(self, ribbon_name):
        data = self.presets.get(ribbon_name)
        if data:
            for side in self.controls:
                for key, widget in self.controls[side].items():
                    if key in data:
                        if isinstance(widget, QSpinBox):
                            widget.blockSignals(True)
                            widget.setValue(data[key])
                            widget.blockSignals(False)
        self.preview.update()

    def update_phrase_categories(self):
        self.phrase_category_right.blockSignals(True)
        self.phrase_category_left.blockSignals(True)
        self.phrase_category_right.clear()
        self.phrase_category_left.clear()
        if "경조사" in self.phrases:
            self.phrase_category_right.addItems(self.phrases["경조사"].keys())
        if "보내는이" in self.phrases:
            self.phrase_category_left.addItems(self.phrases["보내는이"].keys())
        self.phrase_category_right.blockSignals(False)
        self.phrase_category_left.blockSignals(False)
        self.reset_phrase_index('경조사')
        self.reset_phrase_index('보내는이')

    def reset_phrase_index(self, side):
        category_combo = self.phrase_category_right if side == '경조사' else self.phrase_category_left
        category = category_combo.currentText()
        if category:
            self.phrase_indices[side][category] = 0

    def cycle_phrase(self, side, op):
        widget = self.text_right_edit if side == "경조사" else self.text_left_edit
        category_combo = self.phrase_category_right if side == "경조사" else self.phrase_category_left
        category = category_combo.currentText()
        if not category or side not in self.phrases or category not in self.phrases[side]: return
        phrase_list = self.phrases[side][category]
        if not phrase_list: return
        current_index = self.phrase_indices[side].get(category, 0)
        if op == '+': current_index = (current_index + 1) % len(phrase_list)
        elif op == '-': current_index = (current_index - 1 + len(phrase_list)) % len(phrase_list)
        self.phrase_indices[side][category] = current_index
        widget.setText(phrase_list[current_index])
    
    def open_ribbon_settings(self):
        dialog = RibbonSettingsDialog(self.presets, self)
        if dialog.exec():
            self.presets = dialog.presets
            self.update_ribbon_combo()
            self.status_bar.showMessage("리본 설정이 저장되었습니다.")
            
    def _toggle_auto_font_size(self, checked): 
        self.controls['경조사']['글자크기'].setEnabled(not checked)
        self.controls['보내는이']['글자크기'].setEnabled(not checked)
        self.preview.update()

    def sync_and_update(self, value):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setValue(value)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()
        
    def sync_and_update_combo(self, index):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setCurrentIndex(index)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()

    def get_config_for_side(self, side):
        config = {key: widget.value() if isinstance(widget, QSpinBox) else widget.currentText() for key, widget in self.controls[side].items()}
        config['text'] = self.text_right_edit.text() if side == "경조사" else self.text_left_edit.text()
        config['auto_font_size'] = self.auto_font_size_check.isChecked()
        return config

    def clear_all(self): self.status_bar.showMessage("새 리본 작업을 시작합니다.")
    def open_file(self): self.status_bar.showMessage("파일을 열었습니다.")
    def save_file(self): self.status_bar.showMessage("파일이 저장되었습니다.")
    def save_file_as(self): pass
    def show_help(self): QMessageBox.information(self, "도움말", "리본메이커 v8.9\n\n제작: 브릿지앱 전문가")
    def print_ribbon(self): self.status_bar.showMessage("인쇄 명령을 보냈습니다.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RibbonApp()
    window.show()
    sys.exit(app.exec())

import sys
import json
import win32print
import win32ui
from PIL import Image, ImageWin
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QFontComboBox, QSpinBox, 
    QGroupBox, QGridLayout, QFileDialog, QMessageBox, QCheckBox, QLineEdit,
    QStatusBar, QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPixmap, QTransform, QUndoStack, 
    QUndoCommand, QPen, QFontMetrics
)
from PyQt6.QtCore import Qt, QRectF

# --- 데이터 관리 ---
PRESETS_FILE = "ribbon_presets.json"
PHRASES_FILE = "phrases.json"
DEFAULT_PRESETS = {
    "꽃다발 38x400mm": {"리본넓이": 38, "레이스": 5, "리본길이": 400, "상단여백": 80, "하단여백": 50, "인쇄여백": 53},
    "동양란 45x450mm": {"리본넓이": 45, "레이스": 7, "리본길이": 450, "상단여백": 100, "하단여백": 50, "인쇄여백": 57},
    "동양란 50x500mm": {"리본넓이": 50, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 60},
    "동/서양란 55x500mm": {"리본넓이": 55, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 62},
    "서양란 60/65x700mm": {"리본넓이": 60, "레이스": 10, "리본길이": 700, "상단여백": 150, "하단여백": 100, "인쇄여백": 65},
    "영화(을) 70x750mm": {"리본넓이": 70, "레이스": 10, "리본길이": 750, "상단여백": 150, "하단여백": 100, "인쇄여백": 70},
    "장미바구니 95x1000mm": {"리본넓이": 95, "레이스": 10, "리본길이": 1000, "상단여백": 180, "하단여백": 130, "인쇄여백": 82},
    "화분 소 105/110x1100mm": {"리본넓이": 105, "레이스": 23, "리본길이": 1100, "상단여백": 200, "하단여백": 150, "인쇄여백": 87},
    "화분 중 135x1500mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1500, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "화분 대 150x1800mm": {"리본넓이": 150, "레이스": 23, "리본길이": 1800, "상단여백": 350, "하단여백": 350, "인쇄여백": 110},
    "근조 1단 115x1200mm": {"리본넓이": 115, "레이스": 23, "리본길이": 1200, "상단여백": 250, "하단여백": 150, "인쇄여백": 102},
    "근조 2단 135x1700mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1700, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "근조 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
    "축화환 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
}
DEFAULT_PHRASES = { "경조사": {"기본": ["祝開業"]}, "보내는이": {"기본": ["OOO 올림"]} }

def load_data(filename, default_data):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data

def save_presets(presets):
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, ensure_ascii=False, indent=4)

def get_font_for_char(char, config):
    if not char: return config.get('한글', '(한)마린_견궁서B')
    if '\uac00' <= char <= '\ud7a3': return config.get('한글', '(한)마린_견궁서B')
    elif '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf': return config.get('한자', '(한)마린_견궁서B')
    elif '\u0021' <= char <= '\u007e': return config.get('영문', '(한)마린_견궁서B')
    else: return config.get('기타 (외국어)', '(한)마린_견궁서B')

class RibbonSettingsDialog(QDialog):
    def __init__(self, presets_data, parent=None):
        super().__init__(parent)
        self.presets = presets_data.copy()
        self.setWindowTitle("리본 종류 설정")
        self.setMinimumSize(800, 400)
        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("프린터 모델:"))
        printer_combo = QComboBox()
        printer_combo.addItems(["Epson-M105"])
        top_layout.addWidget(printer_combo)
        top_layout.addStretch()
        add_btn = QPushButton("리본 추가")
        del_btn = QPushButton("리스트 삭제")
        add_btn.clicked.connect(self.add_row)
        del_btn.clicked.connect(self.remove_row)
        top_layout.addWidget(add_btn)
        top_layout.addWidget(del_btn)
        layout.addLayout(top_layout)
        self.table = QTableWidget()
        self.column_headers = ["리본이름", "넓이", "레이스", "길이", "상단", "하단", "여백"]
        self.table.setColumnCount(len(self.column_headers))
        self.table.setHorizontalHeaderLabels(self.column_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.populate_table()
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        save_btn = QPushButton("저장/종료")
        cancel_btn = QPushButton("취소")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(cancel_btn)
        layout.addLayout(bottom_layout)

    def populate_table(self):
        self.table.setRowCount(len(self.presets))
        key_map = {"리본넓이": "넓이", "레이스": "레이스", "리본길이": "길이", "상단여백": "상단", "하단여백": "하단", "인쇄여백": "여백"}
        for row, (name, data) in enumerate(self.presets.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            for key, col_name in key_map.items():
                if col_name in self.column_headers:
                    col_index = self.column_headers.index(col_name)
                    self.table.setItem(row, col_index, QTableWidgetItem(str(data.get(key, ''))))

    def add_row(self):
        self.table.insertRow(self.table.rowCount())

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row > -1: self.table.removeRow(current_row)

    def accept(self):
        new_presets = {}
        key_map_inv = {"넓이": "리본넓이", "레이스": "레이스", "길이": "리본길이", "상단": "상단여백", "하단": "하단여백", "여백": "인쇄여백"}
        for row in range(self.table.rowCount()):
            try:
                name_item = self.table.item(row, 0)
                if not name_item or not name_item.text(): continue
                name = name_item.text()
                data = {}
                for col in range(1, self.table.columnCount()):
                    header = self.column_headers[col]
                    key = key_map_inv.get(header)
                    item = self.table.item(row, col)
                    if key and item and item.text(): data[key] = int(item.text())
                new_presets[name] = data
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "입력 오류", f"{row+1}행에 잘못된 숫자 형식이 있습니다.")
                return
        self.presets = new_presets
        save_presets(self.presets)
        super().accept()

class RibbonPreviewWidget(QWidget):
    def __init__(self, app_instance):
        super().__init__(app_instance)
        self.app = app_instance
        self.setMinimumSize(500, 700)
        self.padding = 15

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(220, 220, 220))
        config_right = self.app.get_config_for_side('경조사')
        config_left = self.app.get_config_for_side('보내는이')
        total_original_width = config_right.get('리본넓이', 50) + config_left.get('리본넓이', 50) + 50
        max_original_length = max(config_right.get('리본길이', 400), config_left.get('리본길이', 400))
        if max_original_length <= 0 or total_original_width <= 0: return
        view_width = self.width() - self.padding * 2
        view_height = self.height() - self.padding * 2
        scale_w = view_width / total_original_width
        scale_h = view_height / max_original_length
        scale = min(scale_w, scale_h)
        scaled_width_right = config_right.get('리본넓이', 50) * scale
        scaled_width_left = config_left.get('리본넓이', 50) * scale
        scaled_spacing = 50 * scale
        scaled_height_right = config_right.get('리본길이', 400) * scale
        scaled_height_left = config_left.get('리본길이', 400) * scale
        total_scaled_width = scaled_width_right + scaled_width_left + scaled_spacing
        start_x = (self.width() - total_scaled_width) / 2
        start_y = (self.height() - max(scaled_height_right, scaled_height_left)) / 2
        rect_right = QRectF(start_x, start_y, scaled_width_right, scaled_height_right)
        rect_left = QRectF(start_x + scaled_width_right + scaled_spacing, start_y, scaled_width_left, scaled_height_left)
        self.draw_ruler(painter, rect_right, config_right.get('리본길이', 400), scale)
        self.draw_ruler(painter, rect_left, config_left.get('리본길이', 400), scale)
        painter.fillRect(rect_right, QColor("lightgray"))
        painter.fillRect(rect_left, QColor("lightgray"))
        self.draw_guidelines(painter, rect_right, config_right, scale)
        self.draw_guidelines(painter, rect_left, config_left, scale)
        self.render_side(painter, rect_right, config_right, scale)
        self.render_side(painter, rect_left, config_left, scale)
        self.draw_margins(painter, rect_right, config_right, scale)
        self.draw_margins(painter, rect_left, config_left, scale)
        painter.end()

    def draw_guidelines(self, painter, rect, config, scale):
        painter.save()
        center_pen = QPen(QColor(0, 0, 0, 100), 1, Qt.PenStyle.DashLine)
        painter.setPen(center_pen)
        center_x = rect.center().x()
        painter.drawLine(int(center_x), int(rect.top()), int(center_x), int(rect.bottom()))
        layer_pen = QPen(QColor(0, 0, 255, 120), 1, Qt.PenStyle.DashLine)
        painter.setPen(layer_pen)
        lace_margin = config.get('레이스', 5) * scale
        left_line_x = rect.left() + lace_margin
        right_line_x = rect.right() - lace_margin
        painter.drawLine(int(left_line_x), int(rect.top()), int(left_line_x), int(rect.bottom()))
        painter.drawLine(int(right_line_x), int(rect.top()), int(right_line_x), int(rect.bottom()))
        painter.restore()

    def draw_ruler(self, painter, rect, original_length, scale):
        painter.save()
        ruler_width = 25
        ruler_rect = QRectF(rect.left() - ruler_width, rect.top(), ruler_width, rect.height())
        if ruler_rect.left() < 0 :
             ruler_rect.moveTo(rect.right(), rect.top())
        painter.fillRect(ruler_rect, QColor(14, 209, 69))
        pen = QPen(QColor("white"), 1)
        painter.setPen(pen)
        font = QFont("Arial", 8)
        painter.setFont(font)
        for y_mm in range(0, original_length + 1, 10):
            y_pos = rect.top() + y_mm * scale
            if y_pos > rect.bottom(): break
            if y_mm % 50 == 0:
                painter.drawLine(int(ruler_rect.left() + 5), int(y_pos), int(ruler_rect.right()), int(y_pos))
                if y_mm % 100 == 0: painter.drawText(int(ruler_rect.left()+2), int(y_pos + 10), str(y_mm))
            else:
                painter.drawLine(int(ruler_rect.left() + 15), int(y_pos), int(ruler_rect.right()), int(y_pos))
        painter.restore()

    def draw_margins(self, painter, rect, config, scale):
        painter.save()
        pen = QPen(QColor(255, 0, 0, 150), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        top_margin_y = rect.top() + config.get('상단여백', 80) * scale
        bottom_margin_y = rect.bottom() - config.get('하단여백', 50) * scale
        painter.drawLine(int(rect.left()), int(top_margin_y), int(rect.right()), int(top_margin_y))
        painter.drawLine(int(rect.left()), int(bottom_margin_y), int(rect.right()), int(bottom_margin_y))
        painter.restore()

    def render_side(self, painter, rect, config, scale):
        painter.save()
        text = config.get('text', '')
        if not text or rect.width() <= 0:
            painter.restore()
            return
            
        blocks = []
        i = 0
        current_normal_block = ""
        while i < len(text):
            if text[i] == '[':
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                try:
                    end_index = text.index(']', i)
                    substr = text[i+1:end_index]
                    blocks.append({'type': 'shrink', 'text': substr}); i = end_index + 1
                except ValueError: current_normal_block += text[i]; i += 1
            elif text[i] == '(' and i + 2 < len(text) and text[i+2] == ')' and text[i+1] in ['주', '유', '株']:
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'special', 'text': text[i:i+3]}); i += 3
            elif text[i] == '/' and i > 0 and i < len(text) - 1:
                # "/" 앞뒤 글자를 2열로 배치
                left_char = text[i-1]
                right_char = text[i+1]
                # 이전 글자를 현재 블록에서 제거
                if current_normal_block and current_normal_block[-1] == left_char:
                    current_normal_block = current_normal_block[:-1]
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'two_column', 'left': left_char, 'right': right_char})
                i += 2  # "/" 다음 글자까지 건너뛰기
            else:
                current_normal_block += text[i]
                i += 1
        if current_normal_block:
            blocks.append({'type': 'normal', 'text': current_normal_block})
        
        base_font_size_pt = config.get('글자크기', 40)
        if config.get('auto_font_size', True):
            printable_width_px = (config.get('리본넓이', 50) - (config.get('레이스', 5) * 2)) * scale
            target_pixel_width = printable_width_px * 0.95
            if blocks and printable_width_px > 0:
                temp_font_size_pt = 150
                while temp_font_size_pt > 5:
                    max_char_width_px = 0
                    all_chars_in_blocks = ""
                    for b in blocks:
                        if b['type'] == 'two_column':
                            all_chars_in_blocks += b['left'] + b['right']
                        else:
                            all_chars_in_blocks += b['text']
                    for char in all_chars_in_blocks:
                        font = QFont(get_font_for_char(char, config))
                        font.setPixelSize(int(temp_font_size_pt * scale))
                        fm = QFontMetrics(font)
                        char_width = fm.horizontalAdvance(char) * (config.get('가로폰트', 100) / 100.0)
                        if char_width > max_char_width_px:
                            max_char_width_px = char_width
                    if max_char_width_px <= target_pixel_width:
                        base_font_size_pt = temp_font_size_pt
                        break
                    temp_font_size_pt -= 1

        printable_height = rect.height() - (config.get('상단여백', 80) + config.get('하단여백', 50)) * scale
        base_v_scale = config.get('세로폰트', 100) / 100.0
        
        total_uncompressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * len(block['text']) * base_v_scale
        
        final_v_scale = base_v_scale
        if total_uncompressed_height > printable_height and total_uncompressed_height > 0:
            compression_ratio = printable_height / total_uncompressed_height
            final_v_scale = base_v_scale * compression_ratio
        
        total_compressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * len(block['text']) * final_v_scale
        
        # 전체 글자 수 계산 (justify 배치를 위해)
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 1  # 2열은 1줄로 취급
            elif block['type'] == 'special':
                total_char_count += 1  # special도 1줄로 취급
            else:
                total_char_count += len(block['text'])
        
        # 하단정렬: 하단여백선 위에서 전체 글자 높이만큼 위로 올라가서 시작
        bottom_margin = config.get('하단여백', 50) * scale
        
        # 전체 글자 수 계산
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 2  # 2열은 2글자
            elif block['type'] == 'special':
                total_char_count += len(block['text'])  # special도 글자수만큼
            else:
                total_char_count += len(block['text'])
        
        # 평균 글자 높이로 전체 높이 추정
        temp_font = QFont(get_font_for_char('가', config))
        temp_font.setPixelSize(int(base_font_size_pt * scale))
        temp_fm = QFontMetrics(temp_font)
        avg_char_height = temp_fm.height() * final_v_scale
        total_text_height = total_char_count * avg_char_height
        
        # 하단여백선에서 전체 텍스트 높이만큼 위로 올라간 지점에서 시작
        bottom_y = rect.bottom() - bottom_margin
        current_y = bottom_y - total_text_height
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치 처리
                left_char = block['left']
                right_char = block['right']
                
                for i, char in enumerate([left_char, right_char]):
                    size_ratio = 1.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)

                    char_width = fm.horizontalAdvance(char)
                    scaled_char_width = char_width * h_scale
                    
                    # 왼쪽 글자는 왼쪽에, 오른쪽 글자는 오른쪽에 배치
                    if i == 0:  # 왼쪽 글자
                        char_x = rect.center().x() - scaled_char_width
                    else:  # 오른쪽 글자
                        char_x = rect.center().x()
                    
                    # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    
                    painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                    # 다음 글자 위치로 이동
                    current_y += fm.height() * final_v_scale
                
            elif block['type'] == 'special':
                # (주), (유), (株) 가로 배치 처리
                special_text = block['text']  # 예: "(주)"
                size_ratio = config.get('(주)/(株)', 90) / 100.0
                scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                if scaled_font_size_px <= 0: scaled_font_size_px = 1
                
                # 전체 텍스트의 폭 계산
                total_width = 0
                char_widths = []
                for char in special_text:
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    fm = QFontMetrics(font)
                    char_width = fm.horizontalAdvance(char)
                    char_widths.append(char_width)
                    total_width += char_width
                
                h_scale = config.get('가로폰트', 100) / 100.0 * 0.8  # 80% 가로 축소
                v_scale = final_v_scale
                
                # 중앙 정렬을 위한 시작 x 좌표
                start_x = rect.center().x() - (total_width * h_scale) / 2
                
                # 각 글자를 가로로 배치
                current_x = start_x
                for i, char in enumerate(special_text):
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)
                    
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    painter.drawText(int(current_x / h_scale), int(char_y_pos / v_scale), char)
                    current_x += char_widths[i] * h_scale
                
                # special 블록 전체 처리 후 다음 위치로 이동
                current_y += fm.height() * final_v_scale
                
            else:
                # 일반 텍스트 블록 - justify 배치 적용
                block_text = block['text']
                
                for char in block_text:
                    size_ratio = 1.0
                    if block['type'] == 'shrink': size_ratio = config.get('축소폰트', 70) / 100.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                
                transform = QTransform().scale(h_scale, v_scale)
                painter.setTransform(transform)

                char_width = fm.horizontalAdvance(char)
                scaled_char_width = char_width * h_scale
                
                char_x = rect.center().x() - (scaled_char_width / 2)
                
                # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                char_y_pos = current_y + fm.ascent() * final_v_scale
            
                painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                # 다음 글자 위치로 이동
                current_y += fm.height() * final_v_scale
        painter.restore()

class RibbonApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RibbonMaker - Ribbon Editor (v8.9 최종판)")
        self.setGeometry(50, 50, 1200, 850)
        self.undo_stack = QUndoStack(self)
        self.controls = {'경조사': {}, '보내는이': {}}
        self.phrase_indices = {"경조사": {}, "보내는이": {}}
        self.presets = load_data(PRESETS_FILE, DEFAULT_PRESETS)
        self.phrases = load_data(PHRASES_FILE, DEFAULT_PHRASES)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        self.preview = RibbonPreviewWidget(self)
        main_layout.addWidget(self.preview)
        self.setStatusBar(QStatusBar(self))
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("프로그램 준비 완료.")
        self._connect_signals()
        self.update_ribbon_combo()
        self.update_phrase_categories()
        self._toggle_auto_font_size(True)

    def _create_control_panel(self):
        panel = QWidget()
        panel.setFixedWidth(550)
        top_layout = QVBoxLayout(panel)
        menu_layout = self._create_menu_buttons()
        top_layout.addLayout(menu_layout)
        content_group = self._create_content_inputs()
        top_layout.addWidget(content_group)
        main_grid = self._create_main_grid()
        top_layout.addLayout(main_grid)
        font_group = self._create_font_selectors()
        top_layout.addWidget(font_group)
        env_group = QGroupBox("환경설정")
        env_layout = QHBoxLayout(env_group)
        self.settings_button = QPushButton("리본 설정...")
        self.settings_button.clicked.connect(self.open_ribbon_settings)
        env_layout.addWidget(self.settings_button)
        env_group.setFixedHeight(60)
        top_layout.addWidget(env_group)
        top_layout.addStretch(1)
        return panel
    
    def _create_main_grid(self):
        main_grid = QGridLayout()
        main_grid.setSpacing(5)
        main_grid.addWidget(QLabel("리본종류"), 0, 0)
        self.ribbon_type_combo = QComboBox()
        self.ribbon_type_combo.setMaxVisibleItems(20)  # 최대 20개 항목까지 표시
        self.ribbon_type_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        main_grid.addWidget(self.ribbon_type_combo, 0, 1, 1, 2)
        self.sync_check = QCheckBox("동시적용")
        self.sync_check.setChecked(True)
        main_grid.addWidget(self.sync_check, 0, 3)
        main_grid.addWidget(QLabel("되돌리기"), 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)
        undo_btn = QPushButton("<"); undo_btn.setFixedSize(30,25)
        redo_btn = QPushButton(">"); redo_btn.setFixedSize(30,25)
        undo_btn.clicked.connect(self.undo_stack.undo)
        redo_btn.clicked.connect(self.undo_stack.redo)
        main_grid.addWidget(undo_btn, 0, 5)
        main_grid.addWidget(redo_btn, 0, 6)
        all_fields = ["리본넓이", "레이스", "리본길이", "상단여백", "하단여백", "인쇄여백", "글자크기", "가로폰트", "세로폰트", "축소폰트", "(주)/(株)", "폰트컬러"]
        main_grid.addWidget(QLabel("경조사 설정"), 1, 1, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        main_grid.addWidget(QLabel("보내는이 설정"), 1, 4, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        for i, text in enumerate(all_fields, 2):
            main_grid.addWidget(QLabel(text), i, 0, alignment=Qt.AlignmentFlag.AlignRight)
            for j, side in enumerate(["경조사", "보내는이"]):
                widget = QSpinBox()
                if text == "(주)/(株)":
                    widget.setRange(10, 100); widget.setValue(90); widget.setSuffix('%')
                elif text == "축소폰트":
                    widget.setRange(10, 100); widget.setValue(70); widget.setSuffix('%')
                else:
                    widget.setRange(0, 5000)
                    if text in ["가로폰트", "세로폰트"]: widget.setValue(100)
                    elif text == "글자크기": widget.setValue(40)
                self.controls[side][text] = widget
                main_grid.addWidget(widget, i, 1 + j*3, 1, 2)
        for j, side in enumerate(["경조사", "보내는이"]):
            main_grid.addWidget(QPushButton("그림넣기"), len(all_fields)+2, 1 + j*3)
            main_grid.addWidget(QPushButton("그림수정"), len(all_fields)+2, 2 + j*3)
        return main_grid

    def _create_font_selectors(self):
        group = QGroupBox("서체 설정")
        layout = QGridLayout(group)
        self.auto_font_size_check = QCheckBox("글자 폭 자동 맞춤")
        self.auto_font_size_check.setChecked(True)
        layout.addWidget(self.auto_font_size_check, 0, 0, 1, 2)
        font_types = ["한글", "한자", "영문", "기타 (외국어)"]
        for i, side in enumerate(["경조사", "보내는이"]):
            layout.addWidget(QLabel(f"{side} 서체"), 1, i * 2, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            for j, ftype in enumerate(font_types, 2):
                layout.addWidget(QLabel(ftype), j, i * 2)
                combo = QFontComboBox()
                self.controls[side][ftype] = combo
                layout.addWidget(combo, j, i * 2 + 1)
        return group
    
    def _create_menu_buttons(self):
        menu_layout = QHBoxLayout()
        actions = {"새리본": self.clear_all, "파일열기": self.open_file, "저장": self.save_file,"새로저장": self.save_file_as, "도움말": self.show_help, "인쇄": self.print_ribbon}
        for text, action in actions.items():
            button = QPushButton(text); button.clicked.connect(action); menu_layout.addWidget(button)
        return menu_layout

    def _create_content_inputs(self):
        group = QGroupBox("내용 입력")
        grid = QGridLayout(group)
        self.text_right_edit = QLineEdit("祝開業")
        self.text_left_edit = QLineEdit("대표이사(주)홍길동")
        self.phrase_category_right = QComboBox()
        self.phrase_category_left = QComboBox()
        for i, (side, widget, category_combo) in enumerate([("경조사", self.text_right_edit, self.phrase_category_right), ("보내는이", self.text_left_edit, self.phrase_category_left)]):
            grid.addWidget(QLabel(side), i*2, 0)
            grid.addWidget(widget, i*2, 1)
            btn_layout = QHBoxLayout()
            for btn_text in ['+', '-', 'x']:
                btn = QPushButton(btn_text); btn.setFixedSize(25, 25)
                btn.clicked.connect(lambda _, s=side, op=btn_text: self.cycle_phrase(s, op))
                btn_layout.addWidget(btn)
            grid.addLayout(btn_layout, i*2, 2)
            grid.addWidget(QLabel("샘플 선택"), i*2 + 1, 0)
            grid.addWidget(category_combo, i*2 + 1, 1)
        return group
    
    def _connect_signals(self):
        self.ribbon_type_combo.currentTextChanged.connect(self.update_spins_from_preset)
        self.phrase_category_right.currentTextChanged.connect(lambda: self.reset_phrase_index('경조사'))
        self.phrase_category_left.currentTextChanged.connect(lambda: self.reset_phrase_index('보내는이'))
        self.auto_font_size_check.toggled.connect(self._toggle_auto_font_size)
        for side in self.controls:
            for control in self.controls[side].values():
                if isinstance(control, QSpinBox): control.valueChanged.connect(self.sync_and_update)
                else: control.currentIndexChanged.connect(self.sync_and_update_combo)
        self.text_right_edit.textChanged.connect(self.preview.update)
        self.text_left_edit.textChanged.connect(self.preview.update)

    def update_ribbon_combo(self):
        current_selection = self.ribbon_type_combo.currentText()
        self.ribbon_type_combo.blockSignals(True)
        self.ribbon_type_combo.clear()
        self.ribbon_type_combo.addItems(self.presets.keys())
        index = self.ribbon_type_combo.findText(current_selection)
        if index != -1: self.ribbon_type_combo.setCurrentIndex(index)
        self.ribbon_type_combo.blockSignals(False)
        self.update_spins_from_preset(self.ribbon_type_combo.currentText())

    def update_spins_from_preset(self, ribbon_name):
        data = self.presets.get(ribbon_name)
        if data:
            for side in self.controls:
                for key, widget in self.controls[side].items():
                    if key in data:
                        if isinstance(widget, QSpinBox):
                            widget.blockSignals(True)
                            widget.setValue(data[key])
                            widget.blockSignals(False)
        self.preview.update()

    def update_phrase_categories(self):
        self.phrase_category_right.blockSignals(True)
        self.phrase_category_left.blockSignals(True)
        self.phrase_category_right.clear()
        self.phrase_category_left.clear()
        if "경조사" in self.phrases:
            self.phrase_category_right.addItems(self.phrases["경조사"].keys())
        if "보내는이" in self.phrases:
            self.phrase_category_left.addItems(self.phrases["보내는이"].keys())
        self.phrase_category_right.blockSignals(False)
        self.phrase_category_left.blockSignals(False)
        self.reset_phrase_index('경조사')
        self.reset_phrase_index('보내는이')

    def reset_phrase_index(self, side):
        category_combo = self.phrase_category_right if side == '경조사' else self.phrase_category_left
        category = category_combo.currentText()
        if category:
            self.phrase_indices[side][category] = 0

    def cycle_phrase(self, side, op):
        widget = self.text_right_edit if side == "경조사" else self.text_left_edit
        category_combo = self.phrase_category_right if side == "경조사" else self.phrase_category_left
        category = category_combo.currentText()
        if not category or side not in self.phrases or category not in self.phrases[side]: return
        phrase_list = self.phrases[side][category]
        if not phrase_list: return
        current_index = self.phrase_indices[side].get(category, 0)
        if op == '+': current_index = (current_index + 1) % len(phrase_list)
        elif op == '-': current_index = (current_index - 1 + len(phrase_list)) % len(phrase_list)
        self.phrase_indices[side][category] = current_index
        widget.setText(phrase_list[current_index])
    
    def open_ribbon_settings(self):
        dialog = RibbonSettingsDialog(self.presets, self)
        if dialog.exec():
            self.presets = dialog.presets
            self.update_ribbon_combo()
            self.status_bar.showMessage("리본 설정이 저장되었습니다.")
            
    def _toggle_auto_font_size(self, checked): 
        self.controls['경조사']['글자크기'].setEnabled(not checked)
        self.controls['보내는이']['글자크기'].setEnabled(not checked)
        self.preview.update()

    def sync_and_update(self, value):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setValue(value)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()
        
    def sync_and_update_combo(self, index):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setCurrentIndex(index)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()

    def get_config_for_side(self, side):
        config = {key: widget.value() if isinstance(widget, QSpinBox) else widget.currentText() for key, widget in self.controls[side].items()}
        config['text'] = self.text_right_edit.text() if side == "경조사" else self.text_left_edit.text()
        config['auto_font_size'] = self.auto_font_size_check.isChecked()
        return config

    def clear_all(self): self.status_bar.showMessage("새 리본 작업을 시작합니다.")
    def open_file(self): self.status_bar.showMessage("파일을 열었습니다.")
    def save_file(self): self.status_bar.showMessage("파일이 저장되었습니다.")
    def save_file_as(self): pass
    def show_help(self): QMessageBox.information(self, "도움말", "리본메이커 v8.9\n\n제작: 브릿지앱 전문가")
    def print_ribbon(self): self.status_bar.showMessage("인쇄 명령을 보냈습니다.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RibbonApp()
    window.show()
    sys.exit(app.exec())

import sys
import json
import win32print
import win32ui
from PIL import Image, ImageWin
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QFontComboBox, QSpinBox, 
    QGroupBox, QGridLayout, QFileDialog, QMessageBox, QCheckBox, QLineEdit,
    QStatusBar, QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPixmap, QTransform, QUndoStack, 
    QUndoCommand, QPen, QFontMetrics
)
from PyQt6.QtCore import Qt, QRectF

# --- 데이터 관리 ---
PRESETS_FILE = "ribbon_presets.json"
PHRASES_FILE = "phrases.json"
DEFAULT_PRESETS = {
    "꽃다발 38x400mm": {"리본넓이": 38, "레이스": 5, "리본길이": 400, "상단여백": 80, "하단여백": 50, "인쇄여백": 53},
    "동양란 45x450mm": {"리본넓이": 45, "레이스": 7, "리본길이": 450, "상단여백": 100, "하단여백": 50, "인쇄여백": 57},
    "동양란 50x500mm": {"리본넓이": 50, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 60},
    "동/서양란 55x500mm": {"리본넓이": 55, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 62},
    "서양란 60/65x700mm": {"리본넓이": 60, "레이스": 10, "리본길이": 700, "상단여백": 150, "하단여백": 100, "인쇄여백": 65},
    "영화(을) 70x750mm": {"리본넓이": 70, "레이스": 10, "리본길이": 750, "상단여백": 150, "하단여백": 100, "인쇄여백": 70},
    "장미바구니 95x1000mm": {"리본넓이": 95, "레이스": 10, "리본길이": 1000, "상단여백": 180, "하단여백": 130, "인쇄여백": 82},
    "화분 소 105/110x1100mm": {"리본넓이": 105, "레이스": 23, "리본길이": 1100, "상단여백": 200, "하단여백": 150, "인쇄여백": 87},
    "화분 중 135x1500mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1500, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "화분 대 150x1800mm": {"리본넓이": 150, "레이스": 23, "리본길이": 1800, "상단여백": 350, "하단여백": 350, "인쇄여백": 110},
    "근조 1단 115x1200mm": {"리본넓이": 115, "레이스": 23, "리본길이": 1200, "상단여백": 250, "하단여백": 150, "인쇄여백": 102},
    "근조 2단 135x1700mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1700, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "근조 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
    "축화환 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
}
DEFAULT_PHRASES = { "경조사": {"기본": ["祝開業"]}, "보내는이": {"기본": ["OOO 올림"]} }

def load_data(filename, default_data):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data

def save_presets(presets):
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, ensure_ascii=False, indent=4)

def get_font_for_char(char, config):
    if not char: return config.get('한글', '(한)마린_견궁서B')
    if '\uac00' <= char <= '\ud7a3': return config.get('한글', '(한)마린_견궁서B')
    elif '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf': return config.get('한자', '(한)마린_견궁서B')
    elif '\u0021' <= char <= '\u007e': return config.get('영문', '(한)마린_견궁서B')
    else: return config.get('기타 (외국어)', '(한)마린_견궁서B')

class RibbonSettingsDialog(QDialog):
    def __init__(self, presets_data, parent=None):
        super().__init__(parent)
        self.presets = presets_data.copy()
        self.setWindowTitle("리본 종류 설정")
        self.setMinimumSize(800, 400)
        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("프린터 모델:"))
        printer_combo = QComboBox()
        printer_combo.addItems(["Epson-M105"])
        top_layout.addWidget(printer_combo)
        top_layout.addStretch()
        add_btn = QPushButton("리본 추가")
        del_btn = QPushButton("리스트 삭제")
        add_btn.clicked.connect(self.add_row)
        del_btn.clicked.connect(self.remove_row)
        top_layout.addWidget(add_btn)
        top_layout.addWidget(del_btn)
        layout.addLayout(top_layout)
        self.table = QTableWidget()
        self.column_headers = ["리본이름", "넓이", "레이스", "길이", "상단", "하단", "여백"]
        self.table.setColumnCount(len(self.column_headers))
        self.table.setHorizontalHeaderLabels(self.column_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.populate_table()
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        save_btn = QPushButton("저장/종료")
        cancel_btn = QPushButton("취소")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(cancel_btn)
        layout.addLayout(bottom_layout)

    def populate_table(self):
        self.table.setRowCount(len(self.presets))
        key_map = {"리본넓이": "넓이", "레이스": "레이스", "리본길이": "길이", "상단여백": "상단", "하단여백": "하단", "인쇄여백": "여백"}
        for row, (name, data) in enumerate(self.presets.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            for key, col_name in key_map.items():
                if col_name in self.column_headers:
                    col_index = self.column_headers.index(col_name)
                    self.table.setItem(row, col_index, QTableWidgetItem(str(data.get(key, ''))))

    def add_row(self):
        self.table.insertRow(self.table.rowCount())

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row > -1: self.table.removeRow(current_row)

    def accept(self):
        new_presets = {}
        key_map_inv = {"넓이": "리본넓이", "레이스": "레이스", "길이": "리본길이", "상단": "상단여백", "하단": "하단여백", "여백": "인쇄여백"}
        for row in range(self.table.rowCount()):
            try:
                name_item = self.table.item(row, 0)
                if not name_item or not name_item.text(): continue
                name = name_item.text()
                data = {}
                for col in range(1, self.table.columnCount()):
                    header = self.column_headers[col]
                    key = key_map_inv.get(header)
                    item = self.table.item(row, col)
                    if key and item and item.text(): data[key] = int(item.text())
                new_presets[name] = data
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "입력 오류", f"{row+1}행에 잘못된 숫자 형식이 있습니다.")
                return
        self.presets = new_presets
        save_presets(self.presets)
        super().accept()

class RibbonPreviewWidget(QWidget):
    def __init__(self, app_instance):
        super().__init__(app_instance)
        self.app = app_instance
        self.setMinimumSize(500, 700)
        self.padding = 15

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(220, 220, 220))
        config_right = self.app.get_config_for_side('경조사')
        config_left = self.app.get_config_for_side('보내는이')
        total_original_width = config_right.get('리본넓이', 50) + config_left.get('리본넓이', 50) + 50
        max_original_length = max(config_right.get('리본길이', 400), config_left.get('리본길이', 400))
        if max_original_length <= 0 or total_original_width <= 0: return
        view_width = self.width() - self.padding * 2
        view_height = self.height() - self.padding * 2
        scale_w = view_width / total_original_width
        scale_h = view_height / max_original_length
        scale = min(scale_w, scale_h)
        scaled_width_right = config_right.get('리본넓이', 50) * scale
        scaled_width_left = config_left.get('리본넓이', 50) * scale
        scaled_spacing = 50 * scale
        scaled_height_right = config_right.get('리본길이', 400) * scale
        scaled_height_left = config_left.get('리본길이', 400) * scale
        total_scaled_width = scaled_width_right + scaled_width_left + scaled_spacing
        start_x = (self.width() - total_scaled_width) / 2
        start_y = (self.height() - max(scaled_height_right, scaled_height_left)) / 2
        rect_right = QRectF(start_x, start_y, scaled_width_right, scaled_height_right)
        rect_left = QRectF(start_x + scaled_width_right + scaled_spacing, start_y, scaled_width_left, scaled_height_left)
        self.draw_ruler(painter, rect_right, config_right.get('리본길이', 400), scale)
        self.draw_ruler(painter, rect_left, config_left.get('리본길이', 400), scale)
        painter.fillRect(rect_right, QColor("lightgray"))
        painter.fillRect(rect_left, QColor("lightgray"))
        self.draw_guidelines(painter, rect_right, config_right, scale)
        self.draw_guidelines(painter, rect_left, config_left, scale)
        self.render_side(painter, rect_right, config_right, scale)
        self.render_side(painter, rect_left, config_left, scale)
        self.draw_margins(painter, rect_right, config_right, scale)
        self.draw_margins(painter, rect_left, config_left, scale)
        painter.end()

    def draw_guidelines(self, painter, rect, config, scale):
        painter.save()
        center_pen = QPen(QColor(0, 0, 0, 100), 1, Qt.PenStyle.DashLine)
        painter.setPen(center_pen)
        center_x = rect.center().x()
        painter.drawLine(int(center_x), int(rect.top()), int(center_x), int(rect.bottom()))
        layer_pen = QPen(QColor(0, 0, 255, 120), 1, Qt.PenStyle.DashLine)
        painter.setPen(layer_pen)
        lace_margin = config.get('레이스', 5) * scale
        left_line_x = rect.left() + lace_margin
        right_line_x = rect.right() - lace_margin
        painter.drawLine(int(left_line_x), int(rect.top()), int(left_line_x), int(rect.bottom()))
        painter.drawLine(int(right_line_x), int(rect.top()), int(right_line_x), int(rect.bottom()))
        painter.restore()

    def draw_ruler(self, painter, rect, original_length, scale):
        painter.save()
        ruler_width = 25
        ruler_rect = QRectF(rect.left() - ruler_width, rect.top(), ruler_width, rect.height())
        if ruler_rect.left() < 0 :
             ruler_rect.moveTo(rect.right(), rect.top())
        painter.fillRect(ruler_rect, QColor(14, 209, 69))
        pen = QPen(QColor("white"), 1)
        painter.setPen(pen)
        font = QFont("Arial", 8)
        painter.setFont(font)
        for y_mm in range(0, original_length + 1, 10):
            y_pos = rect.top() + y_mm * scale
            if y_pos > rect.bottom(): break
            if y_mm % 50 == 0:
                painter.drawLine(int(ruler_rect.left() + 5), int(y_pos), int(ruler_rect.right()), int(y_pos))
                if y_mm % 100 == 0: painter.drawText(int(ruler_rect.left()+2), int(y_pos + 10), str(y_mm))
            else:
                painter.drawLine(int(ruler_rect.left() + 15), int(y_pos), int(ruler_rect.right()), int(y_pos))
        painter.restore()

    def draw_margins(self, painter, rect, config, scale):
        painter.save()
        pen = QPen(QColor(255, 0, 0, 150), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        top_margin_y = rect.top() + config.get('상단여백', 80) * scale
        bottom_margin_y = rect.bottom() - config.get('하단여백', 50) * scale
        painter.drawLine(int(rect.left()), int(top_margin_y), int(rect.right()), int(top_margin_y))
        painter.drawLine(int(rect.left()), int(bottom_margin_y), int(rect.right()), int(bottom_margin_y))
        painter.restore()

    def render_side(self, painter, rect, config, scale):
        painter.save()
        text = config.get('text', '')
        if not text or rect.width() <= 0:
            painter.restore()
            return
            
        blocks = []
        i = 0
        current_normal_block = ""
        while i < len(text):
            if text[i] == '[':
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                try:
                    end_index = text.index(']', i)
                    substr = text[i+1:end_index]
                    blocks.append({'type': 'shrink', 'text': substr}); i = end_index + 1
                except ValueError: current_normal_block += text[i]; i += 1
            elif text[i] == '(' and i + 2 < len(text) and text[i+2] == ')' and text[i+1] in ['주', '유', '株']:
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'special', 'text': text[i:i+3]}); i += 3
            elif text[i] == '/' and i > 0 and i < len(text) - 1:
                # "/" 앞뒤 글자를 2열로 배치
                left_char = text[i-1]
                right_char = text[i+1]
                # 이전 글자를 현재 블록에서 제거
                if current_normal_block and current_normal_block[-1] == left_char:
                    current_normal_block = current_normal_block[:-1]
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'two_column', 'left': left_char, 'right': right_char})
                i += 2  # "/" 다음 글자까지 건너뛰기
            else:
                current_normal_block += text[i]
                i += 1
        if current_normal_block:
            blocks.append({'type': 'normal', 'text': current_normal_block})
        
        base_font_size_pt = config.get('글자크기', 40)
        if config.get('auto_font_size', True):
            printable_width_px = (config.get('리본넓이', 50) - (config.get('레이스', 5) * 2)) * scale
            target_pixel_width = printable_width_px * 0.95
            if blocks and printable_width_px > 0:
                temp_font_size_pt = 150
                while temp_font_size_pt > 5:
                    max_char_width_px = 0
                    all_chars_in_blocks = ""
                    for b in blocks:
                        if b['type'] == 'two_column':
                            all_chars_in_blocks += b['left'] + b['right']
                        else:
                            all_chars_in_blocks += b['text']
                    for char in all_chars_in_blocks:
                        font = QFont(get_font_for_char(char, config))
                        font.setPixelSize(int(temp_font_size_pt * scale))
                        fm = QFontMetrics(font)
                        char_width = fm.horizontalAdvance(char) * (config.get('가로폰트', 100) / 100.0)
                        if char_width > max_char_width_px:
                            max_char_width_px = char_width
                    if max_char_width_px <= target_pixel_width:
                        base_font_size_pt = temp_font_size_pt
                        break
                    temp_font_size_pt -= 1

        printable_height = rect.height() - (config.get('상단여백', 80) + config.get('하단여백', 50)) * scale
        base_v_scale = config.get('세로폰트', 100) / 100.0
        
        total_uncompressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * len(block['text']) * base_v_scale
        
        final_v_scale = base_v_scale
        if total_uncompressed_height > printable_height and total_uncompressed_height > 0:
            compression_ratio = printable_height / total_uncompressed_height
            final_v_scale = base_v_scale * compression_ratio
        
        total_compressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * len(block['text']) * final_v_scale
        
        # 전체 글자 수 계산 (justify 배치를 위해)
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 1  # 2열은 1줄로 취급
            elif block['type'] == 'special':
                total_char_count += 1  # special도 1줄로 취급
            else:
                total_char_count += len(block['text'])
        
        # 하단정렬: 하단여백선 위에서 전체 글자 높이만큼 위로 올라가서 시작
        bottom_margin = config.get('하단여백', 50) * scale
        
        # 전체 글자 수 계산
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 2  # 2열은 2글자
            elif block['type'] == 'special':
                total_char_count += len(block['text'])  # special도 글자수만큼
            else:
                total_char_count += len(block['text'])
        
        # 평균 글자 높이로 전체 높이 추정
        temp_font = QFont(get_font_for_char('가', config))
        temp_font.setPixelSize(int(base_font_size_pt * scale))
        temp_fm = QFontMetrics(temp_font)
        avg_char_height = temp_fm.height() * final_v_scale
        total_text_height = total_char_count * avg_char_height
        
        # 하단여백선에서 전체 텍스트 높이만큼 위로 올라간 지점에서 시작
        bottom_y = rect.bottom() - bottom_margin
        current_y = bottom_y - total_text_height
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치 처리
                left_char = block['left']
                right_char = block['right']
                
                for i, char in enumerate([left_char, right_char]):
                    size_ratio = 1.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)

                    char_width = fm.horizontalAdvance(char)
                    scaled_char_width = char_width * h_scale
                    
                    # 왼쪽 글자는 왼쪽에, 오른쪽 글자는 오른쪽에 배치
                    if i == 0:  # 왼쪽 글자
                        char_x = rect.center().x() - scaled_char_width
                    else:  # 오른쪽 글자
                        char_x = rect.center().x()
                    
                    # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    
                    painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                    # 다음 글자 위치로 이동
                    current_y += fm.height() * final_v_scale
                
            elif block['type'] == 'special':
                # (주), (유), (株) 가로 배치 처리
                special_text = block['text']  # 예: "(주)"
                size_ratio = config.get('(주)/(株)', 90) / 100.0
                scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                if scaled_font_size_px <= 0: scaled_font_size_px = 1
                
                # 전체 텍스트의 폭 계산
                total_width = 0
                char_widths = []
                for char in special_text:
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    fm = QFontMetrics(font)
                    char_width = fm.horizontalAdvance(char)
                    char_widths.append(char_width)
                    total_width += char_width
                
                h_scale = config.get('가로폰트', 100) / 100.0 * 0.8  # 80% 가로 축소
                v_scale = final_v_scale
                
                # 중앙 정렬을 위한 시작 x 좌표
                start_x = rect.center().x() - (total_width * h_scale) / 2
                
                # 각 글자를 가로로 배치
                current_x = start_x
                for i, char in enumerate(special_text):
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)
                    
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    painter.drawText(int(current_x / h_scale), int(char_y_pos / v_scale), char)
                    current_x += char_widths[i] * h_scale
                
                # special 블록 전체 처리 후 다음 위치로 이동
                current_y += fm.height() * final_v_scale
                
            else:
                # 일반 텍스트 블록 - justify 배치 적용
                block_text = block['text']
                
                for char in block_text:
                    size_ratio = 1.0
                    if block['type'] == 'shrink': size_ratio = config.get('축소폰트', 70) / 100.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                
                transform = QTransform().scale(h_scale, v_scale)
                painter.setTransform(transform)

                char_width = fm.horizontalAdvance(char)
                scaled_char_width = char_width * h_scale
                
                char_x = rect.center().x() - (scaled_char_width / 2)
                
                # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                char_y_pos = current_y + fm.ascent() * final_v_scale
            
                painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                # 다음 글자 위치로 이동
                current_y += fm.height() * final_v_scale
        painter.restore()

class RibbonApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RibbonMaker - Ribbon Editor (v8.9 최종판)")
        self.setGeometry(50, 50, 1200, 850)
        self.undo_stack = QUndoStack(self)
        self.controls = {'경조사': {}, '보내는이': {}}
        self.phrase_indices = {"경조사": {}, "보내는이": {}}
        self.presets = load_data(PRESETS_FILE, DEFAULT_PRESETS)
        self.phrases = load_data(PHRASES_FILE, DEFAULT_PHRASES)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        self.preview = RibbonPreviewWidget(self)
        main_layout.addWidget(self.preview)
        self.setStatusBar(QStatusBar(self))
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("프로그램 준비 완료.")
        self._connect_signals()
        self.update_ribbon_combo()
        self.update_phrase_categories()
        self._toggle_auto_font_size(True)

    def _create_control_panel(self):
        panel = QWidget()
        panel.setFixedWidth(550)
        top_layout = QVBoxLayout(panel)
        menu_layout = self._create_menu_buttons()
        top_layout.addLayout(menu_layout)
        content_group = self._create_content_inputs()
        top_layout.addWidget(content_group)
        main_grid = self._create_main_grid()
        top_layout.addLayout(main_grid)
        font_group = self._create_font_selectors()
        top_layout.addWidget(font_group)
        env_group = QGroupBox("환경설정")
        env_layout = QHBoxLayout(env_group)
        self.settings_button = QPushButton("리본 설정...")
        self.settings_button.clicked.connect(self.open_ribbon_settings)
        env_layout.addWidget(self.settings_button)
        env_group.setFixedHeight(60)
        top_layout.addWidget(env_group)
        top_layout.addStretch(1)
        return panel
    
    def _create_main_grid(self):
        main_grid = QGridLayout()
        main_grid.setSpacing(5)
        main_grid.addWidget(QLabel("리본종류"), 0, 0)
        self.ribbon_type_combo = QComboBox()
        self.ribbon_type_combo.setMaxVisibleItems(20)  # 최대 20개 항목까지 표시
        self.ribbon_type_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        main_grid.addWidget(self.ribbon_type_combo, 0, 1, 1, 2)
        self.sync_check = QCheckBox("동시적용")
        self.sync_check.setChecked(True)
        main_grid.addWidget(self.sync_check, 0, 3)
        main_grid.addWidget(QLabel("되돌리기"), 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)
        undo_btn = QPushButton("<"); undo_btn.setFixedSize(30,25)
        redo_btn = QPushButton(">"); redo_btn.setFixedSize(30,25)
        undo_btn.clicked.connect(self.undo_stack.undo)
        redo_btn.clicked.connect(self.undo_stack.redo)
        main_grid.addWidget(undo_btn, 0, 5)
        main_grid.addWidget(redo_btn, 0, 6)
        all_fields = ["리본넓이", "레이스", "리본길이", "상단여백", "하단여백", "인쇄여백", "글자크기", "가로폰트", "세로폰트", "축소폰트", "(주)/(株)", "폰트컬러"]
        main_grid.addWidget(QLabel("경조사 설정"), 1, 1, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        main_grid.addWidget(QLabel("보내는이 설정"), 1, 4, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        for i, text in enumerate(all_fields, 2):
            main_grid.addWidget(QLabel(text), i, 0, alignment=Qt.AlignmentFlag.AlignRight)
            for j, side in enumerate(["경조사", "보내는이"]):
                widget = QSpinBox()
                if text == "(주)/(株)":
                    widget.setRange(10, 100); widget.setValue(90); widget.setSuffix('%')
                elif text == "축소폰트":
                    widget.setRange(10, 100); widget.setValue(70); widget.setSuffix('%')
                else:
                    widget.setRange(0, 5000)
                    if text in ["가로폰트", "세로폰트"]: widget.setValue(100)
                    elif text == "글자크기": widget.setValue(40)
                self.controls[side][text] = widget
                main_grid.addWidget(widget, i, 1 + j*3, 1, 2)
        for j, side in enumerate(["경조사", "보내는이"]):
            main_grid.addWidget(QPushButton("그림넣기"), len(all_fields)+2, 1 + j*3)
            main_grid.addWidget(QPushButton("그림수정"), len(all_fields)+2, 2 + j*3)
        return main_grid

    def _create_font_selectors(self):
        group = QGroupBox("서체 설정")
        layout = QGridLayout(group)
        self.auto_font_size_check = QCheckBox("글자 폭 자동 맞춤")
        self.auto_font_size_check.setChecked(True)
        layout.addWidget(self.auto_font_size_check, 0, 0, 1, 2)
        font_types = ["한글", "한자", "영문", "기타 (외국어)"]
        for i, side in enumerate(["경조사", "보내는이"]):
            layout.addWidget(QLabel(f"{side} 서체"), 1, i * 2, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            for j, ftype in enumerate(font_types, 2):
                layout.addWidget(QLabel(ftype), j, i * 2)
                combo = QFontComboBox()
                self.controls[side][ftype] = combo
                layout.addWidget(combo, j, i * 2 + 1)
        return group
    
    def _create_menu_buttons(self):
        menu_layout = QHBoxLayout()
        actions = {"새리본": self.clear_all, "파일열기": self.open_file, "저장": self.save_file,"새로저장": self.save_file_as, "도움말": self.show_help, "인쇄": self.print_ribbon}
        for text, action in actions.items():
            button = QPushButton(text); button.clicked.connect(action); menu_layout.addWidget(button)
        return menu_layout

    def _create_content_inputs(self):
        group = QGroupBox("내용 입력")
        grid = QGridLayout(group)
        self.text_right_edit = QLineEdit("祝開業")
        self.text_left_edit = QLineEdit("대표이사(주)홍길동")
        self.phrase_category_right = QComboBox()
        self.phrase_category_left = QComboBox()
        for i, (side, widget, category_combo) in enumerate([("경조사", self.text_right_edit, self.phrase_category_right), ("보내는이", self.text_left_edit, self.phrase_category_left)]):
            grid.addWidget(QLabel(side), i*2, 0)
            grid.addWidget(widget, i*2, 1)
            btn_layout = QHBoxLayout()
            for btn_text in ['+', '-', 'x']:
                btn = QPushButton(btn_text); btn.setFixedSize(25, 25)
                btn.clicked.connect(lambda _, s=side, op=btn_text: self.cycle_phrase(s, op))
                btn_layout.addWidget(btn)
            grid.addLayout(btn_layout, i*2, 2)
            grid.addWidget(QLabel("샘플 선택"), i*2 + 1, 0)
            grid.addWidget(category_combo, i*2 + 1, 1)
        return group
    
    def _connect_signals(self):
        self.ribbon_type_combo.currentTextChanged.connect(self.update_spins_from_preset)
        self.phrase_category_right.currentTextChanged.connect(lambda: self.reset_phrase_index('경조사'))
        self.phrase_category_left.currentTextChanged.connect(lambda: self.reset_phrase_index('보내는이'))
        self.auto_font_size_check.toggled.connect(self._toggle_auto_font_size)
        for side in self.controls:
            for control in self.controls[side].values():
                if isinstance(control, QSpinBox): control.valueChanged.connect(self.sync_and_update)
                else: control.currentIndexChanged.connect(self.sync_and_update_combo)
        self.text_right_edit.textChanged.connect(self.preview.update)
        self.text_left_edit.textChanged.connect(self.preview.update)

    def update_ribbon_combo(self):
        current_selection = self.ribbon_type_combo.currentText()
        self.ribbon_type_combo.blockSignals(True)
        self.ribbon_type_combo.clear()
        self.ribbon_type_combo.addItems(self.presets.keys())
        index = self.ribbon_type_combo.findText(current_selection)
        if index != -1: self.ribbon_type_combo.setCurrentIndex(index)
        self.ribbon_type_combo.blockSignals(False)
        self.update_spins_from_preset(self.ribbon_type_combo.currentText())

    def update_spins_from_preset(self, ribbon_name):
        data = self.presets.get(ribbon_name)
        if data:
            for side in self.controls:
                for key, widget in self.controls[side].items():
                    if key in data:
                        if isinstance(widget, QSpinBox):
                            widget.blockSignals(True)
                            widget.setValue(data[key])
                            widget.blockSignals(False)
        self.preview.update()

    def update_phrase_categories(self):
        self.phrase_category_right.blockSignals(True)
        self.phrase_category_left.blockSignals(True)
        self.phrase_category_right.clear()
        self.phrase_category_left.clear()
        if "경조사" in self.phrases:
            self.phrase_category_right.addItems(self.phrases["경조사"].keys())
        if "보내는이" in self.phrases:
            self.phrase_category_left.addItems(self.phrases["보내는이"].keys())
        self.phrase_category_right.blockSignals(False)
        self.phrase_category_left.blockSignals(False)
        self.reset_phrase_index('경조사')
        self.reset_phrase_index('보내는이')

    def reset_phrase_index(self, side):
        category_combo = self.phrase_category_right if side == '경조사' else self.phrase_category_left
        category = category_combo.currentText()
        if category:
            self.phrase_indices[side][category] = 0

    def cycle_phrase(self, side, op):
        widget = self.text_right_edit if side == "경조사" else self.text_left_edit
        category_combo = self.phrase_category_right if side == "경조사" else self.phrase_category_left
        category = category_combo.currentText()
        if not category or side not in self.phrases or category not in self.phrases[side]: return
        phrase_list = self.phrases[side][category]
        if not phrase_list: return
        current_index = self.phrase_indices[side].get(category, 0)
        if op == '+': current_index = (current_index + 1) % len(phrase_list)
        elif op == '-': current_index = (current_index - 1 + len(phrase_list)) % len(phrase_list)
        self.phrase_indices[side][category] = current_index
        widget.setText(phrase_list[current_index])
    
    def open_ribbon_settings(self):
        dialog = RibbonSettingsDialog(self.presets, self)
        if dialog.exec():
            self.presets = dialog.presets
            self.update_ribbon_combo()
            self.status_bar.showMessage("리본 설정이 저장되었습니다.")
            
    def _toggle_auto_font_size(self, checked): 
        self.controls['경조사']['글자크기'].setEnabled(not checked)
        self.controls['보내는이']['글자크기'].setEnabled(not checked)
        self.preview.update()

    def sync_and_update(self, value):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setValue(value)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()
        
    def sync_and_update_combo(self, index):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setCurrentIndex(index)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()

    def get_config_for_side(self, side):
        config = {key: widget.value() if isinstance(widget, QSpinBox) else widget.currentText() for key, widget in self.controls[side].items()}
        config['text'] = self.text_right_edit.text() if side == "경조사" else self.text_left_edit.text()
        config['auto_font_size'] = self.auto_font_size_check.isChecked()
        return config

    def clear_all(self): self.status_bar.showMessage("새 리본 작업을 시작합니다.")
    def open_file(self): self.status_bar.showMessage("파일을 열었습니다.")
    def save_file(self): self.status_bar.showMessage("파일이 저장되었습니다.")
    def save_file_as(self): pass
    def show_help(self): QMessageBox.information(self, "도움말", "리본메이커 v8.9\n\n제작: 브릿지앱 전문가")
    def print_ribbon(self): self.status_bar.showMessage("인쇄 명령을 보냈습니다.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RibbonApp()
    window.show()
    sys.exit(app.exec())

import sys
import json
import win32print
import win32ui
from PIL import Image, ImageWin
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QFontComboBox, QSpinBox, 
    QGroupBox, QGridLayout, QFileDialog, QMessageBox, QCheckBox, QLineEdit,
    QStatusBar, QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPixmap, QTransform, QUndoStack, 
    QUndoCommand, QPen, QFontMetrics
)
from PyQt6.QtCore import Qt, QRectF

# --- 데이터 관리 ---
PRESETS_FILE = "ribbon_presets.json"
PHRASES_FILE = "phrases.json"
DEFAULT_PRESETS = {
    "꽃다발 38x400mm": {"리본넓이": 38, "레이스": 5, "리본길이": 400, "상단여백": 80, "하단여백": 50, "인쇄여백": 53},
    "동양란 45x450mm": {"리본넓이": 45, "레이스": 7, "리본길이": 450, "상단여백": 100, "하단여백": 50, "인쇄여백": 57},
    "동양란 50x500mm": {"리본넓이": 50, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 60},
    "동/서양란 55x500mm": {"리본넓이": 55, "레이스": 10, "리본길이": 500, "상단여백": 120, "하단여백": 80, "인쇄여백": 62},
    "서양란 60/65x700mm": {"리본넓이": 60, "레이스": 10, "리본길이": 700, "상단여백": 150, "하단여백": 100, "인쇄여백": 65},
    "영화(을) 70x750mm": {"리본넓이": 70, "레이스": 10, "리본길이": 750, "상단여백": 150, "하단여백": 100, "인쇄여백": 70},
    "장미바구니 95x1000mm": {"리본넓이": 95, "레이스": 10, "리본길이": 1000, "상단여백": 180, "하단여백": 130, "인쇄여백": 82},
    "화분 소 105/110x1100mm": {"리본넓이": 105, "레이스": 23, "리본길이": 1100, "상단여백": 200, "하단여백": 150, "인쇄여백": 87},
    "화분 중 135x1500mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1500, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "화분 대 150x1800mm": {"리본넓이": 150, "레이스": 23, "리본길이": 1800, "상단여백": 350, "하단여백": 350, "인쇄여백": 110},
    "근조 1단 115x1200mm": {"리본넓이": 115, "레이스": 23, "리본길이": 1200, "상단여백": 250, "하단여백": 150, "인쇄여백": 102},
    "근조 2단 135x1700mm": {"리본넓이": 135, "레이스": 23, "리본길이": 1700, "상단여백": 300, "하단여백": 200, "인쇄여백": 102},
    "근조 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
    "축화환 3단 165x2200mm": {"리본넓이": 165, "레이스": 23, "리본길이": 2200, "상단여백": 400, "하단여백": 300, "인쇄여백": 117},
}
DEFAULT_PHRASES = { "경조사": {"기본": ["祝開業"]}, "보내는이": {"기본": ["OOO 올림"]} }

def load_data(filename, default_data):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data

def save_presets(presets):
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, ensure_ascii=False, indent=4)

def get_font_for_char(char, config):
    if not char: return config.get('한글', '(한)마린_견궁서B')
    if '\uac00' <= char <= '\ud7a3': return config.get('한글', '(한)마린_견궁서B')
    elif '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf': return config.get('한자', '(한)마린_견궁서B')
    elif '\u0021' <= char <= '\u007e': return config.get('영문', '(한)마린_견궁서B')
    else: return config.get('기타 (외국어)', '(한)마린_견궁서B')

class RibbonSettingsDialog(QDialog):
    def __init__(self, presets_data, parent=None):
        super().__init__(parent)
        self.presets = presets_data.copy()
        self.setWindowTitle("리본 종류 설정")
        self.setMinimumSize(800, 400)
        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("프린터 모델:"))
        printer_combo = QComboBox()
        printer_combo.addItems(["Epson-M105"])
        top_layout.addWidget(printer_combo)
        top_layout.addStretch()
        add_btn = QPushButton("리본 추가")
        del_btn = QPushButton("리스트 삭제")
        add_btn.clicked.connect(self.add_row)
        del_btn.clicked.connect(self.remove_row)
        top_layout.addWidget(add_btn)
        top_layout.addWidget(del_btn)
        layout.addLayout(top_layout)
        self.table = QTableWidget()
        self.column_headers = ["리본이름", "넓이", "레이스", "길이", "상단", "하단", "여백"]
        self.table.setColumnCount(len(self.column_headers))
        self.table.setHorizontalHeaderLabels(self.column_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.populate_table()
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        save_btn = QPushButton("저장/종료")
        cancel_btn = QPushButton("취소")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(cancel_btn)
        layout.addLayout(bottom_layout)

    def populate_table(self):
        self.table.setRowCount(len(self.presets))
        key_map = {"리본넓이": "넓이", "레이스": "레이스", "리본길이": "길이", "상단여백": "상단", "하단여백": "하단", "인쇄여백": "여백"}
        for row, (name, data) in enumerate(self.presets.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            for key, col_name in key_map.items():
                if col_name in self.column_headers:
                    col_index = self.column_headers.index(col_name)
                    self.table.setItem(row, col_index, QTableWidgetItem(str(data.get(key, ''))))

    def add_row(self):
        self.table.insertRow(self.table.rowCount())

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row > -1: self.table.removeRow(current_row)

    def accept(self):
        new_presets = {}
        key_map_inv = {"넓이": "리본넓이", "레이스": "레이스", "길이": "리본길이", "상단": "상단여백", "하단": "하단여백", "여백": "인쇄여백"}
        for row in range(self.table.rowCount()):
            try:
                name_item = self.table.item(row, 0)
                if not name_item or not name_item.text(): continue
                name = name_item.text()
                data = {}
                for col in range(1, self.table.columnCount()):
                    header = self.column_headers[col]
                    key = key_map_inv.get(header)
                    item = self.table.item(row, col)
                    if key and item and item.text(): data[key] = int(item.text())
                new_presets[name] = data
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "입력 오류", f"{row+1}행에 잘못된 숫자 형식이 있습니다.")
                return
        self.presets = new_presets
        save_presets(self.presets)
        super().accept()

class RibbonPreviewWidget(QWidget):
    def __init__(self, app_instance):
        super().__init__(app_instance)
        self.app = app_instance
        self.setMinimumSize(500, 700)
        self.padding = 15

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(220, 220, 220))
        config_right = self.app.get_config_for_side('경조사')
        config_left = self.app.get_config_for_side('보내는이')
        total_original_width = config_right.get('리본넓이', 50) + config_left.get('리본넓이', 50) + 50
        max_original_length = max(config_right.get('리본길이', 400), config_left.get('리본길이', 400))
        if max_original_length <= 0 or total_original_width <= 0: return
        view_width = self.width() - self.padding * 2
        view_height = self.height() - self.padding * 2
        scale_w = view_width / total_original_width
        scale_h = view_height / max_original_length
        scale = min(scale_w, scale_h)
        scaled_width_right = config_right.get('리본넓이', 50) * scale
        scaled_width_left = config_left.get('리본넓이', 50) * scale
        scaled_spacing = 50 * scale
        scaled_height_right = config_right.get('리본길이', 400) * scale
        scaled_height_left = config_left.get('리본길이', 400) * scale
        total_scaled_width = scaled_width_right + scaled_width_left + scaled_spacing
        start_x = (self.width() - total_scaled_width) / 2
        start_y = (self.height() - max(scaled_height_right, scaled_height_left)) / 2
        rect_right = QRectF(start_x, start_y, scaled_width_right, scaled_height_right)
        rect_left = QRectF(start_x + scaled_width_right + scaled_spacing, start_y, scaled_width_left, scaled_height_left)
        self.draw_ruler(painter, rect_right, config_right.get('리본길이', 400), scale)
        self.draw_ruler(painter, rect_left, config_left.get('리본길이', 400), scale)
        painter.fillRect(rect_right, QColor("lightgray"))
        painter.fillRect(rect_left, QColor("lightgray"))
        self.draw_guidelines(painter, rect_right, config_right, scale)
        self.draw_guidelines(painter, rect_left, config_left, scale)
        self.render_side(painter, rect_right, config_right, scale)
        self.render_side(painter, rect_left, config_left, scale)
        self.draw_margins(painter, rect_right, config_right, scale)
        self.draw_margins(painter, rect_left, config_left, scale)
        painter.end()

    def draw_guidelines(self, painter, rect, config, scale):
        painter.save()
        center_pen = QPen(QColor(0, 0, 0, 100), 1, Qt.PenStyle.DashLine)
        painter.setPen(center_pen)
        center_x = rect.center().x()
        painter.drawLine(int(center_x), int(rect.top()), int(center_x), int(rect.bottom()))
        layer_pen = QPen(QColor(0, 0, 255, 120), 1, Qt.PenStyle.DashLine)
        painter.setPen(layer_pen)
        lace_margin = config.get('레이스', 5) * scale
        left_line_x = rect.left() + lace_margin
        right_line_x = rect.right() - lace_margin
        painter.drawLine(int(left_line_x), int(rect.top()), int(left_line_x), int(rect.bottom()))
        painter.drawLine(int(right_line_x), int(rect.top()), int(right_line_x), int(rect.bottom()))
        painter.restore()

    def draw_ruler(self, painter, rect, original_length, scale):
        painter.save()
        ruler_width = 25
        ruler_rect = QRectF(rect.left() - ruler_width, rect.top(), ruler_width, rect.height())
        if ruler_rect.left() < 0 :
             ruler_rect.moveTo(rect.right(), rect.top())
        painter.fillRect(ruler_rect, QColor(14, 209, 69))
        pen = QPen(QColor("white"), 1)
        painter.setPen(pen)
        font = QFont("Arial", 8)
        painter.setFont(font)
        for y_mm in range(0, original_length + 1, 10):
            y_pos = rect.top() + y_mm * scale
            if y_pos > rect.bottom(): break
            if y_mm % 50 == 0:
                painter.drawLine(int(ruler_rect.left() + 5), int(y_pos), int(ruler_rect.right()), int(y_pos))
                if y_mm % 100 == 0: painter.drawText(int(ruler_rect.left()+2), int(y_pos + 10), str(y_mm))
            else:
                painter.drawLine(int(ruler_rect.left() + 15), int(y_pos), int(ruler_rect.right()), int(y_pos))
        painter.restore()

    def draw_margins(self, painter, rect, config, scale):
        painter.save()
        pen = QPen(QColor(255, 0, 0, 150), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        top_margin_y = rect.top() + config.get('상단여백', 80) * scale
        bottom_margin_y = rect.bottom() - config.get('하단여백', 50) * scale
        painter.drawLine(int(rect.left()), int(top_margin_y), int(rect.right()), int(top_margin_y))
        painter.drawLine(int(rect.left()), int(bottom_margin_y), int(rect.right()), int(bottom_margin_y))
        painter.restore()

    def render_side(self, painter, rect, config, scale):
        painter.save()
        text = config.get('text', '')
        if not text or rect.width() <= 0:
            painter.restore()
            return
            
        blocks = []
        i = 0
        current_normal_block = ""
        while i < len(text):
            if text[i] == '[':
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                try:
                    end_index = text.index(']', i)
                    substr = text[i+1:end_index]
                    blocks.append({'type': 'shrink', 'text': substr}); i = end_index + 1
                except ValueError: current_normal_block += text[i]; i += 1
            elif text[i] == '(' and i + 2 < len(text) and text[i+2] == ')' and text[i+1] in ['주', '유', '株']:
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'special', 'text': text[i:i+3]}); i += 3
            elif text[i] == '/' and i > 0 and i < len(text) - 1:
                # "/" 앞뒤 글자를 2열로 배치
                left_char = text[i-1]
                right_char = text[i+1]
                # 이전 글자를 현재 블록에서 제거
                if current_normal_block and current_normal_block[-1] == left_char:
                    current_normal_block = current_normal_block[:-1]
                if current_normal_block: blocks.append({'type': 'normal', 'text': current_normal_block}); current_normal_block = ""
                blocks.append({'type': 'two_column', 'left': left_char, 'right': right_char})
                i += 2  # "/" 다음 글자까지 건너뛰기
            else:
                current_normal_block += text[i]
                i += 1
        if current_normal_block:
            blocks.append({'type': 'normal', 'text': current_normal_block})
        
        base_font_size_pt = config.get('글자크기', 40)
        if config.get('auto_font_size', True):
            printable_width_px = (config.get('리본넓이', 50) - (config.get('레이스', 5) * 2)) * scale
            target_pixel_width = printable_width_px * 0.95
            if blocks and printable_width_px > 0:
                temp_font_size_pt = 150
                while temp_font_size_pt > 5:
                    max_char_width_px = 0
                    all_chars_in_blocks = ""
                    for b in blocks:
                        if b['type'] == 'two_column':
                            all_chars_in_blocks += b['left'] + b['right']
                        else:
                            all_chars_in_blocks += b['text']
                    for char in all_chars_in_blocks:
                        font = QFont(get_font_for_char(char, config))
                        font.setPixelSize(int(temp_font_size_pt * scale))
                        fm = QFontMetrics(font)
                        char_width = fm.horizontalAdvance(char) * (config.get('가로폰트', 100) / 100.0)
                        if char_width > max_char_width_px:
                            max_char_width_px = char_width
                    if max_char_width_px <= target_pixel_width:
                        base_font_size_pt = temp_font_size_pt
                        break
                    temp_font_size_pt -= 1

        printable_height = rect.height() - (config.get('상단여백', 80) + config.get('하단여백', 50)) * scale
        base_v_scale = config.get('세로폰트', 100) / 100.0
        
        total_uncompressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * base_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_uncompressed_height += fm.height() * len(block['text']) * base_v_scale
        
        final_v_scale = base_v_scale
        if total_uncompressed_height > printable_height and total_uncompressed_height > 0:
            compression_ratio = printable_height / total_uncompressed_height
            final_v_scale = base_v_scale * compression_ratio
        
        total_compressed_height = 0
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치는 1줄 높이만 차지
                font = QFont(get_font_for_char(block['left'], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            elif block['type'] == 'special':
                # (주), (유), (株)는 가로 1줄로 배치되므로 1줄 높이만 차지
                # special 블록의 모든 글자는 한글 폰트를 사용
                font = QFont(config.get('한글', '(한)마린_견궁서B'))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * final_v_scale
            else:
                font = QFont(get_font_for_char(block['text'][0], config))
                font.setPixelSize(int(base_font_size_pt * scale))
                fm = QFontMetrics(font)
                total_compressed_height += fm.height() * len(block['text']) * final_v_scale
        
        # 전체 글자 수 계산 (justify 배치를 위해)
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 1  # 2열은 1줄로 취급
            elif block['type'] == 'special':
                total_char_count += 1  # special도 1줄로 취급
            else:
                total_char_count += len(block['text'])
        
        # 하단정렬: 하단여백선 위에서 전체 글자 높이만큼 위로 올라가서 시작
        bottom_margin = config.get('하단여백', 50) * scale
        
        # 전체 글자 수 계산
        total_char_count = 0
        for block in blocks:
            if block['type'] == 'two_column':
                total_char_count += 2  # 2열은 2글자
            elif block['type'] == 'special':
                total_char_count += len(block['text'])  # special도 글자수만큼
            else:
                total_char_count += len(block['text'])
        
        # 평균 글자 높이로 전체 높이 추정
        temp_font = QFont(get_font_for_char('가', config))
        temp_font.setPixelSize(int(base_font_size_pt * scale))
        temp_fm = QFontMetrics(temp_font)
        avg_char_height = temp_fm.height() * final_v_scale
        total_text_height = total_char_count * avg_char_height
        
        # 하단여백선에서 전체 텍스트 높이만큼 위로 올라간 지점에서 시작
        bottom_y = rect.bottom() - bottom_margin
        current_y = bottom_y - total_text_height
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 배치 처리
                left_char = block['left']
                right_char = block['right']
                
                for i, char in enumerate([left_char, right_char]):
                    size_ratio = 1.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)

                    char_width = fm.horizontalAdvance(char)
                    scaled_char_width = char_width * h_scale
                    
                    # 왼쪽 글자는 왼쪽에, 오른쪽 글자는 오른쪽에 배치
                    if i == 0:  # 왼쪽 글자
                        char_x = rect.center().x() - scaled_char_width
                    else:  # 오른쪽 글자
                        char_x = rect.center().x()
                    
                    # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    
                    painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                    # 다음 글자 위치로 이동
                    current_y += fm.height() * final_v_scale
                
            elif block['type'] == 'special':
                # (주), (유), (株) 가로 배치 처리
                special_text = block['text']  # 예: "(주)"
                size_ratio = config.get('(주)/(株)', 90) / 100.0
                scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                if scaled_font_size_px <= 0: scaled_font_size_px = 1
                
                # 전체 텍스트의 폭 계산
                total_width = 0
                char_widths = []
                for char in special_text:
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    fm = QFontMetrics(font)
                    char_width = fm.horizontalAdvance(char)
                    char_widths.append(char_width)
                    total_width += char_width
                
                h_scale = config.get('가로폰트', 100) / 100.0 * 0.8  # 80% 가로 축소
                v_scale = final_v_scale
                
                # 중앙 정렬을 위한 시작 x 좌표
                start_x = rect.center().x() - (total_width * h_scale) / 2
                
                # 각 글자를 가로로 배치
                current_x = start_x
                for i, char in enumerate(special_text):
                    font_name = config.get('한글', '(한)마린_견궁서B')
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    
                    transform = QTransform().scale(h_scale, v_scale)
                    painter.setTransform(transform)
                    
                    char_y_pos = current_y + fm.ascent() * final_v_scale
                    painter.drawText(int(current_x / h_scale), int(char_y_pos / v_scale), char)
                    current_x += char_widths[i] * h_scale
                
                # special 블록 전체 처리 후 다음 위치로 이동
                current_y += fm.height() * final_v_scale
                
            else:
                # 일반 텍스트 블록 - justify 배치 적용
                block_text = block['text']
                
                for char in block_text:
                    size_ratio = 1.0
                    if block['type'] == 'shrink': size_ratio = config.get('축소폰트', 70) / 100.0
                    
                    scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
                    if scaled_font_size_px <= 0: scaled_font_size_px = 1
                    
                    font_name = get_font_for_char(char, config)
                    font = QFont(font_name)
                    font.setPixelSize(scaled_font_size_px)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    line_height = fm.height()

                    h_scale = config.get('가로폰트', 100) / 100.0
                    v_scale = final_v_scale
                
                transform = QTransform().scale(h_scale, v_scale)
                painter.setTransform(transform)

                char_width = fm.horizontalAdvance(char)
                scaled_char_width = char_width * h_scale
                
                char_x = rect.center().x() - (scaled_char_width / 2)
                
                # 상단정렬: 글자를 현재 위치에 배치하고 다음 위치로 이동
                char_y_pos = current_y + fm.ascent() * final_v_scale
            
                painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
                # 다음 글자 위치로 이동
                current_y += fm.height() * final_v_scale
        painter.restore()

class RibbonApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RibbonMaker - Ribbon Editor (v8.9 최종판)")
        self.setGeometry(50, 50, 1200, 850)
        self.undo_stack = QUndoStack(self)
        self.controls = {'경조사': {}, '보내는이': {}}
        self.phrase_indices = {"경조사": {}, "보내는이": {}}
        self.presets = load_data(PRESETS_FILE, DEFAULT_PRESETS)
        self.phrases = load_data(PHRASES_FILE, DEFAULT_PHRASES)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        self.preview = RibbonPreviewWidget(self)
        main_layout.addWidget(self.preview)
        self.setStatusBar(QStatusBar(self))
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("프로그램 준비 완료.")
        self._connect_signals()
        self.update_ribbon_combo()
        self.update_phrase_categories()
        self._toggle_auto_font_size(True)

    def _create_control_panel(self):
        panel = QWidget()
        panel.setFixedWidth(550)
        top_layout = QVBoxLayout(panel)
        menu_layout = self._create_menu_buttons()
        top_layout.addLayout(menu_layout)
        content_group = self._create_content_inputs()
        top_layout.addWidget(content_group)
        main_grid = self._create_main_grid()
        top_layout.addLayout(main_grid)
        font_group = self._create_font_selectors()
        top_layout.addWidget(font_group)
        env_group = QGroupBox("환경설정")
        env_layout = QHBoxLayout(env_group)
        self.settings_button = QPushButton("리본 설정...")
        self.settings_button.clicked.connect(self.open_ribbon_settings)
        env_layout.addWidget(self.settings_button)
        env_group.setFixedHeight(60)
        top_layout.addWidget(env_group)
        top_layout.addStretch(1)
        return panel
    
    def _create_main_grid(self):
        main_grid = QGridLayout()
        main_grid.setSpacing(5)
        main_grid.addWidget(QLabel("리본종류"), 0, 0)
        self.ribbon_type_combo = QComboBox()
        self.ribbon_type_combo.setMaxVisibleItems(20)  # 최대 20개 항목까지 표시
        self.ribbon_type_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        main_grid.addWidget(self.ribbon_type_combo, 0, 1, 1, 2)
        self.sync_check = QCheckBox("동시적용")
        self.sync_check.setChecked(True)
        main_grid.addWidget(self.sync_check, 0, 3)
        main_grid.addWidget(QLabel("되돌리기"), 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)
        undo_btn = QPushButton("<"); undo_btn.setFixedSize(30,25)
        redo_btn = QPushButton(">"); redo_btn.setFixedSize(30,25)
        undo_btn.clicked.connect(self.undo_stack.undo)
        redo_btn.clicked.connect(self.undo_stack.redo)
        main_grid.addWidget(undo_btn, 0, 5)
        main_grid.addWidget(redo_btn, 0, 6)
        all_fields = ["리본넓이", "레이스", "리본길이", "상단여백", "하단여백", "인쇄여백", "글자크기", "가로폰트", "세로폰트", "축소폰트", "(주)/(株)", "폰트컬러"]
        main_grid.addWidget(QLabel("경조사 설정"), 1, 1, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        main_grid.addWidget(QLabel("보내는이 설정"), 1, 4, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        for i, text in enumerate(all_fields, 2):
            main_grid.addWidget(QLabel(text), i, 0, alignment=Qt.AlignmentFlag.AlignRight)
            for j, side in enumerate(["경조사", "보내는이"]):
                widget = QSpinBox()
                if text == "(주)/(株)":
                    widget.setRange(10, 100); widget.setValue(90); widget.setSuffix('%')
                elif text == "축소폰트":
                    widget.setRange(10, 100); widget.setValue(70); widget.setSuffix('%')
                else:
                    widget.setRange(0, 5000)
                    if text in ["가로폰트", "세로폰트"]: widget.setValue(100)
                    elif text == "글자크기": widget.setValue(40)
                self.controls[side][text] = widget
                main_grid.addWidget(widget, i, 1 + j*3, 1, 2)
        for j, side in enumerate(["경조사", "보내는이"]):
            main_grid.addWidget(QPushButton("그림넣기"), len(all_fields)+2, 1 + j*3)
            main_grid.addWidget(QPushButton("그림수정"), len(all_fields)+2, 2 + j*3)
        return main_grid

    def _create_font_selectors(self):
        group = QGroupBox("서체 설정")
        layout = QGridLayout(group)
        self.auto_font_size_check = QCheckBox("글자 폭 자동 맞춤")
        self.auto_font_size_check.setChecked(True)
        layout.addWidget(self.auto_font_size_check, 0, 0, 1, 2)
        font_types = ["한글", "한자", "영문", "기타 (외국어)"]
        for i, side in enumerate(["경조사", "보내는이"]):
            layout.addWidget(QLabel(f"{side} 서체"), 1, i * 2, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            for j, ftype in enumerate(font_types, 2):
                layout.addWidget(QLabel(ftype), j, i * 2)
                combo = QFontComboBox()
                self.controls[side][ftype] = combo
                layout.addWidget(combo, j, i * 2 + 1)
        return group
    
    def _create_menu_buttons(self):
        menu_layout = QHBoxLayout()
        actions = {"새리본": self.clear_all, "파일열기": self.open_file, "저장": self.save_file,"새로저장": self.save_file_as, "도움말": self.show_help, "인쇄": self.print_ribbon}
        for text, action in actions.items():
            button = QPushButton(text); button.clicked.connect(action); menu_layout.addWidget(button)
        return menu_layout

    def _create_content_inputs(self):
        group = QGroupBox("내용 입력")
        grid = QGridLayout(group)
        self.text_right_edit = QLineEdit("祝開業")
        self.text_left_edit = QLineEdit("대표이사(주)홍길동")
        self.phrase_category_right = QComboBox()
        self.phrase_category_left = QComboBox()
        for i, (side, widget, category_combo) in enumerate([("경조사", self.text_right_edit, self.phrase_category_right), ("보내는이", self.text_left_edit, self.phrase_category_left)]):
            grid.addWidget(QLabel(side), i*2, 0)
            grid.addWidget(widget, i*2, 1)
            btn_layout = QHBoxLayout()
            for btn_text in ['+', '-', 'x']:
                btn = QPushButton(btn_text); btn.setFixedSize(25, 25)
                btn.clicked.connect(lambda _, s=side, op=btn_text: self.cycle_phrase(s, op))
                btn_layout.addWidget(btn)
            grid.addLayout(btn_layout, i*2, 2)
            grid.addWidget(QLabel("샘플 선택"), i*2 + 1, 0)
            grid.addWidget(category_combo, i*2 + 1, 1)
        return group
    
    def _connect_signals(self):
        self.ribbon_type_combo.currentTextChanged.connect(self.update_spins_from_preset)
        self.phrase_category_right.currentTextChanged.connect(lambda: self.reset_phrase_index('경조사'))
        self.phrase_category_left.currentTextChanged.connect(lambda: self.reset_phrase_index('보내는이'))
        self.auto_font_size_check.toggled.connect(self._toggle_auto_font_size)
        for side in self.controls:
            for control in self.controls[side].values():
                if isinstance(control, QSpinBox): control.valueChanged.connect(self.sync_and_update)
                else: control.currentIndexChanged.connect(self.sync_and_update_combo)
        self.text_right_edit.textChanged.connect(self.preview.update)
        self.text_left_edit.textChanged.connect(self.preview.update)

    def update_ribbon_combo(self):
        current_selection = self.ribbon_type_combo.currentText()
        self.ribbon_type_combo.blockSignals(True)
        self.ribbon_type_combo.clear()
        self.ribbon_type_combo.addItems(self.presets.keys())
        index = self.ribbon_type_combo.findText(current_selection)
        if index != -1: self.ribbon_type_combo.setCurrentIndex(index)
        self.ribbon_type_combo.blockSignals(False)
        self.update_spins_from_preset(self.ribbon_type_combo.currentText())

    def update_spins_from_preset(self, ribbon_name):
        data = self.presets.get(ribbon_name)
        if data:
            for side in self.controls:
                for key, widget in self.controls[side].items():
                    if key in data:
                        if isinstance(widget, QSpinBox):
                            widget.blockSignals(True)
                            widget.setValue(data[key])
                            widget.blockSignals(False)
        self.preview.update()

    def update_phrase_categories(self):
        self.phrase_category_right.blockSignals(True)
        self.phrase_category_left.blockSignals(True)
        self.phrase_category_right.clear()
        self.phrase_category_left.clear()
        if "경조사" in self.phrases:
            self.phrase_category_right.addItems(self.phrases["경조사"].keys())
        if "보내는이" in self.phrases:
            self.phrase_category_left.addItems(self.phrases["보내는이"].keys())
        self.phrase_category_right.blockSignals(False)
        self.phrase_category_left.blockSignals(False)
        self.reset_phrase_index('경조사')
        self.reset_phrase_index('보내는이')

    def reset_phrase_index(self, side):
        category_combo = self.phrase_category_right if side == '경조사' else self.phrase_category_left
        category = category_combo.currentText()
        if category:
            self.phrase_indices[side][category] = 0

    def cycle_phrase(self, side, op):
        widget = self.text_right_edit if side == "경조사" else self.text_left_edit
        category_combo = self.phrase_category_right if side == "경조사" else self.phrase_category_left
        category = category_combo.currentText()
        if not category or side not in self.phrases or category not in self.phrases[side]: return
        phrase_list = self.phrases[side][category]
        if not phrase_list: return
        current_index = self.phrase_indices[side].get(category, 0)
        if op == '+': current_index = (current_index + 1) % len(phrase_list)
        elif op == '-': current_index = (current_index - 1 + len(phrase_list)) % len(phrase_list)
        self.phrase_indices[side][category] = current_index
        widget.setText(phrase_list[current_index])
    
    def open_ribbon_settings(self):
        dialog = RibbonSettingsDialog(self.presets, self)
        if dialog.exec():
            self.presets = dialog.presets
            self.update_ribbon_combo()
            self.status_bar.showMessage("리본 설정이 저장되었습니다.")
            
    def _toggle_auto_font_size(self, checked): 
        self.controls['경조사']['글자크기'].setEnabled(not checked)
        self.controls['보내는이']['글자크기'].setEnabled(not checked)
        self.preview.update()

    def sync_and_update(self, value):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setValue(value)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()
        
    def sync_and_update_combo(self, index):
        if not self.sync_check.isChecked(): self.preview.update(); return
        sender = self.sender()
        for side in self.controls:
            for key, widget in self.controls[side].items():
                if widget == sender:
                    other_side = "보내는이" if side == "경조사" else "경조사"
                    self.controls[other_side][key].blockSignals(True)
                    self.controls[other_side][key].setCurrentIndex(index)
                    self.controls[other_side][key].blockSignals(False)
                    break
        self.preview.update()

    def get_config_for_side(self, side):
        config = {key: widget.value() if isinstance(widget, QSpinBox) else widget.currentText() for key, widget in self.controls[side].items()}
        config['text'] = self.text_right_edit.text() if side == "경조사" else self.text_left_edit.text()
        config['auto_font_size'] = self.auto_font_size_check.isChecked()
        return config

    def clear_all(self): self.status_bar.showMessage("새 리본 작업을 시작합니다.")
    def open_file(self): self.status_bar.showMessage("파일을 열었습니다.")
    def save_file(self): self.status_bar.showMessage("파일이 저장되었습니다.")
    def save_file_as(self): pass
    def show_help(self): QMessageBox.information(self, "도움말", "리본메이커 v8.9\n\n제작: 브릿지앱 전문가")
    def print_ribbon(self): self.status_bar.showMessage("인쇄 명령을 보냈습니다.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RibbonApp()
    window.show()
    sys.exit(app.exec())

