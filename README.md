# <img src="frontend/src/assets/wordwizIcon.svg" width="32"/> Word Wiz AI

**Word Wiz AI** is an AI-powered educational web application designed to help young children learn to read through **real-time phoneme-level pronunciation feedback**.

🌐 **[Try it now at wordwizai.com](https://wordwizai.com)**

---

## 📖 About the Project

### The Problem We're Solving

**21% of adults in the United States are considered functionally illiterate.** Reading proficiency begins with early childhood literacy, and pronunciation is fundamental to learning to read. Traditional reading apps provide sentence-level or word-level feedback, but children often struggle with specific sounds within words. 

Word Wiz AI addresses this by analyzing pronunciation at the **phoneme level** - the smallest unit of sound - providing children with precise, actionable feedback on exactly which sounds they need to practice.

### Our Mission

We believe every child deserves access to high-quality, personalized reading instruction. Word Wiz AI uses cutting-edge AI and speech recognition technology to:

- **Identify specific pronunciation errors** at the phoneme level
- **Generate adaptive practice content** that targets each child's unique needs
- **Provide encouraging, age-appropriate feedback** that builds confidence
- **Make learning accessible** from any browser, anywhere

### How It Works

Children read sentences aloud into their device. Our AI:
1. Analyzes their pronunciation with phoneme-level precision
2. Identifies which specific sounds need improvement
3. Generates personalized feedback and new practice sentences
4. Adapts difficulty based on performance

---

## ✨ What Makes Word Wiz AI Unique

### 🎯 Phoneme-Level Precision

Unlike other reading apps that only identify which words are read incorrectly, Word Wiz AI pinpoints **exactly which sounds** within words need practice. For example, if a child says "kat" instead of "cat," the app identifies the specific /k/ vs /c/ sound confusion.

### 🤖 AI-Powered Personalization

Powered by GPT-4 and advanced speech recognition, Word Wiz AI:
- **Generates practice sentences** tailored to each child's error patterns
- **Provides natural, encouraging feedback** that motivates continued learning
- **Adapts difficulty automatically** as children improve

### 🎮 Engaging Practice Modes

- **Unlimited Practice** — Free-form reading with adaptive difficulty
- **Story Mode** — Progress through engaging narratives
- **Choice Story** — Interactive stories where children choose their adventure

### 📊 Progress Tracking for Parents & Teachers

Track improvement over time with detailed analytics showing:
- Pronunciation accuracy trends
- Common error patterns
- Reading session history
- Achievement milestones

---

## 🛠️ Technology & Innovation

Word Wiz AI leverages cutting-edge technology to deliver research-backed literacy instruction:

### Advanced AI & Machine Learning

- **Speech Recognition**: wav2vec2-TIMIT-IPA models trained on the TIMIT phoneme corpus
- **Natural Language**: GPT-4 for context-aware content generation and feedback
- **Text-to-Speech**: Google Cloud TTS for natural-sounding audio responses
- **Performance**: ONNX Runtime optimization delivers 2-3x faster processing

### Modern Web Technology

- **Frontend**: React 19 with TypeScript, Tailwind CSS, Radix UI components
- **Backend**: FastAPI (Python) with real-time WebSocket communication
- **Database**: MySQL for production data persistence
- **Deployment**: Vercel (frontend) and AWS EC2 (backend) for global availability

### Optional Client-Side Processing

For capable devices, phoneme extraction can run **in the browser** using Transformers.js, reducing latency and server load while maintaining accuracy.

---

## 🌟 Roadmap

### ✅ Currently Available

- [X] Real-time phoneme-level pronunciation feedback
- [X] Three engaging practice modes (Unlimited, Story, Choice Story)
- [X] AI-generated adaptive content
- [X] Progress tracking and analytics
- [X] Google OAuth and password authentication
- [X] Mobile-responsive design with light/dark themes
- [X] Deployed and accessible at [wordwizai.com](https://wordwizai.com)

### 🚧 Coming Soon

- [ ] Advanced analytics dashboard for teachers
- [ ] Achievement badges and gamification
- [ ] Parent/teacher accounts with student management
- [ ] Expanded practice mode variety

### 🔮 Future Vision

- Multi-language support (Spanish, French, and more)
- Offline mode for areas with limited connectivity
- Native mobile apps (iOS and Android)
- Integration with classroom learning management systems
- AI tutor mode with conversational practice

---

## 🤝 Contributing

We welcome contributions from developers, educators, and literacy advocates! Whether you want to:

- **Improve the AI models** for better accuracy
- **Design new practice modes** that engage young learners
- **Enhance the user interface** for better accessibility
- **Add new features** that support literacy development
- **Fix bugs** or improve performance
- **Translate the app** to new languages

Please see our [REPOSITORY_GUIDE.md](implementation_guides/REPOSITORY_GUIDE.md) for technical documentation and development setup instructions.

---

## 📄 License & Acknowledgments

This project is part of an educational initiative to combat illiteracy and ensure every child has access to high-quality reading instruction.

### Built With

- **OpenAI** — GPT-4 for intelligent content generation
- **HuggingFace** — wav2vec2 models for speech recognition
- **Google Cloud** — Text-to-Speech services
- **FastAPI & React** — Modern web frameworks
- **The open-source community** — Countless libraries and tools

---

## 📞 Get Involved

- **Try the app**: [wordwizai.com](https://wordwizai.com)
- **Report issues**: [GitHub Issues](https://github.com/wordwizai/word-wiz-ai/issues)
- **Technical docs**: [REPOSITORY_GUIDE.md](implementation_guides/REPOSITORY_GUIDE.md)
- **Frontend guidelines**: [STYLE_GUIDELINES.md](frontend/STYLE_GUIDELINES.md)

---

**Built with ❤️ to help every child learn to read**

*21% of U.S. adults are functionally illiterate. Together, we can change that - one child at a time.*
