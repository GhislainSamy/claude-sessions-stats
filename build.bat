@echo off
echo ============================================
echo  Claude Session Stats — Build EXE
echo ============================================
echo.

:: Vérifier que Python est disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python introuvable dans le PATH.
    pause
    exit /b 1
)

:: Installer les dépendances si besoin
echo [1/3] Installation des dependances...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERREUR] pip install a echoue.
    pause
    exit /b 1
)

:: Nettoyer les anciens builds
echo [2/3] Nettoyage des anciens builds...
if exist "dist\claude_stats.exe" del /f /q "dist\claude_stats.exe"
if exist "build" rmdir /s /q "build"

:: Lancer PyInstaller
echo [3/3] Compilation avec PyInstaller...
python -m PyInstaller claude_stats.spec --noconfirm
if errorlevel 1 (
    echo [ERREUR] PyInstaller a echoue.
    pause
    exit /b 1
)

:: Copier config.ini à côté de l'exe
echo.
echo Copie de config.ini dans dist\...
copy /y "config.ini" "dist\config.ini" >nul

echo.
echo ============================================
echo  Build termine !
echo  Executable : dist\claude_stats.exe
echo  Config     : dist\config.ini
echo ============================================
echo.
pause
