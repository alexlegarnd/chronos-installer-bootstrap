@echo off
IF EXIST "build" (
    RMDIR /S /Q build
)
IF EXIST "dist" (
    RMDIR /S /Q dist
)
IF EXIST "__pycache__" (
    RMDIR /S /Q __pycache__
)
IF EXIST "main.spec" (
    ERASE main.spec
)