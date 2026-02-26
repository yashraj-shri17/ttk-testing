# Talk to Krishna - Backend Architecture & Request Flow

This document details exactly what happens when a user asks a question on "Talk to Krishna". It explains the journey of a user's query from the frontend to the final spiritual answer, including the files involved and the logic used at each step.

---

## 1. High-Level Flow Overview

1.  **Input**: User types/speaks a question on the React Website.
2.  **API**: Request hits `website/api_server.py` (Flask).
3.  **Processing**: The core logic in `src/gita_api.py` handles the request.
4.  **Understanding**: An LLM (Groq) translates and extracts meaning from the query.
5.  **Search**: A **Hybrid Search** finds the most relevant Shlokas from `gita_english.json` using semantic embeddings.
6.  **Answer**: A final LLM prompt generates a personalized answer in Hindi/Hinglish.
7.  **Response**: The answer + audio is sent back to the user.

---

## 2. Detailed Step-by-Step Breakdown

### Step 1: The Request (Frontend -> Backend)
- **User Action**: User presses "Ask Krishna".
- **File**: `website/api_server.py`
- **Endpoint**: `/api/ask` (POST method)
- **What Happens**:
    - The server receives `{ "question": "...", "user_id": ... }`.
    - It checks for **Greetings** locally first (e.g., "Radhe Radhe"). If it's just a greeting, it returns an instant pre-set response to save time.
    - It retrieves the user's **Conversation History** from `users.db` (SQLite) to give the AI context.

### Step 2: Relevance Check (The Gatekeeper)
- **File**: `src/gita_api.py` -> `_is_relevant_to_krishna()`
- **Logic**:
    - Before asking the AI, the code runs a **Regex/Keyword Check**.
    - **Blocked Topics**: Sports (Cricket, Virat Kohli), Politics (Modi, Trump), Tech specs, Recipes, Weather.
    - **Allowed Topics**: Emotions, Life problems, Spiritual questions, Relationships.
    - *Why?* To keep "Krishna" focused on spiritual guidance, not general chatbot trivia.

### Step 3: Understanding the Query (The "Brain")
- **File**: `src/gita_api.py` -> `_understand_query()`
- **Action**:
    - The raw Hindi/Hinglish query (e.g., *"Mummy papa shadi ke liye nahi maan rahe"*) is sent to **Groq (Llama 3)**.
- **Goal**:
    - **Translation**: Convert to English for better search (e.g., *"Parents are not agreeing to marriage"*).
    - **Keyword Extraction**: Identify core concepts (e.g., *"family duty love conflict"*).
    - **Tone Analysis**: Is this a crisis? (Handled in Step 5).

### Step 4: Finding the "Sahi Shloka" (The Search)
- **File**: `src/gita_api.py` -> `search()`
- **Method**: **Hybrid Search** (The secret sauce).
    1.  **Semantic Search (Vector)**: using `FastEmbed` (BAAI/bge-small-en-v1.5).
        - It compares the *meaning* of the English query against the *meaning* of all 700 Shlokas stored in `models/gita_embeddings.pkl`.
    2.  **Keyword Search**:
        - It looks for specific Sanskrit or English keywords (e.g., "Karma", "Dharma").
        - It uses a **"Modern Mapping"** list (`_keyword_search` method) to link modern words like "Suicide", "Depression", "Exams" to specific ancient Shlokas.
    3.  **Ranking**:
        - Scores from both searches are combined.
        - Narrative verses (Sanjay/Dhritarashtra speaking) are penalized to prioritize Krishna/Arjuna's dialogue.
    4.  **Result**: The top 3-5 most relevant Shlokas are selected.

