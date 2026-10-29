# Lenlab | CS

매일 하나씩 정리하는 컴퓨터공학 개념 카드뉴스 — 🇰🇷 KO · 🇺🇸 EN · 🇲🇳 MN

- `posts/<날짜>_<회차>_<과목>_<주제>/` — `slides.html`(내용), 카드 이미지 1080×1350, `caption.txt`, `story.html`·`<NNN>-story.png`(정답 스토리)
- `templates/card-template.html` — 공통 디자인 (High-Contrast Tech 팔레트)
- `brand/` — 로고 (SVG, PNG)
- `build.py` — `python build.py posts/<폴더> [--fonts <node_modules>]` 로 이미지 렌더 + 겹침/넘침 자동 검사
- `build_story.py` — `story.html` → `<NNN>-story.png` (1080×1920, 다음 날 스토리에 올리는 퀴즈 정답 카드)

| # | 날짜 | 과목 | 주제 |
|---|---|---|---|
| 001 | 2026-10-20 | OS | 프로세스 vs 스레드 |
| 002 | 2026-10-21 | DB | 기본키 vs 외래키 |
| 003 | 2026-10-22 | AI | AI ⊃ 머신러닝 ⊃ 딥러닝 |
| 004 | 2026-10-23 | BASIC | 컴파일 언어 vs 인터프리터 언어 |
| 005 | 2026-10-25 | WEEKLY | 1주차 복습 |
| 006 | 2026-10-26 | DS | 배열 vs 연결 리스트 |
| 007 | 2026-10-27 | ARCH | CPU 구조와 명령어 사이클 |
| 008 | 2026-10-28 | NET | OSI 7계층 vs TCP/IP 4계층 |
| 009 | 2026-10-29 | DL | 퍼셉트론과 활성화 함수 |
| 010 | 2026-10-30 | C | 포인터 기초 |
