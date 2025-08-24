# 📘 Gnyansetu – AI-Powered Virtual Teacher Platform  

**Gnyansetu** is an AI + Django + MongoDB based web application that acts as a **virtual teacher**.  
It helps students learn complex topics interactively by explaining concepts in **simple language**, using **diagrams, voice narration, and step-by-step teaching** – just like a real classroom.  

The platform allows students to upload study materials (PDFs, books, notes, etc.), ask questions, and receive **AI-driven explanations**.  

---

✨ **Features**  

### 🎓 AI Virtual Teacher  
- Interactive topic explanations in simple language  
- Whiteboard-style teaching with **voice + diagrams**  
- Step-by-step breakdown of concepts  

### 📚 Study Material Support  
- Upload PDFs or notes
- AI extracts and explains content  
- Summarization + Q&A on uploaded materials  

### 🔎 Smart Q&A  
- Ask questions on any topic  
- AI searches within uploaded materials + knowledge base  
- Retrieval-Augmented Generation (RAG) for accurate answers  

### 👥 User Management  
- Secure login system  
- Personalized learning environment

---

🛠 **Technology Stack**  

- **Frontend:** React + TailwindCSS  
- **Backend:** Django + Django Channels (for real-time interaction), Daphene server
- **Database:** MongoDB 
- **AI Models:** OpenAI/Generative AI APIs, LangChain  
- **Architecture:** Modular + Microservices-ready  

---

⚙️ **Installation & Setup**

### Prerequisites
- Python 3.10+
- React
- Django
- Daphne (`pip install daphne`)
- MongoDB

### Steps
```bash
# Clone repository
git clone https://github.com/yourusername/Daphene-Server.git
cd Daphene-Server

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start Daphne server
daphne -b 0.0.0.0 -p 8000 yourproject.asgi:application

## 👥 Contributors

- [**Aarya Khatate**](https://github.com/aaryaKhatate)
- [**Vinay Gone**](https://github.com/VinayGone2006)
- [**Yashraj Patil**](https://github.com/Yashrajpatil22)

---

## 📜 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
