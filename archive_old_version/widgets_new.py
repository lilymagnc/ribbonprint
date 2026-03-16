"""
완전히 새로운 텍스트 렌더링 로직
간단하고 명확한 균등분배 + 자동 세로비율 조정
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from utils import get_font_for_char
import re

class RibbonPreviewWidget(QWidget):
    """리본 미리보기 위젯 - 완전히 새로운 렌더링 로직"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 800)
        self.left_config = {}
        self.right_config = {}
    
    def update_config(self, left_config, right_config):
        """설정 업데이트"""
        self.left_config = left_config
        self.right_config = right_config
        self.update()
    
    def paintEvent(self, event):
        """페인트 이벤트"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 배경 그리기
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        # 리본 영역들 계산 및 그리기
        if self.left_config or self.right_config:
            self._draw_ribbons(painter)
    
    def _draw_ribbons(self, painter):
        """리본들 그리기"""
        widget_width = self.width()
        widget_height = self.height()
        
        # 좌우 리본 영역 계산
        ribbon_width = 50  # 기본값
        if self.left_config:
            ribbon_width = self.left_config.get('리본넓이', 50)
        elif self.right_config:
            ribbon_width = self.right_config.get('리본넓이', 50)
        
        scale = min(widget_width / (ribbon_width * 3), widget_height / 400)
        
        ribbon_width_px = ribbon_width * scale
        ribbon_height_px = 400 * scale
        spacing = 20 * scale
        
        # 중앙 정렬
        total_width = ribbon_width_px * 2 + spacing
        start_x = (widget_width - total_width) / 2
        start_y = (widget_height - ribbon_height_px) / 2
        
        # 왼쪽 리본
        if self.left_config and self.left_config.get('text'):
            left_rect = QRectF(start_x, start_y, ribbon_width_px, ribbon_height_px)
            self._draw_single_ribbon(painter, left_rect, self.left_config, scale)
        
        # 오른쪽 리본  
        if self.right_config and self.right_config.get('text'):
            right_rect = QRectF(start_x + ribbon_width_px + spacing, start_y, ribbon_width_px, ribbon_height_px)
            self._draw_single_ribbon(painter, right_rect, self.right_config, scale)
    
    def _draw_single_ribbon(self, painter, rect, config, scale):
        """단일 리본 그리기"""
        # 리본 배경
        painter.fillRect(rect, QColor(100, 200, 100))
        
        # 여백선 그리기
        top_margin = config.get('상단여백', 80) * scale
        bottom_margin = config.get('하단여백', 50) * scale
        
        painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.PenStyle.DashLine))
        painter.drawLine(rect.left(), rect.top() + top_margin, 
                        rect.right(), rect.top() + top_margin)
        painter.drawLine(rect.left(), rect.bottom() - bottom_margin,
                        rect.right(), rect.bottom() - bottom_margin)
        
        # 텍스트 렌더링 - 새로운 로직
        self._render_text_simple(painter, rect, config, scale)
    
    def _render_text_simple(self, painter, rect, config, scale):
        """완전히 새로운 간단한 텍스트 렌더링"""
        text = config.get('text', '')
        if not text:
            return
        
        # 기본 설정
        font_size = config.get('글자크기', 40)
        h_ratio = config.get('가로폰트', 100) / 100.0
        v_ratio = config.get('세로폰트', 100) / 100.0
        top_margin = config.get('상단여백', 80) * scale
        bottom_margin = config.get('하단여백', 50) * scale
        
        # 텍스트를 개별 글자로 분리 (특수 처리 포함)
        chars = self._parse_text_to_chars(text)
        if not chars:
            return
        
        # 사용 가능한 세로 공간
        available_height = rect.height() - top_margin - bottom_margin
        
        # 글자 하나의 기본 높이
        test_font = QFont('함초롱바탕')
        test_font.setPixelSize(int(font_size * scale))
        test_fm = QFontMetrics(test_font)
        base_char_height = test_fm.height()
        
        # 필요한 총 높이 계산
        total_needed_height = len(chars) * base_char_height * v_ratio
        
        # 자동 세로비율 조정
        if total_needed_height > available_height:
            # 세로비율을 자동으로 줄여서 맞춤
            v_ratio = available_height / (len(chars) * base_char_height)
            v_ratio = max(0.3, v_ratio)  # 최소 30%
        
        # 실제 글자 높이
        actual_char_height = base_char_height * v_ratio
        
        # 균등 분배 계산
        if len(chars) == 1:
            # 글자 하나면 중앙
            y_positions = [rect.top() + top_margin + available_height / 2 - actual_char_height / 2]
        else:
            # 여러 글자면 균등 분배
            y_positions = []
            for i in range(len(chars)):
                # 첫 글자는 상단여백 아래, 마지막 글자는 하단여백 위
                ratio = i / (len(chars) - 1)
                y = rect.top() + top_margin + ratio * (available_height - actual_char_height)
                y_positions.append(y)
        
        # 각 글자 렌더링
        for i, char in enumerate(chars):
            self._render_single_char_simple(painter, rect, char, y_positions[i], 
                                          font_size, scale, h_ratio, v_ratio, config)
    
    def _parse_text_to_chars(self, text):
        """텍스트를 개별 글자로 파싱 (특수 처리 포함)"""
        chars = []
        i = 0
        while i < len(text):
            # (주) 처리
            if i + 2 < len(text) and text[i] == '(' and text[i+2] == ')' and text[i+1] in ['주', '유', '株']:
                chars.append({'type': 'special', 'text': text[i:i+3]})
                i += 3
            # [] 축소폰트 처리  
            elif text[i] == '[':
                try:
                    end_idx = text.index(']', i)
                    inner_text = text[i+1:end_idx]
                    if inner_text:
                        chars.append({'type': 'shrink', 'text': inner_text})
                    i = end_idx + 1
                except ValueError:
                    chars.append({'type': 'normal', 'text': text[i]})
                    i += 1
            # 일반 글자
            else:
                chars.append({'type': 'normal', 'text': text[i]})
                i += 1
        return chars
    
    def _render_single_char_simple(self, painter, rect, char_info, y_pos, font_size, scale, h_ratio, v_ratio, config):
        """단일 글자 렌더링 - 간단 버전"""
        if char_info['type'] == 'normal':
            # 일반 글자
            self._draw_char(painter, rect, char_info['text'], y_pos, font_size, scale, h_ratio, v_ratio, config)
        
        elif char_info['type'] == 'special':
            # (주) 특수 처리
            special_ratio = config.get('(주)/(株)', 90) / 100.0
            special_size = font_size * special_ratio
            
            # 가로로 배치
            total_width = 0
            for c in char_info['text']:
                font = QFont(get_font_for_char(c, config))
                font.setPixelSize(int(special_size * scale))
                fm = QFontMetrics(font)
                total_width += fm.horizontalAdvance(c) * h_ratio * 0.8
            
            start_x = rect.center().x() - total_width / 2
            current_x = start_x
            
            for c in char_info['text']:
                font = QFont(get_font_for_char(c, config))
                font.setPixelSize(int(special_size * scale))
                painter.setFont(font)
                fm = QFontMetrics(font)
                
                transform = QTransform().scale(h_ratio * 0.8, v_ratio)
                painter.setTransform(transform)
                
                char_y = y_pos + fm.ascent()
                painter.drawText(int(current_x / (h_ratio * 0.8)), int(char_y), c)
                current_x += fm.horizontalAdvance(c) * h_ratio * 0.8
                
            painter.resetTransform()
        
        elif char_info['type'] == 'shrink':
            # [] 축소폰트
            shrink_ratio = config.get('축소폰트', 70) / 100.0
            shrink_size = font_size * shrink_ratio
            
            # 세로로 배치
            chars = char_info['text']
            char_height = shrink_size * scale * v_ratio * 0.9
            total_height = len(chars) * char_height
            
            start_y = y_pos + (font_size * scale * v_ratio - total_height) / 2
            
            for i, c in enumerate(chars):
                char_y = start_y + i * char_height
                self._draw_char(painter, rect, c, char_y, shrink_size, scale, h_ratio, v_ratio, config)
    
    def _draw_char(self, painter, rect, char, y_pos, font_size, scale, h_ratio, v_ratio, config):
        """기본 글자 그리기"""
        font_name = get_font_for_char(char, config)
        font = QFont(font_name)
        font.setPixelSize(int(font_size * scale))
        painter.setFont(font)
        fm = QFontMetrics(font)
        
        # 변형 적용
        transform = QTransform().scale(h_ratio, v_ratio)
        painter.setTransform(transform)
        
        # 중앙 정렬
        char_width = fm.horizontalAdvance(char) * h_ratio
        char_x = rect.center().x() - char_width / 2
        char_y = y_pos + fm.ascent()
        
        painter.drawText(int(char_x / h_ratio), int(char_y), char)
        painter.resetTransform()
