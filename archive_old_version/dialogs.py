# -*- coding: utf-8 -*-
"""
리본 메이커 다이얼로그 클래스 모듈
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from utils import save_presets


class RibbonSettingsDialog(QDialog):
    """리본 종류 설정 다이얼로그"""
    
    def __init__(self, presets_data, parent=None):
        super().__init__(parent)
        self.presets = presets_data.copy()
        self.setWindowTitle("리본 종류 설정")
        self.setMinimumSize(800, 400)
        self._setup_ui()
        
    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        
        # 상단 레이아웃
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("프린터 모델:"))
        printer_combo = QComboBox()
        printer_combo.addItems(["Epson-M105"])
        top_layout.addWidget(printer_combo)
        top_layout.addStretch()
        
        # 버튼들
        add_btn = QPushButton("리본 추가")
        del_btn = QPushButton("리스트 삭제")
        add_btn.clicked.connect(self.add_row)
        del_btn.clicked.connect(self.remove_row)
        top_layout.addWidget(add_btn)
        top_layout.addWidget(del_btn)
        layout.addLayout(top_layout)
        
        # 테이블
        self.table = QTableWidget()
        self.column_headers = ["리본이름", "넓이", "레이스", "길이", "상단", "하단", "여백"]
        self.table.setColumnCount(len(self.column_headers))
        self.table.setHorizontalHeaderLabels(self.column_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.populate_table()
        
        # 하단 버튼
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
        """테이블에 프리셋 데이터 채우기"""
        self.table.setRowCount(len(self.presets))
        key_map = {
            "리본넓이": "넓이", 
            "레이스": "레이스", 
            "리본길이": "길이", 
            "상단여백": "상단", 
            "하단여백": "하단", 
            "인쇄여백": "여백"
        }
        
        for row, (name, data) in enumerate(self.presets.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            for key, col_name in key_map.items():
                if col_name in self.column_headers:
                    col_index = self.column_headers.index(col_name)
                    self.table.setItem(row, col_index, QTableWidgetItem(str(data.get(key, ''))))

    def add_row(self):
        """행 추가"""
        self.table.insertRow(self.table.rowCount())

    def remove_row(self):
        """선택된 행 삭제"""
        current_row = self.table.currentRow()
        if current_row > -1:
            self.table.removeRow(current_row)

    def accept(self):
        """설정 저장 및 다이얼로그 닫기"""
        new_presets = {}
        key_map_inv = {
            "넓이": "리본넓이", 
            "레이스": "레이스", 
            "길이": "리본길이", 
            "상단": "상단여백", 
            "하단": "하단여백", 
            "여백": "인쇄여백"
        }
        
        for row in range(self.table.rowCount()):
            try:
                name_item = self.table.item(row, 0)
                if not name_item or not name_item.text():
                    continue
                    
                name = name_item.text()
                data = {}
                
                for col in range(1, self.table.columnCount()):
                    header = self.column_headers[col]
                    key = key_map_inv.get(header)
                    item = self.table.item(row, col)
                    if key and item and item.text():
                        data[key] = int(item.text())
                        
                new_presets[name] = data
                
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "입력 오류", f"{row+1}행에 잘못된 숫자 형식이 있습니다.")
                return
                
        self.presets = new_presets
        save_presets(self.presets)
        super().accept()
