@echo off
setlocal

REM =========================
REM  Git repo root 확인
REM =========================
for /f "delims=" %%i in ('git rev-parse --show-toplevel 2^>nul') do set "REPO=%%i"
if not defined REPO (
  echo [ERROR] Git 저장소 안에서 실행해 주세요.
  exit /b 1
)

REM =========================
REM  경로 변수
REM =========================
set "HOOKDIR=%REPO%\.githooks"
set "COMMITMSG=%HOOKDIR%\commit-msg"

REM ---- 커밋 템플릿 탐색 우선순위 (.gitlab -> .github -> 루트) ----
set "TPL="
if exist "%REPO%\.gitlab\.gitmessage.txt" set "TPL=%REPO%\.gitlab\.gitmessage.txt"
if not defined TPL if exist "%REPO%\.github\.gitmessage.txt" set "TPL=%REPO%\.github\.gitmessage.txt"
if not defined TPL if exist "%REPO%\.gitmessage.txt"        set "TPL=%REPO%\.gitmessage.txt"

echo [INFO] REPO     = %REPO%
echo [INFO] HooksDir = %HOOKDIR%
if defined TPL (
  echo [INFO] Template = %TPL%
) else (
  echo [WARN] 커밋 템플릿(.gitmessage.txt)을 찾지 못했습니다.
  echo        다음 중 한 곳에 파일을 만들어 주세요:
  echo          - .gitlab\.gitmessage.txt
  echo          - .github\.gitmessage.txt
  echo          - (리포지토리 루트)\.gitmessage.txt
)

REM =========================
REM  훅 폴더/파일 확인
REM =========================
if not exist "%HOOKDIR%" mkdir "%HOOKDIR%"
if not exist "%COMMITMSG%" (
  echo [ERROR] 훅 파일 없음: %COMMITMSG%
  echo         .githooks\commit-msg 를 먼저 만들어 주세요.
  exit /b 1
)

REM =========================
REM  (보강) 과거 전역/시스템 설정이 꼬여있을 수 있으니 조용히 정리
REM  - 실패해도 무시(2>nul)
REM =========================
git config --global --unset commit.template  2>nul
git config --system --unset commit.template  2>nul

REM =========================
REM  Git 설정(현재 저장소 "로컬"로 강제 덮어쓰기)
REM =========================
if defined TPL git config --local commit.template "%TPL%"
git config --local core.hooksPath "%HOOKDIR%"

REM (선택) VS Code를 커밋 에디터로 지정하려면 주석 해제
REM git config --local core.editor "code -w"

REM =========================
REM  실행 권한 부여(가능한 경우: Git Bash/WSL)
REM =========================
where bash >nul 2>nul
if %ERRORLEVEL%==0 (
  bash -lc "chmod +x '%COMMITMSG%'" 2>nul
)

REM =========================
REM  [보조] GitHub PR 템플릿 -> GitLab MR 템플릿 복사
REM  - GitLab 경로: .gitlab/merge_request_templates/*.md
REM =========================
set "GH_PR_DIR=%REPO%\PULL_REQUEST_TEMPLATE"
set "GL_MR_DIR=%REPO%\.gitlab\merge_request_templates"
if exist "%GH_PR_DIR%" (
  if not exist "%GL_MR_DIR%" mkdir "%GL_MR_DIR%"
  for %%F in ("%GH_PR_DIR%\*.md") do (
    if not exist "%GL_MR_DIR%\%%~nxF" (
      copy "%%~fF" "%GL_MR_DIR%\%%~nxF" >nul
      echo [INFO] MR 템플릿으로 복사: %%~nxF  ^(-> .gitlab\merge_request_templates\%%~nxF^)
    )
  )
)

REM =========================
REM  Windows 예약 장치명(nul 등) 존재 시 안내
REM =========================
if exist "%REPO%\nul" (
  echo [WARN] 'nul' 항목이 리포 루트에 존재합니다. Windows 예약 장치명이라 Git 에러가 납니다.
  echo        아래 명령으로 제거해 주세요 (Git Bash에서 실행):
  echo        cmd /c "del /f /q \\?\%%CD%%\nul" ^&^& cmd /c "rd /s /q \\?\%%CD%%\nul"
)

echo.
echo [OK] 로컬 Git 설정을 강제로 덮어썼습니다.
if defined TPL echo  - 템플릿: %TPL%
echo  - 훅 경로: %HOOKDIR%
echo.
echo 사용법: 템플릿을 쓰려면 ^`git commit^` (-m 없이) 를 사용하세요.
echo VS Code를 기본 에디터로 쓰려면:  git config --local core.editor "code -w"
echo.
endlocal
