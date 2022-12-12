:stop
sc stop Intel(R)LMTTargetService

rem cause a ~10 second sleep before checking the service state
ping 127.0.0.1 -n 10 -w 1000 > nul

sc query Intel(R)LMTTargetService | find /I "STATE" | find "STOPPED"
if errorlevel 1 goto :stop
goto :start

:start
net start | find /i "My Service">nul && goto :start
sc start Intel(R)LMTTargetService