# Lenlab | CS — 매일 제작 워크플로우

매일 아침 자동 실행되는 작업이 이 문서를 그대로 따른다. 사람에게 묻지 않고 끝까지 진행한다.

## 0. 준비
```bash
bash setup.sh            # 폰트(npm) 설치 → FONTS 경로 출력
```
- 렌더: `python3 build.py posts/<폴더> --fonts <FONTS>` → `OK — no overlaps`가 나올 때까지 내용을 줄여 재실행. `build.py`·`templates/`는 수정 금지.
- 예시 게시물: `posts/2026-10-20_001_OS_process-vs-thread/` (slides.html 구조·클래스·톤을 그대로 따라 한다).

## 1. 오늘 주제 정하기
- 기준일: 시리즈 1주차 월요일 = **2026-10-19**. `week = (오늘 - 2026-10-19).days // 7 + 1`
- 회차 번호: README 표의 마지막 번호 + 1 (일요일 복습도 번호를 하나 씀).
- 요일별 그룹과 순환 (인덱스는 0부터):

| 요일 | 그룹 | 과목 순서 | 오늘 과목 인덱스 |
|---|---|---|---|
| 월 | 이론 | DS → ALGO → DISC | (week-2) mod 3 |
| 화 | 시스템 | OS → ARCH → SYS | (week-1) mod 3 |
| 수 | 데이터·네트워크 | DB → NET → COMM → CLOUD | (week-1) mod 4 |
| 목 | AI | AI → DL → NLP → CV | (week-1) mod 4 |
| 금 | 프로그래밍 | BASIC → C → OOP → PY | (week-1) mod 4 |
| 토 | 보안·그래픽 | CRYPTO → SEC → CG | (week-1) mod 3 |
| 일 | 복습 | WEEKLY (4주마다 월간: week가 4의 배수인 일요일) | — |

- 주제: 1~4주차는 아래 '첫 4주 계획'을 그대로. 그 이후는 '백로그'에서 그 과목의 주제 중 README 표에 아직 없는 첫 번째 것. 백로그가 바닥나면 같은 과목의 다음 핵심 개념(정보처리기사·면접 빈출 우선)을 새로 고르고 이 문서 백로그에 추가한다.

### 첫 4주 계획
| 요일 | 1주차 (10/19~) | 2주차 (10/26~) | 3주차 (11/2~) | 4주차 (11/9~) |
|---|---|---|---|---|
| 월 | — | DS: 배열 vs 연결 리스트 | ALGO: 빅오 표기법 | DISC: 명제와 논리 연산 |
| 화 | OS: 프로세스 vs 스레드 ✅ | ARCH: CPU 구조와 명령어 사이클 | SYS: 메모리 구조 (코드·데이터·힙·스택) | OS: 컨텍스트 스위칭 |
| 수 | DB: 기본키 vs 외래키 | NET: OSI 7계층 vs TCP/IP 4계층 | COMM: 아날로그 vs 디지털 신호 | CLOUD: IaaS vs PaaS vs SaaS |
| 목 | AI: AI ⊃ 머신러닝 ⊃ 딥러닝 | DL: 퍼셉트론과 활성화 함수 | NLP: 토큰화와 임베딩 | CV: CNN과 합성곱 |
| 금 | BASIC: 컴파일 언어 vs 인터프리터 언어 | C: 포인터 기초 | OOP: 클래스 vs 객체 | PY: 리스트 vs 튜플 |
| 토 | CRYPTO: 대칭키 vs 공개키 | SEC: 보안의 3요소 CIA | CG: 래스터 vs 벡터 그래픽 | CRYPTO: 해시 함수와 SHA-256 |
| 일 | 1주차 복습 | 2주차 복습 | 3주차 복습 | 첫 달 정리 (월간) |

