@echo off
setlocal

REM ==== Git 저장소 루트 확인 ====
for /f "delims=" %%i in ('git rev-parse --show-toplevel 2^>nul') do set "REPO=%%i"
if not defined REPO (
  echo [ERROR] Git 저장소 안에서 실행해 주세요.
  exit /b 1
)

REM ==== 경로(후크/템플릿) 기본값 ====
set "HOOKDIR=%REPO%\.githooks"
set "COMMITMSG=%HOOKDIR%\commit-msg"

REM ---- 커밋 템플릿 탐색 우선순위 (.gitlab -> .github -> 루트) ----
set "TPL="
if exist "%REPO%\.gitlab\.gitmessage.txt" ( set "TPL=%REPO%\.gitlab\.gitmessage.txt" )
if not defined TPL if exist "%REPO%\.github\.gitmessage.txt" ( set "TPL=%REPO%\.github\.gitmessage.txt" )
if not defined TPL if exist "%REPO%\.gitmessage.txt" ( set "TPL=%REPO%\.gitmessage.txt" )

echo [INFO] REPO     = %REPO%
echo [INFO] HooksDir = %HOOKDIR%

if defined TPL (
  echo [INFO] Template = %TPL%
) else (
  echo [WARN] 커밋 템플릿(.gitmessage.txt)을 찾지 못했습니다.
  echo        아래 경로 중 한 곳에 파일을 만들어 주세요:
  echo          - .gitlab\.gitmessage.txt
  echo          - .github\.gitmessage.txt
  echo          - (리포지토리 루트)\.gitmessage.txt
)

REM ==== 훅 폴더/파일 확인 ====
if not exist "%HOOKDIR%" mkdir "%HOOKDIR%"
if not exist "%COMMITMSG%" (
  echo [ERROR] 훅 파일 없음: %COMMITMSG%
  echo         .githooks\commit-msg 를 먼저 만들어 주세요.
  exit /b 1
)

REM ==== Git 설정(현재 저장소 한정) ====
if defined TPL git config commit.template "%TPL%"
git config core.hooksPath "%HOOKDIR%"

REM ==== 실행 권한(가능하면 부여; Windows+Git Bash 환경) ====
where bash >nul 2>nul
if %ERRORLEVEL%==0 (
  bash -lc "chmod +x '%COMMITMSG%'" 2>nul
)

REM ==== [보조] GitHub PR 템플릿을 GitLab MR 템플릿으로 복사 ====
REM GitLab MR 템플릿 경로: .gitlab/merge_request_templates/*.md
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

echo.
echo [OK] 커밋 템플릿/훅 적용 완료.
if defined TPL echo  - 템플릿: %TPL%
echo  - 훅 경로: %HOOKDIR%
echo.
echo VS Code를 기본 에디터로 쓰려면:
echo   git config core.editor "code -w"
echo.
endlocal
