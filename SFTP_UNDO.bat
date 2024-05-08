call "%~dp0\WPy64-3720\scripts\env_for_icons.bat"
set /p hostname="Enter cube name (eg: s02049): "
python cli.py %hostname% --undo-sftp
pause