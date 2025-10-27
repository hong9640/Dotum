#!/usr/bin/env bash
set -euo pipefail

# =========================
# Git repo root 확인
# =========================
if ! REPO="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  echo "[ERROR] Run this inside a Git repository." >&2
  exit 1
fi

# =========================
# 경로 변수
# =========================
HOOKDIR="$REPO/.githooks"
COMMITMSG="$HOOKDIR/commit-msg"

# ---- 커밋 템플릿 탐색 우선순위 (.gitlab -> .github -> 루트) ----
TPL=""
if   [ -f "$REPO/.gitlab/.gitmessage.txt" ]; then TPL="$REPO/.gitlab/.gitmessage.txt"
elif [ -f "$REPO/.github/.gitmessage.txt" ]; then TPL="$REPO/.github/.gitmessage.txt"
elif [ -f "$REPO/.gitmessage.txt"        ]; then TPL="$REPO/.gitmessage.txt"
fi

echo "[INFO] REPO     = $REPO"
echo "[INFO] HooksDir = $HOOKDIR"
if [ -n "$TPL" ]; then
  echo "[INFO] Template = $TPL"
else
  cat <<'EOF'
[WARN] 커밋 템플릿(.gitmessage.txt)을 찾지 못했습니다.
       다음 중 한 곳에 파일을 만들어 주세요:
         - .gitlab/.gitmessage.txt
         - .github/.gitmessage.txt
         - (리포지토리 루트)/.gitmessage.txt
EOF
fi

# =========================
# 훅 폴더/파일 확인
# =========================
mkdir -p "$HOOKDIR"
if [ ! -f "$COMMITMSG" ]; then
  echo "[ERROR] 훅 파일 없음: $COMMITMSG"
  echo "        .githooks/commit-msg 를 먼저 만들어 주세요."
  exit 1
fi

# =========================
# (보강) 과거 전역/시스템 설정 정리(조용히, 실패 무시)
# =========================
git config --global --unset commit.template  >/dev/null 2>&1 || true
git config --system --unset commit.template  >/dev/null 2>&1 || true

# =========================
# Git 설정(현재 저장소 '로컬'로 강제 덮어쓰기)
# =========================
if [ -n "$TPL" ]; then
  git config --local commit.template "$TPL"
fi
git config --local core.hooksPath "$HOOKDIR"

# (선택) VS Code를 커밋 에디터로 지정하려면 주석 해제
# git config --local core.editor "code -w"

# =========================
# 훅 실행 권한 부여(가능한 경우)
# =========================
chmod +x "$COMMITMSG" 2>/dev/null || true

# =========================
# [보조] GitHub PR 템플릿 -> GitLab MR 템플릿 복사
#  - GitLab 경로: .gitlab/merge_request_templates/*.md
# =========================
GH_PR_DIR="$REPO/PULL_REQUEST_TEMPLATE"
GL_MR_DIR="$REPO/.gitlab/merge_request_templates"
if [ -d "$GH_PR_DIR" ]; then
  mkdir -p "$GL_MR_DIR"
  did_copy=0
  for f in "$GH_PR_DIR"/*.md; do
    [ -e "$f" ] || continue
    b="$(basename "$f")"
    if [ ! -e "$GL_MR_DIR/$b" ]; then
      cp "$f" "$GL_MR_DIR/$b"
      echo "[INFO] MR 템플릿으로 복사: $b -> .gitlab/merge_request_templates/$b"
      did_copy=1
    fi
  done
  [ "$did_copy" -eq 0 ] && echo "[INFO] 복사할 PR 템플릿(.md)이 없습니다."
fi

# =========================
# Windows 예약 장치명(nul 등) 존재 시 안내
# =========================
if [ -e "$REPO/nul" ]; then
  cat <<'EOF'
[WARN] 'nul' 항목이 리포 루트에 있습니다. Windows 예약 장치명이라 Git 에러가 납니다.
       Git Bash에서 아래 명령으로 삭제하세요:
         cmd /c "del /f /q \\?\%CD%\nul" && cmd /c "rd /s /q \\?\%CD%\nul"
EOF
fi

echo
echo "[OK] 로컬 Git 설정을 강제로 덮어썼습니다."
[ -n "$TPL" ] && echo " - 템플릿: $TPL"
echo " - 훅 경로: $HOOKDIR"
echo
echo "사용법: 템플릿을 쓰려면 'git commit' (-m 없이) 를 사용하세요."
echo "(선택) VS Code를 기본 에디터로: git config --local core.editor \"code -w\""
