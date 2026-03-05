@ECHO OFF
title demo1 Folder Locker

:: Check if the folder is already locked. If so, jump to the UNLOCK section.
if EXIST "demo1.{21EC2020-3AEA-1069-A2DD-08002B30309D}" goto UNLOCK

:: Check if the "demo1" folder exists to be locked. If not, show an error.
if NOT EXIST "demo1" goto NOTFOUND

:LOCK
echo Are you sure you want to lock the "demo1" folder? (Y/N)
set /p "cho=>"
if /i "%cho%"=="Y" (
    ren "demo1" "demo1.{21EC2020-3AEA-1069-A2DD-08002B30309D}"
    attrib +h +s "demo1.{21EC2020-3AEA-1069-A2DD-08002B30309D}"
    echo The "demo1" folder has been locked.
)
goto END

:UNLOCK
set /p "pass=>Enter password to unlock: "
if NOT %pass%==MyPass123@04 goto FAIL
attrib -h -s "demo1.{21EC2020-3AEA-1069-A2DD-08002B30309D}"
ren "demo1.{21EC2020-3AEA-1069-A2DD-08002B30309D}" "demo1"
echo The "demo1" folder has been unlocked.
goto END

:FAIL
echo Invalid password.
goto END

:NOTFOUND
echo Error: Could not find the "demo1" folder in this directory.
goto END

:END
pause
