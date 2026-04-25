
------------------------------
## COM (Companion Of Master) 🤖
COM is a lightweight, Agentic AI Floating Assistant specifically engineered to run on hardware with limited resources. By leveraging Small Language Models (SLM) and an efficient Python harness, COM provides a seamless bridge between high-level AI reasoning and local system automation.


------------------------------
## 🌟 Overview
Unlike resource-heavy AI applications, COM (Companion Of Master) is built for speed and utility. It sits unobtrusively on your screen, ready to assist with Godot Game Development or handle mundane General Tasks like generating documents, all while keeping your RAM usage under control.
## 🚀 Key Features

* Always-on-Top Floating UI: A minimalist, transparent interface that stays visible while you work in Godot or other software.
* Godot Dev Specialist: Deeply understands GDScript 4.x and game architecture patterns.
* Agentic Workflow: Beyond just chatting, COM can trigger Python scripts to generate:
* 📊 Excel spreadsheets for asset tracking.
   * 📄 PDF reports or documentation.
   * 📂 PPT presentations.
* Low-Hardware Optimized: Specifically tuned to run on systems with as little as 4GB RAM (using ~1GB - 1.5GB total).

------------------------------
## 🧠 System Philosophy
COM follows the "Modular Intelligence" approach:

   1. The Brain: Powered by qwen2.5:1.5b via Ollama. We use quantization to ensure the neural network fits into limited RAM.
   2. The Harness: A Python-based agentic layer that interprets AI intent and executes local system commands.
   3. The Interface: A lightweight Tkinter GUI that minimizes overhead compared to Electron-based apps.

------------------------------
## 🛠️ Installation & Setup## 1. Prerequisites

* [Python 3.10+](https://www.python.org/)
* [Ollama](https://ollama.com/)

## 2. Prepare the Model
Pull the base model and create the COM Persona:

ollama pull qwen2.5:1.5b

Create a Modelfile in your directory:

FROM qwen2.5:1.5b
SYSTEM "You are COM (Companion Of Master), a concise and expert AI assistant. You specialize in Godot Game Dev (GDScript) and office automation. Keep responses brief."
PARAMETER temperature 0.5

Register the model:

ollama create com-agent -f Modelfile

## 3. Clone and Run

git clone https://github.com
cd COM-Companion-Of-Master
pip install -r requirements.txt
python main.py

------------------------------
## 📅 Roadmap

* Initial Floating UI Implementation.
* Phase 2: Function calling for Excel and PDF generation.
* Phase 3: Godot Engine socket integration for real-time script injection.
* Phase 4: Advanced context memory using RAG (Retrieval-Augmented Generation).

------------------------------
## 🤝 Contribution
COM is a testament that you don't need a supercomputer to build powerful AI agents. If you are passionate about Small Language Models (SLMs) or Local AI, feel free to fork, submit PRs, or open issues!
------------------------------
COM: Small Brain, Big Deeds.
Developed with ❤️ for the Low-Spec Community.
------------------------------
Apakah Anda ingin saya menambahkan bagian "Technical Theory" (seperti menyebutkan pengaruh Backpropagation atau arsitektur Neural Network) ke dalam README ini agar terlihat lebih edukatif?
