# -*- coding: utf-8 -*-
"""
리본 메이커 유틸리티 함수 모듈
"""

import json
from config import PRESETS_FILE, DEFAULT_PRESETS, DEFAULT_PHRASES


def load_data(filename, default_data):
    """
    JSON 파일에서 데이터를 로드하거나 기본값을 생성합니다.
    
    Args:
        filename (str): 로드할 파일명
        default_data (dict): 파일이 없을 경우 사용할 기본 데이터
        
    Returns:
        dict: 로드된 데이터 또는 기본 데이터
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data


def save_presets(presets):
    """
    프리셋 데이터를 파일에 저장합니다.
    
    Args:
        presets (dict): 저장할 프리셋 데이터
    """
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, ensure_ascii=False, indent=4)


def get_font_for_char(char, config):
    """
    문자에 따라 적절한 폰트를 반환합니다.
    
    Args:
        char (str): 확인할 문자
        config (dict): 폰트 설정 정보
        
    Returns:
        str: 사용할 폰트명
    """
    if '\u4e00' <= char <= '\u9fff':  # 한자
        return config.get('한자', '(한)마린_견궁서B')
    elif '\uac00' <= char <= '\ud7af':  # 한글
        return config.get('한글', '(한)마린_견궁서B')
    else:  # 영문, 숫자, 기타
        return config.get('영문', '(한)마린_견궁서B')


def extract_chinese_only(text):
    """
    텍스트에서 한자(한글) 형태가 있으면 한자만 추출합니다.
    예: "祝開業 (축개업)" → "祝開業"
    
    Args:
        text (str): 원본 텍스트
        
    Returns:
        str: 한자만 추출된 텍스트 또는 원본 텍스트
    """
    import re
    
    # "한자 (한글)" 패턴 찾기
    pattern = r'([一-龯]+)\s*\([^)]+\)'
    match = re.search(pattern, text)
    
    if match:
        return match.group(1)  # 한자 부분만 반환
    else:
        return text  # 패턴이 없으면 원본 반환
