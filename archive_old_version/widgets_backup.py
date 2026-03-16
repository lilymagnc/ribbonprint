# -*- coding: utf-8 -*-
"""
리본 메이커 위젯 클래스 모듈
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QTransform, QFontMetrics
from PyQt6.QtCore import Qt, QRectF
from utils import get_font_for_char


class RibbonPreviewWidget(QWidget):
    """리본 미리보기 위젯"""
    
    def __init__(self, app_instance):
        super().__init__(app_instance)
        self.app = app_instance
        self.setMinimumSize(500, 700)
        self.padding = 15

    def paintEvent(self, event):
        """위젯 그리기 이벤트 처리"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(220, 220, 220))
        
        config_right = self.app.get_config_for_side('경조사')
        config_left = self.app.get_config_for_side('보내는이')
        
        total_original_width = config_right.get('리본넓이', 50) + config_left.get('리본넓이', 50) + 50
        max_original_length = max(config_right.get('리본길이', 400), config_left.get('리본길이', 400))
        
        if max_original_length <= 0 or total_original_width <= 0:
            return
            
        # 스케일 계산
        view_width = self.width() - self.padding * 2
        view_height = self.height() - self.padding * 2
        scale_w = view_width / total_original_width
        scale_h = view_height / max_original_length
        scale = min(scale_w, scale_h)
        
        # 리본 크기 계산
        scaled_width_right = config_right.get('리본넓이', 50) * scale
        scaled_width_left = config_left.get('리본넓이', 50) * scale
        scaled_spacing = 50 * scale
        scaled_height_right = config_right.get('리본길이', 400) * scale
        scaled_height_left = config_left.get('리본길이', 400) * scale
        
        total_scaled_width = scaled_width_right + scaled_width_left + scaled_spacing
        start_x = (self.width() - total_scaled_width) / 2
        start_y = (self.height() - max(scaled_height_right, scaled_height_left)) / 2
        
        # 리본 영역 정의
        rect_right = QRectF(start_x, start_y, scaled_width_right, scaled_height_right)
        rect_left = QRectF(start_x + scaled_width_right + scaled_spacing, start_y, scaled_width_left, scaled_height_left)
        
        # 요소들 그리기
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
        """가이드라인 그리기"""
        painter.save()
        
        # 중앙선
        center_pen = QPen(QColor(0, 0, 0, 100), 1, Qt.PenStyle.DashLine)
        painter.setPen(center_pen)
        center_x = rect.center().x()
        painter.drawLine(int(center_x), int(rect.top()), int(center_x), int(rect.bottom()))
        
        # 레이스 여백선
        layer_pen = QPen(QColor(0, 0, 255, 120), 1, Qt.PenStyle.DashLine)
        painter.setPen(layer_pen)
        lace_margin = config.get('레이스', 5) * scale
        left_line_x = rect.left() + lace_margin
        right_line_x = rect.right() - lace_margin
        painter.drawLine(int(left_line_x), int(rect.top()), int(left_line_x), int(rect.bottom()))
        painter.drawLine(int(right_line_x), int(rect.top()), int(right_line_x), int(rect.bottom()))
        
        painter.restore()

    def draw_ruler(self, painter, rect, original_length, scale):
        """눈금자 그리기"""
        painter.save()
        ruler_width = 25
        ruler_rect = QRectF(rect.left() - ruler_width, rect.top(), ruler_width, rect.height())
        
        if ruler_rect.left() < 0:
            ruler_rect.moveTo(rect.right(), rect.top())
            
        painter.fillRect(ruler_rect, QColor(14, 209, 69))
        pen = QPen(QColor("white"), 1)
        painter.setPen(pen)
        font = QFont("Arial", 8)
        painter.setFont(font)
        
        for y_mm in range(0, original_length + 1, 10):
            y_pos = rect.top() + y_mm * scale
            if y_pos > rect.bottom():
                break
                
            if y_mm % 50 == 0:
                painter.drawLine(int(ruler_rect.left() + 5), int(y_pos), int(ruler_rect.right()), int(y_pos))
                if y_mm % 100 == 0:
                    painter.drawText(int(ruler_rect.left()+2), int(y_pos + 10), str(y_mm))
            else:
                painter.drawLine(int(ruler_rect.left() + 15), int(y_pos), int(ruler_rect.right()), int(y_pos))
                
        painter.restore()

    def draw_margins(self, painter, rect, config, scale):
        """여백선 그리기"""
        painter.save()
        pen = QPen(QColor(255, 0, 0, 150), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        top_margin_y = rect.top() + config.get('상단여백', 80) * scale
        bottom_margin_y = rect.bottom() - config.get('하단여백', 50) * scale
        
        painter.drawLine(int(rect.left()), int(top_margin_y), int(rect.right()), int(top_margin_y))
        painter.drawLine(int(rect.left()), int(bottom_margin_y), int(rect.right()), int(bottom_margin_y))
        
        painter.restore()

    def render_side(self, painter, rect, config, scale):
        """텍스트 렌더링"""
        painter.save()
        text = config.get('text', '')
        
        if not text or rect.width() <= 0:
            painter.restore()
            return
            
        # 텍스트 블록 파싱
        blocks = self._parse_text_blocks(text)
        
        # 폰트 크기 계산
        base_font_size_pt = self._calculate_font_size(blocks, config, scale, rect)
        
        # 텍스트 렌더링
        self._render_text_blocks(painter, rect, config, scale, blocks, base_font_size_pt)
        
        painter.restore()

    def _parse_text_blocks(self, text):
        """텍스트를 블록으로 파싱"""
        blocks = []
        i = 0
        current_normal_block = ""
        
        while i < len(text):
            if text[i] == '[':
                if current_normal_block:
                    blocks.append({'type': 'normal', 'text': current_normal_block})
                    current_normal_block = ""
                try:
                    end_index = text.index(']', i)
                    substr = text[i+1:end_index]
                    
                    # 축소폰트 내용만 처리 ([ ] 는 공간 차지하지 않음)
                    if substr:  # 내용이 있을 때만 추가
                        blocks.append({'type': 'shrink', 'text': substr})
                    
                    i = end_index + 1
                except ValueError:
                    current_normal_block += text[i]
                    i += 1
            elif text[i] == '(' and i + 2 < len(text) and text[i+2] == ')' and text[i+1] in ['주', '유', '株']:
                if current_normal_block:
                    blocks.append({'type': 'normal', 'text': current_normal_block})
                    current_normal_block = ""
                blocks.append({'type': 'special', 'text': text[i:i+3]})
                i += 3
            elif text[i] == '/' and i > 0 and i < len(text) - 1:
                # "/" 앞뒤 글자를 2열로 배치
                left_char = text[i-1]
                right_char = text[i+1]
                # 이전 글자를 현재 블록에서 제거
                if current_normal_block and current_normal_block[-1] == left_char:
                    current_normal_block = current_normal_block[:-1]
                if current_normal_block:
                    blocks.append({'type': 'normal', 'text': current_normal_block})
                    current_normal_block = ""
                blocks.append({'type': 'two_column', 'left': left_char, 'right': right_char})
                i += 2  # "/" 다음 글자까지 건너뛰기
            else:
                current_normal_block += text[i]
                i += 1
                
        if current_normal_block:
            blocks.append({'type': 'normal', 'text': current_normal_block})
            
        return blocks

    def _calculate_font_size(self, blocks, config, scale, rect):
        """폰트 크기 계산"""
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
                        char_width = fm.horizontalAdvance(char)  # 기본 폭만 사용 (비율 적용 안함)
                        if char_width > max_char_width_px:
                            max_char_width_px = char_width
                    
                    if max_char_width_px <= target_pixel_width:
                        base_font_size_pt = temp_font_size_pt
                        break
                    temp_font_size_pt -= 1
                    
        return base_font_size_pt

    def _render_text_blocks(self, painter, rect, config, scale, blocks, base_font_size_pt):
        """텍스트 블록 렌더링 - 균등 분배"""
        top_margin = config.get('상단여백', 80) * scale
        bottom_margin = config.get('하단여백', 50) * scale
        printable_height = rect.height() - (top_margin + bottom_margin)
        base_v_scale = config.get('세로폰트', 100) / 100.0
        
        # 모든 렌더링 단위(글자/블록) 수집
        render_units = []
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 블록은 하나의 단위로 처리
                render_units.append({
                    'type': 'two_column',
                    'block': block,
                    'char_count': 1  # 하나의 렌더링 단위
                })
            elif block['type'] == 'special':
                # (주), (유), (株)는 하나의 단위로 처리
                render_units.append({
                    'type': 'special',
                    'block': block,
                    'char_count': 1  # 하나의 렌더링 단위
                })
            elif block['type'] == 'shrink':
                # [] 축소폰트는 하나의 덩어리로 처리 (간격도 축소)
                render_units.append({
                    'type': 'shrink',
                    'block': block,
                    'char_count': 1  # 하나의 렌더링 단위
                })
            else:
                # 일반 텍스트는 각 글자가 하나의 단위
                for char in block['text']:
                    render_units.append({
                        'type': 'normal',
                        'block': block,
                        'char': char,
                        'char_count': 1
                    })
        
        total_units = len(render_units)
        if total_units == 0:
            return
            
        # 폰트 높이 계산 (글자 배치를 위해) - 기본 높이만 사용 (비율 적용 안함)
        temp_font = QFont(get_font_for_char('가', config))
        temp_font.setPixelSize(int(base_font_size_pt * scale))
        temp_fm = QFontMetrics(temp_font)
        font_height = temp_fm.height()  # 세로비율 적용하지 않음
        
        # 1단계: 먼저 기본 세로비율로 글자를 균등분배
        # 첫 글자의 baseline은 상단여백 아래, 마지막 글자의 bottom은 하단여백 위
        start_baseline = rect.top() + top_margin + temp_fm.ascent()
        end_baseline = rect.bottom() - bottom_margin - temp_fm.descent()
        
        # 사용 가능한 세로 공간
        available_baseline_height = end_baseline - start_baseline
        
        if total_units == 1:
            # 글자가 하나면 가운데 배치
            y_positions = [start_baseline]
            effective_v_scale = base_v_scale
        else:
            # 여러 글자일 때 균등분배
            y_positions = []
            for i in range(total_units):
                ratio = i / (total_units - 1)
                baseline_y = start_baseline + available_baseline_height * ratio
                y_positions.append(baseline_y)
            
            # 2단계: 글자 겹침 검사 및 세로비율 자동 조정
            # 글자 간 실제 필요한 최소 간격 (ascent + descent)
            min_required_spacing = temp_fm.ascent() + temp_fm.descent()
            
            # 현재 배치에서 최소 간격 계산
            actual_min_spacing = float('inf')
            for i in range(total_units - 1):
                spacing = y_positions[i + 1] - y_positions[i]
                actual_min_spacing = min(actual_min_spacing, spacing)
            
            # 글자가 겹칠 위험이 있으면 세로비율 자동 축소
            scaled_min_required = min_required_spacing * base_v_scale
            if scaled_min_required > actual_min_spacing:
                # 간격에 맞는 세로비율 계산 (최소 30%까지만)
                optimal_v_scale = actual_min_spacing / min_required_spacing
                effective_v_scale = max(0.3, optimal_v_scale)
            else:
                effective_v_scale = base_v_scale
        
        # 각 단위 렌더링
        for i, unit in enumerate(render_units):
            # y_positions는 baseline 좌표이므로 ascent를 빼서 top 좌표로 변환
            current_y = y_positions[i] - temp_fm.ascent()
            
            if unit['type'] == 'two_column':
                self._render_two_column_unit(painter, rect, config, scale, unit['block'], base_font_size_pt, effective_v_scale, current_y)
            elif unit['type'] == 'special':
                self._render_special_unit(painter, rect, config, scale, unit['block'], base_font_size_pt, effective_v_scale, current_y)
            elif unit['type'] == 'shrink':
                self._render_shrink_unit(painter, rect, config, scale, unit['block'], base_font_size_pt, effective_v_scale, current_y)
            else:
                self._render_normal_unit(painter, rect, config, scale, unit['block'], unit['char'], base_font_size_pt, effective_v_scale, current_y)

    def _render_two_column_unit(self, painter, rect, config, scale, block, base_font_size_pt, base_v_scale, y_position):
        """2열 단위 렌더링"""
        left_char = block['left']
        right_char = block['right']
        
        # 왼쪽 글자 렌더링
        self._render_single_char(painter, rect, config, scale, left_char, base_font_size_pt, base_v_scale, y_position, 'left')
        # 오른쪽 글자 렌더링  
        self._render_single_char(painter, rect, config, scale, right_char, base_font_size_pt, base_v_scale, y_position, 'right')

    def _render_special_unit(self, painter, rect, config, scale, block, base_font_size_pt, base_v_scale, y_position):
        """특수 단위 ((주), (유), (株)) 렌더링"""
        special_text = block['text']
        size_ratio = config.get('(주)/(株)', 90) / 100.0
        scaled_font_size_px = int(base_font_size_pt * scale * size_ratio)
        if scaled_font_size_px <= 0:
            scaled_font_size_px = 1
        
        # 전체 텍스트의 폭 계산
        total_width = 0
        char_widths = []
        for char in special_text:
            font_name = get_font_for_char(char, config)
            font = QFont(font_name)
            font.setPixelSize(scaled_font_size_px)
            fm = QFontMetrics(font)
            char_width = fm.horizontalAdvance(char)
            char_widths.append(char_width)
            total_width += char_width
        
        h_scale = config.get('가로폰트', 100) / 100.0 * 0.8  # 80% 가로 축소
        v_scale = base_v_scale
        
        # 중앙 정렬을 위한 시작 x 좌표
        start_x = rect.center().x() - (total_width * h_scale) / 2
        
        # 각 글자를 가로로 배치
        current_x = start_x
        for i, char in enumerate(special_text):
            font_name = get_font_for_char(char, config)
            font = QFont(font_name)
            font.setPixelSize(scaled_font_size_px)
            painter.setFont(font)
            fm = QFontMetrics(font)
            
            transform = QTransform().scale(h_scale, v_scale)
            painter.setTransform(transform)
            
            char_y_pos = y_position + fm.ascent()
            painter.drawText(int(current_x / h_scale), int(char_y_pos), char)
            current_x += char_widths[i] * h_scale

    def _render_shrink_unit(self, painter, rect, config, scale, block, base_font_size_pt, base_v_scale, y_position):
        """축소폰트 단위 렌더링 (하나의 글자 공간에 여러 글자를 세로로 배치)"""
        shrink_text = block['text']
        if not shrink_text:
            return
            
        size_ratio = config.get('축소폰트', 70) / 100.0
        
        h_scale = config.get('가로폰트', 100) / 100.0
        v_scale = base_v_scale
        
        # 일반 글자 하나의 높이 (이 공간 안에 축소폰트들을 배치)
        normal_font = QFont(get_font_for_char('가', config))
        normal_font.setPixelSize(int(base_font_size_pt * scale))
        normal_fm = QFontMetrics(normal_font)
        available_height = normal_fm.height() * v_scale
        
        # 축소폰트 크기 - 설정값 그대로 사용 (70%)
        char_count = len(shrink_text)
        
        # 축소폰트 설정값을 그대로 적용 (추가 축소 없음)
        target_font_size = base_font_size_pt * size_ratio
        
        # 축소폰트로 각 글자 높이 계산
        temp_font = QFont(get_font_for_char(shrink_text[0], config))
        temp_font.setPixelSize(int(target_font_size * scale))
        temp_fm = QFontMetrics(temp_font)
        char_height = temp_fm.height() * v_scale
        
        # 간격 조절을 최소화 - 축소폰트는 원래 크기 유지
        actual_char_height = char_height * 0.9  # 90% 간격으로 조금만 압축
        total_height = char_count * actual_char_height
        
        # 전체 높이가 너무 크면 최소한만 조절
        if total_height > available_height:
            # 최대 80%까지만 압축 (너무 작아지지 않게)
            compression_ratio = max(0.8, available_height / total_height)
            actual_char_height = char_height * compression_ratio
            total_height = char_count * actual_char_height
        
        # 할당된 공간(y_position) 중앙에 축소폰트 블록 배치
        start_y = y_position - (total_height / 2) + (actual_char_height / 2)
        
        # 각 글자를 세로로 배치 (예쁘게)
        current_y = start_y
        for char in shrink_text:
            font_name = get_font_for_char(char, config)
            font = QFont(font_name)
            font.setPixelSize(int(target_font_size * scale))
            painter.setFont(font)
            fm = QFontMetrics(font)
            
            # 세로 스케일링 최소화 (축소폰트 크기 유지)
            final_v_scale = v_scale  # 원래 세로 비율 유지
            transform = QTransform().scale(h_scale, final_v_scale)
            painter.setTransform(transform)
            
            char_width = fm.horizontalAdvance(char)
            scaled_char_width = char_width * h_scale
            char_x = rect.center().x() - (scaled_char_width / 2)
            
            char_y_pos = current_y + fm.ascent()
            painter.drawText(int(char_x / h_scale), int(char_y_pos), char)
            
            # 다음 글자 위치
            current_y += actual_char_height

    def _render_normal_unit(self, painter, rect, config, scale, block, char, base_font_size_pt, base_v_scale, y_position):
        """일반 글자 단위 렌더링"""
        size_ratio = 1.0
        
        self._render_single_char(painter, rect, config, scale, char, base_font_size_pt * size_ratio, base_v_scale, y_position, 'center')

    def _render_single_char(self, painter, rect, config, scale, char, font_size_pt, v_scale, y_position, alignment='center'):
        """단일 글자 렌더링"""
        scaled_font_size_px = int(font_size_pt * scale)
        if scaled_font_size_px <= 0:
            scaled_font_size_px = 1
        
        font_name = get_font_for_char(char, config)
        font = QFont(font_name)
        font.setPixelSize(scaled_font_size_px)
        painter.setFont(font)
        fm = QFontMetrics(font)

        h_scale = config.get('가로폰트', 100) / 100.0
        
        transform = QTransform().scale(h_scale, v_scale)
        painter.setTransform(transform)

        char_width = fm.horizontalAdvance(char)
        scaled_char_width = char_width * h_scale
        
        # 정렬에 따른 X 좌표 계산
        if alignment == 'left':
            char_x = rect.center().x() - scaled_char_width
        elif alignment == 'right':
            char_x = rect.center().x()
        else:  # center
            char_x = rect.center().x() - (scaled_char_width / 2)
        
        # Y 좌표는 세로 스케일링에 영향받지 않도록 수정
        char_y_pos = y_position + fm.ascent()
        painter.drawText(int(char_x / h_scale), int(char_y_pos), char)
