@echo off
title Menu Itineraires

:MENU
cls
echo ============================================
echo            MENU DES ITINERAIRES
echo ============================================
echo 1. Paris - Culturel
echo 2. Paris - Nature
echo 3. Limoux - Culturel
echo 4. Limoux - Nature
echo 5. Lyon - Culturel
echo 6. Lyon - Nature
echo 7. Quitter
echo ============================================
set /p choix="Votre choix : "

if "%choix%"=="1" call :RUN paris culturel
if "%choix%"=="2" call :RUN paris nature
if "%choix%"=="3" call :RUN limoux culturel
if "%choix%"=="4" call :RUN limoux nature
if "%choix%"=="5" call :RUN lyon culturel
if "%choix%"=="6" call :RUN lyon nature
if "%choix%"=="7" exit

goto MENU

:RUN
cls
set VILLE=%1
set THEME=%2

echo ============================================
echo   TRAITEMENT : %VILLE% - %THEME%
echo ============================================

echo Import des POI de %VILLE%...
python neo4j_module\import\import_city_pois.py %VILLE% data\%VILLE%_pois.json

echo Precalcul des distances pour %VILLE%...
python neo4j_module\precalc\precompute_distances.py %VILLE%

set TESTFILE=tests\test_%VILLE%_%THEME%.py

echo Lancement du test : %TESTFILE%
pytest %TESTFILE% -q

echo ============================================
echo   FIN DU TRAITEMENT %VILLE% - %THEME%
echo ============================================
pause
goto MENU

