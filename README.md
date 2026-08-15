# 🏛️ Manipur Civic & RAG Assistant

A secure, local AI-powered assistant designed to help citizens and administrators in **Manipur** query local administrative services, public welfare schemes, emergency helpline details, and live internet data. Powered by [Ollama](https://ollama.com) (`qwen2.5:7b-instruct`), [Streamlit](https://streamlit.io), and [ChromaDB](https://pypi.org).

---

## 🚀 Features

- **Local RAG Engine:** Semantically searches local administrative files and utility records stored persistently via ChromaDB.
- **Live Internet Search:** Integrated real-time web retrieval via DuckDuckGo search (`ddgs`) for public officeholders and current news.
- **Secure Authentication:** Role-based access using `streamlit-authenticator` backed by local configurations.
- **Civic Focus:** Designed to streamline access to local utility guidance and public knowledge in Manipur.

---

## 📂 Project Structure

```text
enterprise_agent/
├── app.py           # Streamlit UI, login portal, and chat loop
├── engine.py        # Asynchronous LLM router and tool execution layer
├── tools.py         # Tool definitions (ChromaDB RAG, web search, math)
├── config.yaml      # User credentials and authentication settings
├── .gitignore       # Excludes local databases, secrets, and virtual environments
└── README.md        # Project guide
```

---

## 🛠️ Installation & Local Setup

1. **Clone the repository:**
   ```bash
   https://github.com/OlaileoKH/manipur-civic-assistant
   cd manipur-civic-assistant
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install streamlit streamlit-authenticator chromadb ddgs httpx PyYAML
   ```

4. **Pull the AI Model via Ollama:**
   Ensure Ollama is running, then download the model:
   ```bash
   ollama pull qwen2.5:7b-instruct
   ```

5. **Run the Streamlit Application:**
   ```bash
   streamlit run app.py
   ```
