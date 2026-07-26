# Gundam Assault Survive (J) 한국어화 작업 기록

최종 업데이트: 2026-07-26

---

## 1. 개요

- **대상**: `Gundam Assault Survive (Japan).iso` (PSP, 디스크 ID **ULJS-00281**, 854MB)
- **산출물**: `Gundam Assault Survive (Korean).iso` (원본 불변, 사본 패치)
- **배포 패치**: `GAS_KR_v1.1.xdelta` — 원본 J에 적용 시 K와 **SHA-256 완전 일치** 검증됨 (v1.0은 진행불가 문제로 대체됨)
- **핵심**: 전작 **건담 배틀 유니버스(GBU)** 와 **동일 사내 엔진(gpsp3)**. GBU에서 만든 도구 체인이 거의 그대로 이식됨.

### v1.1 — 미션 진행불가 원인 규명

- **증상**: 일부 미션에서 에어리어 전환 트리거가 발동하지 않아 진행 불가. 적 부대가 나왔다 사라지는 케이스 포함.
- **원인**: EBOOT의 게임 데이터 이름 테이블(`CsvCategory`/`FIELD_DATA`/`TABLE_DATA` 파서로 로드되는 오브젝트/유닛/캐릭터 이름 풀) 중
  **캐릭터·파일럿 고유명**을 한글화하면 엔진의 이름 기반 오브젝트 식별이 실패. 미션 데이터는 유닛을 ID 코드(`ms_guf`, `pz_rnb` 등)로
  참조하지만, 특정 이벤트/스폰 매칭이 이 이름 문자열에 의존.
- **판별**: EBOOT 전체 원문 복원 시 정상, mz_0100 자체 데이터(FES·CSV·GIM) 원복은 무효 → 공용 EBOOT 문제로 좁힘.
  이후 `ui_short`(MS·오브젝트 이름)는 한글 유지해도 정상이고, `eboot_ui.csv`의 캐릭터명만 원문 유지하면 해결됨을 실기 검증.
- **조치**: 캐릭터·파일럿 고유명 128개(미션 CSV 등장 이름 ∩ EBOOT)만 원문 유지. MS·기체·오브젝트 이름, 계급, 프롤로그는 한글 유지.

---

## 2. 포맷 분석 (규명·왕복검증 완료)

| 포맷 | 내용 |
|---|---|
| `gundam.idx` | **PIDX0** 인덱스 (17,347 파일) |
| `fileset.dat` | **FSTS** 번들 세트 (1,502 세트) |
| 압축 | **RAIC** (매직 `' 3;1'`) — GBU와 동일 코덱 |
| 폰트 | `font_data_j14x14.fnt` = 448px 4bpp 선형 텍스처, 6976 글리프 평면 배열 |
| 이미지 | **GIM** (4bpp, 팔레트 알파 램프) — UI/버튼/제목 글자 |
| 무전 | **FES** 바이트코드 — NUL 종단 SJIS 문자열 풀 |
| 실행본 | **EBOOT.BIN** (`~PSP` PRX, type2) — 하드코딩 SJIS 다수 |

주요 텍스트는 **평문 SJIS(cp932) CSV**(`inst_ms.csv` 등)와 **EBOOT 하드코딩 문자열**, **FES 무전 풀**, **GIM 이미지 글자**에 분산되어 있다.

### EBOOT 복호 (순수 파이썬)
`~PSP` PRX, tag `0xD91612F0` = type2 / code `0x5D`. pspdecrypt(John-K) 포팅으로 kirk7(AES-128-CBC) + CMD1 마스터키 복호 → MIPS ELF 5,142,244B. **PPSSPP는 복호된 ELF를 EBOOT.BIN 자리에 넣으면 그대로 부팅**한다(암호화 재적용 불필요, 실기 CFW도 동작). 도구: `decrypt_prx.py` + `gas_keys.py`.

---

## 3. 인코딩 전략 (핵심)

- **폰트 재매핑**: 게임 폰트의 미사용 한자 슬롯("도너")에 한글 글리프를 주입하고, 번역문을 그 슬롯 코드로 재인코딩한다. cp932에는 한글이 없으므로 이 단계가 필수.
- **charset 테이블은 GBU와 100% 바이트 동일**(6953개) → GBU의 donor/`kr_map`/인코딩을 그대로 이식.
- **폰트 로드 경로 함정**: 게임은 `gundam.dat`가 아니라 **fileset.dat gameinit 번들의 RAIC 사본**에서 폰트를 로드한다. 양쪽 모두 주입.
- **★도너 배정은 세이브에 각인됨**: 세이브에 저장되는 텍스트(소대명·파일럿명)는 저장 시점의 도너 바이트로 기록된다. 빌드마다 배정이 바뀌면 옛 세이브 텍스트가 깨진다. → `kr_map_stable.json`에 char→donor를 **append-only 고정**. **배포 후 패치 갱신 시에도 이 파일을 유지해야 세이브 호환.**

---

## 4. fileset 수정 규칙 (인게임 반복 테스트로 확정)

파일은 커져도 되지만(FSTS 엔트리 off/usize/csize 갱신) **두 가지 제약**이 있다.

