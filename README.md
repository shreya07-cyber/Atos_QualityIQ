
# 🚀 QualityIQ — AI-Driven Testing Platform

QualityIQ is an **Autonomous AI Testing Agent Platform** that transforms software testing from reactive validation to **predictive, risk-driven quality engineering**.

It understands requirements, prioritizes risk, generates intelligent test cases, detects regressions, identifies missing test coverage, and continuously improves using learning memory.

---

## 🧠 Problem Statement

Modern agile testing is:

- Manual and checklist-driven  
- Limited reuse of historical defect intelligence  
- Reactive to regressions  
- Dependent on static automation scripts  
- Prone to production defect leakage  

### ⚠️ Result:
- Longer testing cycles  
- Low release confidence  
- Increased production bugs  

---

## 💡 Proposed Solution

QualityIQ introduces an AI-driven system that:

- Ingests user stories from Jira / Azure DevOps  
- Generates functional, negative, and edge test cases  
- Executes automated workflows using Playwright  
- Detects regressions proactively  
- Identifies missing test coverage (Gap Detection)  
- Provides root cause analysis for failures and gaps  
- Learns from historical defects (Learning Memory)  
- Assigns risk scores and prioritizes execution  

---

## 🏗️ System Architecture

![System Flow](https://raw.githubusercontent.com/shreya07-cyber/Atos_QualityIQ/main/images/Systemflow.png)

<br>

![AI Decision Flow](https://raw.githubusercontent.com/shreya07-cyber/Atos_QualityIQ/main/images/AI_decision_making_process_flow.png)

<br>

![Post Test Flow](https://raw.githubusercontent.com/shreya07-cyber/Atos_QualityIQ/main/images/post_test_flow.png)


---

## 🔥 Key Features

- 🎯 Risk-Based Execution — runs high-risk modules first  
- 🧪 Intelligent Test Generation — functional + negative + edge cases  
- 🔄 Regression Detection — detects failures in previously working features  
- 💡 AI Insights — explains root cause with confidence score  
- 🔍 Gap Detection — identifies missing test scenarios + root cause  
- 🧠 Learning Memory — improves testing using past defects  
- 📊 Dashboard — risk heatmap, test results, alerts  
- 🔔 Email Notifications — alerts developers for failures  
- 🗂️ Defect Logs & History — track executions and issues  

---

## 🛠️ Tech Stack

- Frontend/UI: Streamlit  
- Backend: Python  
- Automation: Playwright  
- Storage: Local storage (JSON / files)  
- AI Logic: Rule-based + prompt-driven  

---

## ⚙️ Installation & Setup

### 🔹 Prerequisites

- Python (>= 3.8)  
- pip  
- Node.js (for Playwright)  

---

### 🔹 Step 1: Clone Repository

```bash
git clone https://github.com/your-username/QualityIQ.git
cd QualityIQ
````

---

### 🔹 Step 2: Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# OR
source venv/bin/activate  # Mac/Linux
```

---

### 🔹 Step 3: Install Dependencies

```bash
pip install streamlit playwright pandas
```

---

### 🔹 Step 4: Install Playwright Browsers

```bash
playwright install
```

---

## ▶️ Running the Project

### 🔹 Run Dashboard (Main UI)

```bash
cd ai_agent
streamlit run dashboard.py
```

Open in browser:

```
http://localhost:8501
```

---

### 🔹 Run Demo Application

Open another terminal:

```bash
cd demo_ecommerce
python app.py
```

---

## 🧪 How to Use

1. Enter or fetch a user story
2. Click **Run Tests**
3. View test results
4. Check regression detection
5. Explore AI insights
6. View gap detection
7. Analyze risk priority
8. Check notifications and logs

---

## 🎯 Key Innovation

> QualityIQ introduces an intelligent testing agent that decides what to test, detects what is missing, explains failures, and continuously improves.

---

## 👩‍💻 Team

Team Anveshak

---

## 📌 Future Enhancements

* CI/CD integration
* ML-based risk prediction
* Cross-project learning memory
* Cloud deployment

---

## 📄 License

For academic and innovation purposes.

````
✅ Create a **cool project banner image**
✅ Or make your repo look **top 1% professional**
