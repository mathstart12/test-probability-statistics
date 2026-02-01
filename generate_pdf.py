#!/usr/bin/env python3
"""
확률과 통계 - 전체 챕터 PDF 생성 스크립트
index.html에서 문제 데이터를 추출하여 PDF로 변환
"""

import re
import os
import pyjson5


def extract_categories(html_path):
    """index.html에서 categories JS 배열을 pyjson5로 파싱"""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'const categories = (\[.*?\n    \]);', content, re.DOTALL)
    if not match:
        raise ValueError("categories 데이터를 찾을 수 없습니다.")

    return pyjson5.loads(match.group(1))


def latex_to_readable(latex_str):
    """LaTeX 수식을 읽기 쉬운 유니코드 텍스트로 변환"""
    r = latex_str
    # 분수
    r = re.sub(r'\\frac\{([^}]*)\}\{([^}]*)\}', r'(\1)/(\2)', r)
    # 아래첨자/위첨자 (중괄호)
    r = re.sub(r'_\{([^}]*)\}', lambda m: ''.join(SUB_MAP.get(c, f'_{c}') for c in m.group(1)) if all(c in SUB_MAP for c in m.group(1)) else f'_{m.group(1)}', r)
    r = re.sub(r'\^\{([^}]*)\}', lambda m: ''.join(SUP_MAP.get(c, f'^{c}') for c in m.group(1)) if all(c in SUP_MAP for c in m.group(1)) else f'^({m.group(1)})', r)
    # 단순 아래첨자/위첨자
    r = re.sub(r'_([a-zA-Z0-9])', lambda m: SUB_MAP.get(m.group(1), f'_{m.group(1)}'), r)
    r = re.sub(r'\^([a-zA-Z0-9])', lambda m: SUP_MAP.get(m.group(1), f'^{m.group(1)}'), r)

    replacements = {
        '\\leq': '≤', '\\geq': '≥', '\\neq': '≠',
        '\\times': '×', '\\cdot': '·', '\\cdots': '⋯', '\\ldots': '…',
        '\\infty': '∞', '\\sum': 'Σ', '\\prod': 'Π',
        '\\sqrt': '√', '\\pi': 'π', '\\sigma': 'σ', '\\mu': 'μ',
        '\\alpha': 'α', '\\beta': 'β', '\\lambda': 'λ',
        '\\left(': '(', '\\right)': ')', '\\left[': '[', '\\right]': ']',
        '\\left\\{': '{', '\\right\\}': '}', '\\left|': '|', '\\right|': '|',
        '\\{': '{', '\\}': '}',
        '\\,': ' ', '\\;': ' ', '\\:': ' ', '\\!': '',
        '\\quad': '  ', '\\qquad': '    ',
        '\\displaystyle': '', '\\text': '', '\\mathrm': '',
        '\\bar': '', '\\overline': '', '\\underline': '',
    }
    for old, new in replacements.items():
        r = r.replace(old, new)

    # 남은 \command 패턴 정리
    r = re.sub(r'\\([a-zA-Z]+)', r'\1', r)
    return r


# 유니코드 첨자 매핑
SUB_MAP = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    'a': 'ₐ', 'e': 'ₑ', 'i': 'ᵢ', 'n': 'ₙ', 'r': 'ᵣ',
    'x': 'ₓ', '+': '₊', '-': '₋', '=': '₌',
}
SUP_MAP = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    'n': 'ⁿ', 'r': 'ʳ', '+': '⁺', '-': '⁻',
}


def process_text(text):
    """질문 텍스트 처리: HTML 정리 + LaTeX 변환"""
    # img 태그를 placeholder로 변환
    text = re.sub(
        r"<img\s+src='([^']+)'[^>]*>",
        r'<img src="\1" style="max-width:300px; margin:8px 0; display:block;">',
        text
    )
    # <br> 정리
    text = text.replace('<br>', '<br/>')

    # LaTeX 인라인 수식 변환: \(...\)
    text = re.sub(
        r'\\\((.+?)\\\)',
        lambda m: f'<b style="color:#c2410c;">{latex_to_readable(m.group(1))}</b>',
        text, flags=re.DOTALL
    )
    # LaTeX 디스플레이 수식 변환: \[...\]
    text = re.sub(
        r'\\\[(.+?)\\\]',
        lambda m: f'<div style="text-align:center;margin:6px 0;"><b style="color:#c2410c;">{latex_to_readable(m.group(1))}</b></div>',
        text, flags=re.DOTALL
    )
    return text