### Step 5: Generating the Answer (The "Voice")
- **File**: `src/llm_generator.py` -> `generate_answer()`
- **Action**:
    1.  **Tone Classification**: The AI decides if the query is a **Crisis** (Suicidal/Hopeless), **Distress** (Sad/Anxious), or **General** (Curious).
    2.  **System Prompt Construction**:
        - Based on the tone, a specific "Persona" is chosen for Krishna.
        - **Crisis**: Highly compassionate, non-preachy, emphasizing life's value.
        - **General**: Philosophical and direct.
    3.  **Final Generation**: The LLM (Groq) receives:
        - The User's Question.
        - The Selected Shlokas (Sanskrit + Meaning).
        - The "Persona" instructions.
    - **Output**: A structured response:
        > "Bhagavad Gita, Adhyay X, Shlok Y..."
        > [Sanskrit Verse]
        > "Simple Hindi explanation connecting the shloka to the user's life problem."

### Step 6: Audio Generation (TTS)
- **File**: `website/api_server.py`
- **Action**:
    - If `include_audio` is true, the response text is sent to `edge_tts`.
    - It generates audio in the background (Async) using a fast Neural Voice (`hi-IN-MadhurNeural`).
    - The frontend receives an `audio_url` to play it.

---

## 3. Database & Files Used

### Databases
1.  **`models/gita_embeddings.pkl`** (Vector DB):
    - Stores the mathematical representation (vectors) of all 700 Gita verses.
    - Loaded into memory for fast searching.
2.  **`users.db`** (SQLite):
    - **Users Table**: Stores email/password/name.
    - **Conversations Table**: Stores every Question, Answer, and Shloka shown (for history).

### Key Code Files
| File | Role |
|Data | |
| `src/gita_api.py` | **The Core Brain**. Handles relevance, understanding, and orchestrates the search. |
| `src/llm_generator.py` | **The Writer**. Handles prompt engineering and tone classification to generate the final text. |
| `src/create_embeddings.py`| **The Builder**. Creates the `pkl` file from the raw JSON data. |
| `website/api_server.py` | **The Server**. Flask app that connects the React frontend to the Python backend. |
| `data/gita_english.json` | **The Source**. Contains all 700 verses with English/Hindi meanings and emotions. |

---

## 4. Summary of the Logic Flow

```mermaid
graph TD
    A[User Question] -->|HTTP POST| B(API Server)
    B -->|Check| C{Is Greeting?}
    C -->|Yes| D[Return Instant Hello]
    C -->|No| E[Check Relevance]
    E -->|Irrelevant| F[Return Rejection Message]
    E -->|Relevant| G[Understand Query via LLM]
    G -->|Extract| H[English Keywords]
    H -->|Search| I[Hybrid Search]
    I -->|Vector + Keyword| J[Select Top 5 Shlokas]
    J -->|Context| K[Generate Answer via LLM]
    K -->|Text| L[Generate Audio]

## 5. Enhanced Intelligence Layer (New!)

To fix vague answers and improve relevance, we implemented a sophisticated **Multi-Stage Reasoning Pipeline**:

### A. Deep Understanding (Start)
Instead of just keywords, the AI now rewrites the query into a clear problem statement and detects the emotional state:
- **Input**: "Man bahut pareshan hai"
- **Output**:
  ```json
  {
    "rewritten_query": "My mind is very restless and I seek peace.",
    "emotional_state": "confused",
    "intent": "seeking_peace"
  }
  ```

### B. Smart Filtering & Boosting
- **Emotion Matching**: If the user is "confused", verses tagged with "confusion" get a huge score boost (+3.0).
- **Narrative Penalty**: Verses spoken by Sanjaya/Dhritarashtra are penalized (-5.0) unless critical context.

### C. The "Second Opinion" (Reranking)
After finding the top 15 candidates, we don't just trust the math. We ask the LLM to **Rank them**:
> "Here are 15 potential verses. Given the user's specific problem 'My mind is restless', which one is the absolute best solution? Rank top 5."

### D. Strict Answer Generation
The final answer follows a strict 7-point rule:
1.  **Emotional Connection**: Acknowledge the feeling first.
2.  **The Shloka**: Quote exactly ONE best verse.
3.  **Direct Application**: Explain *why* this verse solves *this* problem.
4.  **Action Plan**: Give 2 concrete steps (e.g., "Do this breathing exercise").
5.  **Crisis Handling**: Special compassionate protocol for rigorous safety.

This ensures Krishna sounds like a wise, empathetic guide, not a generic chatbot.
