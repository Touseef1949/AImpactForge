import streamlit as st

# Set page config at the very beginning
st.set_page_config(
    page_title="AI Chatbot Evaluation Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Imports ---
from agno.agent import Agent
from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.pdf import PDFKnowledgeBase
# from agno.models.anthropic import Claude # Keep if you might switch back
from agno.models.groq import Groq # Use Groq
# from agno.tools.reasoning import ReasoningTools # Commented out as it's removed below
from agno.vectordb.pgvector import PgVector, SearchType
from agno.run.response import RunEvent, RunResponse # Keep RunResponse if needed for type hints, RunEvent might not be used directly here

import markdown
import os

# --- load_knowledge_base function remains the same ---
@st.cache_resource
def load_knowledge_base():
    db_url = os.getenv("PGVECTOR_DB_URL", "postgresql+psycopg://ai:ai@localhost:5532/ai")
    pdf_path = os.getenv("AI_EVALS_GUIDE_PATH", "") # Define path to your PDF here or via env var

    # if not pdf_path:
    #     st.warning("PDF path for AI Evals Guide is not set. Knowledge base might be empty. "
    #                "Set the AI_EVALS_GUIDE_PATH environment variable or update the code.")
    #     # Optionally provide a default path if you want to bundle a guide
    #     # pdf_path = "./path/to/your/default_guide.pdf"
    #     # if not os.path.exists(pdf_path):
    #     #     st.error(f"Default PDF path not found: {pdf_path}")
    #     #     st.stop()

    if not os.path.exists(pdf_path) and pdf_path:
         st.error(f"Specified PDF path does not exist: {pdf_path}")
         st.stop()

    try:
        eval_knowledge_base = PDFKnowledgeBase(
            path=pdf_path,
            vector_db=PgVector(
                table_name="eval_guide",
                db_url=db_url,
                search_type=SearchType.hybrid,
                embedder=OllamaEmbedder(id="nomic-embed-text", dimensions=768),
            ),
        )
        # Uncomment the line below ONLY during the very first run to load the KB
        # print("Attempting to load knowledge base (first run)...")
        # eval_knowledge_base.load(recreate=True)
        # print("Knowledge base loading process initiated (if uncommented). Run takes time.")
        return eval_knowledge_base
    except Exception as e:
        st.error(f"Failed to initialize knowledge base components: {e}")
        st.info("Ensure PostgreSQL/PgVector is running and accessible at the specified DB_URL, "
                "and the PDF path is correct.")
        st.stop() # Stop if KB setup fails critically

# --- UPDATED create_planning_agent (using Groq, NO tools) ---
@st.cache_resource
def create_planning_agent(_eval_knowledge_base, model_id):
    """Creates the planning agent using the specified Groq model ID."""
    # Ensure API key is set for Groq (agno might read GROQ_API_KEY env var)
    if not os.getenv("GROQ_API_KEY"):
        st.warning("GROQ_API_KEY environment variable not set. Agent may fail.")
        # Consider adding st.stop() here if the key is absolutely required

    return Agent(
        model=Groq(id=model_id), # Use selected Groq model
        knowledge=_eval_knowledge_base,
        search_knowledge=True,
        # *** REMOVED tools parameter to avoid tool_use_failed error ***
        # tools=[ReasoningTools(add_instructions=True)],
        instructions=[
            "You are an expert AI evaluation planning agent.",
            "Analyze the provided chatbot requirements meticulously.",
            "Break down the requirements into clear, distinct evaluation dimensions.",
            "For each dimension, identify:",
            "  - Essential features the chatbot *must* have.",
            "  - Potential edge cases or challenging scenarios.",
            "  - Critical evaluation metrics (both qualitative and quantitative where applicable).",
            "Output *only* a structured plan in well-formatted Markdown format.",
            "Do not include conversational filler, apologies, or summaries of your own instructions.",
            "The plan should be directly usable for creating a detailed evaluation framework.",
        ],
        markdown=True, # Request clean markdown output
    )

# --- UPDATED create_knowledge_agent (using Groq, NO tools) ---
@st.cache_resource
def create_knowledge_agent(_eval_knowledge_base, model_id):
    """Creates the knowledge agent using the specified Groq model ID."""
    if not os.getenv("GROQ_API_KEY"):
        st.warning("GROQ_API_KEY environment variable not set. Agent may fail.")
        # Consider adding st.stop() here if the key is absolutely required

    return Agent(
        model=Groq(id=model_id), # Use selected Groq model
        knowledge=_eval_knowledge_base,
        search_knowledge=True,
        # *** REMOVED tools parameter to avoid tool_use_failed error ***
        # tools=[ReasoningTools(add_instructions=True)],
        instructions=[
            "You are a specialized agent tasked with creating comprehensive AI evaluation frameworks based on the AI Evals Guide principles.",
            "Given the user's chatbot requirements and a structured evaluation plan, generate a detailed evaluation framework.",
            "Strictly follow the 4-step process outlined in the AI Evals Guide:",
            "1.  **Create 'Goldens':** Provide *at least 5* detailed examples. Each example must include a realistic user input and the corresponding ideal chatbot output.",
            "2.  **Generate Synthetic Data:** Clearly explain the strategy for generating synthetic data. Provide *specific examples* of prompts you would use to generate variations for testing different scenarios (e.g., edge cases, different tones).",
            "3.  **Grade Outputs:** Define clear, measurable evaluation metrics and detailed rubrics for grading the chatbot's actual outputs against the 'Goldens' or ideal responses. Cover dimensions identified in the plan (e.g., accuracy, tone, helpfulness, safety).",
            "4.  **Build Autoraters:** Provide specific, actionable instructions for creating automated evaluation tools ('autoraters'). Include example prompts or criteria that an LLM-based autorater could use.",
            "Tailor all examples, metrics, and instructions specifically to the provided chatbot requirements and evaluation plan.",
            "Cite relevant sections from the AI Evals Guide document when applicable (e.g., 'Referencing Section 2.2 of the guide...').",
            "Output *only* the complete 4-step evaluation framework in well-formatted Markdown.",
            "Do not add introductory or concluding remarks outside the framework structure."
        ],
        markdown=True, # Request clean markdown output
    )


# --- CORRECTED generate_chatbot_eval function ---
def generate_chatbot_eval(user_requirement, planning_agent, knowledge_agent, progress_callback=None):
    """
    Generate a comprehensive evaluation framework for a chatbot based on user requirements.

    Args:
        user_requirement (str): Detailed description of the chatbot requirements
        planning_agent (Agent): Agent for planning the evaluation structure
        knowledge_agent (Agent): Agent for generating detailed evaluation framework
        progress_callback (func): Optional callback function for updating progress

    Returns:
        dict: Containing the evaluation plan and detailed framework, or None on error.
    """
    evaluation_plan = None
    detailed_eval_framework = None

    if progress_callback:
        progress_callback(0.1, "Analyzing requirements with Planning Agent...")

    # First, use the planning agent
    planning_prompt = f"""
    Analyze the following chatbot requirements and create a structured evaluation plan following your instructions.

    Chatbot Requirements:
    ```
    {user_requirement}
    ```

    Ensure the output is only the structured plan in Markdown format.
    """
    try:
        # *** FIX: Call run() and get the response object ***
        response_plan = planning_agent.run(planning_prompt)

        # *** FIX: Extract the .content attribute ***
        if hasattr(response_plan, 'content') and isinstance(response_plan.content, str):
            evaluation_plan = response_plan.content
            # Optional: Clean up potential leading/trailing whitespace
            evaluation_plan = evaluation_plan.strip()
        elif response_plan is not None: # Handle cases where it might return non-RunResponse but not None
             st.warning(f"Planning agent returned type {type(response_plan)}, attempting to get content or string.")
             evaluation_plan = getattr(response_plan, 'content', str(response_plan)) # Get content if possible, else stringify
             evaluation_plan = evaluation_plan.strip()
        else:
            st.error("Planning agent returned an empty response (None).")
            raise ValueError("Empty response from planning agent") # Or handle differently

        # Check if we actually got content after potential extraction/conversion
        if not evaluation_plan:
             st.error("Planning agent failed to generate content for the plan after processing the response.")
             raise ValueError("Empty plan content from planning agent")


    except Exception as e:
        st.error(f"Error during planning agent execution: {e}")
        # import traceback
        # st.exception(e) # Uncomment for full traceback in UI
        # Return None or raise specific error if planning fails
        raise # Re-raise to stop execution in the main block

    if progress_callback:
        progress_callback(0.5, "Creating evaluation framework with Knowledge Agent...")

    # Then, use the knowledge agent
    knowledge_prompt = f"""
    Based on the following chatbot requirements and evaluation plan, create a comprehensive AI evaluation framework following the 4-step process as per your instructions.

    Chatbot Requirements:
    ```
    {user_requirement}
    ```

    Evaluation Plan:
    ```markdown
    {evaluation_plan}
    ```

    Ensure the output is only the 4-step framework in Markdown format.
    """
    try:
        # *** FIX: Call run() and get the response object ***
        response_framework = knowledge_agent.run(knowledge_prompt)

        # *** FIX: Extract the .content attribute ***
        if hasattr(response_framework, 'content') and isinstance(response_framework.content, str):
            detailed_eval_framework = response_framework.content
            # Optional: Clean up potential leading/trailing whitespace
            detailed_eval_framework = detailed_eval_framework.strip()
        elif response_framework is not None:
            st.warning(f"Knowledge agent returned type {type(response_framework)}, attempting to get content or string.")
            detailed_eval_framework = getattr(response_framework, 'content', str(response_framework))
            detailed_eval_framework = detailed_eval_framework.strip()
        else:
            st.error("Knowledge agent returned an empty response (None).")
            raise ValueError("Empty response from knowledge agent")

        # Check if we actually got content after potential extraction/conversion
        if not detailed_eval_framework:
             st.error("Knowledge agent failed to generate content for the framework after processing the response.")
             raise ValueError("Empty framework content from knowledge agent")

    except Exception as e:
        st.error(f"Error during knowledge agent execution: {e}")
        # import traceback
        # st.exception(e) # Uncomment for full traceback in UI
        raise # Re-raise to stop execution

    if progress_callback:
        progress_callback(1.0, "Evaluation framework generation complete!")

    # Ensure both parts were generated successfully before returning
    # (The checks above should already guarantee this if no exception was raised)
    if evaluation_plan and detailed_eval_framework:
        return {
            "plan": evaluation_plan,
            "framework": detailed_eval_framework
        }
    else:
        # This case should ideally be caught by the exceptions above, but as a fallback:
        st.error("Failed to generate either the plan or the framework content (This shouldn't normally be reached).")
        return None # Indicate failure


# --- Session State Initialization remains the same ---
if 'results' not in st.session_state:
    st.session_state.results = None
if 'progress' not in st.session_state:
    st.session_state.progress = 0.0
if 'status' not in st.session_state:
    st.session_state.status = ""
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'last_selected_template' not in st.session_state:
        st.session_state.last_selected_template = "Custom"


# --- Load knowledge base (with error handling) ---
# Ensure this is called only once or is cached effectively
eval_knowledge_base = load_knowledge_base() # Call the function


# --- Main content ---
st.title("🤖 AI Chatbot Evaluation Generator (Groq Edition)") # Updated title slightly
st.write("""
This tool helps you create comprehensive evaluation frameworks for AI chatbots using Groq models,
following the 4-step process from the AI Evals Guide. Enter your chatbot requirements below.
""")

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    st.info("Ensure the `GROQ_API_KEY` and `AI_EVALS_GUIDE_PATH` environment variables are set, and PgVector is running.")

    # Model options specific to Groq (Ensure these IDs are valid for agno's Groq integration)
    # Using the IDs you provided in your code. Double-check if these are the exact IDs
    # expected by agno.models.groq.Groq
    model_options = {
        # Common Groq Llama 3 models:
        "Llama4 Scout": "meta-llama/llama-4-scout-17b-16e-instruct",
        "Llama4 Maverick": "meta-llama/llama-4-maverick-17b-128e-instruct",
        # Gemma on Groq
        "Gemma 7B (Groq)": "gemma-7b-it",
        # Mixtral on Groq
        "Mixtral 8x7B (Groq)": "mixtral-8x7b-32768",
         # Keep your custom ones if you are sure they work with agno.Groq:
         # "Llama4 Scout (Custom?)": "meta-llama/llama-4-scout-17b-16e-instruct",
         # "Llama4 Maverick (Custom?)": "meta-llama/llama-4-maverick-17b-128e-instruct",
         # "Llama 3.3 (Custom?)": "llama-3.3-70b-versatile",
    }

    # Default to standard Groq models if available, otherwise use the first one
    default_planning_index = 0
    default_knowledge_index = 1
    model_keys = list(model_options.keys())
    if "Llama4 Scout" in model_options:
       default_planning_index = model_keys.index("Llama4 Scout")
    if "Llama4 Maverick" in model_options:
       default_knowledge_index = model_keys.index("Llama4 Maverick")
    elif len(model_options) > 1:
        default_knowledge_index = 1 # Fallback to second option if 70B not listed


    planning_model_name = st.selectbox(
        "Planning Agent Model (Groq)",
        model_keys,
        index=default_planning_index,
        key="planning_model_name"
    )
    planning_model_id = model_options[planning_model_name]

    knowledge_model_name = st.selectbox(
        "Knowledge Agent Model (Groq)",
        model_keys,
        index=default_knowledge_index,
        key="knowledge_model_name"
    )
    knowledge_model_id = model_options[knowledge_model_name]

    st.write("---")
    st.subheader("📋 Example Templates")
    # Example templates remain the same
    example_templates = {
        "E-commerce Support Bot": """I need to create a customer support chatbot for an e-commerce platform selling electronics.
        The chatbot should handle order tracking, returns, technical support questions, and product recommendations.
        It should be professional but friendly in tone, and know when to escalate to human support.""",

        "Healthcare Assistance Bot": """I'm building a healthcare assistance chatbot that helps patients book appointments,
        answer basic medical questions, provide medication reminders, and direct emergencies to appropriate services.
        It needs to be empathetic and clear, while remaining HIPAA compliant and cautious with medical advice.""",

        "Educational Tutor Bot": """I want to develop an educational chatbot that helps students with math problems,
        explains scientific concepts, provides study tips, and creates quizzes. It should be encouraging and
        adapt its explanations based on the student's age and understanding level."""
    }
    template_options = ["Custom"] + list(example_templates.keys())
    # Ensure selected_template uses session state correctly if needed for persistence across reruns caused by Load Template
    if 'selected_template_key' not in st.session_state:
        st.session_state.selected_template_key = "Custom"

    selected_template = st.selectbox(
        "Choose a template",
        template_options,
        index=template_options.index(st.session_state.selected_template_key), # Use session state index
        key="template_selector" # Give unique key to selector itself
    )
    st.session_state.selected_template_key = selected_template # Update session state on selection change

    if st.button("Load Template"):
        if selected_template != "Custom":
            st.session_state.user_input = example_templates[selected_template]
            # No need to set last_selected_template here, selected_template_key handles it
            st.rerun() # Rerun to update the text_area with the loaded template
        else:
            st.info("Select a template other than 'Custom' to load its content.")

    # Setup instructions remain the same
    st.write("---")
    st.sidebar.info(
        "**First time setup:**\n"
        "1. Ensure PostgreSQL/PgVector is running (e.g., via Docker `docker compose up -d`) at `localhost:5532` with user `ai`/`ai`.\n"
        "2. Place your 'AI Evals Guide' PDF file somewhere accessible.\n"
        "3. Set the `AI_EVALS_GUIDE_PATH` environment variable to the PDF's path OR update the path directly in `load_knowledge_base()`.\n"
        "4. Set the `GROQ_API_KEY` environment variable.\n"
        "5. *Only on the very first run:* Uncomment the `eval_knowledge_base.load(recreate=True)` line in `load_knowledge_base()`.\n"
        "6. Run the Streamlit app (`streamlit run your_script_name.py`). The first run (with `.load()`) will take time to process the PDF.\n"
        "7. After successful loading, comment out the `.load()` line again for faster subsequent startups."
    )


# --- User input section remains the same ---
with st.expander("Chatbot Requirements", expanded=True):
    # Use st.session_state.user_input to ensure template loading works
    user_input_value = st.text_area(
        "Describe your chatbot requirements in detail:",
        value=st.session_state.user_input, # Bind value to session state
        height=200,
        key="user_input_area",
        placeholder="E.g., I need to create a customer support chatbot for an e-commerce platform..."
    )
    # Update session state if the user types manually
    st.session_state.user_input = user_input_value
    generate_button = st.button("Generate Evaluation Framework", type="primary", use_container_width=True)


# --- UPDATED Display results section ---
if generate_button and st.session_state.user_input: # Check session state input
    # Check for Groq API key before proceeding
    if not os.getenv("GROQ_API_KEY"):
         st.error("GROQ_API_KEY environment variable is not set. Cannot generate evaluation. Please set it and restart.")
         st.stop()
    # Check if KB loaded successfully (eval_knowledge_base should not be None)
    if not eval_knowledge_base:
         st.error("Knowledge Base could not be loaded. Cannot generate evaluation. Check previous errors.")
         st.stop()

    progress_bar = st.progress(0.0, text="Initializing...")
    status_text = st.empty()
    status_text.text("Initializing...")

    # Define update_progress callback (same as before)
    def update_progress(progress, status):
        st.session_state.progress = progress
        st.session_state.status = status
        # Ensure progress value is between 0.0 and 1.0
        progress_val = max(0.0, min(float(progress), 1.0))
        progress_bar.progress(progress_val, text=status)
        status_text.text(status)

    update_progress(0.05, "Initializing agents...")
    try:
        # Agents are cached, so creation should be fast after the first time
        planning_agent = create_planning_agent(eval_knowledge_base, planning_model_id)
        knowledge_agent = create_knowledge_agent(eval_knowledge_base, knowledge_model_id)
        update_progress(0.08, "Agents initialized.")

        # *** Update the call and handling of results ***
        st.session_state.results = None # Reset results before trying
        generation_result = None # Initialize generation_result

        # Call the corrected generation function
        generation_result = generate_chatbot_eval(
            st.session_state.user_input, # Use value from session state
            planning_agent,
            knowledge_agent,
            progress_callback=update_progress
        )

        # Check if the function returned a valid dict
        if generation_result and "plan" in generation_result and "framework" in generation_result:
             st.session_state.results = generation_result
             # Ensure progress bar completes IF successful
             update_progress(1.0, "Evaluation framework generated successfully!")
        else:
            # Error messages should have been shown inside generate_chatbot_eval via st.error
            # If generation_result is None or malformed, keep progress where it failed
             update_progress(st.session_state.progress, "Generation failed. Check error messages above.")
             # Optional: Add a generic error if no specific one was shown
             if not generation_result:
                 st.error("Generation process did not complete successfully and returned no result.")


    except Exception as e:
        # Catch exceptions raised from generate_chatbot_eval or agent creation
        st.error(f"An critical error occurred during generation: {str(e)}")
        # import traceback
        # st.exception(e) # Uncomment for full traceback in UI
        st.session_state.results = None
        # Update progress bar to show error state
        update_progress(st.session_state.progress, f"Error during generation: {str(e)}")

# --- Display results if available (this part should now work correctly) ---
# Check if results exist in session state and are valid
if st.session_state.results and isinstance(st.session_state.results, dict) and "plan" in st.session_state.results and "framework" in st.session_state.results:
    st.success("Evaluation framework generated successfully!") # Keep success message here
    tab1, tab2 = st.tabs(["📊 Evaluation Framework", "📝 Evaluation Plan"])

    with tab1:
        st.header("📊 Evaluation Framework")
        framework_content = st.session_state.results.get("framework", "Error: Framework content missing.")
        st.markdown(framework_content)
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            try:
                st.download_button(
                    label="⬇️ Download Framework (Markdown)",
                    data=framework_content,
                    file_name="chatbot_evaluation_framework.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="download_framework_md"
                )
            except Exception as e: st.error(f"MD download button error: {e}")
        with col2:
            try:
                # Ensure markdown library is imported
                html_content = markdown.markdown(framework_content)
                st.download_button(
                    label="⬇️ Download Framework (HTML)",
                    data=html_content,
                    file_name="chatbot_evaluation_framework.html",
                    mime="text/html",
                    use_container_width=True,
                    key="download_framework_html"
                )
            except Exception as e: st.error(f"HTML download button error: {e}")

    with tab2:
        st.header("📝 Evaluation Plan")
        plan_content = st.session_state.results.get("plan", "Error: Plan content missing.")
        st.markdown(plan_content)
        st.write("---")
        try:
            st.download_button(
                label="⬇️ Download Plan (Markdown)",
                data=plan_content,
                file_name="chatbot_evaluation_plan.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_plan_md"
            )
        except Exception as e: st.error(f"Plan download button error: {e}")

elif generate_button and not st.session_state.user_input:
    st.warning("Please enter chatbot requirements before generating.")

# Add a small footer or note about dependencies if desired
# st.sidebar.write("---")
# st.sidebar.caption("Requires `agno`, `streamlit`, `markdown`, `psycopg[binary]`, `pgvector`, `ollama` (optional, for embedder)")
