@echo off
REM This script executes the main Python application using 'uv'.

echo.
echo =================================================
echo      Starting the Repository Mining Process
echo =================================================
echo.

REM Executes the main.py script using uv
uv run main.py

echo.
echo =================================================
echo      Process Finished
echo =================================================
echo.

REM Pauses the execution to allow the user to see the final output.
pause