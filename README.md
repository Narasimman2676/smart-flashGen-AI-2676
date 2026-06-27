# Smart Flashcard Generator using NLP

An intelligent, full-stack web application designed to help students and educators study more efficiently. By uploading study materials (PDF, DOCX, or TXT), the application automatically extracts key concepts, identifies named entities, and generates active-recall flashcards and multiple-choice quizzes using state-of-the-art Natural Language Processing (NLP) models.

---

## 📖 Project Description

This project converts raw study notes, textbook chapters, or lecture slides into structured flashcards and interactive quizzes automatically using NLP. It features a complete user authentication system, a clean study dashboard with quick statistics, a drag-and-drop document upload interface, a 3D flipping flashcard study room, an examination platform with timer-based grading, and an analytics suite that tracks mastery levels and identifies weak topics for focused review.

---

## ✨ Features

- **User Authentication (JWT):** Secure registration, login, token-based session management, and protected routes using hashed passwords (bcrypt) and JSON Web Tokens.
- **Dynamic Study Dashboard:** Displays personalized greetings, quick learning stats (total documents, flashcards created, quizzes taken, average score), study recommendations, and a list of recently uploaded documents.
- **Intelligent Document Upload:** Drag-and-drop file uploader (supporting PDF, DOCX, and TXT files up to 100MB) with step-by-step progress tracking, upload timeline, and real-time text extraction.
- **AI-Powered Flashcard Generation:** Automatically analyzes extracted text to find high-yield concepts and constructs cloze deletion or question-answer style flashcards.
- **Immersive Study Room:** 3D card-flipping carousel interface with keyboard shortcut support (Arrow keys for navigation, Spacebar to flip) along with a management grid to edit, delete, or star key cards.
- **Assessment MCQ Quiz Mode:** Dynamic timer-driven 10-question quizzes generated from active study sets, featuring A/B/C/D option bubbles, real-time timer countdowns, auto-submission, and a detailed performance review sheet with mastery indicators.
- **Analytics Dashboard:** Deep-dive metrics including average performance scores, correct-vs-incorrect ratios, and automated tracking of weak topics to guide study sessions.

---

## 🛠️ Technology Stack

### Frontend
- **React (Vite):** Reactive component-based single-page application framework.
- **React Router:** Handles secure declarative routing and protected layouts.
- **Axios:** Asynchronous HTTP communication with the backend API.
- **Lucide React:** Premium clean iconography suite.
- **Vanilla CSS:** Beautifully crafted, responsive user interfaces with CSS custom properties (variables), featuring glassmorphism, responsive grids, and clean micro-animations.

### Backend
- **Flask:** Lightweight Python WSGI web framework.
- **Flask-SQLAlchemy:** Object-Relational Mapping (ORM) to interface with the database.
- **Flask-JWT-Extended:** Handles JWT signing, token refreshes, and route protection.
- **Flask-CORS:** Configures Cross-Origin Resource Sharing for secure communication.
- **Bcrypt:** Secure password hashing and verification.

### Database
- **SQLite:** Lightweight, serverless relational database engine.

### Natural Language Processing (NLP) Pipeline
The backend uses a multi-tiered hybrid NLP pipeline to extract, refine, and generate questions:
1. **KeyBERT:** Extracts prominent keywords and keyphrases from documents using SentenceTransformer embeddings.
2. **spaCy (`en_core_web_sm`):** Used for Named Entity Recognition (NER) (e.g. locating names, locations, organizations) and noun-phrase parsing to select optimal question candidates.
3. **Hugging Face Transformers (`t5-small`):** A sequence-to-sequence text-generation model used to translate contextual sentences and keywords into high-quality educational questions.
4. **SentenceTransformers (`all-MiniLM-L6-v2`):** Used to evaluate semantic similarity, group related concepts, and filter out low-yield or redundant questions.
5. **NLTK (`punkt`, `stopwords`):** Used for robust sentence tokenization, boundary detection, and filtering out common English stopwords.

---

## 📂 Project Structure

```text
flash-generator/
├── backend/                   # Flask Backend Application
│   ├── config/                # Environment and app configurations
│   ├── database/              # Database initializers and sessions
│   ├── models/                # SQLAlchemy database models (User, Document, Flashcard, etc.)
│   ├── nlp/                   # NLP processing scripts (extractor, generator)
│   ├── routes/                # Flask blueprints and API endpoints
│   ├── tests/                 # Unit and integration test suites
│   ├── uploads/               # Local directory for processed document storage
│   ├── flashcards.db          # SQLite Database file
│   ├── requirements.txt       # Python dependencies list
│   └── run.py                 # Application entry point script
│
├── frontend/                  # React Frontend Application
│   ├── src/
│   │   ├── assets/            # Static assets and illustrations
│   │   ├── components/        # Reusable components (Navbar, Layout, etc.)
│   │   ├── pages/             # Page views (Dashboard, Login, Upload, Flashcards, Quiz, Analytics)
│   │   ├── services/          # API services (Axios interceptors)
│   │   ├── styles/            # Vanilla CSS styling files (index.css, auth.css, dashboard.css, etc.)
│   │   ├── App.jsx            # Main app router and provider setup
│   │   └── main.jsx           # Entry point
│   ├── package.json           # Frontend dependency manifest
│   └── vite.config.js         # Vite dev server and proxy configurations
│
├── README.md                  # Project documentation (this file)
└── .gitignore                 # Version control exclusions
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Node.js (v16.x or higher) and npm

---

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a Python virtual environment:
   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - **On Windows (Command Prompt / PowerShell):**
     ```powershell
     .venv\Scripts\activate
     ```
   - **On macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the database initializations and start the Flask development server:
   ```bash
   python run.py
   ```
   *The backend will boot up and start listening on `http://127.0.0.1:5000`.*

