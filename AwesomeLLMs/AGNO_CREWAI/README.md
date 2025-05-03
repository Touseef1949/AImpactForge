
 # Agentic RAG with Agno, Groq, Ollama, and Streamlit

This project demonstrates a Retrieval-Augmented Generation (RAG) chatbot application built using the `agno` framework, `streamlit` for the UI, `Groq` for the LLM, `Ollama` for embeddings, and `PostgreSQL` with `pgvector` for the vector store.

The agent is configured to answer questions based on the content of the CrewAI documentation, leveraging thinking tools before accessing the knowledge base.

## Features

*   Interactive chat interface using Streamlit.
*   RAG pipeline powered by the `agno` library.
*   Knowledge sourced from CrewAI documentation URL.
*   Embeddings generated locally via Ollama (`nomic-embed-text` model).
*   Vector storage and retrieval using PostgreSQL + pgvector.
*   Fast LLM inference via Groq (`meta-llama/llama-4-scout-17b-16e-instruct` model).
*   Agent utilizes `ThinkingTools` for planning and `KnowledgeTools` for retrieval.
*   Chat history persistence within a session.
*   Option to save chat history to a local file (`chat_history.txt`).

## Architecture

1.  **User Input:** User asks a question via the Streamlit interface.
2.  **Agent Execution:** The `agno` Agent receives the prompt.
3.  **Thinking:** The Agent uses `ThinkingTools` to plan its response.
4.  **Knowledge Retrieval:** The Agent uses `KnowledgeTools` to query the `PgVector` database for relevant chunks from the CrewAI documentation.
5.  **LLM Generation:** The prompt, retrieved context, and thinking steps are sent to the Groq API (Llama 4 Scout model).
6.  **Response Streaming:** The generated response is streamed back to the Streamlit UI.

## Prerequisites

*   **Python:** 3.9+ recommended.
*   **Git:** To clone the repository.
*   **PostgreSQL:** A running instance (e.g., version 15+).
*   **pgvector Extension:** Enabled in your PostgreSQL database.
*   **Ollama:** Installed and running locally. [https://ollama.com/](https://ollama.com/)
*   **Ollama Model:** The `nomic-embed-text` model pulled: `ollama pull nomic-embed-text`
*   **Groq API Key:** Obtain an API key from [https://groq.com/](https://groq.com/).

## Setup & Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2.  **Create and Activate Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up PostgreSQL Database:**
    *   Connect to your PostgreSQL instance.
    *   Create the database (if it doesn't exist): `CREATE DATABASE ai;`
    *   Create the user and grant privileges (matching the script's DB_URL):
        ```sql
        CREATE USER ai WITH PASSWORD 'ai';
        GRANT ALL PRIVILEGES ON DATABASE ai TO ai;
        -- Connect to the 'ai' database (\c ai in psql) before running the next command
        CREATE EXTENSION IF NOT EXISTS vector;
        ```
    *   Ensure PostgreSQL is running on `localhost:5532` or update the `db_url` variable in the script accordingly.

5.  **Set up Environment Variables:**
    *   Create a file named `.env` in the project root.
    *   Add your Groq API key:
        ```
        GROQ_API_KEY=your_groq_api_key_here
        ```

6.  **Start Ollama:**
    *   Make sure the Ollama application or service is running in the background.

## Data Loading (One-Time Step)

The script needs to ingest the documentation into the vector database the first time.

1.  **Edit `app.py` (or your script file):** Uncomment the following lines:
    ```python
    # you can uncomment the below upsert methods to load the data
    crewai_docs.load(upsert=True)
    # agno_docs.load(upsert=True) # Optional: Uncomment if you want to load Agno docs too
    ```
2.  **Run the Streamlit App Once:**
    ```bash
    streamlit run app.py
    ```
    *   Wait for the application to start and monitor the console output. You should see logs indicating data fetching, embedding, and insertion. This might take a few minutes depending on your connection and CPU/GPU.
    *   You can also check the `crewai_docs2` table in your `ai` database to confirm data insertion.
3.  **Stop the App:** Press `Ctrl+C` in the terminal where Streamlit is running.
4.  **Edit `app.py` Again:** Re-comment the `.load(upsert=True)` lines you uncommented in step 1. This prevents reloading the data every time you start the app.
    ```python
    # you can uncomment the below upsert methods to load the data
    # crewai_docs.load(upsert=True)
    # agno_docs.load(upsert=True)
    ```
5.  **Save the file.**

## Running the Application

Ensure your PostgreSQL server and Ollama service are running.

```bash
streamlit run app.py
