"""
inZOI Object Catalog Generator
===============================
엑셀(object.xlsx)에서 오브젝트 데이터를 읽어 HTML 카탈로그를 생성/업데이트합니다.

사용법:
  python generate_catalog.py

필요 라이브러리:
  pip install pandas openpyxl

폴더 구조:
  D:/inzoiObjectList/
    ├── generate_catalog.py    (이 스크립트)
    ├── object.xlsx            (원본 데이터)
    ├── inzoi_catalog.html     (생성될 카탈로그)
    ├── _prev_data.json        (변경 추적용, 자동 생성)
    └── img/
        └── *.png              (오브젝트 아이콘들)
"""

import pandas as pd
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# === 설정 ===
SCRIPT_DIR = Path(__file__).parent
EXCEL_FILE = SCRIPT_DIR / "object.xlsx"
HTML_FILE = SCRIPT_DIR / "inzoi_catalog.html"
PREV_DATA_FILE = SCRIPT_DIR / "_prev_data.json"
IMG_DIR = SCRIPT_DIR / "img"

# JSON 데이터가 삽입될 라인의 시작 패턴
DATA_MARKER = "const ALL_DATA = "


def extract_objects_from_excel(excel_path):
    """엑셀의 Object 시트에서 오브젝트 데이터를 추출합니다."""
    print(f"[1/4] 엑셀 파일 읽는 중: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name="Object", header=None)

    # Row 0 = 메타데이터, Row 1 = 헤더, Row 2+ = 데이터
    data = df.iloc[2:]
    objects = data[data.iloc[:, 0].notna()].copy()

    items = []
    for _, row in objects.iterrows():
        item = {
            "id": str(row.iloc[0]) if pd.notna(row.iloc[0]) else "",
            "name": str(row.iloc[2]) if pd.notna(row.iloc[2]) else "",
            "desc": str(row.iloc[4]) if pd.notna(row.iloc[4]) else "",
            "category": str(row.iloc[8]) if pd.notna(row.iloc[8]) else "",
            "filter": str(row.iloc[9]) if pd.notna(row.iloc[9]) else "",
            "icon": str(row.iloc[14]) if pd.notna(row.iloc[14]) else "",
            "price": int(row.iloc[33]) if pd.notna(row.iloc[33]) else 0,
            "tags": str(row.iloc[17]) if pd.notna(row.iloc[17]) else "",
        }
        if item["name"] and item["icon"]:
            items.append(item)

    print(f"   → {len(items)}개 오브젝트 추출 완료")
    return items


def compare_data(new_items, prev_file):
    """이전 데이터와 비교하여 변경사항을 출력합니다."""
    print(f"\n[2/4] 변경사항 확인 중...")

    if not prev_file.exists():
        print("   → 이전 데이터 없음 (최초 실행)")
        return

    with open(prev_file, "r", encoding="utf-8") as f:
        prev_items = json.load(f)

    prev_ids = {item["id"]: item for item in prev_items}
    new_ids = {item["id"]: item for item in new_items}

    added = [id for id in new_ids if id not in prev_ids]
    removed = [id for id in prev_ids if id not in new_ids]
    modified = []
    for id in new_ids:
        if id in prev_ids and new_ids[id] != prev_ids[id]:
            modified.append(id)

    print(f"\n   ┌─────────────────────────────────────┐")
    print(f"   │  변경사항 요약                        │")
    print(f"   ├─────────────────────────────────────┤")
    print(f"   │  이전: {len(prev_items):>5}개                      │")
    print(f"   │  현재: {len(new_items):>5}개                      │")
    print(f"   │  추가: {len(added):>5}개  ✅                    │")
    print(f"   │  삭제: {len(removed):>5}개  ❌                    │")
    print(f"   │  수정: {len(modified):>5}개  ✏️                     │")
    print(f"   └─────────────────────────────────────┘")

    if added:
        print(f"\n   ✅ 추가된 오브젝트 ({len(added)}개):")
        for id in added[:20]:
            item = new_ids[id]
            print(f"      + {item['name']} ({id}) [{item['filter']}]")
        if len(added) > 20:
            print(f"      ... 외 {len(added) - 20}개")

    if removed:
        print(f"\n   ❌ 삭제된 오브젝트 ({len(removed)}개):")
        for id in removed[:20]:
            item = prev_ids[id]
            print(f"      - {item['name']} ({id})")
        if len(removed) > 20:
            print(f"      ... 외 {len(removed) - 20}개")

    if modified:
        print(f"\n   ✏️  수정된 오브젝트 ({len(modified)}개):")
        for id in modified[:10]:
            old = prev_ids[id]
            new = new_ids[id]
            changes = []
            for key in ["name", "filter", "price", "category", "tags", "desc"]:
                if old.get(key) != new.get(key):
                    changes.append(key)
            print(f"      ~ {new['name']} ({id}) → {', '.join(changes)} 변경")
        if len(modified) > 10:
            print(f"      ... 외 {len(modified) - 10}개")

    # 이미지 파일 체크
    if IMG_DIR.exists():
        missing = []
        for item in new_items:
            img_path = IMG_DIR / f"{item['icon']}.png"
            if not img_path.exists():
                missing.append(item)
        if missing:
            print(f"\n   ⚠️  이미지 없는 오브젝트 ({len(missing)}개):")
            for item in missing[:10]:
                print(f"      ! {item['name']} → img/{item['icon']}.png")
            if len(missing) > 10:
                print(f"      ... 외 {len(missing) - 10}개")
        else:
            print(f"\n   ✅ 모든 오브젝트의 이미지 파일이 존재합니다")


def update_html(items, html_path):
    """HTML 파일의 JSON 데이터 부분만 교체합니다."""
    print(f"\n[3/4] HTML 카탈로그 업데이트 중...")
    compact_json = json.dumps(items, ensure_ascii=False, separators=(",", ":"))

    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith(DATA_MARKER):
                lines[i] = f"{DATA_MARKER}{compact_json};\n"
                updated = True
                break

        if updated:
            with open(html_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"   → 기존 HTML 업데이트 완료: {html_path}")
            return

    print(f"   ⚠️  HTML 파일이 없거나 데이터 마커를 찾을 수 없습니다")
    print(f"   → inzoi_catalog.html 파일이 같은 폴더에 있는지 확인하세요")
    sys.exit(1)


def save_current_data(items, prev_file):
    """현재 데이터를 다음 비교용으로 저장합니다."""
    print(f"\n[4/4] 현재 데이터 저장 중...")
    with open(prev_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)
    print(f"   → 저장 완료: {prev_file}")


def main():
    print("=" * 50)
    print("  inZOI Object Catalog Generator")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    if not EXCEL_FILE.exists():
        print(f"\n❌ 엑셀 파일을 찾을 수 없습니다: {EXCEL_FILE}")
        sys.exit(1)

    if not HTML_FILE.exists():
        print(f"\n❌ HTML 템플릿 파일을 찾을 수 없습니다: {HTML_FILE}")
        print(f"   inzoi_catalog.html 파일을 같은 폴더에 넣어주세요")
        sys.exit(1)

    items = extract_objects_from_excel(EXCEL_FILE)
    compare_data(items, PREV_DATA_FILE)
    update_html(items, HTML_FILE)
    save_current_data(items, PREV_DATA_FILE)

    print(f"\n{'=' * 50}")
    print(f"  ✅ 완료! 브라우저에서 열어보세요:")
    print(f"  {HTML_FILE}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
