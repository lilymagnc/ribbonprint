# -*- coding: utf-8 -*-
"""
프린터 선택 다이얼로그
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from printer_bridge import PrinterManager
import logging

logger = logging.getLogger(__name__)


class PrinterSelectionDialog(QDialog):
    """프린터 선택 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("프린터 선택")
        self.setModal(True)
        self.resize(600, 400)
        
        self.printer_manager = PrinterManager()
        self.selected_printer = None
        
        self._setup_ui()
        self._refresh_printers()
        
    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        
        # 프린터 목록 그룹
        printer_group = QGroupBox("사용 가능한 프린터 (독자적인 브릿지 드라이버)")
        printer_layout = QVBoxLayout(printer_group)
        
        # 새로고침 버튼
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.clicked.connect(self._refresh_printers)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        printer_layout.addLayout(refresh_layout)
        
        # 프린터 테이블
        self.printer_table = QTableWidget()
        self.printer_table.setColumnCount(5)
        self.printer_table.setHorizontalHeaderLabels(["프린터 이름", "브랜드", "모델", "상태", "설명"])
        
        # 테이블 설정
        header = self.printer_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        self.printer_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.printer_table.setAlternatingRowColors(True)
        
        printer_layout.addWidget(self.printer_table)
        layout.addWidget(printer_group)
        
        # 프린터 정보 그룹
        info_group = QGroupBox("선택된 프린터 정보")
        info_layout = QVBoxLayout(info_group)
        
        self.printer_info_text = QTextEdit()
        self.printer_info_text.setMaximumHeight(100)
        self.printer_info_text.setReadOnly(True)
        info_layout.addWidget(self.printer_info_text)
        
        layout.addWidget(info_group)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("테스트 출력")
        self.test_btn.clicked.connect(self._test_print)
        self.test_btn.setEnabled(False)
        
        self.select_btn = QPushButton("선택")
        self.select_btn.clicked.connect(self._select_printer)
        self.select_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.test_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.select_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 테이블 선택 이벤트 연결
        self.printer_table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        
    def _refresh_printers(self):
        """프린터 목록 새로고침"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("검색 중...")
        
        try:
            printers = self.printer_manager.refresh_printers()
            self._update_printer_table(printers)
            
            if not printers:
                QMessageBox.information(self, "알림", 
                    "지원되는 프린터를 찾을 수 없습니다.\n\n"
                    "다음을 확인해주세요:\n"
                    "• 프린터가 연결되어 있는지\n"
                    "• 프린터 드라이버가 설치되어 있는지\n"
                    "• 프린터가 켜져 있는지\n\n"
                    "지원 브랜드: Epson (M/L 시리즈), HP (LaserJet, DeskJet, OfficeJet)")
                    
        except Exception as e:
            QMessageBox.critical(self, "오류", f"프린터 검색 중 오류가 발생했습니다:\n{str(e)}")
            logger.error(f"프린터 검색 오류: {e}")
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("새로고침")
    
    def _update_printer_table(self, printers):
        """프린터 테이블 업데이트"""
        self.printer_table.setRowCount(len(printers))
        
        for row, printer in enumerate(printers):
            # 프린터 이름
            name_item = QTableWidgetItem(printer['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, printer)
            self.printer_table.setItem(row, 0, name_item)
            
            # 브랜드
            brand_item = QTableWidgetItem(printer.get('brand', 'Unknown'))
            self.printer_table.setItem(row, 1, brand_item)
            
            # 모델
            model_item = QTableWidgetItem(printer['model'])
            self.printer_table.setItem(row, 2, model_item)
            
            # 상태
            status_item = QTableWidgetItem(printer['status'])
            if printer['status'] == 'Ready':
                status_item.setBackground(Qt.GlobalColor.green)
            else:
                status_item.setBackground(Qt.GlobalColor.gray)
            self.printer_table.setItem(row, 3, status_item)
            
            # 설명
            specs = self.printer_manager.bridge.PRINTER_MODELS.get(printer['model'], {})
            description = f"최대폭: {specs.get('max_width', 'N/A')}mm, DPI: {specs.get('dpi', 'N/A')}"
            desc_item = QTableWidgetItem(description)
            self.printer_table.setItem(row, 4, desc_item)
    
    def _on_selection_changed(self):
        """프린터 선택 변경 시 호출"""
        current_row = self.printer_table.currentRow()
        
        if current_row >= 0:
            printer_item = self.printer_table.item(current_row, 0)
            if printer_item:
                printer_info = printer_item.data(Qt.ItemDataRole.UserRole)
                self._update_printer_info(printer_info)
                self.select_btn.setEnabled(True)
                self.test_btn.setEnabled(printer_info['status'] == 'Ready')
        else:
            self.printer_info_text.clear()
            self.select_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
    
    def _update_printer_info(self, printer_info):
        """프린터 정보 업데이트"""
        specs = self.printer_manager.bridge.PRINTER_MODELS.get(printer_info['model'], {})
        
        info_text = f"""
프린터 이름: {printer_info['name']}
브랜드: {printer_info.get('brand', 'Unknown')}
모델: {printer_info['model']}
상태: {printer_info['status']}

기술 사양:
• 최대 폭: {specs.get('max_width', 'N/A')}mm
• 최대 길이: {specs.get('max_length', 'N/A')}mm
• 해상도: {specs.get('dpi', 'N/A')} DPI
• 드라이버 타입: {specs.get('driver_type', 'N/A')}
• 브릿지 드라이버: {'사용' if printer_info.get('bridge_driver', False) else 'N/A'}
        """.strip()
        
        self.printer_info_text.setText(info_text)
    
    def _test_print(self):
        """테스트 출력"""
        current_row = self.printer_table.currentRow()
        if current_row < 0:
            return
            
        printer_item = self.printer_table.item(current_row, 0)
        printer_info = printer_item.data(Qt.ItemDataRole.UserRole)
        
        # 프린터 선택
        if not self.printer_manager.select_printer(printer_info['name']):
            QMessageBox.critical(self, "오류", "프린터 선택에 실패했습니다.")
            return
        
        # 테스트 출력 데이터
        test_config = {
            '리본넓이': 50,
            '리본길이': 200,
            '상단여백': 20,
            '하단여백': 20,
            '레이스': 5,
            '글자크기': 30
        }
        
        test_text = {
            '경조사': 'TEST',
            '보내는이': '테스트 출력',
            'font': 'Arial'
        }
        
        try:
            success = self.printer_manager.print_ribbon(test_config, test_text)
            
            if success:
                QMessageBox.information(self, "성공", "테스트 출력이 완료되었습니다.")
            else:
                QMessageBox.warning(self, "경고", "테스트 출력에 실패했습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"테스트 출력 중 오류가 발생했습니다:\n{str(e)}")
            logger.error(f"테스트 출력 오류: {e}")
    
    def _select_printer(self):
        """프린터 선택"""
        current_row = self.printer_table.currentRow()
        if current_row < 0:
            return
            
        printer_item = self.printer_table.item(current_row, 0)
        printer_info = printer_item.data(Qt.ItemDataRole.UserRole)
        
        if printer_info['status'] != 'Ready':
            reply = QMessageBox.question(self, "확인", 
                f"선택한 프린터의 상태가 '{printer_info['status']}'입니다.\n"
                "그래도 선택하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.selected_printer = printer_info
        self.accept()
    
    def get_selected_printer(self):
        """선택된 프린터 정보 반환"""
        return self.selected_printer
