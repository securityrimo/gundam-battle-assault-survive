<p class="badges">
  <img src="https://img.shields.io/badge/버전-v1.0-0a3d91" alt="버전">
  <img src="https://img.shields.io/badge/플랫폼-PSP-c8102e" alt="플랫폼">
  <img src="https://img.shields.io/badge/형식-xdelta3-informational" alt="형식">
  <img src="https://img.shields.io/badge/번역-한국어-success" alt="한국어">
</p>

> ⬇️ **패치 다운로드**: [GAS_KR_v1.0.xdelta](https://github.com/kimjh-eclipse/gundam-battle-assault-survive/raw/main/GAS_KR_v1.0.xdelta) (약 4.1MB)

# 기동전사 건담 어설트 서바이브 한국어 패치

PSP용 **기동전사 건담 어설트 서바이브**(機動戦士ガンダム アサルトサヴァイブ, 반다이남코, 2010)를 한국어로 번역한 팬 패치입니다.
프롤로그·미션 브리핑·전투 무전을 비롯한 텍스트 전반을 번역하고, 샵·VS 배틀·시추에이션 시작 제목 등 이미지 글자까지 한글로 다시 그렸습니다.

> ※ 이 패치는 PSP판(디스크 ID **ULJS-00281**)용입니다.
> 같은 사내 엔진 계열의 전작 **건담 배틀 유니버스**와는 별개 패치입니다.

## 한눈에 보기

| 항목 | 내용 |
|---|---|
| 대상 게임 | Gundam Assault Survive (J) · 854MB · 디스크 ID ULJS-00281 |
| 원본 SHA-256 | `2CA94945…39664` |
| 패치 형식 | xdelta3 (`.xdelta`) |
| 최신 버전 | **v1.0** |
| 동작 확인 | PPSSPP · CFW 실기 |

## 설치 및 적용

1. 원본 일본판 ISO를 준비합니다. **(이 저장소는 게임 이미지를 포함하지 않습니다.)**
   - 파일: `Gundam Assault Survive (Japan).iso` (854,491,136 bytes)
   - SHA-256: `2CA94945B4E72CADA3B79CD92954704DE6B43326A734116053BC572834039664`
2. [패치 파일 `GAS_KR_v1.0.xdelta`](https://github.com/kimjh-eclipse/gundam-battle-assault-survive/raw/main/GAS_KR_v1.0.xdelta)을 내려받아 xdelta3(또는 xdeltaUI, Delta Patcher 등)로 적용합니다.

   ```bash
   xdelta3 -d -s "Gundam Assault Survive (Japan).iso" GAS_KR_v1.0.xdelta "Gundam Assault Survive (Korean).iso"
   ```
3. 적용 결과를 확인합니다 (선택).
   - 한국어판 SHA-256: `F41375D9304432BFE4064911EC5D44872F7D84394823B1F48ACD8CAB096611A7`

> 💡 GUI 툴만 쓰신다면 **xdeltaUI**에서 원본 ISO를 Source, 패치를 Patch로 지정하고 Apply Patch를 누르면 됩니다.

## 번역 범위

### 텍스트
- **시대 도입 내레이션(프롤로그)** — 0079 연방/지온 등
- **미션 브리핑·전투 무전** 4,603문자열 (전 미션, FES 무전 풀)
- **미션 데이터** — 성립/실패 조건 등
- **HUD 표시명** 1,627셀
- **얼럿/확인 다이얼로그** 104종
- **메뉴·UI 문자열** 2,047종 + 단일한자 칭호 79종
- **한글 폰트**: 게임 폰트(j14x14 4bpp)에 글리프 주입

### 그래픽 (이미지 글자)
- **시추에이션 시작 연출 미션명** 181종 (`intro_<mission>.gim`)
- **샵 화면**: 파일럿·파츠·스킬·칭호·개발 계획·시크릿, 표 헤더
- **VS 배틀 규정 화면**: 모드명·양쪽 REGULATION 항목·결정/초기 설정 복원
- **VS 편성 선택**: 파일럿·자동 선택·사용 안 함
- **메인 메뉴 우측 대시보드**: 소지금·플레이 시간·전투 기록(출격 횟수·격추수·파츠·미션 등)

전체 변경 내역과 미번역 잔여 항목은 **[📝 패치노트](patch-notes.md)** 에 정리되어 있습니다.

## 저장소 구성

| 경로 | 내용 |
|---|---|
| `GAS_KR_v1.0.xdelta` | 한국어 패치 본체 |
| `docs/patch-notes.md` | 패치노트 (적용법 · 번역 범위 · 알려진 한계) |
| `docs/dev-log.md` | 리버스 엔지니어링 · 한글화 작업 기록 |
| `tools/` | 언팩/리팩, RAIC 코덱, 폰트 주입, GIM 식자, EBOOT/FES 패치, 에뮬레이터 자동화 도구 |

## 참여

- 리버스 엔지니어링·파이프라인·번역: Claude (Anthropic), Codex (OpenAI)
- 기획·검증: 이클립스

## 저작권 고지

- 이 저장소는 **게임 이미지나 원본 게임 자산을 포함하지 않습니다.** 패치는 정품 소지자의 개인적 이용을 전제로 합니다.
- 機動戦士ガンダム 및 관련 자산의 모든 권리는 **반다이남코 · 창통에이전시(SOTSU) · 선라이즈**에 있습니다.
  본 패치는 비영리 팬 번역이며, 권리자의 요청이 있을 경우 배포를 중단합니다.
- `tools/`의 소스 코드는 저장소 라이선스를 따릅니다.
