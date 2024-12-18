@echo off
echo Starting Chat System...

:: Abrir o Binder
start cmd /k "python binder/binder.py"

:: Esperar 2 segundos para garantir que o Binder está ativo
timeout /t 2 /nobreak > nul

:: Abrir o Servidor
start cmd /k "python server/server.py"

:: Esperar 2 segundos para garantir que o Servidor está ativo
timeout /t 2 /nobreak > nul

:: Abrir o Cliente 1
start cmd /k "python cliente/cliente.py"

:: Abrir o Cliente 2
start cmd /k "python cliente/cliente.py"

echo Chat System started. Close this window if you do not need it.
