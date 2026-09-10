# AgentCS 📚🤖

An intelligent, context-aware Retrieval-Augmented Generation (RAG) system built with **Microsoft Azure AI Foundry** to empower students preparing for the **Cambridge AS & A Level Computer Science (9618)** examinations.

---

## 📌 Overview

Preparing for the Cambridge AS & A Level Computer Science exam (Syllabus Code: 9618) requires precise alignment with mark schemes, pseudocode standards, and official syllabus guidelines. **AgentCS** acts as a personalized, 24/7 exam coach. Instead of manually sifting through scattered PDF archives of past papers, students can query any syllabus topic and instantly retrieve:

1. **Relevant Past Paper Questions**
2. **Official Marking Criteria & Point Allocations**
3. **Step-by-Step Model Solutions & Pseudocode Representations**

---

## 🏗️ Technical Architecture & Features

The system leverages state-of-the-art cloud infrastructure and agentic frameworks to achieve zero-hallucination, grounded responses:

- 🧠 **Frontier Reasoning Model:** Deployed **GPT-5** via **Microsoft Azure AI Foundry** to evaluate complex computer science concepts, parse pseudocode, and produce accurate explanations.
- 🔌 **Model Context Protocol (MCP):** Integrated standardized **MCP Servers** for extensible tool execution, enabling modular communication between agent reasoning loops and backend services.
- 📁 **Cloud Storage & Ground-Truth Knowledge Base:** Structured past papers, mark schemes, and official syllabus documents ingested into **Azure Blob Storage**.
- 🧠 **Context Routing via Foundry IQ:** Connected knowledge stores directly to the agent runtime through **Foundry IQ** for dynamic context routing.
- ⚡ **Hybrid RAG Pipeline (Azure AI Search):** Engineered hybrid retrieval combining dense vector embeddings (for semantic intent) with lexical keyword matching (for specific terms like bit manipulation, pseudocode syntax, and algorithmic logic).
- 💻 **Interactive UI:** Built an intuitive, responsive web frontend using **Streamlit** for effortless student interaction.

---

## 🛠️ Tech Stack

| Component | Technology / Service |
| :--- | :--- |
| **LLM Orchestration** | GPT-5 via Microsoft Azure AI Foundry |
| **Context Protocol** | Model Context Protocol (MCP) |
| **Vector & Hybrid Search** | Azure AI Search |
| **Agentic Context Routing** | Foundry IQ |
| **Document Storage** | Azure Blob Storage |
| **Frontend UI** | Streamlit |
| **Language** | Python 3.10+ |

---

## 🚦 System Architecture Workflow
+-------------------+       +-----------------------+       +-------------------------+
|  Student Query    | ----> |   Streamlit Frontend  | ----> | Agentic Reasoning Loop  |
|  (Streamlit UI)   |       +-----------------------+       |  (GPT-5 via Foundry)    |
+-------------------+                                       +-------------------------+
|
v
+-------------------+       +-----------------------+       +-------------------------+
| Grounded Response | <---- |   Foundry IQ Router   | <---- |    MCP Server & Tool    |
| (Questions + MS)  |       |   & Azure AI Search   |       |       Executors         |
+-------------------+       +-----------------------+       +-------------------------+
|
v
+-----------------------+
|  Azure Blob Storage   |
| (Past Papers & MS)    |
+-----------------------+
