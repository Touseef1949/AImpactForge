import streamlit as st
import os
import json
from PIL import Image as PILImage
import io
import base64

# Import your existing modules (assuming they're in the same directory or properly installed)
try:
    from agno.agent import Agent
    from agno.models.groq import Groq
    from agno.models.openai import OpenAIChat
    from agno.team.team import Team
    from agno.tools.reasoning import ReasoningTools
    from agno.tools.exa import ExaTools
    from agno.media import Image as AgnoImage
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please ensure all required packages are installed and accessible (`pip install agno` and other dependencies).")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Product Health Assessment",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #2E86AB;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 3rem;
    }
    .upload-section {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
    }
    .analysis-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-top: 2rem;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-danger {
        color: #dc3545;
        font-weight: bold;
    }
    .sidebar-info {
        background-color: #e9ecef;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_agents():
    """Initialize all the agents with proper configuration"""
    try:
        # Check for API keys
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        EXA_API_KEY = os.getenv("EXA_API_KEY")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

        if not GROQ_API_KEY:
            st.error("GROQ_API_KEY not found in environment variables")
            return None
        if not EXA_API_KEY:
            st.error("EXA_API_KEY not found in environment variables")
            return None
        if not OPENAI_API_KEY:
            st.error("OPENAI_API_KEY not found in environment variables (required for Vision Agent)")
            return None

        # Vision Agent - Use OpenAI for vision capabilities
        vision_agent = Agent(
            name="Smart Vision Agent",
            role="Extract ingredient lists directly from product label images.",
            model=Groq(id="meta-llama/llama-4-maverick-17b-128e-instruct"),  # Use OpenAI for vision
            instructions=[
                "You are an expert at visually scanning product labels and extracting the full ingredient list.",
                "You will be provided with an image of a product label. Identify the 'Ingredients:' section or similar keywords.",
                "Extract all listed ingredients precisely, including any E-numbers, INS codes, or common chemical names for additives.",
                "Return the ingredients as a clean, comma-separated list, without any additional interpretation or analysis.",
                "If no ingredient list is clearly visible or identifiable, return 'NO_INGREDIENT_LIST_FOUND'."
            ],
            add_datetime_to_instructions=True,
        )

        # Linguist Agent
        linguist_agent = Agent(
            name="Linguist Agent",
            role="Parse raw ingredient text, normalize names, and prepare targeted web search queries.",
            model=Groq(id="meta-llama/llama-4-maverick-17b-128e-instruct"),
            tools=[ReasoningTools()],
            instructions=[
                "You will receive a comma-separated string of raw ingredients.",
                "Your task is to:",
                "1. Split the string into individual ingredient items.",
                "2. Normalize each ingredient name and simplify complex names where possible.",
                "3. For each normalized ingredient, generate 1-3 highly effective web search queries.",
                "4. Return a JSON string with 'original_name', 'normalized_name', and 'search_queries' for each ingredient.",
                "Ensure the output is valid JSON."
            ],
            add_datetime_to_instructions=True,
        )

        # Research Agent
        research_agent = Agent(
            name="Research Agent",
            role="Perform web searches for ingredients and return concise, relevant snippets.",
            model=Groq(id="meta-llama/llama-4-maverick-17b-128e-instruct"),
            tools=[ExaTools()],
            instructions=[
                "You will receive a JSON string containing ingredient objects with search queries.",
                "For each ingredient, use ExaTools to search for relevant health information.",
                "Summarize health impacts, artificial status, and safety notes for each ingredient.",
                "Return JSON with 'normalized_name' and 'search_summary' for each ingredient."
            ],
            add_datetime_to_instructions=True,
        )

        # Nutritionist Agent
        nutritionist_agent = Agent(
            name="Nutritionist-Evaluator Agent",
            role="Synthesize web search results to assess ingredient health impacts and generate a comprehensive report.",
            model=Groq(id="meta-llama/llama-4-maverick-17b-128e-instruct"),
            tools=[ReasoningTools()],
            instructions=[
                "Generate a comprehensive Markdown report with:",
                "**a. Overall Health Verdict:** Provide overall health assessment",
                "**b. Identified Artificial Additives:** List concerning artificial additives",
                "**c. Major Health Considerations:** Summarize key health concerns",
                "**d. Full Ingredient Breakdown:** Detailed analysis of each ingredient",
                "Output only the structured Markdown report."
            ],
            add_datetime_to_instructions=True,
        )

        # Team Coordinator
        team_coordinator = Team(
            name="Product Health Assessment Team",
            mode="coordinate",
            model=Groq(id="meta-llama/llama-4-maverick-17b-128e-instruct"),
            members=[vision_agent, linguist_agent, research_agent, nutritionist_agent],
            tools=[ReasoningTools(add_instructions=True)],
            instructions=[
                "Follow this sequential workflow:",
                "1. Extract ingredients from image using Smart Vision Agent",
                "2. Normalize ingredients and prepare queries using Linguist Agent",
                "3. Research ingredients using Research Agent",
                "4. Generate final report using Nutritionist-Evaluator Agent",
                "Output only the final Markdown report."
            ],
            markdown=True,
            show_members_responses=False,
            enable_agentic_context=True,
            add_datetime_to_instructions=True,
            success_criteria="A comprehensive health assessment report has been generated."
        )

        return team_coordinator

    except Exception as e:
        st.error(f"Error initializing agents: {str(e)}")
        st.info("Please ensure your API keys (GROQ_API_KEY, EXA_API_KEY, OPENAI_API_KEY) are set as environment variables.")
        return None

def main():
    # Header
    st.markdown('<h1 class="main-header">🏥 Product Health Assessment</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Upload a product label image to analyze ingredient health impacts using AI-powered research</p>', unsafe_allow_html=True)

    # Sidebar with information and settings
    with st.sidebar:
        st.markdown("### 📋 How it works")
        st.markdown("""
        <div class="sidebar-info">
        1. <strong>Upload Image:</strong> Select a clear photo of product ingredients<br>
        2. <strong>AI Vision:</strong> Extracts ingredient list from the image<br>
        3. <strong>Research:</strong> Searches web for health information<br>
        4. <strong>Analysis:</strong> Generates comprehensive health report
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ⚙️ Settings")
        show_intermediate = st.checkbox("Show intermediate steps", value=False)

        st.markdown("### 📝 Requirements")
        st.markdown("""
        - Clear image of ingredient list
        - GROQ_API_KEY in environment
        - EXA_API_KEY in environment
        - OPENAI_API_KEY in environment (for vision agent)
        """)

        # API Key status
        st.markdown("### 🔑 API Status")
        groq_status = "✅ Connected" if os.getenv("GROQ_API_KEY") else "❌ Missing"
        exa_status = "✅ Connected" if os.getenv("EXA_API_KEY") else "❌ Missing"
        openai_status = "✅ Connected" if os.getenv("OPENAI_API_KEY") else "❌ Missing"
        st.markdown(f"**GROQ:** {groq_status}")
        st.markdown(f"**EXA:** {exa_status}")
        st.markdown(f"**OPENAI:** {openai_status}")

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📸 Upload Product Image")

        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear image showing the product's ingredient list"
        )

        if uploaded_file is not None:
            # Display uploaded image
            image = PILImage.open(uploaded_file)
            st.image(image, caption="Uploaded Product Image", use_column_width=True, output_format="PNG")

            # Image info
            st.markdown(f"**File:** {uploaded_file.name}")
            st.markdown(f"**Size:** {uploaded_file.size} bytes")
            st.markdown(f"**Dimensions:** {image.size[0]} x {image.size[1]} pixels")

    with col2:
        st.markdown("### 🔍 Analysis Controls")

        if uploaded_file is not None:
            analyze_button = st.button(
                "🚀 Analyze Product Health",
                type="primary",
                use_container_width=True
            )

            if analyze_button:
                # Check API keys before proceeding
                if not os.getenv("GROQ_API_KEY") or not os.getenv("EXA_API_KEY") or not os.getenv("OPENAI_API_KEY"):
                    st.error("Missing one or more required API keys. Please check your environment variables.")
                    st.stop()

                try:
                    # Get image bytes from the uploaded file
                    image_bytes = uploaded_file.getvalue()

                    # Initialize agents
                    with st.spinner("Initializing AI agents..."):
                        team_coordinator = initialize_agents()

                    if team_coordinator is None:
                        st.error("Failed to initialize AI agents")
                        st.stop()

                    # Create an AgnoImage object with raw bytes and mime_type
                    agno_image_for_agent = AgnoImage(content=image_bytes, mime_type=uploaded_file.type)

                    # Run analysis
                    with st.spinner("Analyzing product ingredients... This may take a few minutes."):
                        # Create a container for the analysis results
                        analysis_container = st.container()

                        with analysis_container:
                            st.markdown("### 📊 Analysis Results")

                            # Progress indicators
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            # Update progress
                            progress_bar.progress(25)
                            status_text.text("🔍 Extracting ingredients from image...")

                            # Run the team coordinator
                            try:
                                # Alternative approach: Use different methods to get cleaner response

                                # Method 1: Try to use run() and extract content properly
                                response = team_coordinator.run(
                                    "Analyze the healthiness of the product based on its ingredient list extracted from the provided image. Follow the workflow strictly to ensure a comprehensive assessment.",
                                    stream=False,
                                    images=[agno_image_for_agent],
                                )

                                progress_bar.progress(100)
                                status_text.text("✅ Analysis complete!")

                                # Debug information
                                if st.checkbox("Show debug info", key="debug_response"):
                                    st.write("**Response Type:**", type(response))
                                    st.write("**Response Attributes:**", dir(response) if hasattr(response, '__dict__') else "No attributes")
                                    if hasattr(response, '__dict__'):
                                        st.write("**Response Dict:**", response.__dict__)

                                # Display results - Extract content properly from TeamRunResponse
                                if response:
                                    # Handle TeamRunResponse object
                                    if hasattr(response, 'content') and response.content:
                                        content = response.content
                                        st.markdown("---")
                                        st.markdown(content)
                                    # Handle direct string response
                                    elif isinstance(response, str):
                                        st.markdown("---")
                                        st.markdown(response)
                                    # Handle other response types
                                    else:
                                        # Try to extract content from response attributes
                                        response_str = str(response)
                                        if "content='" in response_str:
                                            # Extract content from the string representation
                                            start = response_str.find("content='") + 9
                                            end = response_str.find("', content_type")
                                            if start > 8 and end > start:
                                                content = response_str[start:end]
                                                # Unescape newlines and other characters
                                                content = content.replace('\\n', '\n').replace("\\'", "'")
                                                st.markdown("---")
                                                st.markdown(content)
                                            else:
                                                st.warning("Could not extract content from response.")
                                                with st.expander("Raw Response (for debugging)"):
                                                    st.text(response_str[:1000] + "..." if len(response_str) > 1000 else response_str)
                                        else:
                                            st.warning("Unexpected response format.")
                                            with st.expander("Raw Response (for debugging)"):
                                                st.text(str(response)[:1000] + "..." if len(str(response)) > 1000 else str(response))
                                else:
                                    st.warning("No response generated. Please try again.")
                                    st.info("Check the terminal/console for any error messages or debug output.")

                            except Exception as e:
                                st.error(f"Analysis failed: {str(e)}")
                                st.exception(e)  # Show full traceback for debugging

                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")
                    st.exception(e)

        else:
            st.info("👆 Upload an image to start the analysis")

    # Footer with additional information
    st.markdown("---")
    with st.expander("ℹ️ About this tool"):
        st.markdown("""
        This AI-powered tool analyzes food product ingredients to assess their health impact:

        **Features:**
        - 🔍 **Computer Vision**: Automatically extracts ingredient lists from product images
        - 🌐 **Web Research**: Searches for up-to-date health information about each ingredient
        - 📊 **Health Analysis**: Provides comprehensive health verdicts and recommendations
        - 🏷️ **Additive Detection**: Identifies artificial colors, flavors, and preservatives

        **Powered by:**
        - Groq's Llama models for AI processing
        - OpenAI's GPT models for vision capabilities
        - Exa API for web research
        - Agno framework for agent coordination
        """)

if __name__ == "__main__":
    main()