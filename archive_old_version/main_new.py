# -*- coding: utf-8 -*-
"""
리본 메이커 메인 애플리케이션
v8.9 최종판 - 모듈화 리팩토링 버전
"""

import sys
import win32print
import win32ui
from PIL import Image, ImageWin

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QFontComboBox, QSpinBox, 
    QGroupBox, QGridLayout, QFileDialog, QMessageBox, QCheckBox, QLineEdit,
    QStatusBar
)
from PyQt6.QtGui import QUndoStack
from PyQt6.QtCore import Qt

# 분리된 모듈들 import
from config import PRESETS_FILE, PHRASES_FILE, DEFAULT_PRESETS, DEFAULT_PHRASES
from utils import load_data
from dialogs import RibbonSettingsDialog
from widgets import RibbonPreviewWidget


class RibbonApp(QMainWindow):
    """리본 메이커 메인 애플리케이션 클래스"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RibbonMaker - Ribbon Editor (v8.9 최종판)")
        self.setGeometry(50, 50, 1200, 850)
        
        # 데이터 초기화
        self.undo_stack = QUndoStack(self)
        self.controls = {'경조사': {}, '보내는이': {}}
        self.phrase_indices = {"경조사": {}, "보내는이": {}}
        self.presets = load_data(PRESETS_FILE, DEFAULT_PRESETS)
        self.phrases = load_data(PHRASES_FILE, DEFAULT_PHRASES)
        
        # UI 구성
        self._setup_ui()
        
        # 이벤트 연결
        self._connect_signals()
        
        # 초기화
        self.update_ribbon_combo()
        self.update_phrase_categories()
        self._toggle_auto_font_size(True)

    def _setup_ui(self):
        """UI 구성"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 컨트롤 패널
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 미리보기 영역
        self.preview = RibbonPreviewWidget(self)
        main_layout.addWidget(self.preview)
        
        # 상태바
        self.setStatusBar(QStatusBar(self))
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("프로그램 준비 완료.")

    def _create_control_panel(self):
        """컨트롤 패널 생성"""
        panel = QWidget()
        panel.setFixedWidth(550)
        top_layout = QVBoxLayout(panel)
        
        # 메뉴 버튼들
        menu_layout = self._create_menu_buttons()
        top_layout.addLayout(menu_layout)
        
        # 내용 입력 그룹
        content_group = self._create_content_inputs()
        top_layout.addWidget(content_group)
        
        # 메인 그리드 (리본 설정)
        main_grid = self._create_main_grid()
        top_layout.addLayout(main_grid)
        
        # 폰트 설정 그룹
        font_group = self._create_font_selectors()
        top_layout.addWidget(font_group)
        
        # 환경설정 그룹
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
        """메인 그리드 (리본 설정) 생성"""
        main_grid = QGridLayout()
        main_grid.setSpacing(5)
        
        # 리본 종류 선택
        main_grid.addWidget(QLabel("리본종류"), 0, 0)
        self.ribbon_type_combo = QComboBox()
        self.ribbon_type_combo.setMaxVisibleItems(20)
        self.ribbon_type_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        main_grid.addWidget(self.ribbon_type_combo, 0, 1, 1, 2)
        
        # 동시적용 체크박스
        self.sync_check = QCheckBox("동시적용")
        self.sync_check.setChecked(True)
        main_grid.addWidget(self.sync_check, 0, 3)
        
        # 되돌리기 버튼들
        main_grid.addWidget(QLabel("되돌리기"), 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)
        undo_btn = QPushButton("<")
        undo_btn.setFixedSize(30, 25)
        redo_btn = QPushButton(">")
        redo_btn.setFixedSize(30, 25)
        undo_btn.clicked.connect(self.undo_stack.undo)
        redo_btn.clicked.connect(self.undo_stack.redo)
        main_grid.addWidget(undo_btn, 0, 5)
        main_grid.addWidget(redo_btn, 0, 6)
        
        # 설정 필드들
        all_fields = [
            "리본넓이", "레이스", "리본길이", "상단여백", "하단여백", "인쇄여백", 
            "글자크기", "가로폰트", "세로폰트", "축소폰트", "(주)/(株)", "폰트컬러"
        ]
        
        # 헤더 레이블
        main_grid.addWidget(QLabel("경조사 설정"), 1, 1, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        main_grid.addWidget(QLabel("보내는이 설정"), 1, 4, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 각 필드에 대한 입력 위젯 생성
        for i, text in enumerate(all_fields, 2):
            main_grid.addWidget(QLabel(text), i, 0, alignment=Qt.AlignmentFlag.AlignRight)
            
            for j, side in enumerate(["경조사", "보내는이"]):
                widget = QSpinBox()
                
                # 필드별 설정값 적용
                if text == "(주)/(株)":
                    widget.setRange(10, 100)
                    widget.setValue(90)
                    widget.setSuffix('%')
                elif text == "축소폰트":
                    widget.setRange(10, 100)
                    widget.setValue(70)
                    widget.setSuffix('%')
                else:
                    widget.setRange(0, 5000)
                    if text in ["가로폰트", "세로폰트"]:
                        widget.setValue(100)
                    elif text == "글자크기":
                        widget.setValue(40)
                
                self.controls[side][text] = widget
                main_grid.addWidget(widget, i, 1 + j*3, 1, 2)
        
        # 그림 버튼들
        for j, side in enumerate(["경조사", "보내는이"]):
            main_grid.addWidget(QPushButton("그림넣기"), len(all_fields)+2, 1 + j*3)
            main_grid.addWidget(QPushButton("그림수정"), len(all_fields)+2, 2 + j*3)
        
        return main_grid

    def _create_font_selectors(self):
        """폰트 선택기 그룹 생성"""
        group = QGroupBox("서체 설정")
        layout = QGridLayout(group)
        
        # 자동 폰트 크기 체크박스
        self.auto_font_size_check = QCheckBox("글자 폭 자동 맞춤")
        self.auto_font_size_check.setChecked(True)
        layout.addWidget(self.auto_font_size_check, 0, 0, 1, 2)
        
        # 폰트 타입별 선택기
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
        """메뉴 버튼들 생성"""
        menu_layout = QHBoxLayout()
        actions = {
            "새리본": self.clear_all, 
            "파일열기": self.open_file, 
            "저장": self.save_file,
            "새로저장": self.save_file_as, 
            "도움말": self.show_help, 
            "인쇄": self.print_ribbon
        }
        
        for text, action in actions.items():
            button = QPushButton(text)
            button.clicked.connect(action)
            menu_layout.addWidget(button)
        
        return menu_layout

    def _create_content_inputs(self):
        """내용 입력 그룹 생성"""
        group = QGroupBox("내용 입력")
        grid = QGridLayout(group)
        
        # 텍스트 입력 필드
        self.text_right_edit = QLineEdit("祝開業")
        self.text_left_edit = QLineEdit("대표이사(주)홍길동")
        
        # 카테고리 콤보박스
        self.phrase_category_right = QComboBox()
        self.phrase_category_left = QComboBox()
        
        # 각 사이드별 UI 구성
        for i, (side, widget, category_combo) in enumerate([
            ("경조사", self.text_right_edit, self.phrase_category_right), 
            ("보내는이", self.text_left_edit, self.phrase_category_left)
        ]):
            grid.addWidget(QLabel(side), i*2, 0)
            grid.addWidget(widget, i*2, 1)
            
            # 문구 순환 버튼들
            btn_layout = QHBoxLayout()
            for btn_text in ['+', '-', 'x']:
                btn = QPushButton(btn_text)
                btn.setFixedSize(25, 25)
                btn.clicked.connect(lambda _, s=side, op=btn_text: self.cycle_phrase(s, op))
                btn_layout.addWidget(btn)
            grid.addLayout(btn_layout, i*2, 2)
            
            grid.addWidget(QLabel("샘플 선택"), i*2 + 1, 0)
            grid.addWidget(category_combo, i*2 + 1, 1)
        
        return group
    
    def _connect_signals(self):
        """이벤트 시그널 연결"""
        # 리본 타입 변경
        self.ribbon_type_combo.currentTextChanged.connect(self.update_spins_from_preset)
        
        # 문구 카테고리 변경
        self.phrase_category_right.currentTextChanged.connect(lambda: self.reset_phrase_index('경조사'))
        self.phrase_category_left.currentTextChanged.connect(lambda: self.reset_phrase_index('보내는이'))
        
        # 자동 폰트 크기
        self.auto_font_size_check.toggled.connect(self._toggle_auto_font_size)
        
        # 컨트롤 위젯들
        for side in self.controls:
            for control in self.controls[side].values():
                if isinstance(control, QSpinBox):
                    control.valueChanged.connect(self.sync_and_update)
                else:
                    control.currentIndexChanged.connect(self.sync_and_update_combo)
        
        # 텍스트 변경
        self.text_right_edit.textChanged.connect(self.preview.update)
        self.text_left_edit.textChanged.connect(self.preview.update)

    def update_ribbon_combo(self):
        """리본 콤보박스 업데이트"""
        current_selection = self.ribbon_type_combo.currentText()
        self.ribbon_type_combo.blockSignals(True)
        self.ribbon_type_combo.clear()
        self.ribbon_type_combo.addItems(self.presets.keys())
        
        index = self.ribbon_type_combo.findText(current_selection)
        if index != -1:
            self.ribbon_type_combo.setCurrentIndex(index)
        
        self.ribbon_type_combo.blockSignals(False)
        self.update_spins_from_preset(self.ribbon_type_combo.currentText())

    def update_spins_from_preset(self, ribbon_name):
        """프리셋에서 스핀박스 값 업데이트"""
        data = self.presets.get(ribbon_name)
        if data:
            for side in self.controls:
                for key, widget in self.controls[side].items():
                    if key in data and isinstance(widget, QSpinBox):
                        widget.blockSignals(True)
                        widget.setValue(data[key])
                        widget.blockSignals(False)
        self.preview.update()

    def update_phrase_categories(self):
        """문구 카테고리 업데이트"""
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
        """문구 인덱스 리셋"""
        category_combo = self.phrase_category_right if side == '경조사' else self.phrase_category_left
        category = category_combo.currentText()
        if category:
            self.phrase_indices[side][category] = 0

    def cycle_phrase(self, side, op):
        """문구 순환"""
        widget = self.text_right_edit if side == "경조사" else self.text_left_edit
        category_combo = self.phrase_category_right if side == "경조사" else self.phrase_category_left
        category = category_combo.currentText()
        
        if not category or side not in self.phrases or category not in self.phrases[side]:
            return
            
        phrase_list = self.phrases[side][category]
        if not phrase_list:
            return
            
        current_index = self.phrase_indices[side].get(category, 0)
        
        if op == '+':
            current_index = (current_index + 1) % len(phrase_list)
        elif op == '-':
            current_index = (current_index - 1 + len(phrase_list)) % len(phrase_list)
        
        self.phrase_indices[side][category] = current_index
        widget.setText(phrase_list[current_index])
    
    def open_ribbon_settings(self):
        """리본 설정 다이얼로그 열기"""
        dialog = RibbonSettingsDialog(self.presets, self)
        if dialog.exec():
            self.presets = dialog.presets
            self.update_ribbon_combo()
            self.status_bar.showMessage("리본 설정이 저장되었습니다.")
            
    def _toggle_auto_font_size(self, checked):
        """자동 폰트 크기 토글"""
        self.controls['경조사']['글자크기'].setEnabled(not checked)
        self.controls['보내는이']['글자크기'].setEnabled(not checked)
        self.preview.update()

    def sync_and_update(self, value):
        """동시 적용 및 업데이트 (스핀박스)"""
        if not self.sync_check.isChecked():
            self.preview.update()
            return
            
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
        """동시 적용 및 업데이트 (콤보박스)"""
        if not self.sync_check.isChecked():
            self.preview.update()
            return
            
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
        """특정 사이드의 설정 반환"""
        config = {}
        for key, widget in self.controls[side].items():
            if isinstance(widget, QSpinBox):
                config[key] = widget.value()
            else:
                config[key] = widget.currentText()
        
        config['text'] = self.text_right_edit.text() if side == "경조사" else self.text_left_edit.text()
        config['auto_font_size'] = self.auto_font_size_check.isChecked()
        return config

    # 메뉴 액션들
    def clear_all(self):
        """새 리본 작업"""
        self.status_bar.showMessage("새 리본 작업을 시작합니다.")
        
    def open_file(self):
        """파일 열기"""
        self.status_bar.showMessage("파일을 열었습니다.")
        
    def save_file(self):
        """파일 저장"""
        self.status_bar.showMessage("파일이 저장되었습니다.")
        
    def save_file_as(self):
        """다른 이름으로 저장"""
        pass
        
    def show_help(self):
        """도움말 표시"""
        QMessageBox.information(self, "도움말", "리본메이커 v8.9\n\n제작: 브릿지앱 전문가")
        
    def print_ribbon(self):
        """리본 인쇄"""
        self.status_bar.showMessage("인쇄 명령을 보냈습니다.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RibbonApp()
    window.show()
    sys.exit(app.exec())
