# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**데이터 업데이트** (엑셀 → JSON):
```bash
pip install pandas openpyxl
python generate_catalog.py
```

**로컬 개발 서버** (HTTP 서버 필요, file:// 직접 열기 불가 - fetch 사용):
```bash
python -m http.server 8080
```

**배포** (Cloudflare Pages):
```bash
npx wrangler pages deploy ./ --project-name inzoi-catalog
```

## Architecture

단일 HTML 파일(`index.html`) + 외부 데이터 파일 구조. 빌드 과정 없음.

### 데이터 흐름
- `object.xlsx` → `generate_catalog.py` → `data/objects.json` (오브젝트 목록)
- `data/meta.json` : 카테고리 계층(`catHier`), 필터 한글명(`filterKo`), 오브젝트 태그(`objTags`)
- `data/posmap_positions.json` : 포지셔닝맵 기본 좌표 (정적 fallback)
- Cloudflare KV (`POSMAP_KV`) : 포지셔닝맵 위치 서버 저장소, `/api/posmap` GET/PUT

### 인증
- `/api/auth` (Cloudflare Pages Function): 비밀번호 검증 → SHA-256 토큰 발급
- 토큰은 `localStorage('inzoi_auth')`에 90일 저장
- 모든 데이터 로드는 인증 후 `startApp()` → `loadData()` 순서

### 핵심 JS 구조 (`index.html` 내 `<script>`)
- `state` 객체: 현재 뷰(`category`/`grid`/`posmap`/`treemap`), 필터, 정렬, 언어 등 모든 UI 상태 관리
- `ALL_DATA`: 전체 오브젝트 배열 (id, name, desc, category, filter, icon, price, tags)
- `getFiltered()`: `state`를 기반으로 필터/검색/정렬 적용한 배열 반환
- `render()`: `state.view`에 따라 `renderCategory` / `renderGrid` / `renderTreemap` / `renderPosmap` 분기
- `appendMore()`: 무한 스크롤, `state.loaded` 배치 단위로 `.grid-view`에 카드 추가

### 뷰 종류
- **카테고리**: `filter` 필드로 그룹핑, 카테고리별 최대 24개 미리보기
- **그리드**: 가상 무한 스크롤 (배치 로드)
- **포지셔닝맵**: D3.js 기반 드래그 가능한 scatter plot, KV에 위치 저장
- **트리맵**: D3.js 기반 카테고리별 크기 시각화

### Cloudflare Pages Functions
- `functions/api/auth.js`: POST(로그인), GET(토큰 검증)
- `functions/api/posmap.js`: GET(위치 로드), PUT(위치 저장) — `POSMAP_KV` 바인딩 필요

### 이미지
- `img/` 폴더에 `{icon}.PNG` 형식 (대문자 확장자)
- 오브젝트의 `icon` 필드값이 파일명 (확장자 제외)

### 스타일
- CSS 변수 기반 다크/라이트 테마 (`data-theme` 속성으로 전환)
- 반응형 브레이크포인트: `700px` (모바일)
- 모바일 헤더: 1줄(로고+stats+필터버튼+테마버튼) + 2줄(뷰 모드 버튼, order:9) + 3줄(검색창, order:10)
