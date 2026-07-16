@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "OUT=%ROOT%out"
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
set "VSINSTALL="

if exist "%VSWHERE%" (
  for /f "usebackq delims=" %%I in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSINSTALL=%%I"
)

if not defined VSINSTALL if exist "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" set "VSINSTALL=C:\Program Files\Microsoft Visual Studio\18\Community"
if not defined VSINSTALL (
  echo ERROR: Visual Studio with the x64 C++ toolchain was not found.
  exit /b 1
)

set "VCVARS=%VSINSTALL%\VC\Auxiliary\Build\vcvars64.bat"
if not exist "%VCVARS%" (
  echo ERROR: vcvars64.bat was not found under "%VSINSTALL%".
  exit /b 1
)

call "%VCVARS%" >nul
if errorlevel 1 exit /b 1

if not exist "%OUT%" mkdir "%OUT%"
if errorlevel 1 exit /b 1

set "COMMON=/nologo /std:c++17 /EHsc /W4 /permissive- /Zc:__cplusplus /O2 /MT /DNDEBUG /DUNICODE /D_UNICODE /DWIN32_LEAN_AND_MEAN /DNOMINMAX"

cl %COMMON% /Fo"%OUT%\injector.obj" /Fd"%OUT%\injector.pdb" "%ROOT%injector.cpp" /Fe"%OUT%\olm_injector.exe" /link Advapi32.lib
if errorlevel 1 exit /b 1

cl %COMMON% /LD /Fo"%OUT%\smoother2_collector.obj" /Fd"%OUT%\smoother2_collector.pdb" "%ROOT%smoother2_collector.cpp" /Fe"%OUT%\olm_smoother2_collector.dll" /link Advapi32.lib Bcrypt.lib Psapi.lib
if errorlevel 1 exit /b 1

echo Built:
echo   %OUT%\olm_injector.exe
echo   %OUT%\olm_smoother2_collector.dll
exit /b 0