def generate_html(categories, base_dir):
    """전체 HTML 문서 생성"""
    parts = []
    parts.append('''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>확률과 통계 - 전체 문제 정리</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

@page {
    size: A4;
    margin: 2cm 1.8cm;
}
@page :first { margin-top: 0; }

* {
    font-family: 'Noto Sans KR', sans-serif;
    box-sizing: border-box;
}
body {
    font-size: 10pt;
    line-height: 1.65;
    color: #1a1a1a;
    margin: 0; padding: 0;
}

/* 표지 */
.cover {
    page-break-after: always;
    text-align: center;
    padding-top: 250px;
}
.cover h1 {
    font-size: 36pt; font-weight: 800; color: #f97316;
    margin-bottom: 12px;
}
.cover h2 {
    font-size: 14pt; font-weight: 500; color: #666;
    margin-bottom: 30px;
}
.cover p { font-size: 11pt; color: #999; }

/* 목차 */
.toc { page-break-after: always; }
.toc h2 {
    font-size: 16pt; font-weight: 700; color: #333;
    border-bottom: 2px solid #f97316; padding-bottom: 6px; margin-bottom: 16px;
}
.toc-ch { font-weight: 700; color: #333; margin-top: 10px; font-size: 10.5pt; }
.toc-pt { margin-left: 20px; color: #555; font-size: 9.5pt; margin-top: 3px; }

/* 챕터 */
.ch-title {
    font-size: 18pt; font-weight: 800; color: #f97316;
    border-bottom: 3px solid #f97316; padding-bottom: 6px;
    margin-top: 0; margin-bottom: 10px;
    page-break-before: always;
}
.pt-title {
    font-size: 12pt; font-weight: 700; color: #333;
    margin-top: 20px; margin-bottom: 8px;
    padding: 6px 10px;
    background: #fff7ed;
    border-left: 4px solid #f97316;
}

/* 문제 블록 */
.q-block {
    margin: 8px 0;
    padding: 8px 10px;
    background: #fafafa;
    border: 1px solid #e5e5e5;
    border-radius: 4px;
    page-break-inside: avoid;
}
.q-main { font-weight: 500; }
.sim-box {
    margin-top: 6px; padding-left: 12px;
    border-left: 2px solid #fed7aa;
}
.sim-label { font-size: 8pt; color: #f97316; font-weight: 600; margin-bottom: 2px; }
.sim-q { font-size: 8.5pt; color: #555; margin: 2px 0; }

img { max-width: 300px; }
</style>
</head>
<body>
''')

    # 표지
    total_q = sum(
        len(q.get('similarQuestions', [])) + 1
        for cat in categories
        for ch in cat.get('chapters', [])
        for q in ch.get('questions', [])
    )
    main_q = sum(
        len(ch.get('questions', []))
        for cat in categories
        for ch in cat.get('chapters', [])
    )
    parts.append(f'''
<div class="cover">
    <h1>확률과 통계</h1>
    <h2>구두테스트 퀴즈 전체 문제 정리</h2>
    <p>Chapter 1 ~ Chapter 9 | 메인 문제 {main_q}개 | 유사 문제 포함 총 {total_q}개</p>
</div>
''')

    # 목차
    parts.append('<div class="toc"><h2>목차</h2>')
    for cat in categories:
        parts.append(f'<div class="toc-ch">{cat["name"]}</div>')
        for ch in cat.get('chapters', []):
            qc = len(ch.get('questions', []))
            parts.append(f'<div class="toc-pt">{ch["name"]} ({qc}문제)</div>')
    parts.append('</div>')

    # 각 챕터
    for cat in categories:
        parts.append(f'<h1 class="ch-title">{cat["name"]}</h1>')

        for ch in cat.get('chapters', []):
            parts.append(f'<div class="pt-title">{ch["name"]}</div>')

            for q in ch.get('questions', []):
                main_text = process_text(q.get('question', ''))
                parts.append(f'<div class="q-block"><div class="q-main">{main_text}</div>')

                sqs = q.get('similarQuestions', [])
                if sqs:
                    parts.append('<div class="sim-box"><div class="sim-label">유사 문제</div>')
                    for sq in sqs:
                        sq_text = process_text(sq.get('question', '') if isinstance(sq, dict) else str(sq))
                        parts.append(f'<div class="sim-q">{sq_text}</div>')
                    parts.append('</div>')

                parts.append('</div>')

    parts.append('</body></html>')
    return '\n'.join(parts)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, 'index.html')
    output_html = os.path.join(base_dir, 'all_chapters.html')
    output_pdf = os.path.join(base_dir, 'all_chapters.pdf')

    print("1. 데이터 추출 중...")
    categories = extract_categories(html_path)
    print(f"   {len(categories)}개 챕터 추출")

    for cat in categories:
        total = sum(len(ch.get('questions', [])) for ch in cat.get('chapters', []))
        print(f"   - {cat['name']}: {len(cat.get('chapters',[]))}개 파트, {total}개 문제")

    print("\n2. HTML 생성 중...")
    html = generate_html(categories, base_dir)
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"   {output_html} 저장 완료")

    print("\n3. PDF 변환 중...")
    from weasyprint import HTML
    HTML(filename=output_html, base_url=base_dir).write_pdf(output_pdf)
    print(f"   {output_pdf} 저장 완료")

    # 통계
    total_main = sum(len(ch.get('questions', [])) for cat in categories for ch in cat.get('chapters', []))
    total_sim = sum(
        len(q.get('similarQuestions', []))
        for cat in categories for ch in cat.get('chapters', []) for q in ch.get('questions', [])
    )
    print(f"\n=== 완료 ===")
    print(f"챕터: {len(categories)}개 | 메인 문제: {total_main}개 | 유사 문제: {total_sim}개 | 전체: {total_main + total_sim}개")


if __name__ == '__main__':
    main()
