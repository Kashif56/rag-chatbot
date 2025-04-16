# RAG Chatbot

A powerful Retrieval-Augmented Generation (RAG) chatbot built with Django, allowing users to interact with their custom knowledge base through a conversational interface.

![RAG Chatbot Dashboard](https://raw.githubusercontent.com/yourusername/rag-chatbot/main/screenshots/dashboard.png)

## 🌟 Features

- **Custom Knowledge Base Management**
  - Upload PDF, DOC, DOCX, and TXT files
  - Import content from URLs (with optional web scraping)
  - Add text content directly
  - View, edit, and delete knowledge sources

- **Intelligent Chat Interface**
  - Context-aware responses based on your knowledge base
  - Smooth conversational experience
  - Citation of sources used in responses
  - Chat history tracking

- **Vector Database Integration**
  - Pinecone vector database for efficient similarity search
  - Automatic chunking and embedding of content
  - Fast retrieval of relevant information

- **Modern UI/UX**
  - Responsive design works on all devices
  - Dark mode support
  - Clean and intuitive interface
  - Real-time feedback

## 🔧 Technology Stack

- **Backend**
  - Django 5.2 (Python web framework)
  - LangChain for RAG pipeline management
  - Pinecone for vector storage and similarity search
  - Google Gemini for text generation

- **Frontend**
  - Bootstrap 5 for responsive UI components
  - JavaScript for interactive elements
  - HTML5 & CSS3 for structure and styling

- **Data Processing**
  - PDF processing with PyPDF2
  - Document handling with python-docx
  - Web scraping with BeautifulSoup4

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Pinecone API key (free tier available)
- Google API key for Gemini (with usage limits)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/rag-chatbot.git
   cd rag-chatbot
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root with:
   ```
   PINECONE_API_KEY=your_pinecone_api_key
   GOOGLE_API_KEY=your_google_api_key
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:8000/`

## 📚 Usage

### Adding Data Sources

1. **Log in** to your account
2. Navigate to the **Knowledge Base** section
3. Click **Add Data Source**
4. Choose your data source type:
   - **File**: Upload PDF, DOC, DOCX, or TXT files
   - **URL**: Enter a website URL to index content
   - **Text**: Paste or type text directly

### Chatting with Your Knowledge

1. Go to the **Chat Interface**
2. Type your question in the message input
3. The system will:
   - Retrieve relevant information from your knowledge base
   - Generate a coherent, contextual response
   - Provide sources for the information used

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -am 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

