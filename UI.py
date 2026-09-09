import json
import os
import re  # Added for cleaning up citations
import streamlit as st
from dotenv import load_dotenv

# 1. Page Config MUST be the very first Streamlit call
st.set_page_config(
    page_title="Past Paper Expert-Developed by Irfana",
    page_icon="🤖",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* 1. Base Gradient on the main viewport */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle, #2a2e43 0%, #151724 100%);
    }

    /* 2. Strip standard backgrounds from layout headers */
    [data-testid="stHeader"] {
        background: transparent !important;
    }

    /* 3. Force the bottom drawer and ALL its inner wrappers to drop solid fills */
    [data-testid="stBottom"], 
    [data-testid="stBottom"] > div, 
    [data-testid="stBottomBlockContainer"] {
        background: transparent !important;
        background-color: transparent !important;
    }
    
    /* ✨ FIX: Modern Academic Alignment & Layout Engine */
    .readable-container {
        max-width: 850px;
        line-height: 1.8 !important;
        font-size: 1.05rem;
        color: #E2E8F0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Add distinct structural breathing room below paragraphs */
    .readable-container p {
        margin-top: 0px;
        margin-bottom: 18px !important;
    }

    /* Align exam sub-questions cleanly (e.g., 5 (a), (b)) */
    .readable-container strong, 
    .readable-container b {
        color: #4ADE80; /* Highlights question parts in a crisp green tint */
        display: inline-block;
        margin-top: 14px;
        margin-bottom: 6px;
    }

    /* Beautifully align dotted exam answer lines */
    .readable-container p:contains("......."),
    .readable-container p:contains("____") {
        letter-spacing: 2px;
        color: rgba(255, 255, 255, 0.3) !important;
        margin-top: 8px !important;
        margin-bottom: 8px !important;
    }

    /* Make list items space out nicely instead of squeezing together */
    .readable-container ul, .readable-container ol {
        margin-top: 10px;
        margin-bottom: 20px;
        padding-left: 24px;
    }
    .readable-container li {
        margin-bottom: 10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load Environment Variables
load_dotenv()

from azure.identity import AzureCliCredential, DefaultAzureCredential
from azure.ai.projects import AIProjectClient

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AGENT_NAME = os.getenv("AGENT_NAME")

st.title("Cambridge Past Paper Expert Agent (9618)")

if not PROJECT_ENDPOINT or not AGENT_NAME:
    st.error("❌ Missing `PROJECT_ENDPOINT` or `AGENT_NAME` in `.env` file.")
    st.stop()


# 2. Authentication
@st.cache_resource(show_spinner="Connecting to Azure AI Services...")
def get_azure_clients():
    try:
        try:
            credential = AzureCliCredential()
            credential.get_token("https://management.azure.com/.default")
        except Exception:
            credential = DefaultAzureCredential()

        project_client = AIProjectClient(
            endpoint=PROJECT_ENDPOINT,
            credential=credential,
        )
        openai_client = project_client.get_openai_client()
        agent = project_client.agents.get(agent_name=AGENT_NAME)

        return project_client, openai_client, agent
    except Exception as e:
        raise e


try:
    project_client, openai_client, agent = get_azure_clients()
    st.sidebar.success(f"Connected to: **{agent.name}**")
except Exception as e:
    st.error("❌ Authentication / Connection Failed")
    st.exception(e)
    st.info("💡 **Fix:** Run `az login` in your terminal to authenticate your session.")
    st.stop()


# 3. Inject Fixed Stylish Footer directly into the Sidebar
st.sidebar.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        position: relative;
    }
    .stylish-footer {
        position: absolute;
        bottom: 20px;
        left: 15px;
        right: 15px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px 16px;
        text-align: center;
        backdrop-filter: blur(8px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .stylish-footer p {
        margin: 0;
        font-size: 0.78rem;
        color: #94A3B8;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        font-weight: 500;
    }
    .stylish-footer .author {
        color: #4ADE80;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-shadow: 0 0 10px rgba(74, 222, 128, 0.3);
    }
    </style>

    <div class="stylish-footer">
        <p>Developed with ❤️ by <span class="author">IRFANA</span></p>
    </div>
    """,
    unsafe_allow_html=True
)

# 4. Session State Initialization
if "conversation_id" not in st.session_state:
    try:
        conversation = openai_client.conversations.create(items=[])
        st.session_state.conversation_id = conversation.id
    except Exception as e:
        st.error("Failed to establish conversation thread.")
        st.exception(e)
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None

if "awaiting_response" not in st.session_state:
    st.session_state.awaiting_response = False


# 5. Helper Functions
def submit_approval(approved: bool):
    approval_req = st.session_state.pending_approval

    approval_payload = {
        "type": "mcp_approval_response",
        "approval_request_id": approval_req.id,
        "approve": approved,
    }

    openai_client.conversations.items.create(
        conversation_id=st.session_state.conversation_id,
        items=[approval_payload],
    )

    st.session_state.pending_approval = None
    st.session_state.awaiting_response = True


# 6. Render Message History (With Readability Containment)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown('<div class="readable-container">', unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)
        if msg.get("citations"):
            with st.expander("📚 View Citations"):
                for cite in msg["citations"]:
                    st.write(f"- {cite}")


# 7. Human-in-the-loop Approval Widget
if st.session_state.pending_approval:
    app_req = st.session_state.pending_approval

    with st.status(f"⚠️ Approval Required: `{getattr(app_req, 'name', 'Tool Call')}`", expanded=True):
        st.write(f"**Server:** {getattr(app_req, 'server_label', 'MCP Server')}")

        try:
            parsed_args = json.loads(app_req.arguments)
            st.json(parsed_args)
        except Exception:
            st.code(getattr(app_req, "arguments", "No args"))

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Approve", type="primary", use_container_width=True):
                submit_approval(approved=True)
                st.rerun()

        with col2:
            if st.button("❌ Deny", type="secondary", use_container_width=True):
                submit_approval(approved=False)
                st.rerun()


# 8. User Input Processing
user_input = st.chat_input("Ask a question from computer science past papers...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(f'<div class="readable-container">{user_input}</div>', unsafe_allow_html=True)

    openai_client.conversations.items.create(
        conversation_id=st.session_state.conversation_id,
        items=[{"type": "message", "role": "user", "content": user_input}],
    )

    st.session_state.awaiting_response = True


# =====================================================================
# 9. Corrected & Optimized Streaming Response Handling
# =====================================================================
if st.session_state.awaiting_response and not st.session_state.pending_approval:
    with st.chat_message("assistant"):
        text_placeholder = st.empty()
        full_text = ""
        citations_list = []

        try:
            # 1. Open the response stream using stream=True
            response_stream = openai_client.responses.create(
                conversation=st.session_state.conversation_id,
                extra_body={
                    "agent_reference": {
                        "name": agent.name,
                        "type": "agent_reference",
                    }
                },
                input="",
                stream=True
            )

            # 2. Safely parse incoming stream events
            for event in response_stream:
                if getattr(event, "type", None) == "response.output_text.delta":
                    full_text += event.delta
                    
                    # Clean custom delimiter tokens into standard markdown paragraph separations
                    clean_display_text = full_text.replace(" ⊗ ", "\n\n")
                    
                    # Strip out messy bracket citations (e.g., 【6:17†9618_s23_qp_43.pdf】) dynamically
                    #clean_display_text = re.sub(r'【[^】]*】', '', clean_display_text)
                    #  FIXED CODE
                    clean_display_text = re.sub(r'【[^】]*】', '', clean_display_text)

                    
                    # Display the streamed text inside a custom CSS block to keep it clean and scannable
                    text_placeholder.markdown(
                        f'<div class="readable-container">{clean_display_text}</div>', 
                        unsafe_allow_html=True
                    )

                # Capture citations if populated in the stream chunks
                if hasattr(event, "citations") and event.citations:
                    for citation in event.citations:
                        source_val = getattr(citation, "content", "Knowledge Base")
                        if source_val not in citations_list:
                            citations_list.append(source_val)

                # Intercept MCP human-in-the-loop validation requests
                if getattr(event, "type", None) == "mcp_approval_request":
                    st.session_state.pending_approval = event
                    break

        except Exception as e:
            st.error("Error streaming agent response.")
            st.exception(e)

    st.session_state.awaiting_response = False

    # Halt and refresh UI to present approval buttons if tool requests validation
    if st.session_state.pending_approval:
        st.rerun()

           # Save finalized payload to historical messages
        if full_text:
            final_clean_text = re.sub(r'【[^】]*】', '', full_text).replace(" ⊗ ", "\n\n")
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_clean_text,
                "citations": citations_list,
            })
            st.rerun()
