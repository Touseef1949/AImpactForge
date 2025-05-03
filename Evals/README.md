# AI Chatbot Evaluation Generator (Groq Edition) 🤖

This Streamlit application helps users generate comprehensive evaluation frameworks for AI chatbots. It leverages the `agno` library, Groq models for generation, a PgVector database for knowledge storage, and Ollama for embeddings, following principles outlined in a specified "AI Evals Guide" PDF.

**Core Features:**

*   Takes detailed chatbot requirements as input.
*   Uses a Planning Agent (Groq LLM) to create a structured evaluation plan.
*   Uses a Knowledge Agent (Groq LLM) informed by a PDF knowledge base to generate a detailed 4-step evaluation framework:
    1.  Create 'Goldens' (Example Inputs/Outputs)
    2.  Generate Synthetic Data (Strategy & Examples)
    3.  Grade Outputs (Metrics & Rubrics)
    4.  Build Autoraters (Instructions & Examples)
*   Retrieval-Augmented Generation (RAG) using a PDF (`AI_EVALS_GUIDE_PATH`), PgVector, and Ollama embeddings (`nomic-embed-text`).
*   Allows selection of different Groq models (Llama 4 Scout/Maverick, Gemma, Mixtral).
*   Provides example requirement templates.
*   Offers download options for the generated plan (Markdown) and framework (Markdown, HTML).

---

## Prerequisites

Before you begin, ensure you have the following installed and configured:

1.  **Python:** Version 3.9 or higher recommended.
2.  **Git:** For cloning the repository.
3.  **Docker & Docker Compose (Recommended):** For easily setting up PostgreSQL + PgVector. Alternatively, a manually configured instance.
4.  **PostgreSQL Database:** Version 15+ recommended, with the **PgVector extension** enabled.
5.  **Ollama:** Installed and running locally. You need to pull the required embedding model:
    ```bash
    ollama pull nomic-embed-text
    ```
6.  **Groq API Key:** Obtain an API key from [GroqCloud](https://console.groq.com/keys).
7.  **AI Evals Guide PDF:** You need the specific PDF document that this application uses as its knowledge base. Place it in an accessible location.
8.  **`agno` Library:** This project depends on the `agno` library. **[CRITICAL: Provide specific instructions here on how to install `agno`. Examples: "Clone the `agno` repository from [URL] into the parent directory" or "Install via pip: `pip install -e git+ssh://...#egg=agno`" or "Contact [Person/Team] for access."]**

---

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Install `agno` Library:**
    *   Follow the specific instructions you determined in the Prerequisites section for installing `agno`.

3.  **Set up Python Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure Environment Variables:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and fill in your actual values:
        *   `GROQ_API_KEY`: Your Groq API key.
        *   `AI_EVALS_GUIDE_PATH`: The *full, absolute path* to your AI Evals Guide PDF file.
        *   `PGVECTOR_DB_URL`: The connection string for your PostgreSQL/PgVector database. (Defaults match the optional Docker Compose setup below).

6.  **Set up PostgreSQL + PgVector:**
    *   **Recommended (Docker):** If you have Docker installed, you can use the provided `docker-compose.yml` (create this file if desired, see section below):
        ```bash
        docker compose up -d
        ```
        This will start a PostgreSQL container with PgVector enabled, accessible at `postgresql+psycopg://ai:ai@localhost:5532/ai`.
    *   **Manual:** If you have an existing PostgreSQL instance, ensure the `pgvector` extension is created in your target database:
        ```sql
        CREATE EXTENSION IF NOT EXISTS vector;
        ```
        Update the `PGVECTOR_DB_URL` in your `.env` file accordingly.

7.  **Ensure Ollama is Running:**
    *   Start the Ollama application or service.
    *   Verify the `nomic-embed-text` model is available (`ollama list`).

8.  **Initial Knowledge Base Loading (First Time Only):**
    *   The application needs to process and index your PDF file into the PgVector database the first time it runs.
    *   **Method 1 (Using the App - Requires Code Change):**
        *   Temporarily **uncomment** the line `eval_knowledge_base.load(recreate=True)` inside the `load_knowledge_base` function in `app.py`.
        *   Run the Streamlit app: `streamlit run app.py`.
        *   Wait for the console output indicating the knowledge base loading is complete (this can take several minutes depending on the PDF size). You might see errors in the Streamlit UI during this time if agents try to run before loading finishes.
        *   Once loading is done, **stop the app** (`Ctrl+C` in the terminal) and **re-comment** the `eval_knowledge_base.load(recreate=True)` line in `app.py`.
    *   **Method 2 (Using Separate Script - Recommended if `setup_knowledge_base.py` is created):**
        *   Run the dedicated setup script: `python setup_knowledge_base.py`.
        *   Wait for it to complete.

---

## Running the Application

1.  **Ensure Prerequisites:** Make sure your `.env` file is configured, PostgreSQL/PgVector is running, and Ollama is running.
2.  **Activate Virtual Environment:**
    ```bash
    source venv/bin/activate # Or `venv\Scripts\activate` on Windows
    ```
3.  **Run Streamlit:**
    ```bash
    streamlit run app.py
    ```
4.  Open your web browser to the URL provided by Streamlit (usually `http://localhost:8501`).

---

## Usage

1.  Enter the detailed requirements for the chatbot you want to evaluate in the text area.
2.  (Optional) Select different Groq models for the Planning and Knowledge agents using the sidebar dropdowns.
3.  (Optional) Choose an example template from the sidebar and click "Load Template".
4.  Click the "Generate Evaluation Framework" button.
5.  Monitor the progress bar and status updates.
6.  View the generated "Evaluation Plan" and "Evaluation Framework" in the respective tabs.
7.  Use the download buttons to save the generated content.

---

## Troubleshooting

*   **`ModuleNotFoundError: No module named 'agno'`**: Ensure you followed the specific installation steps for the `agno` library correctly.
*   **Database Connection Error**: Verify PostgreSQL/PgVector is running and accessible. Check your `PGVECTOR_DB_URL` in the `.env` file matches the database credentials and address. Ensure the database and user exist. Check firewall rules.
*   **Ollama Connection Error / Model Not Found**: Make sure the Ollama service is running locally and accessible. Ensure you have pulled the `nomic-embed-text` model (`ollama list`).
*   **Groq API Key Error**: Ensure the `GROQ_API_KEY` is correctly set in your `.env` file and is valid.
*   **PDF Not Found Error**: Double-check the `AI_EVALS_GUIDE_PATH` in your `.env` file. It should be the full, absolute path to the PDF. Ensure the file exists and the application has permission to read it.
*   **Knowledge Base Empty/Errors after First Run**: Make sure you successfully completed the "Initial Knowledge Base Loading" step and then *commented out* the `.load(recreate=True)` line again.

---

## Disclaimer

This tool generates evaluation frameworks based on AI models and predefined instructions. The quality of the output depends on the input requirements, the chosen models, and the content of the "AI Evals Guide" PDF. Always review and adapt the generated frameworks to your specific needs and context. This tool does not guarantee compliance with regulations like HIPAA; ensure any healthcare applications meet all necessary legal and ethical standards independently.
