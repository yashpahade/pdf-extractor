# 📄 AI PDF Extractor & Summarizer

A highly scalable, LLM-powered Full-Stack application that allows users to upload, process, and chat with their documents (PDF, DOCX, Images). It intelligently extracts text, chunks it, and uses multiple AI models to summarize and answer questions using RAG (Retrieval-Augmented Generation).

## ✨ Features
- **Multi-Format Support**: Upload PDFs, DOCX, and Images (JPG/PNG).
- **Smart Extraction**: Uses PyMuPDF for lightning-fast PDF text extraction and Tesseract OCR for images.
- **Vector Database**: Integrated with ChromaDB for semantic search and RAG capabilities.
- **Multi-Key Load Balancing**: Bypasses strict free-tier API rate limits by automatically round-robining multiple Groq API keys and gracefully failing over to Google Gemini.
- **Interactive Chat**: Chat directly with your documents to extract specific information.
- **Premium Dark UI**: A highly polished, animated, and responsive LLM-style user interface.

## 🛠️ Tech Stack
- **Frontend**: React, TypeScript, Vite, CSS
- **Backend**: FastAPI, Python, SQLAlchemy (SQLite)
- **Vector Store**: ChromaDB
- **AI Providers**: Groq SDK (Qwen/Llama) & Google GenAI SDK (Gemini Flash)

## 🚀 How to Run Locally

### 1. Backend Setup
Navigate to the backend directory and set up a Python virtual environment:
```bash
cd backend
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` folder with your API keys:
```env
# You can provide multiple Groq keys separated by commas for load balancing!
APP_GROQ_API_KEY=your_groq_key_1,your_groq_key_2
APP_GEMINI_API_KEY=your_gemini_key
APP_GEMINI_MODEL=gemini-flash-latest
APP_GROQ_MODEL=qwen/qwen3.8-27b
```

Start the FastAPI server:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup
Open a **new terminal** and navigate to the frontend directory:
```bash
cd frontend
npm install
npm run dev
```

Open your browser to `http://localhost:5173` (or the port Vite provides) to use the application!
