# 🤖 Junyu's AI Digital Twin: Telegram Assistant

A production-grade Telegram Bot architecture integrating **Google Gemini 3.1 Flash Lite** and **FastAPI**. This project demonstrates the seamless deployment of an LLM-driven agent with industrial-standard logging and security configurations.

## 🌟 Project Highlights

-   **State-of-the-Art LLM**: Powered by **Gemini 3.1 Flash Lite**, optimized for high-throughput (500 RPD) and low-latency interactions.
-   **Webhook Architecture**: Implemented with **FastAPI** to handle asynchronous callbacks from Telegram servers, ensuring high concurrency.
-   **Security & Secret Management**: Fully decoupled configuration using `.env` files and OS-level environment variables to protect API credentials.
-   **Observability (Logging)**: Integrated Python's `logging` module for dual-stream audit trails (Console + `chat_history.log`), critical for production debugging.
-   **Custom Digital Persona**: A fine-tuned system instruction set that maintains a witty persona.

## 🛠️ Technical Specifications

-   **Runtime**: Python 3.12+
-   **Web Framework**: FastAPI / Uvicorn
-   **AI SDK**: `google-genai` v1.69.0
-   **Dependencies**: managed via `requirements.txt` (including `python-dotenv` for local environment emulation)

## 📂 Project Structure

```text
.
├── main.py              # Application entry point & Webhook logic
├── requirements.txt     # Locked dependencies for environment parity
├── .env                 # Local secrets (Excluded via .gitignore)
├── .gitignore           # Security policy for Git commits
├── README.md            # Project documentation
└── chat_history.log     # Persistent audit logs