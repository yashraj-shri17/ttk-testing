# 🔍 Talk to Krishna — Question Relevance Judging System

Jab bhi koi user ek question puchta hai, system usse **3 alag gates** se guzarta hai — ek ke baad ek.
Agar koi bhi gate question ko rok de, toh Krishna ji ek polite rejection message return karte hain.

---

## 🗺️ Full Flow Diagram

```
User Question
     │
     ▼
┌─────────────────────────────┐
│  GATE 1: Greeting Check     │  ← `_is_greeting()` in gita_api.py
│  "Kya sirf greeting hai?"   │
└─────────────────────────────┘
     │ YES → Return greeting response (no rejection, welcome message)
     │ NO  ↓
     ▼
┌─────────────────────────────┐
│  GATE 2: Regex Pattern Check│  ← `_is_relevant_to_krishna()` in gita_api.py
│  "Kya banned topic hai?"    │
└─────────────────────────────┘
     │ IRRELEVANT → Return rejection message
     │ RELEVANT   ↓
     ▼
┌─────────────────────────────┐
│  GATE 3: AI (LLM) Check     │  ← `_understand_query()` via Groq API
│  "AI ka final verdict"      │
└─────────────────────────────┘
     │ is_relevant=false → Return rejection message
     │ is_relevant=true  ↓
     ▼
  ✅ Question is VALID → Proceed to Shloka Retrieval & Answer Generation
```

---

## 🚪 GATE 1 — Greeting Check (`_is_greeting()`)

**File:** `src/gita_api.py` → function `_is_greeting()`
**Type:** Rule-based (hardcoded list)

### Kya karta hai?
Ye check karta hai ki user ne sirf ek greeting ki hai, koi actual question nahi. Agar haan, toh system seedha ek warm welcome message deta hai without going through the full pipeline.

### Kaise judge karta hai?
- Query ko lowercase + punctuation-free kar deta hai
- Ek **hardcoded greetings list** se compare karta hai

### Greeting Words List (Examples):

| Language | Examples |
|----------|----------|
| English | `hi`, `hello`, `hey`, `good morning`, `howdy`, `wassup`, `whatsup`, `greetings`, `good afternoon` |
| Hindi (Roman) | `namaste`, `pranam`, `radhe radhe`, `hare krishna`, `jai shri krishna`, `jai shri ram`, `haribol`, `suprabhat`, `shubh ratri` |
| Hindi (Devanagari) | `नमस्ते`, `राधे राधे`, `जय श्री कृष्ण`, `हेलो`, `कैसे हो`, `प्रणाम`, `सुप्रभात`, `हर हर महादेव` |
| Casual | `sup`, `wassup`, `yo`, `kaise ho`, `kya haal`, `kya chal raha hai`, `aur sunao`, `kese ho` |

### Logic Rules:
| Query Length | Rule |
|---|---|
| 1–3 words | Greeting if ANY word matches the greeting list |
| 4–6 words | Greeting if it STARTS with greeting word AND has no question words |
| 2-word phrase | Direct match like `"good morning"`, `"jai shri krishna"` |

> **Result:** Returns `True` (greeting) → System replies: `"राधे राधे! मैं श्री कृष्ण हूँ। कहिये, मैं आपकी क्या सहायता कर सकता हूँ?"`

---

## 🚪 GATE 2 — Regex (Pattern) Relevance Check (`_is_relevant_to_krishna()`)

**File:** `src/gita_api.py` → function `_is_relevant_to_krishna()`
**Type:** Rule-based (keyword + regex pattern matching)
**Speed:** Very fast (no API call)

### Kaise kaam karta hai?
Query ko `NFKC Unicode normalize` + `casefold` karta hai, phir do lists ke against check karta hai:

---

### PART A: ✅ RELEVANT Keywords (Priority Allow List)

Agar query mein koi bhi **genuine help/spiritual** keyword hota hai, to system use turant ALLOW kar deta hai. **Ye check sabse pehle hota hai** taaki kisi genuine problem ko galat tarah se reject na kiya jaye (jaise "business mein *loss*").

| Category | Examples |
|---|---|
| **Spiritual/Divine** | `krishna`, `bhagwan`, `gita`, `dharma`, `karma`, `yoga`, `bhakti`, `atma`, `moksha`, `dhyan`, `shiva`, `ram`, `maya`, `paap`, `punya` |
| **Emotions/Mental Health** | `anger`, `peace`, `fear`, `anxiety`, `stress`, `depression`, `hopeless`, `pareshan`, `tension`, `overthinking`, `guilt`, `regret`, `lonely` |
| **Relationships** | `love`, `family`, `breakup`, `marriage`, `mummy`, `papa`, `divorce`, `pyaar`, `girlfriend`, `boyfriend`, `dhokha`, `betrayal`, `toxic`, `jhagda` |
| **Work/Career/Study** | `job`, `naukri`, `exam`, `failure`, `success`, `study`, `career`, `business`, `future`, `interview`, `result`, `marks`, `fail` |
| **Life Guidance** | `problem`, `solution`, `help`, `kya karu`, `batao`, `samjhao`, `kaise karoon`, `mushkil`, `rasta`, `duvidha`, `decision` |
| **Existential** | `why`, `death`, `birth`, `suffering`, `desire`, `attachment`, `ego`, `who am I`, `pride`, `ghamand` |

---

### PART B: ❌ IRRELEVANT Topics (Rejection List)

Agar Part A mein koi matching keyword nahi mila, tab query ko irrelevant topics ke against check kiya jata hai. Agar koi bhi **pattern match** ho jata hai, question REJECT ho jata hai.