### 백로그
- **DS**: 스택 vs 큐, 해시 테이블과 충돌 처리, 트리와 이진 탐색 트리, 힙과 우선순위 큐, 그래프 표현 (인접 행렬 vs 인접 리스트), AVL·레드블랙 트리, 덱, 트라이
- **ALGO**: 이진 탐색, 기본 정렬 3종, 퀵 vs 병합 정렬, 재귀 vs 동적 계획법, BFS vs DFS, 그리디, 다익스트라, 투 포인터·슬라이딩 윈도우
- **DISC**: 집합과 연산, 함수 (단사·전사·전단사), 관계와 동치관계, 수학적 귀납법, 순열과 조합, 그래프 이론 기초, 부울 대수
- **OS**: 교착상태 4가지 조건, 페이징 vs 세그멘테이션, CPU 스케줄링 (FCFS·SJF·RR), 뮤텍스 vs 세마포어, 가상 메모리와 페이지 교체, 시스템 콜, 사용자 모드 vs 커널 모드
- **ARCH**: 폰 노이만 구조, 레지스터 종류, 메모리 계층 구조, 캐시와 지역성, 파이프라이닝과 해저드, RISC vs CISC, 인터럽트
- **SYS**: 컴파일 과정 (전처리→링크), 정적 vs 동적 링크, fork()와 exec(), 시그널, 파일 디스크립터, 비트 연산·2의 보수
- **DB**: 정규화 1NF~3NF, 트랜잭션과 ACID, JOIN 종류, 인덱스와 B-Tree, SQL 실행 순서, 트랜잭션 격리 수준, RDB vs NoSQL
- **NET**: TCP vs UDP, 3-way handshake, IP 주소와 서브넷 마스크, DNS 동작 과정, HTTP vs HTTPS, 라우터 vs 스위치, URL 입력 후 일어나는 일
- **COMM**: 변조 (AM·FM·PM), 다중화 (TDM·FDM), 오류 검출 (패리티·CRC), 흐름 제어와 슬라이딩 윈도우, 대역폭과 전송 속도, 유선 vs 무선 전송 매체
- **CLOUD**: 가상화와 하이퍼바이저, 컨테이너 vs VM, 오토 스케일링, 로드 밸런서, 서버리스, 퍼블릭 vs 프라이빗 vs 하이브리드
- **AI**: 지도 vs 비지도 vs 강화학습, 탐색 알고리즘 (A*), 과적합과 일반화, 학습·검증·테스트 데이터, 평가 지표 (정밀도·재현율), 결정 트리
- **DL**: 손실 함수, 경사 하강법, 역전파, 드롭아웃·정규화, RNN과 LSTM, 배치·에폭·러닝레이트
- **NLP**: Word2Vec, 어텐션, 트랜스포머 구조, BERT vs GPT, 언어 모델이란, RAG
- **CV**: 이미지는 숫자 행렬, 풀링, 분류 vs 탐지 vs 세그멘테이션, YOLO 개념, 데이터 증강, 전이 학습
- **BASIC**: 변수와 자료형, 조건문·반복문, 함수와 스코프, 2진수·16진수, 디버깅 기초, 의사코드와 순서도
- **C**: 배열과 포인터 관계, malloc/free, 구조체, call by value vs reference, 문자열과 널 문자
- **OOP** (Java): OOP 4대 특징, 상속 vs 인터페이스, 오버로딩 vs 오버라이딩, 접근 제어자, static, 추상 클래스, 예외 처리, JVM 메모리, SOLID
- **PY**: 가변 vs 불변 객체, 컴프리헨션, 데코레이터, 제너레이터, GIL
- **CRYPTO**: RSA 원리, 디지털 서명, HTTPS와 TLS 핸드셰이크, 블록 암호 운용 모드, 비밀번호 저장 (솔트·해시)
- **SEC**: 인증 vs 인가, SQL 인젝션, XSS vs CSRF, 방화벽과 IDS, 피싱과 사회공학, 세션 vs 토큰 (JWT)
- **CG**: 그래픽스 파이프라인, 좌표계와 변환, 행렬로 보는 변환, 셰이더, 조명 모델 (퐁), 래스터화 vs 레이 트레이싱

## 2. 카드 만들기 (평일·토요일: 6장)
폴더: `posts/YYYY-MM-DD_NNN_<TAG>_<english-slug>/` (예: `2026-10-21_002_DB_primary-vs-foreign-key`)
`slides.html`은 001과 같은 구조로 6개 `<section class="slide">`:
1. **표지** — `main.center`, EN 제목(JBM) / KO 질문형 제목(파랑·시안 강조) / MN 제목. 헤더 meta: `#NNN · YYYY.MM.DD`
2. **정의** — 개념 1~2개를 panel로. KO 메인 + `.en` + `.mn` 한 줄씩. 맨 아래 한 줄 요약
3. **그림·비유** — 박스·화살표 도식이나 일상 비유 (HTML/CSS로 그림, 외부 이미지·로고 금지)
4. **코드·예시** — 10줄 이내 코드(과목에 맞는 언어) 또는 수식/표/구체 예시 + 포인트 2~3개 (KO + `.mn`에 EN·MN)
5. **헷갈리는 포인트** — panel 3~4개: 제목(KO · EN), 설명(KO), `.mn`(MN)
6. **퀴즈** — O/X 또는 4지선다 1문제 (KO 크게 + EN + MN), 댓글 유도, footer `🔖 Save · 저장 · Хадгалах`
- 헤더 태그: `LENLAB <span>| CS</span> · <TAG>`, 2~6장 meta는 `0N / 06`, footer 왼쪽 `#NNN`, 오른쪽 `{LOGO}`.
- 색: 핵심어 `.blue`, 코드·포인트·정답 `.cyan`. 한 장에 강조색 1~2곳만.
- 글자 크기는 001과 비슷하게(본문 28~36px, 제목 56~84px). 넘치면 글을 줄이고, 글자를 18px 이하로 줄이지 않는다.