---

### 2. Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install the node packages:
   ```bash
   npm install
   ```

3. Start the Vite local development server:
   ```bash
   npm run dev
   ```
   *Vite will compile your assets and serve the app, typically at `http://localhost:5173/` or `http://localhost:5174/`.*

---

## 🌐 Deployment

### Backend (Render.com)
The Flask backend is deployed live at: `https://smart-flashgen-ai-2676.onrender.com`

### Frontend (Vercel)
The React (Vite) frontend is configured to build and deploy seamlessly to Vercel:
1. **Vite Environment Variables**: In production mode, the API endpoint is configured using `VITE_API_URL` which points to `https://smart-flashgen-ai-2676.onrender.com` inside the production config ([`.env.production`](file:///c:/Users/Narasimman/OneDrive/Desktop/flash%20generator/frontend/.env.production)).
2. **Client-Side Routing (`vercel.json`)**: To prevent `404` errors when reloading direct routes (like `/login`, `/dashboard`), the rewrite configuration is defined in [`vercel.json`](file:///c:/Users/Narasimman/OneDrive/Desktop/flash%20generator/frontend/vercel.json).

**How to Deploy the Frontend to Vercel:**
- Go to the Vercel Dashboard, and click **Add New > Project**.
- Select and import your Git repository.
- Under **Configure Project**, set the **Root Directory** as `frontend` (this is very important since your frontend is inside a subfolder).
- Vercel will automatically detect the **Vite** preset and configure the build command (`npm run build`) and output directory (`dist`).
- Click **Deploy**.

---

### ⚙️ Low-Memory Deployment Optimization (e.g. Render.com Free Tier)

By default, the backend loads heavy Natural Language Processing models (like `KeyBERT`, `t5-small`, and `SentenceTransformer` with PyTorch) which consume **1.2GB - 1.5GB of RAM** on startup. This causes Out-Of-Memory (OOM) crashes in environments with memory limits like Render's free tier (512MB RAM).

To resolve this, the codebase includes an optimized low-memory execution path that uses lightweight, built-in python fallbacks (NLTK and Regex algorithms) that consume **under 100MB of RAM**.

To enable low-memory optimization, set the environment variable:
```bash
LOW_MEMORY_MODE=True
```

#### Run in Low-Memory Mode Locally:
- **On Windows (PowerShell):**
  ```powershell
  $env:LOW_MEMORY_MODE="True"
  python run.py
  ```
- **On macOS/Linux:**
  ```bash
  export LOW_MEMORY_MODE=True
  python run.py
  ```

---

## 🔌 API Endpoints

All backend API routes are prefixed with `/api` and are structured as follows:

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/auth/signup` | Registers a new user account | No |
| **POST** | `/api/auth/login` | Authenticates a user & returns access token | No |
| **POST** | `/api/auth/logout` | Revokes user session | Yes (JWT) |
| **POST** | `/api/upload` | Uploads study note files (PDF/DOCX/TXT) and triggers NLP pipeline | Yes (JWT) |
| **GET** | `/api/flashcards` | Retrieves all generated flashcards for the active user | Yes (JWT) |
| **PUT** | `/api/flashcards/<id>`| Updates/edits the text or starred status of a flashcard | Yes (JWT) |
| **DELETE**| `/api/flashcards/<id>`| Deletes a specific flashcard | Yes (JWT) |
| **POST** | `/api/quiz` | Generates a randomized multiple-choice assessment | Yes (JWT) |
| **POST** | `/api/quiz/submit` | Submits quiz answers, grades them, and saves progress | Yes (JWT) |
| **GET** | `/api/analytics` | Retrieves study stats, scores, and weak topics lists | Yes (JWT) |

---

## 📸 Screenshots

*Below are descriptions of the core screens designed for the application. You can place your actual application screenshots in a `docs/screenshots/` folder and link them below.*

### 1. Login & Signup Page
A modern split-screen design featuring a custom vectors illustration alongside a clean glassmorphism container for forms, equipped with password-visibility toggles and comprehensive input validation.
*(Path: `docs/screenshots/login.png`)*

### 2. Dashboard
A student-friendly command center featuring a personalized greeting card, numerical quick-stats, daily study recommendations, and a list of recently uploaded study materials.
*(Path: `docs/screenshots/dashboard.png`)*

### 3. Flashcards Study Room
An interactive 3D study interface. Supports a carousel viewport that flips cards with smooth CSS 3D transitions (via Spacebar or Click) and a management grid table to filter, edit, or delete items.
*(Path: `docs/screenshots/flashcards.png`)*

### 4. MCQ Examination Room
A sleek, single-question-at-a-time assessment system with options mapped to letter bubbles (A, B, C, D), a visible countdown clock, and an automated submission process upon timeout.
*(Path: `docs/screenshots/quiz.png`)*

### 5. Analytics Dashboard
A visual reporting dashboard showing overall quiz scores, correct vs. incorrect answers metrics, and a dedicated panel highlighting weak topics to study again.
*(Path: `docs/screenshots/analytics.png`)*

---

## 🔮 Future Enhancements

- **AI-Powered Synthesized Summaries:** Automatically generate short summary cards for each uploaded document.
- **Enhanced PDF Parsing:** Integrate OCR support for scanned documents and image-heavy lecture slides.
- **Voice-Based Active Recall Quiz:** Let students speak their answers, using speech-to-text models to assess conceptual knowledge.
- **Mobile Companion Application:** Develop a responsive React Native mobile app for offline active-recall on the go.

---

## 👥 Authors

- **Team Members:** [Your Names Here]
- **College Name:** [Your College Name Here]

---

## 📄 License

This project is licensed under the **MIT License** (or is provided *For Educational Purposes Only*). See your repository files for full licensing terms.
