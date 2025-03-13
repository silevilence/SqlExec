@echo off
echo 正在打包 SQL Exec...
uv run pyinstaller sqlexec.spec --clean
echo.
echo 打包完成！
pause 