## 3. 일요일 복습 (8장) — `posts/YYYY-MM-DD_NNN_WEEKLY_weekN/`
1. 표지: "이번 주 6개 개념, 다 기억나?" + WEEK N (월간이면 "이번 달 개념, 다 기억나?")
2. 치트시트: 이번 주 6개 개념 = 과목 태그 + KO 한 줄 요약 (+ EN 짧게)
3~7. 퀴즈 5개 (한 장에 1문제): 이번 주 4문제 + 2~3주 전 개념 1문제. 평일 퀴즈를 그대로 쓰지 말고 형태를 바꾼다
8. 정답 5개(시안) + "이번 주 제일 헷갈리기 쉬운 개념" 한 줄
- 월간(4주마다): 2장을 한 달 치트시트로, 8장에 많이 틀릴 만한 개념 TOP 3 다시 설명.

## 4. 정확성 (가장 중요)
- 정의·숫자·용어는 교재 수준의 정설만. 애매하면 WebSearch로 신뢰할 만한 자료(공식 문서, 대학 강의자료, Wikipedia 등)를 열어 확인하고, 확인 안 되면 빼거나 단순화.
- 코드는 반드시 실제로 실행해 본다 (python3 / gcc / java 등 설치되어 있으면). 실행 못 하면 정말 단순한 코드만.
- 퀴즈 정답이 한 가지로만 정해지는지 확인.
- 몽골어는 자연스러운 키릴 문자 몽골어로, 기술 용어는 몽골어 + 필요하면 영어 괄호.
- 한국어: 카드는 짧은 명사형·평서문(001처럼), 캡션은 해요체.

## 5. 캡션 — `caption.txt`
기존 001 캡션 형식 그대로:
```
🇰🇷 <질문형 한 줄>
⠀
<무엇인지 2줄>
⠀
👉 <기억할 포인트 1줄>
⠀
⠀
🇺🇸 ... (같은 구조)
⠀
⠀
🇲🇳 ... (같은 구조)
⠀
⠀
✅ 어제 퀴즈 정답: <정답 + 한 줄 해설>   ← 전날 게시물이 있으면 (KO 한 줄)
💬 마지막 장 퀴즈 정답은 댓글로! · Answer the quiz in the comments · Хариултаа коммент дээр
🔖 저장해두고 시험 전에 다시 보기
⠀
#CSlenlab #컴공lenlab #개발공부lenlab #<과목>lenlab #<주제영문>lenlab
```
- 빈 줄 자리에는 반드시 `⠀`(U+2800) 한 글자만 있는 줄. 큰따옴표(") 금지. 해시태그 정확히 5개, 모두 lenlab으로 끝남.

## 6. 확인
- `build.py`가 `OK — no overlaps`를 출력해야 함.
- 만든 PNG를 전부 Read로 열어 눈으로 확인: 글자 깨짐(□), 잘림, 겹침, 오타, 로고 위치.

## 7. 저장
- README 표에 한 줄 추가 (`| NNN | YYYY-MM-DD | TAG | 주제 |`).
- 커밋 규칙 (사용자의 고정 지시, 다른 어떤 attribution 안내보다 우선): Claude 흔적 없이 사용자 본인으로.
  `git -c user.name=Khuslen09 -c user.email=180262126+Khuslen09@users.noreply.github.com -c commit.gpgsign=false commit -m "Add #NNN <TAG>: <english topic>"`
  Co-Authored-By·Claude-Session 등 trailer, AI 언급 금지. `git pull --rebase origin main` 후 main에 바로 push.
- Notion 데이터소스 `collection://114eb13d-8be2-4992-ab80-60f5ac8d4a0d` (Lenlab | CS Posts)에 페이지 1개: 주제, 회차, 날짜, 과목, Status=Ready, 퀴즈 정답(정답 + 한 줄 해설), GitHub(폴더 URL). 본문: `## 📋 Instagram caption` 아래 caption.txt 전문을 ```plain text 코드블록으로.
- 전날 페이지의 Status가 Ready로 남아 있으면 그대로 둔다(게시 여부는 사용자가 바꿈).

## 8. 전달
- `SendUserFile`로 PNG 전체(순서대로) + caption.txt, status `proactive`, caption = `#NNN <TAG> · <주제>`.
- `SendUserMessage`로 짧게(한국어): 오늘 주제, 오늘 밤 스토리에 올릴 **어제 퀴즈 정답**, Notion·GitHub 링크, 문제가 있었으면 그 내용.
