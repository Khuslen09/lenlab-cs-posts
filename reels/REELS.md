# Lenlab | CS — 매일 릴스 워크플로우

매일 카드뉴스(07:45 작업, `WORKFLOW.md`)가 `posts/<폴더>/`를 커밋한 뒤, 같은 게시물을 9:16 릴스(30~60초)로 만든다.
게시물 1개 = 릴스 1개. 사람에게 묻지 않고 끝까지 진행한다. **Instagram 업로드는 사람이 한다.**

## 0. 준비
```bash
pip install -r reels/requirements.txt   # numpy Pillow fonttools edge-tts imageio-ffmpeg
```
- macOS 시스템 폰트(Apple SD Gothic Neo, Menlo, Apple Color Emoji)를 쓴다.
- 음성은 Microsoft 뉴럴 TTS(edge-tts, 무료, 인터넷 필요):
  렝 = `ko-KR-InJoonNeural`(남), 칩코 = `ko-KR-SunHiNeural` +12Hz(여), 깜빡 = `fr-FR-VivienneMultilingualNeural`(여).
- `reels/render.py`, `reels/sprites/`는 수정하지 않는다.

## 1. 대상 게시물 찾기
`posts/` 중 `reel.json`이 없는 폴더(보통 오늘 날짜 폴더). 여러 개면 날짜순으로 전부 만든다.

## 2. `reel.json` 쓰기
같은 폴더의 `slides.html`, `caption.txt`를 읽고 내용을 정확히 옮긴다(새 사실을 지어내지 않는다).
예시: `posts/2026-11-23_034_ALGO_binary-search/reel.json` (형식·톤을 그대로 따른다).

```json
{"n": 34, "tag": "ALGO", "guest": "blink", "title": "이진 탐색", "scenes": [ ... ]}
```
- `n`: 회차 번호, `tag`: 폴더의 과목 태그
- `guest`: 하드웨어·OS·시스템·C·신호(OS, ARCH, SYS, C, COMM) → `"chipko"`;
  DB·NET·SEC·CRYPTO·CLOUD·DS·ALGO·BASIC·OOP·PY → `"blink"`; AI·DL·NLP·CV·DISC·CG → `null`(렝 혼자)
- 장면 순서(평일): `hook` → `bubble`(guest 비유) → `cards`/`steps`/`code` 1~2개 → `bubble`(렝 반전·질문, 선택) → `point` → `quiz` → `outro`
- 일요일 WEEKLY: `hook` → `steps`(이번 주 개념 한 줄씩) → `bubble`(제일 헷갈리는 것) → `point` → `quiz` → `outro`

장면 타입과 필드 (모든 장면에 `v` = 한국어 음성 대사, `en` = 영어 자막):
| t | 필드 |
|---|---|
| `hook` | `lines`: 큰 제목 2줄 (궁금증·반전·숫자로 시작) |
| `bubble` | `who`: `"guest"`/`"leng"`, `pose`(렝일 때): `explain`·`think`·`surprise`, `b`: 말풍선 2줄 |
| `cards` | `items`: 2~4개 `{e: 이모지, t: 제목, d: 설명(줄바꿈 \n, 3줄 이내)}` — 2개면 VS 카드 |
| `steps` | `items`: 3~6줄 문자열, 앞에 이모지 |
| `code` | `code`: 4줄 이내 코드/수식 |
| `point` | `text`: 핵심 1~2줄 |
| `quiz` | `q`: 질문, `opts`: `["O","X"]` 또는 보기 2~4개, `ans`: 정답 인덱스(0부터), `why`: 정답 한 줄, `why_v`·`why_en`: 정답 음성·자막 |
| `outro` | `v`: 저장·공유·팔로우 유도 한 줄 |

작성 규칙
- 렝 말투: 친구 같은 반말, **비유 먼저 · 용어는 나중에**. 한 대사 1~2문장.
- 화면 글자에서 `*강조*`는 민트색. 화면에 별표(*)를 그대로 보여야 하면 전각 `＊`를 쓴다.
- `v`(음성)는 TTS가 읽기 쉽게: 영문 약어·기호는 한글 발음으로 (`O(n)` → "오 엔", `PC` → "피씨", `&` → "앰퍼샌드"). 화면 글자(`lines`·`b`·`d`·`code`…)는 원래 표기 그대로.
- `en`은 `v`의 자연스러운 영어 번역(자막). 퀴즈는 `en` = 질문, `why_en` = 정답 해설.
- 퀴즈는 카드 6장의 퀴즈와 같은 문제·정답을 쓴다.
- 길이: 대사 총합 약 250~330자 → 영상 40~55초.

## 3. 렌더
```bash
python3 reels/render.py posts/<폴더>
```
- `OK #NNN 47.2s posts/<폴더>/NNN-reel.mp4`가 나와야 한다.
- `LENGTH_OUT_OF_RANGE`(30초 미만·60초 초과)면 대사를 줄이거나 늘려 다시 렌더한다.
- mp4는 `.gitignore`에 있어 커밋되지 않는다(로컬에서 업로드).

## 4. `reel_caption.txt` 쓰기
`caption.txt`를 바탕으로 릴스용 짧은 캡션을 만든다. 예시: `posts/2026-11-23_034_ALGO_binary-search/reel_caption.txt`.
- 🇰🇷 / 🇺🇸 / 🇲🇳 각 3줄: 훅 질문(+이모지) / 비유 또는 핵심 정의 / 👉 핵심 포인트
- 맨 끝에 공통 마무리(💬 댓글 · 🔖 저장 · ➕ 팔로우, 3개 국어)와 해시태그를 예시 그대로 붙인다.
- **몽골어는 캡션에만** 쓴다(영상 자막은 한국어+영어). `caption.txt`의 🇲🇳 문단과 아래 용어를 우선 쓴다.

### 몽골어 용어 (검증된 표기)
процесс · урсгал(thread) · үндсэн/гадаад түлхүүр · хөрвүүлэгч/тайлбарлагч · массив · холбоост жагсаалт ·
заагч · регистр · давхарга · сүлжээнд хандах давхарга(Network Access; "холбоос" 아님) · перцептрон · идэвхжүүлэх функц ·
нууцлал / бүрэн бүтэн байдал / хүртээмж (CIA) · стек / дараалал(queue) · эрэмбэлэгдсэн массив · хоёртын хайлт ·
хяналттай / хяналтгүй / бататгах сургалт · баталгаажуулалт(authN) / эрх олголт(authZ) · хэвшүүлэлт(정규화) · хувьсагч · өгөгдлийн төрөл
- 위 용어 중 정규화·강화학습·인증/인가는 몽골어 IT 용어가 통일돼 있지 않으니, 처음 쓰는 용어는 괄호에 영어를 함께 쓴다.

## 5. 확인
- 렌더 결과 `OK`, mp4 존재, 길이 30~60초.
- `reel.json` 퀴즈 정답이 `slides.html` 퀴즈와 같은지 다시 본다.

## 6. 저장
```bash
git add posts/<폴더>/reel.json posts/<폴더>/reel_caption.txt
git commit -m "Add #NNN reel script and caption"
git push
```
