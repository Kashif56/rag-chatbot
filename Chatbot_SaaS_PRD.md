# 📄 Chatbot SaaS – Product Requirements Document (PRD)

## 🧠 Project Overview

Build a Django-based SaaS platform (no APIs, only Django views and templates) that enables users to create multiple intelligent chatbots from their custom knowledge base (PDFs, DOCX, TXT, and URLs). Each chatbot can be deployed on WhatsApp, SMS (via Twilio), and optionally Email.

---

## ✅ Key Features

### 👥 Multi-User & Multi-Chatbot
- Each user can create multiple chatbots
- Each chatbot is independent and has:
  - A name and personality configuration
  - Deployment settings
  - Multiple knowledge base sources (files & URLs)

---

### 🧠 Knowledge Base Management
- Supported data sources:
  - `.pdf` via **PyPDF2**
  - `.docx` via **python-docx**
  - `.txt` via direct upload
  - Web URLs (scraped using **BeautifulSoup**)
- Text extraction → Chunking → Embedding using **LangChain**
- Store vector embeddings in **Pinecone**

---

### 💬 Chat Interface
- A preview chat interface for every chatbot using Django template views
- Chat powered by **LangChain RAG pipeline** (with OpenAI / Gemini / DeepSeek)

---

### 📤 Deployment Channels
- **Twilio WhatsApp & SMS**:
  - Users configure Twilio numbers in dashboard
  - Incoming messages handled by Django views, trigger RAG response
- **Email (Optional)**:
  - Support for auto-reply via SendGrid or Mailgun (future phase)

---

### 📊 Dashboard Features
- View, edit, or delete chatbots
- Add or remove knowledge sources for each chatbot
- Test chat functionality
- Monitor usage and message logs

---

## 🔐 Authentication & Billing
- User registration/login using Django auth
- Email verification
- Plans (Stripe Integration):
  - **Free**: 1 bot, limited monthly messages
  - **Pro**: Unlimited bots & messages
- Track usage per user and per chatbot

---

## 🛠️ Tech Stack

| Layer              | Technology                         |
|-------------------|-------------------------------------|
| Backend           | Django (views/templates only)       |
| AI Layer          | LangChain + OpenAI/DeepSeek/Gemini |
| Vector DB         | Pinecone                            |
| Frontend          | Vanilla JS + Bootstrap              |
| File Parsing      | PyPDF2, python-docx                 |
| Web Scraping      | BeautifulSoup                       |
| Messaging         | Twilio (WhatsApp, SMS)              |
| Email (Optional)  | SendGrid / Mailgun                  |
| Deployment        | Railway / Render / Docker           |

---

## 📁 Data Models

```python
User
├── username
├── email
├── password
└── subscription_type

ChatBot
├── user (FK to User)
├── name
├── description
├── tone
├── twilio_number
└── created_at

KnowledgeBase
├── chatbot (FK to ChatBot)
├── type (file/url)
├── file_upload (nullable)
├── url (nullable)
├── processed_text
└── created_at

MessageLog
├── chatbot (FK to ChatBot)
├── from_number
├── to_number
├── channel (SMS/WhatsApp)
├── content
└── timestamp
