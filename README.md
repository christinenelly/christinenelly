# Fast Bank Transfer (minimal)

This is a minimal FastAPI-based bank app demonstrating fast, atomic transfers with accurate balance updates.

Quick start

1. Create a virtualenv and install:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run the server:

```bash
uvicorn app.main:app --reload
```

3. Endpoints:
- `POST /accounts` {"owner":"Alice","initial_balance":100.00}
- `GET /accounts/{id}`
- `POST /transfer` {"from_id":1,"to_id":2,"amount":10.50}

Design notes
- Balances are stored as integer cents to avoid floating-point errors.
- Transfers use atomic SQL `UPDATE` statements inside a transaction so updates are accurate and safe under concurrency.

API key
- Endpoints require an API key sent in the `X-API-Key` header. Default for development is `devkey`.

Frontend
- A minimal frontend is available at `/` after starting the server. It uses the default `devkey` API key; change `API_KEY` environment variable to override.
- 👋 Hi, I’m @christinenelly
- 👀 I’m interested in game/web development...
- 🌱 I’m currently learning web development...
- 💞️ I’m looking to collaborate on a website...
- 📫 How to reach me on my mail ekeadachinomnso@gmail.com...
- 😄 Pronouns: ... her
- ⚡ Fun fact: ... i love anime and building sites plus animals😂

<!---
christinenelly/christinenelly is a ✨ special ✨ repository because its `README.md` (this file) appears on your GitHub profile.
You can click the Preview link to take a look at your changes.
--->
