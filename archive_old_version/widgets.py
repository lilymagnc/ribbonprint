# -*- coding: utf-8 -*-
"""
리본 메이커 위젯 클래스 모듈
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QTransform, QFontMetrics, QPixmap
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
        
        # 중앙선 (검은색 점선)
        center_pen = QPen(QColor(0, 0, 0, 150), 1, Qt.PenStyle.DashLine)
        painter.setPen(center_pen)
        center_x = rect.center().x()
        painter.drawLine(int(center_x), int(rect.top()), int(center_x), int(rect.bottom()))
        
        # 레이스 여백선 (파란색 점선) - 텍스트 영역 경계
        lace_margin = config.get('레이스', 5) * scale
        if lace_margin > 0:
            layer_pen = QPen(QColor(0, 0, 255, 150), 1, Qt.PenStyle.DashLine)
            painter.setPen(layer_pen)
            left_line_x = rect.left() + lace_margin
            right_line_x = rect.right() - lace_margin
            
            # 레이스 선이 리본 경계 내에 있는지 확인
            if left_line_x < right_line_x:
                painter.drawLine(int(left_line_x), int(rect.top()), int(left_line_x), int(rect.bottom()))
                painter.drawLine(int(right_line_x), int(rect.top()), int(right_line_x), int(rect.bottom()))
                
                # 텍스트 영역 표시 (연한 파란색 배경)
                text_area_rect = QRectF(left_line_x, rect.top(), right_line_x - left_line_x, rect.height())
                painter.fillRect(text_area_rect, QColor(0, 100, 255, 30))
        
        # 리본 경계선 (빨간색 실선)
        border_pen = QPen(QColor(255, 0, 0, 200), 2, Qt.PenStyle.SolidLine)
        painter.setPen(border_pen)
        painter.drawRect(rect)
        
        # 디버그 정보 표시 (작은 폰트로)
        debug_font = QFont("Arial", 8)
        painter.setFont(debug_font)
        painter.setPen(QPen(QColor(0, 0, 0, 200)))
        
        ribbon_width = config.get('리본넓이', 50)
        lace_value = config.get('레이스', 5)
        text_area_width = ribbon_width - (lace_value * 2)
        
        debug_text = f"리본: {ribbon_width}mm, 레이스: {lace_value}mm, 텍스트영역: {text_area_width}mm"
        painter.drawText(int(rect.left() + 5), int(rect.top() + 15), debug_text)
        
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
        font = QFont("(한)마린_견궁서B", 8)
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
        """텍스트 및 이미지 렌더링"""
        painter.save()
        text = config.get('text', '')
        
        # 텍스트 렌더링
        if text and rect.width() > 0:
            # 텍스트 블록 파싱
            blocks = self._parse_text_blocks(text)
            
            # 폰트 크기 계산
            base_font_size_pt = self._calculate_font_size(blocks, config, scale, rect)
            
            # 텍스트 렌더링
            self._render_text_blocks(painter, rect, config, scale, blocks, base_font_size_pt)
        
        # 이미지 렌더링
        self._render_images(painter, rect, config, scale)
        
        painter.restore()

    def _render_images(self, painter, rect, config, scale):
        """이미지 렌더링"""
        # 보내는이 영역에만 회사 로고 렌더링
        if hasattr(self.app, 'company_logo_path') and self.app.company_logo_path:
            self._render_company_logo(painter, rect, config, scale)
        

    def _render_company_logo(self, painter, rect, config, scale):
        """회사 로고 렌더링"""
        try:
            pixmap = QPixmap(self.app.company_logo_path)
            if pixmap.isNull():
                return
            
            # 글씨 크기와 동일한 크기로 조정
            font_size = config.get('글자크기', 40)
            logo_size = int(font_size * scale)
            
            # 이미지 크기 조정
            scaled_pixmap = pixmap.scaled(logo_size, logo_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # 텍스트와 겹치지 않도록 위치 계산
            text_center_x = rect.center().x()
            text_center_y = rect.center().y()
            
            # 텍스트 영역을 피해서 로고 위치 조정
            logo_x = text_center_x - scaled_pixmap.width() // 2
            logo_y = text_center_y - scaled_pixmap.height() // 2
            
            # 리본 영역 내에 있는지 확인
            if (rect.left() <= logo_x <= rect.right() - scaled_pixmap.width() and
                rect.top() <= logo_y <= rect.bottom() - scaled_pixmap.height()):
                painter.drawPixmap(int(logo_x), int(logo_y), scaled_pixmap)
                
        except Exception as e:
            print(f"회사 로고 렌더링 오류: {e}")


    def _convert_to_light_gray(self, pixmap):
        """이미지를 연한 회색으로 변환"""
        try:
            # QPixmap을 QImage로 변환
            image = pixmap.toImage()
            
            # 각 픽셀을 연한 회색으로 변환
            for x in range(image.width()):
                for y in range(image.height()):
                    pixel = image.pixel(x, y)
                    # 알파 채널 유지
                    alpha = (pixel >> 24) & 0xFF
                    if alpha > 0:  # 투명하지 않은 픽셀만 처리
                        # 연한 회색 (RGB: 200, 200, 200)으로 설정
                        gray_pixel = (alpha << 24) | (200 << 16) | (200 << 8) | 200
                        image.setPixel(x, y, gray_pixel)
            
            # QImage를 다시 QPixmap으로 변환
            return QPixmap.fromImage(image)
            
        except Exception as e:
            print(f"이미지 색상 변환 오류: {e}")
            return pixmap  # 오류 시 원본 반환

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
                        # [] 안에서 (주), (유), (株) 특수 블록 처리
                        if substr in ['(주)', '(유)', '(株)']:
                            blocks.append({'type': 'special', 'text': substr})
                        # [] 안에서 / 처리
                        elif '/' in substr:
                            # / 앞뒤 텍스트를 분리
                            parts = substr.split('/', 1)
                            if len(parts) == 2:
                                left_text = parts[0].strip()
                                right_text = parts[1].strip()
                                blocks.append({'type': 'shrink_two_column', 'left': left_text, 'right': right_text})
                            else:
                                blocks.append({'type': 'shrink', 'text': substr})
                        else:
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
            
            if blocks and printable_width_px > 0:
                # 일반 텍스트와 축소폰트를 분리하여 각각 계산
                normal_blocks = [b for b in blocks if b['type'] not in ['shrink', 'shrink_two_column']]
                shrink_blocks = [b for b in blocks if b['type'] in ['shrink', 'shrink_two_column']]
                
                # 일반 텍스트 폰트 크기 계산 (0.95 적용)
                normal_font_size = base_font_size_pt
                if normal_blocks:
                    normal_font_size = self._calculate_font_size_for_blocks(normal_blocks, config, scale, printable_width_px * 0.95)
                
                # 축소폰트 크기 계산 (0.75 적용)
                shrink_font_size = base_font_size_pt
                if shrink_blocks:
                    shrink_font_size = self._calculate_font_size_for_blocks(shrink_blocks, config, scale, printable_width_px * 0.75)
                
                # 일반 텍스트가 있으면 일반 텍스트 크기를 우선시, 없으면 축소폰트 크기 사용
                if normal_blocks:
                    base_font_size_pt = normal_font_size
                else:
                    base_font_size_pt = shrink_font_size
                    
        return base_font_size_pt

    def _calculate_font_size_for_blocks(self, blocks, config, scale, target_pixel_width):
        """특정 블록들에 대한 폰트 크기 계산"""
        temp_font_size_pt = 150
        while temp_font_size_pt > 5:
            max_char_width_px = 0
            
            for b in blocks:
                if b['type'] == 'two_column':
                    # 2열의 경우 각 열의 최대 폭만 고려
                    left_char = b['left']
                    right_char = b['right']
                    for char in [left_char, right_char]:
                        font = QFont(get_font_for_char(char, config))
                        font.setPixelSize(int(temp_font_size_pt * scale))
                        fm = QFontMetrics(font)
                        char_width = fm.horizontalAdvance(char)
                        if char_width > max_char_width_px:
                            max_char_width_px = char_width
                elif b['type'] == 'shrink_two_column':
                    # 축소폰트 2열의 경우 각 열의 최대 폭만 고려 (더 보수적으로)
                    left_text = b.get('left', '')
                    right_text = b.get('right', '')
                    for text in [left_text, right_text]:
                        for char in text:
                            font = QFont(get_font_for_char(char, config))
                            # 2열 텍스트는 90% 크기로 계산 (더 보수적)
                            adjusted_font_size = int(temp_font_size_pt * scale * 0.9)
                            font.setPixelSize(adjusted_font_size)
                            fm = QFontMetrics(font)
                            char_width = fm.horizontalAdvance(char)
                            if char_width > max_char_width_px:
                                max_char_width_px = char_width
                else:
                    # 일반 텍스트의 경우
                    text = b.get('text', '')
                    for char in text:
                        font = QFont(get_font_for_char(char, config))
                        font.setPixelSize(int(temp_font_size_pt * scale))
                        fm = QFontMetrics(font)
                        char_width = fm.horizontalAdvance(char)
                        if char_width > max_char_width_px:
                            max_char_width_px = char_width
            
            if max_char_width_px <= target_pixel_width:
                return temp_font_size_pt
            temp_font_size_pt -= 1
        
        return temp_font_size_pt

    def _render_text_blocks(self, painter, rect, config, scale, blocks, base_font_size_pt):
        """텍스트 블록 렌더링 - 균등 분배"""
        top_margin = config.get('상단여백', 80) * scale
        bottom_margin = config.get('하단여백', 50) * scale
        printable_height = rect.height() - (top_margin + bottom_margin)
        base_v_scale = config.get('세로폰트', 100) / 100.0
        
        # 모든 렌더링 단위(글자/블록) 수집
        # 베이스 폰트 높이(레이아웃 단위)를 먼저 계산
        base_font_for_layout = QFont(get_font_for_char('가', config))
        base_font_for_layout.setPixelSize(int(base_font_size_pt * scale))
        base_fm_for_layout = QFontMetrics(base_font_for_layout)
        layout_unit_height = base_fm_for_layout.height()  # 세로비율 미적용(레이아웃 간격)
        render_units = []
        for block in blocks:
            if block['type'] == 'two_column':
                # 2열 블록은 하나의 단위로 처리
                render_units.append({
                    'type': 'two_column',
                    'block': block,
                    'char_count': 1,
                    'units': 1
                })
            elif block['type'] == 'special':
                # (주), (유), (株)는 하나의 단위로 처리
                render_units.append({
                    'type': 'special',
                    'block': block,
                    'char_count': 1,
                    'units': 1
                })
            elif block['type'] == 'shrink':
                # [] 축소폰트는 내부 글자 수와 크기에 따라 더 많은 세로 공간을 차지
                size_ratio = config.get('축소폰트', 70) / 100.0
                # 축소 글자의 대략적인 픽셀 높이(세로비율 적용)
                shrink_font = QFont(get_font_for_char('가', config))
                shrink_font.setPixelSize(int(base_font_size_pt * size_ratio * scale))
                shrink_fm = QFontMetrics(shrink_font)
                shrink_glyph_h = shrink_fm.height() * base_v_scale
                # 한 줄이 필요로 하는 레이아웃 단위 수 (여유 포함)
                from math import ceil
                per_line_needed = shrink_glyph_h / max(1.0, layout_unit_height)
                per_line_needed *= 1.15  # 여유 15%
                units_per_line = max(1, int(ceil(per_line_needed)))
                total_units_needed = units_per_line * max(1, len(block.get('text', '')))
                
                # 축소폰트 간격 설정에 따라 전체 블록이 차지하는 공간 조정
                shrink_spacing_ratio = config.get('축소폰트간격', 80) / 100.0
                total_units_needed = int(total_units_needed * shrink_spacing_ratio)
                render_units.append({
                    'type': 'shrink',
                    'block': block,
                    'char_count': 1,
                    'units': total_units_needed
                })
            elif block['type'] == 'shrink_two_column':
                # [] 안에서 / 처리된 2열 축소폰트
                size_ratio = config.get('축소폰트', 70) / 100.0
                shrink_font = QFont(get_font_for_char('가', config))
                shrink_font.setPixelSize(int(base_font_size_pt * size_ratio * scale))
                shrink_fm = QFontMetrics(shrink_font)
                shrink_glyph_h = shrink_fm.height() * base_v_scale
                
                # 왼쪽과 오른쪽 텍스트 중 더 긴 것을 기준으로 단위 계산
                left_text = block.get('left', '')
                right_text = block.get('right', '')
                max_text_length = max(len(left_text), len(right_text))
                
                from math import ceil
                per_line_needed = shrink_glyph_h / max(1.0, layout_unit_height)
                per_line_needed *= 1.15  # 여유 15%
                units_per_line = max(1, int(ceil(per_line_needed)))
                total_units_needed = units_per_line * max(1, max_text_length)
                
                # 축소폰트 간격 설정에 따라 전체 블록이 차지하는 공간 조정
                shrink_spacing_ratio = config.get('축소폰트간격', 80) / 100.0
                total_units_needed = int(total_units_needed * shrink_spacing_ratio)
                render_units.append({
                    'type': 'shrink_two_column',
                    'block': block,
                    'char_count': 1,
                    'units': total_units_needed
                })
            else:
                # 일반 텍스트는 각 글자가 하나의 단위
                for char in block['text']:
                    render_units.append({
                        'type': 'normal',
                        'block': block,
                        'char': char,
                        'char_count': 1,
                        'units': 1
                    })
        
        total_units = len(render_units)
        if total_units == 0:
            return
            
        # 폰트 높이 계산 (글자 배치를 위해) - 기본 높이만 사용 (비율 적용 안함)
        temp_font = QFont(get_font_for_char('가', config))
        temp_font.setPixelSize(int(base_font_size_pt * scale))
        temp_fm = QFontMetrics(temp_font)
        font_height = temp_fm.height()  # 세로비율 적용하지 않음
        
        # 간단하고 확실한 글자 배치 (Baseline 균등 배치)
        available_height = rect.bottom() - bottom_margin - rect.top() - top_margin

        # 기준 폰트의 ascent/descent로 baseline 범위를 계산
        # 세로비율을 고려하여 상단여백에 추가 여유 공간 확보
        ascent_height = temp_fm.ascent()
        descent_height = temp_fm.descent()
        # 세로비율이 클 때 텍스트가 위로 확장되므로 상단에 여유 공간 추가
        vertical_expansion = ascent_height * (base_v_scale - 1.0) if base_v_scale > 1.0 else 0
        baseline_start = rect.top() + top_margin + ascent_height + vertical_expansion
        baseline_end = rect.bottom() - bottom_margin - descent_height

        # 총 슬롯 수(레이아웃 단위 합)
        total_slots = sum(u.get('units', 1) for u in render_units)
        total_baseline_span = max(1.0, baseline_end - baseline_start)
        if total_slots <= 1:
            step = total_baseline_span
        else:
            step = total_baseline_span / (total_slots - 1)

        # 세로비율은 한 슬롯 간격을 넘지 않도록 제한
        max_v_scale_allowed = step / max(1.0, font_height)
        effective_v_scale = min(base_v_scale, max(0.3, max_v_scale_allowed))

        # 각 유닛의 중심 baseline과 셀 높이를 계산
        y_cells = []  # (y, cell_height)
        cursor = 0.0
        for unit in render_units:
            units = unit.get('units', 1)
            # 이 유닛이 차지하는 슬롯 중앙 위치
            center_index = cursor + (units - 1) / 2.0
            y = baseline_start + center_index * step
            cell_height = max(step * units, 1.0)
            y_cells.append((y, cell_height))
            cursor += units
        
        # 각 단위 렌더링
        for i, unit in enumerate(render_units):
            current_y, cell_height = y_cells[i]
            
            if unit['type'] == 'two_column':
                self._render_two_column_unit(painter, rect, config, scale, unit['block'], base_font_size_pt, effective_v_scale, current_y)
            elif unit['type'] == 'special':
                self._render_special_unit(painter, rect, config, scale, unit['block'], base_font_size_pt, effective_v_scale, current_y)
            elif unit['type'] == 'shrink':
                self._render_shrink_unit(painter, rect, config, scale, unit['block'], base_font_size_pt, effective_v_scale, current_y, cell_height)
            elif unit['type'] == 'shrink_two_column':
                self._render_shrink_two_column_unit(painter, rect, config, scale, unit['block'], base_font_size_pt, effective_v_scale, current_y, cell_height)
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
            
            # y_position은 baseline 좌표. 스케일이 위치에 영향 주지 않도록 분리
            char_y_pos = y_position
            painter.drawText(int(current_x / h_scale), int(char_y_pos / v_scale), char)
            current_x += char_widths[i] * h_scale

    def _render_shrink_unit(self, painter, rect, config, scale, block, base_font_size_pt, base_v_scale, y_position, cell_height):
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
        # 상위 셀에서 보장된 세로 공간을 그대로 사용 (겹침 금지)
        available_height = cell_height
        
        # 축소폰트 크기 - 기본 픽셀 크기
        char_count = len(shrink_text)
        target_font_px = int(base_font_size_pt * size_ratio * scale)
        
        # 축소폰트로 각 글자 높이 계산
        temp_font = QFont(get_font_for_char(shrink_text[0], config))
        temp_font.setPixelSize(target_font_px)
        temp_fm = QFontMetrics(temp_font)
        char_height = temp_fm.height() * v_scale
        
        # 겹침 금지: 각 줄에 동일한 공간 분배 + 여유 간격 확보
        per_line_space = (available_height / char_count) if char_count > 0 else available_height
        # 설정에서 축소폰트 간격 값을 가져와서 사용
        shrink_spacing_ratio = config.get('축소폰트간격', 80) / 100.0
        fill_ratio = shrink_spacing_ratio
        
        # fill_ratio를 직접 char_height에 적용하여 간격 조정
        actual_char_height = char_height * fill_ratio
        # 최소 줄 간격(px) 보장: 너무 붙어 보이지 않게 (간격 조정을 위해 완화)
        min_gap_px = max(1.0, 0.01 * cell_height)  # 더 작은 최소 간격으로 완화
        if per_line_space - actual_char_height < min_gap_px:
            actual_char_height = max(1.0, per_line_space - min_gap_px)
        total_height = char_count * actual_char_height
        
        # y_position은 이 셀의 baseline. 셀 전체 높이(available_height) 안에서 줄 간격 기반으로 배치
        # 첫 줄의 top = 셀 상단 + (per_line_space - actual_char_height)/2 로 중앙 정렬
        current_y_top = (y_position - (available_height / 2)) + (per_line_space - actual_char_height) / 2
        for idx, char in enumerate(shrink_text):
            font_name = get_font_for_char(char, config)
            font = QFont(font_name)
            # 폰트 크기는 원래 크기 유지 (간격 조정과 분리)
            font.setPixelSize(target_font_px)
            painter.setFont(font)
            fm = QFontMetrics(font)
            
            # 세로 스케일링 최소화 (축소폰트 크기 유지)
            final_v_scale = v_scale  # 원래 세로 비율 유지
            transform = QTransform().scale(h_scale, final_v_scale)
            painter.setTransform(transform)
            
            char_width = fm.horizontalAdvance(char)
            scaled_char_width = char_width * h_scale
            char_x = rect.center().x() - (scaled_char_width / 2)
            
            # 각 줄의 baseline = line_top + ascent * v_scale
            char_y_pos = current_y_top + fm.ascent() * v_scale
            painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
            painter.resetTransform()
            
            # 다음 줄의 top: fill_ratio를 적용한 줄 간격
            adjusted_line_space = per_line_space * fill_ratio
            current_y_top += adjusted_line_space

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
        
        # y_position은 baseline 좌표. 스케일이 위치에 영향 주지 않도록 분리
        char_y_pos = y_position
        painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)

    def _render_shrink_two_column_unit(self, painter, rect, config, scale, block, base_font_size_pt, base_v_scale, y_position, cell_height):
        """축소폰트 2열 단위 렌더링 ([] 안에서 / 처리된 경우)"""
        left_text = block.get('left', '')
        right_text = block.get('right', '')
        
        if not left_text and not right_text:
            return
            
        size_ratio = config.get('축소폰트', 70) / 100.0
        h_scale = config.get('가로폰트', 100) / 100.0
        v_scale = base_v_scale
        
        # 축소폰트 크기
        target_font_px = int(base_font_size_pt * size_ratio * scale)
        
        # 축소폰트 간격 설정
        shrink_spacing_ratio = config.get('축소폰트간격', 80) / 100.0
        
        # 왼쪽 텍스트 렌더링
        if left_text:
            self._render_shrink_text_column(painter, rect, config, scale, left_text, target_font_px, h_scale, v_scale, y_position, cell_height, shrink_spacing_ratio, 'left')
        
        # 오른쪽 텍스트 렌더링
        if right_text:
            self._render_shrink_text_column(painter, rect, config, scale, right_text, target_font_px, h_scale, v_scale, y_position, cell_height, shrink_spacing_ratio, 'right')

    def _render_shrink_text_column(self, painter, rect, config, scale, text, target_font_px, h_scale, v_scale, y_position, cell_height, shrink_spacing_ratio, alignment):
        """축소폰트 텍스트 열 렌더링"""
        if not text:
            return
            
        # 사용 가능한 높이
        available_height = cell_height
        
        # 글자 수에 따른 줄 간격 계산
        char_count = len(text)
        per_line_space = (available_height / char_count) if char_count > 0 else available_height
        
        # 첫 줄의 시작 위치
        current_y_top = (y_position - (available_height / 2)) + (per_line_space - target_font_px * v_scale) / 2
        
        for idx, char in enumerate(text):
            font_name = get_font_for_char(char, config)
            font = QFont(font_name)
            font.setPixelSize(target_font_px)
            painter.setFont(font)
            fm = QFontMetrics(font)
            
            # 가로 정렬에 따른 X 좌표 계산
            char_width = fm.horizontalAdvance(char)
            scaled_char_width = char_width * h_scale
            
            if alignment == 'left':
                char_x = rect.center().x() - scaled_char_width  # 왼쪽 열
            else:  # right
                char_x = rect.center().x()  # 오른쪽 열
            
            # 세로 스케일링
            transform = QTransform().scale(h_scale, v_scale)
            painter.setTransform(transform)
            
            # 각 줄의 baseline
            char_y_pos = current_y_top + fm.ascent() * v_scale
            painter.drawText(int(char_x / h_scale), int(char_y_pos / v_scale), char)
            painter.resetTransform()
            
            # 다음 줄의 top: fill_ratio를 적용한 줄 간격
            adjusted_line_space = per_line_space * shrink_spacing_ratio
            current_y_top += adjusted_line_space