| Category | Examples of Banned Keywords |
|---|---|
| **Sports** | `cricket`, `ipl`, `match`, `wicket`, `goal`, `messi`, `kohli`, `dhoni`, `bgmi`, `pubg`, `क्रिकेट`, `मैच`, `wwe`, `basketball` |
| **Politics** | `election`, `minister`, `modi`, `bjp`, `congress`, `vote`, `pm`, `lok sabha`, `चुनाव`, `नेता`, `protest`, `budget` |
| **Entertainment** | `movie`, `film`, `bollywood`, `actor`, `netflix`, `singer`, `salman`, `shahrukh`, `viral`, `reels`, `oscar`, `cinema` |
| **Technology** | `github`, `coding`, `python code`, `react`, `nodejs`, `laptop`, `wifi`, `install`, `download`, `password`, `bug`, `iphone specs` |
| **Finance** | `stock market`, `crypto`, `bitcoin`, `loan`, `credit card`, `salary`, `gold price`, `lottery`, `satta`, `emi`, `insurance` |
| **Trivia/Math** | `capital of`, `2+2`, `formula`, `who invented`, `solve x`, `geometry`, `physics`, `joke`, `chutkula`, `essay on` |
| **Science** | `chemical formula`, `dna`, `virus`, `vaccine`, `nasa`, `planet`, `black hole`, `photosynthesis`, `प्रयोगशाला` |
| **Food** | `recipe`, `pizza`, `biryani`, `chai kaise`, `chicken`, `swiggy`, `zomato`, `रोटी`, `सब्जी`, `dessert`, `menu` |
| **Weather/Travel** | `weather forecast`, `mausam`, `train ticket`, `flight booking`, `temperature`, `bus`, `uber`, `ola` |

**Matching Logic:**
```python
# Word-boundary safe matching — "match" in "attachment" se nahi phansega!
if re.search(rf'\b{re.escape(pattern)}\b', norm_query):
    return False  # REJECTED
```

> **Default Behavior (Fallback):** Agar koi bhi list mein match nahi hua (Part A and Part B), **question ALLOW hota hai by default.** System assumes life ke problems kai tarah se expressed ho sakte hain.

---

## 🚪 GATE 3 — AI (LLM) Relevance Check (`_understand_query()`)

**File:** `src/gita_api.py` → function `_understand_query()`
**Type:** AI-based (Groq API call using `LLM_CLASSIFIER_MODEL`)
**Speed:** ~200–400ms (fast LLM call)

### Kaise kaam karta hai?
Ye Gate 2 se zyada smart hai. Ek **Groq LLM** ko prompt bheja jaata hai jo query ko deeply analyze karta hai aur ek **JSON response** deta hai:

```json
{
  "rewritten_query": "Clear English version of the user's core problem",
  "emotional_state": "neutral | confused | angry | fear | distress | crisis | depressive | grateful | happy",
  "keywords": "3-5 relevant spiritual concepts",
  "is_relevant": true / false
}
```

### `is_relevant` Judge karne ke Rules (LLM ko di gayi instructions):

**TRUE (Relevant) agar:**
- Personal koi problem hai
- Emotional distress hai
- Life/death/God ke baare mein philosophical question hai
- Spiritual guidance maangi ja rahi hai

**FALSE (Irrelevant) agar:**
| Type | Example |
|---|---|
| Cooking | `"chai kaise banaye"`, `"pizza recipe"` |
| Math/Science Homework | `"2+2 kitna hai"`, `"gravity formula"` |
| Coding/Technical | `"github repo kaise banaye"`, `"python list sort"` |
| General Trivia/GK | `"capital of India"`, `"who won match"` |
| Shallow Chat | `"bored hai"`, `"ek joke sunao"`, `"hi"` |

### Real Examples (LLM ke liye given in the prompt):

```
"Github par repo kaise banaye"  →  is_relevant: false
"Chai kaise banate hain?"       →  is_relevant: false
"2+2 kitna hota hai?"           →  is_relevant: false
"Mummy papa shaadi ke liye nahi maan rahe"  →  is_relevant: true
"Man bahut pareshan hai"        →  is_relevant: true
```

---

## 📊 Summary Table

| Gate | Method | Speed | What it checks |
|---|---|---|---|
| **Gate 1** — Greeting Check | Regex / Hardcoded List | ⚡ Instant | Kya sirf ek greeting hai? |
| **Gate 2** — Pattern Check | Regex + Keyword Lists | ⚡ Instant | Kya banned topic hai? Kya relevant keyword hai? |
| **Gate 3** — AI Check | LLM (Groq API) | ⏱️ ~300ms | Deep semantic relevance — AI ka final verdict |

---

## ❌ Rejection Response

Agar Gate 2 ya Gate 3 question ko reject kare, user ko ye message milta hai:

```
क्षमा करें, मैं श्री कृष्ण हूँ और केवल जीवन की समस्याओं, आध्यात्मिकता,
और भगवद गीता के ज्ञान के बारे में मार्गदर्शन दे सकता हूँ।

आप मुझसे पूछ सकते हैं:
• जीवन की समस्याओं का समाधान (क्रोध, डर, चिंता)
• कर्म, धर्म, और आत्मा के बारे में
• रिश्तों और भावनाओं के बारे में
• ध्यान, शांति, और आत्म-विकास के बारे में

कृपया इन विषयों पर प्रश्न पूछें।
```

---

## 🧠 Why 3 Gates? (Design Rationale)

| Gate | Purpose |
|---|---|
| Gate 1 | User engagement — greetings ko reject karna wrong feel hota |
| Gate 2 | Fast, no-cost filtering of obviously irrelevant topics (sports, food, coding) |
| Gate 3 | Smart, context-aware LLM judgment for edge cases that regex can't catch |

> **Default Philosophy:** "Benefit of doubt always." Agar koi query pattern se match nahi hoti, system assume karta hai ki ye life ki koi real problem hai aur usse allow karta hai.

