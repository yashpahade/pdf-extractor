1. Backend Run Karne Ke Liye (Terminal 1)
powershell


cd "c:\Users\omkar\Desktop\pdf extracter\backend"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
2. Frontend Run Karne Ke Liye (Terminal 2)
powershell


cd "c:\Users\omkar\Desktop\pdf extracter\frontend"
npx vite --host 127.0.0.1
(Frontend run hone ke baad aap usme diye gaye link jaise http://127.0.0.1:5173/ ya 5174 par click karke UI open kar sakte hain).
