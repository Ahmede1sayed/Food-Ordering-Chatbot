# Pizza Chatbot

A bilingual (English & Arabic) AI-powered chatbot API for a pizza restaurant, allowing customers to browse the menu, manage their cart, and place orders through natural conversation.

---

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Database**: MySQL via PyMySQL + SQLAlchemy ORM
- **Migrations**: Alembic
- **NLP**: Hybrid (Regex-first → LLM fallback)
- **LLM Providers**: Groq (default, free tier) / OpenAI
- **LLM Model**: `llama-3.3-70b-versatile` (via Groq)
- **Validation**: Pydantic v2
- **Containerisation**: Docker + Docker Compose

---

## Architecture

```
User Message
    ↓
POST /api/chat
    ↓
ChatService
    ↓
ConversationOrchestrator
    ├── HybridNLPService (Regex → LLM fallback)
    ├── ClarificationService (detect missing fields)
    ├── IntentRouter → Handler
    │     ├── AddItemHandler
    │     ├── BatchAddItemHandler
    │     ├── RemoveItemHandler
    │     ├── GetCartHandler
    │     ├── ClearCartHandler
    │     ├── CheckoutHandler
    │     ├── BrowseMenuHandler
    │     ├── ConfirmationHandler
    │     └── RejectionHandler
    ├── RecommendationEngine
    └── LLM Response Generation
```

### Key Design Decisions

- **Regex-first NLP**: structured commands (add, remove, checkout) are handled instantly by regex without an LLM call, falling back to Groq only when needed — keeping latency low and costs at zero for most requests.
- **Batch item support**: `BatchAddItemHandler` is registered before `AddItemHandler` so multi-item orders like *"add a large margherita and two colas"* are handled in a single pass.
- **Bilingual prompts**: separate Arabic and English prompt templates are loaded at runtime based on the detected language of the user's message.
- **Pluggable LLM**: `LLMProviderFactory` supports Groq and OpenAI — switch by changing the `LLM_PROVIDER` env variable.

---

## Project Structure

```
primos-chatbot/
├── app/
│   ├── main.py                  # FastAPI app factory
│   ├── routes/
│   │   └── chat.py              # POST /api/chat endpoint
│   ├── chat/services/
│   │   ├── chat_service.py      # Entry point, wires everything together
│   │   └── state_manager.py     # Loads/saves user cart & conversation history
│   ├── core/
│   │   ├── conversation_orchestrator.py   # Main flow controller
│   │   ├── conversation_context.py        # Shared context object per request
│   │   └── intent_router.py               # Routes intents to handlers
│   ├── handlers/                # One file per intent
│   ├── nlp/
│   │   ├── HybridNLPService.py  # Regex → LLM fallback pipeline
│   │   └── RegexNLPService.py   # Pattern matching for all intents
│   ├── llm/
│   │   ├── LLMProviderFactory.py
│   │   ├── providers/
│   │   │   ├── GroqProvider.py
│   │   │   └── OpenAIProvider.py
│   │   └── templates/locales/
│   │       ├── en/prompt.py
│   │       └── ar/prompt.py
│   ├── services/
│   │   ├── cart_service.py
│   │   ├── menu_service.py
│   │   ├── order_service.py
│   │   ├── pricing_service.py
│   │   ├── clarification_service.py
│   │   ├── recommendation_engine.py
│   │   ├── item_validation_service.py
│   │   ├── multi_item_parser.py
│   │   └── suggestion_service.py
│   ├── models/                  # SQLAlchemy models (User, MenuItem, Cart, Order)
│   ├── schemas/                 # Pydantic request/response schemas
│   └── database/
│       ├── connection.py
│       └── seed_menu.py
├── alembic/                     # Database migrations
└── docker/
    └── docker-compose.yml       # MySQL container
```

---

## Getting Started

### 1. Start the database

```bash
cd docker
docker-compose up -d
```

### 2. Install dependencies

```bash
cd app
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file in `app/`:

```env
DATABASE_URL=mysql+pymysql://chatbot_user:yourpassword@localhost:3307/food_chatbot

LLM_PROVIDER=groq           # or openai
GROQ_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # only if using openai

LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.1
LLM_DEFAULT_LANG=en         # or ar
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Seed the menu

```bash
python database/seed_menu.py
```

### 6. Create a user

```bash
python database/create_user.py
```

### 7. Start the server

```bash
uvicorn app.main:app --reload
```

API available at: `http://localhost:8000`  
Health check: `http://localhost:8000/health`

---

## API Usage

### Send a message

**POST** `/api/chat`

```json
{
  "user_id": 1,
  "text": "add a large margherita"
}
```

**Response:**

```json
{
  "response": "Added Large Margherita Pizza (140 EGP) to your cart! 🎯 You might also like: Cola (20 EGP), Fries (50 EGP)",
  "intent": "add_item",
  "lang": "en"
}
```

### Example conversation

```
User: show menu
Bot:  Here's what we have: Margherita Pizza, Pepperoni Pizza, Super Supreme...

User: add margherita large and 2 colas
Bot:  Added 3 items to your cart!

User: show cart
Bot:  Your cart: Large Margherita (140 EGP) x1, Cola (20 EGP) x2. Total: 180 EGP

User: checkout
Bot:  Order confirmed! Total: 180 EGP. Thank you!
```

---

## Supported Intents

| Intent | English examples | Arabic examples |
|---|---|---|
| `welcome` | hi, hello | اهلا، مرحبا |
| `browse_menu` | show menu, what do you have | قائمة، في إيه |
| `add_item` | add large pepperoni | ضيف بيتزا كبيرة |
| `remove_item` | remove pepperoni | شيل البيبروني |
| `view_cart` | show my cart, what's my total | اعرض الطلب |
| `clear_cart` | clear cart | امسح السلة |
| `checkout` | confirm, place order, pay | اكمل، ادفع |
| `confirmation` | yes, ok, sure | نعم، ماشي |
| `rejection` | no, cancel that | لا |

---

## Database Models

- **User** — stores registered users
- **MenuItem** — menu items with category (pizza, drink, side) and availability flag
- **MenuSize** — S / M / L / REG sizes with individual prices
- **Cart / CartItem** — active user cart
- **Order / OrderItem** — confirmed orders with price snapshot at purchase time
- **ConversationHistory** — stores message history per user

---

## Recommendation Engine

After a successful cart action, the engine suggests items based on:

- **Complementary items** — drinks or sides that pair with what's in the cart
- **User history** — items the user has ordered before
- **Popular items** — most ordered globally
- **Time-based** — different suggestions for lunch vs dinner

---

## Notes

- `app/controllers/chat_controller.py` exists in the codebase but is **not used** — the active request flow goes through `routes/chat.py` directly.
- The Groq free tier allows 14,400 requests/day, which covers most regex-unmatched messages.
