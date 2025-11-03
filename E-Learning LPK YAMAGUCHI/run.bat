@echo off
title LMS Japan - Auto Start with Ngrok
cd /d "C:\Users\MSI\Downloads\E-Learning LPK YAMAGUCHI V1.1"

echo ========================================
echo    Starting LMS Japan dengan Ngrok
echo ========================================
echo.

:: 1. Set ngrok auth token
echo [1/4] Setting Ngrok Auth Token...
ngrok authtoken 34utbZYQl80GDch5ccZw57PfVZm_659m5PdLnM5A54CYeHXTY

:: 2. Jalankan Flask di background
echo [2/4] Menjalankan aplikasi Flask...
start "" /min python app.py

:: 3. Tunggu Flask siap
echo [3/4] Menunggu Flask aktif...
timeout /t 8 >nul

:: 4. Jalankan Ngrok otomatis dan tampilkan URL publik
echo [4/4] Membuka tunnel Ngrok...
for /f "tokens=2 delims=: " %%A in ('ngrok http 5000 ^| findstr "url"') do set URL=%%A

:: Jalankan ngrok normal (bisa lihat URL di CMD)
start "" /wait ngrok http 5000

echo.
echo ========================================
echo  LMS Japan sudah berjalan!
echo  Buka browser ke alamat lokal:
echo      http://127.0.0.1:5000
echo.
echo  Atau gunakan URL publik Ngrok di atas.
echo ========================================
pause
