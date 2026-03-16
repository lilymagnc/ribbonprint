# -*- coding: utf-8 -*-
"""
리본 메이커 메인 애플리케이션
v8.9 최종판 - 모듈화 리팩토링 버전
"""

import sys
import json
import os
from datetime import datetime
import win32print
import win32ui
from PIL import Image, ImageWin

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QFontComboBox, QSpinBox, 
    QGroupBox, QGridLayout, QFileDialog, QMessageBox, QCheckBox, QLineEdit,
    QStatusBar, QDialog
)
from PyQt6.QtGui import QUndoStack
from PyQt6.QtCore import Qt

# 분리된 모듈들 import
from config import PRESETS_FILE, PHRASES_FILE, DEFAULT_PRESETS, DEFAULT_PHRASES
from utils import load_data, extract_chinese_only
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
        self.presets = load_data(PRESETS_FILE, DEFAULT_PRESETS)
        self.phrases = load_data(PHRASES_FILE, DEFAULT_PHRASES)
        self.current_file_path = None  # 현재 열린 파일 경로
        
        # 이미지 관련 변수
        self.company_logo_path = None  # 회사 로고 경로
        
        # UI 구성
        self._setup_ui()
        
        # 이벤트 연결
        self._connect_signals()
        
        # 초기화
        self.update_ribbon_combo()
        self.update_phrase_combos()
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
        
        # 리본 설정 버튼
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
            "글자크기", "가로비율", "세로비율", "축소폰트", "축소폰트간격", "(주)/(株)", "폰트컬러"
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
                elif text == "축소폰트간격":
                    widget.setRange(50, 100)
                    widget.setValue(80)
                    widget.setSuffix('%')
                else:
                    widget.setRange(0, 5000)
                    if text in ["가로비율", "세로비율"]:
                        widget.setValue(100)
                        widget.setSuffix('%')
                    elif text == "글자크기":
                        widget.setValue(40)
                
                self.controls[side][text] = widget
                main_grid.addWidget(widget, i, 1 + j*3, 1, 2)
        
        # 그림 버튼들
        for j, side in enumerate(["경조사", "보내는이"]):
            if side == "보내는이":
                # 보내는이: 회사 로고 버튼
                company_logo_btn = QPushButton("회사로고넣기")
                company_logo_edit_btn = QPushButton("회사로고수정")
                company_logo_btn.clicked.connect(self.insert_company_logo)
                company_logo_edit_btn.clicked.connect(self.edit_company_logo)
                main_grid.addWidget(company_logo_btn, len(all_fields)+2, 1 + j*3)
                main_grid.addWidget(company_logo_edit_btn, len(all_fields)+2, 2 + j*3)
            else:
                # 경조사: 기존 그림 버튼 (향후 확장 가능)
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
        
        # 경조사어 선택 드롭다운 (모든 경조사어를 하나의 리스트로)
        self.phrase_combo_right = QComboBox()
        self.phrase_combo_right.setEditable(True)  # 직접 입력도 가능
        
        self.phrase_combo_left = QComboBox()
        self.phrase_combo_left.setEditable(True)  # 직접 입력도 가능
        
        # UI 구성
        grid.addWidget(QLabel("경조사"), 0, 0)
        grid.addWidget(self.text_right_edit, 0, 1)
        grid.addWidget(self.phrase_combo_right, 0, 2)
        
        grid.addWidget(QLabel("보내는이"), 1, 0)
        grid.addWidget(self.text_left_edit, 1, 1)
        grid.addWidget(self.phrase_combo_left, 1, 2)
        
        return group
    
    def _connect_signals(self):
        """이벤트 시그널 연결"""
        # 리본 타입 변경
        self.ribbon_type_combo.currentTextChanged.connect(self.update_spins_from_preset)
        
        # 문구 드롭다운 변경
        self.phrase_combo_right.currentTextChanged.connect(self._on_phrase_combo_changed)
        self.phrase_combo_left.currentTextChanged.connect(self._on_phrase_combo_changed)
        
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

    def _on_phrase_combo_changed(self, text):
        """문구 드롭다운 변경 처리"""
        # 카테고리 구분자인 경우 텍스트 입력하지 않음
        if text.startswith("--- ") and text.endswith(" ---"):
            return
        
        # 발신자에 따라 적절한 텍스트 필드에 설정
        sender = self.sender()
        if sender == self.phrase_combo_right:
            self.text_right_edit.setText(text)
        elif sender == self.phrase_combo_left:
            self.text_left_edit.setText(text)

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
                    if key in data:
                        if isinstance(widget, QSpinBox):
                            widget.blockSignals(True)
                            widget.setValue(data[key])
                            widget.blockSignals(False)
                        elif isinstance(widget, QFontComboBox):
                            # 폰트 콤보박스 기본값 설정
                            font_name = data[key]
                            index = widget.findText(font_name)
                            if index != -1:
                                widget.blockSignals(True)
                                widget.setCurrentIndex(index)
                                widget.blockSignals(False)
        self.preview.update()

    def update_phrase_combos(self):
        """문구 드롭다운 업데이트"""
        self.phrase_combo_right.blockSignals(True)
        self.phrase_combo_left.blockSignals(True)
        
        self.phrase_combo_right.clear()
        self.phrase_combo_left.clear()
        
        # 경조사 문구들을 오른쪽 드롭다운에 추가
        if "경조사" in self.phrases:
            for category, phrases in self.phrases["경조사"].items():
                # 카테고리 구분자 추가
                self.phrase_combo_right.addItem(f"--- {category} ---")
                for phrase in phrases:
                    self.phrase_combo_right.addItem(phrase)
        
        # 보내는이 문구들을 왼쪽 드롭다운에 추가
        if "보내는이" in self.phrases:
            for category, phrases in self.phrases["보내는이"].items():
                # 카테고리 구분자 추가
                self.phrase_combo_left.addItem(f"--- {category} ---")
                for phrase in phrases:
                    self.phrase_combo_left.addItem(phrase)
        
        self.phrase_combo_right.blockSignals(False)
        self.phrase_combo_left.blockSignals(False)
    
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
        
        # 가로비율, 세로비율을 위젯에서 인식할 수 있는 키로 변환
        if '가로비율' in config:
            config['가로폰트'] = config['가로비율']
        if '세로비율' in config:
            config['세로폰트'] = config['세로비율']
        
        # 텍스트 가져오기
        if side == "경조사":
            text = self.text_right_edit.text()
            # 경조사 텍스트에서 한자만 추출
            config['text'] = extract_chinese_only(text)
        else:
            config['text'] = self.text_left_edit.text()
        
        config['auto_font_size'] = self.auto_font_size_check.isChecked()
        return config

    # 메뉴 액션들
    def clear_all(self):
        """새 리본 작업"""
        # 현재 리본 타입 저장
        current_ribbon_type = self.ribbon_type_combo.currentText()
        
        # 리본종류를 제외한 모든 필드를 기본값으로 리셋
        self._reset_all_fields_to_default()
        
        # 리본 타입 복원
        ribbon_index = self.ribbon_type_combo.findText(current_ribbon_type)
        if ribbon_index != -1:
            self.ribbon_type_combo.setCurrentIndex(ribbon_index)
        
        # 현재 파일 경로 초기화
        self.current_file_path = None
        self._update_window_title()
        
        # 미리보기 업데이트
        self.preview.update()
        
        self.status_bar.showMessage("새 리본 작업을 시작합니다.")
        
    def open_file(self):
        """파일 열기"""
        # 윈도우 표준 파일 대화상자 사용
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "리본 파일 열기",
            os.path.expanduser("~/Documents"),  # 사용자 문서 폴더
            "리본 파일 (*.ribbon);;모든 파일 (*.*)"
        )
        
        if file_path:
            self._load_from_file(file_path)
        
    def save_file(self):
        """파일 저장"""
        if self.current_file_path:
            # 기존 파일이 있으면 그대로 저장
            self._save_to_file(self.current_file_path)
        else:
            # 새 파일로 저장
            self.save_file_as()
        
    def save_file_as(self):
        """다른 이름으로 저장"""
        # 윈도우 표준 파일 대화상자 사용
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "리본 파일 저장",
            os.path.expanduser("~/Documents"),  # 사용자 문서 폴더
            "리본 파일 (*.ribbon);;모든 파일 (*.*)"
        )
        
        if file_path:
            # 확장자가 없으면 .ribbon 추가
            if not file_path.endswith('.ribbon'):
                file_path += '.ribbon'
            
            self._save_to_file(file_path)
            self.current_file_path = file_path
            self._update_window_title()
        
    def show_help(self):
        """도움말 표시"""
        QMessageBox.information(self, "도움말", "리본메이커 v8.9\n\n제작: 브릿지앱 전문가")
        
    def print_ribbon(self):
        """리본 인쇄"""
        try:
            # 프린터 선택 다이얼로그 열기
            from printer_dialog import PrinterSelectionDialog
            dialog = PrinterSelectionDialog(self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_printer = dialog.get_selected_printer()
                if selected_printer:
                    self._perform_print(selected_printer)
                else:
                    self.status_bar.showMessage("프린터가 선택되지 않았습니다.")
            else:
                self.status_bar.showMessage("인쇄가 취소되었습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "인쇄 오류", f"인쇄 중 오류가 발생했습니다:\n{str(e)}")
            self.status_bar.showMessage("인쇄 실패")
    
    def _perform_print(self, printer_info):
        """실제 인쇄 수행"""
        try:
            from printer_bridge import PrinterManager
            
            # 프린터 매니저 생성 및 프린터 선택
            printer_manager = PrinterManager()
            if not printer_manager.select_printer(printer_info['name']):
                raise Exception("프린터 선택에 실패했습니다")
            
            # 현재 설정 수집
            config_right = self.get_config_for_side('경조사')
            config_left = self.get_config_for_side('보내는이')
            
            # 리본 설정
            ribbon_config = {
                '리본넓이': config_right.get('리본넓이', 50),
                '리본길이': config_right.get('리본길이', 400),
                '상단여백': config_right.get('상단여백', 80),
                '하단여백': config_right.get('하단여백', 50),
                '레이스': config_right.get('레이스', 5),
                '글자크기': config_right.get('글자크기', 40)
            }
            
            # 텍스트 설정
            text_config = {
                '경조사': config_right.get('text', ''),
                '보내는이': config_left.get('text', ''),
                'font': config_right.get('한글', '(한)마린_견궁서B')
            }
            
            # 인쇄 실행
            self.status_bar.showMessage("인쇄 중...")
            
            success = printer_manager.print_ribbon(ribbon_config, text_config)
            
            if success:
                self.status_bar.showMessage(f"인쇄 완료: {printer_info['name']}")
                QMessageBox.information(self, "인쇄 완료", 
                    f"리본이 성공적으로 인쇄되었습니다.\n\n"
                    f"프린터: {printer_info['name']}\n"
                    f"모델: {printer_info['model']}")
            else:
                raise Exception("인쇄에 실패했습니다")
                
        except Exception as e:
            QMessageBox.critical(self, "인쇄 오류", f"인쇄 중 오류가 발생했습니다:\n{str(e)}")
            self.status_bar.showMessage("인쇄 실패")

    def _save_to_file(self, file_path):
        """파일로 저장하는 헬퍼 메서드"""
        try:
            # 현재 설정 수집
            config_right = self.get_config_for_side('경조사')
            config_left = self.get_config_for_side('보내는이')
            
            # 리본 타입
            ribbon_type = self.ribbon_type_combo.currentText()
            
            # 저장할 데이터 구조
            save_data = {
                "version": "1.0",
                "created_date": datetime.now().isoformat(),
                "ribbon_type": ribbon_type,
                "settings": {
                    "경조사": config_right,
                    "보내는이": config_left
                },
                "phrases": {
                    "경조사": self.text_right_edit.text(),
                    "보내는이": self.text_left_edit.text()
                },
                "images": {
                    "company_logo": self.company_logo_path
                }
            }
            
            # JSON 파일로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            self.status_bar.showMessage(f"파일이 저장되었습니다: {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"파일 저장 중 오류가 발생했습니다:\n{str(e)}")
            self.status_bar.showMessage("파일 저장에 실패했습니다.")

    def _load_from_file(self, file_path):
        """파일에서 데이터를 불러오는 헬퍼 메서드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 버전 확인
            version = data.get('version', '1.0')
            if version != '1.0':
                QMessageBox.warning(self, "버전 경고", 
                    f"이 파일은 버전 {version}으로 생성되었습니다.\n"
                    f"현재 버전 1.0과 호환되지 않을 수 있습니다.")
            
            # 리본 타입 설정
            ribbon_type = data.get('ribbon_type', '기본')
            ribbon_index = self.ribbon_type_combo.findText(ribbon_type)
            if ribbon_index != -1:
                self.ribbon_type_combo.setCurrentIndex(ribbon_index)
            
            # 설정값 적용
            settings = data.get('settings', {})
            for side in ['경조사', '보내는이']:
                if side in settings:
                    self._apply_settings_to_ui(side, settings[side])
            
            # 문구 설정
            phrases = data.get('phrases', {})
            if '경조사' in phrases:
                self.text_right_edit.setText(phrases['경조사'])
            if '보내는이' in phrases:
                self.text_left_edit.setText(phrases['보내는이'])
            
            # 이미지 설정
            images = data.get('images', {})
            if 'company_logo' in images and images['company_logo']:
                self.company_logo_path = images['company_logo']
            
            # 현재 파일 경로 저장
            self.current_file_path = file_path
            self._update_window_title()
            
            # 미리보기 업데이트
            self.preview.update()
            
            self.status_bar.showMessage(f"파일을 열었습니다: {os.path.basename(file_path)}")
            
        except FileNotFoundError:
            QMessageBox.critical(self, "파일 오류", "파일을 찾을 수 없습니다.")
            self.status_bar.showMessage("파일을 찾을 수 없습니다.")
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "파일 오류", f"파일 형식이 올바르지 않습니다:\n{str(e)}")
            self.status_bar.showMessage("파일 형식 오류")
        except Exception as e:
            QMessageBox.critical(self, "파일 오류", f"파일을 열 수 없습니다:\n{str(e)}")
            self.status_bar.showMessage("파일 열기 실패")

    def _apply_settings_to_ui(self, side, settings):
        """설정값을 UI에 적용하는 헬퍼 메서드"""
        for key, value in settings.items():
            if key in self.controls[side]:
                widget = self.controls[side][key]
                if isinstance(widget, QSpinBox):
                    widget.blockSignals(True)
                    widget.setValue(value)
                    widget.blockSignals(False)
                elif isinstance(widget, QFontComboBox):
                    widget.blockSignals(True)
                    index = widget.findText(value)
                    if index != -1:
                        widget.setCurrentIndex(index)
                    widget.blockSignals(False)
        
        # 자동 폰트 크기 설정
        if 'auto_font_size' in settings:
            self.auto_font_size_check.blockSignals(True)
            self.auto_font_size_check.setChecked(settings['auto_font_size'])
            self.auto_font_size_check.blockSignals(False)

    def _reset_all_fields_to_default(self):
        """모든 필드를 기본값으로 리셋"""
        # 기본 프리셋 데이터 가져오기
        default_preset = DEFAULT_PRESETS.get("기본", {})
        
        # 모든 컨트롤 위젯 리셋
        for side in ['경조사', '보내는이']:
            for key, widget in self.controls[side].items():
                if isinstance(widget, QSpinBox):
                    # 기본값 설정
                    if key in default_preset:
                        widget.blockSignals(True)
                        widget.setValue(default_preset[key])
                        widget.blockSignals(False)
                    else:
                        # 기본값이 없으면 100% 또는 0으로 설정
                        widget.blockSignals(True)
                        if key in ['가로비율', '세로비율', '축소폰트', '(주)/(株)', '축소폰트간격']:
                            widget.setValue(100)
                        elif key in ['리본넓이', '레이스', '리본길이', '상단여백', '하단여백', '인쇄여백', '글자크기']:
                            widget.setValue(0)
                        else:
                            widget.setValue(0)
                        widget.blockSignals(False)
                elif isinstance(widget, QFontComboBox):
                    # 폰트는 기본값으로 설정
                    widget.blockSignals(True)
                    if key in default_preset:
                        index = widget.findText(default_preset[key])
                        if index != -1:
                            widget.setCurrentIndex(index)
                    widget.blockSignals(False)
        
        # 자동 폰트 크기 체크박스 리셋
        self.auto_font_size_check.blockSignals(True)
        self.auto_font_size_check.setChecked(True)
        self.auto_font_size_check.blockSignals(False)
        
        # 텍스트 입력 필드 리셋
        self.text_right_edit.clear()
        self.text_left_edit.clear()
        
        # 문구 드롭다운 리셋
        self.phrase_combo_right.setCurrentIndex(0)
        self.phrase_combo_left.setCurrentIndex(0)
        
        # 이미지 경로 초기화
        self.company_logo_path = None

    def insert_company_logo(self):
        """회사 로고 삽입"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "회사 로고 선택",
            os.path.expanduser("~/Documents"),
            "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.gif);;모든 파일 (*.*)"
        )
        
        if file_path:
            self.company_logo_path = file_path
            self.preview.update()
            self.status_bar.showMessage(f"회사 로고가 삽입되었습니다: {os.path.basename(file_path)}")

    def edit_company_logo(self):
        """회사 로고 수정"""
        if self.company_logo_path:
            # 기존 로고가 있으면 교체
            self.insert_company_logo()
        else:
            QMessageBox.information(self, "알림", "삽입된 회사 로고가 없습니다.\n먼저 '회사로고넣기'를 클릭해주세요.")


    def _update_window_title(self):
        """윈도우 제목 업데이트"""
        if self.current_file_path:
            filename = os.path.basename(self.current_file_path)
            self.setWindowTitle(f"RibbonMaker - Ribbon Editor (v8.9 최종판) - {filename}")
        else:
            self.setWindowTitle("RibbonMaker - Ribbon Editor (v8.9 최종판)")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RibbonApp()
    window.show()
    sys.exit(app.exec())
