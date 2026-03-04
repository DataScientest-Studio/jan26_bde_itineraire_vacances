@echo off
echo ============================================
echo   PARIS : IMPORT + PRECALC + TESTS
echo ============================================
python import\import_city_pois.py Paris data\paris_pois.json
python precalc\precompute_distances.py Paris
pytest tests\test_paris_culturel.py -q
pytest tests\test_paris_nature.py -q

echo.
echo ============================================
echo   LYON : IMPORT + PRECALC + TESTS
echo ============================================
python import\import_city_pois.py Lyon data\lyon_pois.json
python precalc\precompute_distances.py Lyon
pytest tests\test_lyon_culturel.py -q
pytest tests\test_lyon_nature.py -q

echo.
echo ============================================
echo   LIMOUX : IMPORT + PRECALC + TESTS
echo ============================================
python import\import_city_pois.py Limoux data\limoux_pois.json
python precalc\precompute_distances.py Limoux
pytest tests\test_limoux_culturel.py -q
pytest tests\test_limoux_nature.py -q

echo.
echo ============================================
echo   TOUS LES TESTS SONT TERMINÉS
echo ============================================
pause