1. **번들 이동 금지** — 전역 재패킹으로 번들 위치(doff)가 바뀌면 크래시. 반드시 모든 번들을 원위치에 두는 **최소 변경 재패킹**(dsize만 갱신)을 쓴다.
2. **파일 성장 금지(원칙)** — 커진 파일이 뒤 파일을 밀면, 밀린 파일(특히 GIM)의 오프셋을 참조하는 외부 stale 포인터 때문에 손상된다. → **모든 파일을 원본 `csize` 이내로 맞추고 0 패딩.** GIM은 원본 압축 크기보다 커지면 반영하지 않는다.

RAIC로 재압축한 한글 데이터가 원문보다 커지는 경우(흩어진 한자 바이트쌍은 압축률이 나쁨)가 잦아, 공백 제거·간결 번역·폰트 크기 축소로 슬롯 이내에 맞춘다.

---

## 5. 번역 소스별 처리

| 소스 | 처리 | 도구 |
|---|---|---|
| 평문 CSV 9종 | 셀 단위 in-place, 원문 csize 이내 | `build_kr.py` |
| EBOOT 얼럿 104 | 슬롯≤원본, NUL 패딩 | `eboot_strings.py` |
| EBOOT UI 2,047 + 칭호 79 | 오프셋 직접 패치 | `eboot_ui_*`, `eboot_titles_extra.py` |
| FES 무전 4,603 | NUL 종단 in-place, 바이트코드 무변조 | `fes_extract.py`, `fes_patch.py` |
| HUD 표시명(locate) 1,627 | 번들별 in-place (동명이본 안전) | `locate_tl.py` |
| GIM 이미지 글자 | ARK의 실제 TXOS crop 셀 단위 재도색 | `patch_shop/vs/myroom/situation_titles.py` |

### GIM 식자 노하우 (반복 실패 끝에 확정)
- 엔진은 라벨을 **고정 crop(UV 사각)** 으로 잘라 배치한다. crop 경계 밖을 지우면 이웃 스프라이트가 손상되고, 셀보다 크게 그리면 잘린다. → ARK(ARKF)의 **TXOS crop 좌표를 규명**해 셀 단위로만 교체.
- **팔레트 0번이 투명이라고 가정하면 안 된다**(반투명 검정인 경우 있음). 팔레트에서 **알파가 가장 낮은 실제 투명 인덱스**를 찾아 지운다(`patch_alpha`).
- 조밀한 아틀라스(대시보드 등)는 crop 테이블을 규명하기 전까지 보류했다가, `myroom_00.ark`의 ARKF 구조를 해석해 실제 셀을 확정한 뒤 반영.

---

## 6. 교훈 (버그 이력)

- **엔진 내부 식별자는 번역 금지**: EBOOT 문자열 중 `テキスト1/2`(event.csv 컬럼명), `なし`(스크롤 방향 값) 등은 표시용이 아니라 엔진이 CSV를 찾는 **룩업 키**다. 이를 번역하면 컬럼 매칭이 깨져 프롤로그 텍스트가 통째로 사라졌다. → 블랙리스트로 방어.
- **용어 사전은 최장 일치 우선**: `ロックオン`→잠금, `ジオン`→`ジオング` 처럼 짧은 패턴이 긴 고유명사를 먹는 오역 발생. 사전을 긴 것부터 등록.
- **★크래시 원인 = 에뮬레이터 버그였음**: 샵 진입·전투 중 간헐 크래시가 전부 Windows 이벤트 로그상 동일 지점(`PPSSPPWindows64.exe+0x55b2ac`)이었다. 패치와 무관한 **PPSSPP 1.19.3 IR Interpreter 버그**. `ppsspp.ini`에서 `CPUCore=2`(IR)→`1`(JIT)로 해결. → 게임 크래시를 이분 탐색하기 전에 **호스트 프로세스 종료 여부와 이벤트 로그 오프셋부터** 확인할 것.
- **세이브 스테이트 함정**: 구형 `.ppst`는 EBOOT RAM을 복원하므로, 완성 ISO의 EBOOT 바이트가 정상이어도 옛 텍스트가 재현된다. 검증은 반드시 새 부팅으로.

---

## 7. 빌드

```bash
cd tools
python build_kr.py            # 폰트 주입 + CSV/GIM/locate/FES/EBOOT 전체 반영
python patch_event.py         # event.csv(gundam.dat flat) 반영
python verify_shop_gim.py     # 정적 검증
python verify_vs_gim.py
python verify_myroom_gim.py
python verify_situation_titles.py
python verify_situation_title_gim.py
```

환경변수로 영역별 비활성화: `GAS_NO_SHOP` / `GAS_NO_VS` / `GAS_NO_MYROOM` / `GAS_NO_SITUATION_TITLE` / `GAS_NO_LOCATE` / `GAS_NO_FES`.

최종 빌드 검증: 샵 GIM 4 · VS GIM 6사본 · 대시보드 · 시추에이션명 181 · 시추에이션 제목 GIM 181 전부 통과, fileset 이동·성장 0.
