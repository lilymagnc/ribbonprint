# [] 축소폰트 줄 간격 조절 안내

이 문서는 `[]` 블록(축소폰트) 내부 줄 간 간격을 조절하는 방법을 정리합니다.

## 수정 위치

- 파일: `widgets.py`
- 함수: `_render_shrink_unit(...)`

해당 함수에서 줄 간격은 다음 변수들로 결정됩니다.

```python
# 한 줄(라인)에 배정되는 공간
per_line_space = (available_height / char_count) if char_count > 0 else available_height

# 글자가 차지하는 비율(값이 클수록 간격이 줄어듦)
if char_count <= 2:
    fill_ratio = 0.55
elif char_count <= 4:
    fill_ratio = 0.70
else:
    fill_ratio = 0.85

actual_char_height = min(char_height, per_line_space * fill_ratio)

# 최소 줄 간격(px) 보장 — 너무 붙어 보이지 않게 하는 안전장치
min_gap_px = max(2.0, 0.02 * cell_height)
if per_line_space - actual_char_height < min_gap_px:
    actual_char_height = max(1.0, per_line_space - min_gap_px)
```

## 어떻게 조절하나요?

1) 간격을 “조금 줄이기” (타이트하게)

- `fill_ratio` 값을 약간 키웁니다.
  - 권장 예:
    - 0.55 → 0.62
    - 0.70 → 0.76
    - 0.85 → 0.90
- (선택) `min_gap_px` 완화(간격 더 줄이기):
  - `max(2.0, 0.02 * cell_height)` → `max(1.0, 0.01 * cell_height)`

2) 간격을 “조금 늘리기” (여유 있게)

- `fill_ratio` 값을 작게 조정합니다. (예: 0.55 → 0.50, 0.70 → 0.65, 0.85 → 0.80)
- (선택) `min_gap_px`를 키워 여유를 강제합니다. (예: 0.02 → 0.03)

## 한 개 노브(One‑knob) 방식으로 간단히

여러 구간 분기를 없애고 고정값 하나로 제어할 수도 있습니다.

```python
# 분기 삭제 후 고정값 하나로 제어 (값이 클수록 간격이 좁아짐)
fill_ratio = 0.90  # 0.88 ~ 0.92 범위에서 미세 조정 추천
```

## 참고: 픽셀 크기 강제 조정

줄 높이 안에서 확실히 겹치지 않도록 각 글자의 픽셀 크기를 줄 높이에 맞춰 보정합니다.

```python
desired_px = max(1, int(actual_char_height / max(0.1, v_scale)))
font.setPixelSize(min(target_font_px, desired_px))
```

`fill_ratio`/`min_gap_px`를 조절해도 간격이 기대와 다르면, 이 보정 구간을 통해 글자 자체의 픽셀 높이를 줄 높이에 더 정확히 맞출 수 있습니다.

## 요약

- “간격”은 `per_line_space`(줄 공간)와 `fill_ratio`(글자 채움 비율)로 결정됩니다.
- `fill_ratio`를 키우면 타이트, 줄이면 여유가 생깁니다.
- `min_gap_px`는 최소 여백을 보장하는 안전장치입니다.
- 간단 조절을 원하면 `fill_ratio` 한 값만 두고 미세 조정하세요.


