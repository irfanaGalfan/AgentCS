import json
import os
import re
import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.ai.projects import AIProjectClient

# 1. Page Config (Must be the first Streamlit command)
st.set_page_config(
    page_title="Past Paper Expert - Developed by Irfana",
    page_icon="🤖",
    layout="wide",
)

# Custom Styling Engine
st.markdown(
    """
    <style>
    /* Base Gradient Viewport */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle, #2a2e43 0%, #151724 100%);
    }

    /* Transparent Headers */
    [data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Drop solid fills on bottom containers */
    [data-testid="stBottom"], 
    [data-testid="stBottom"] > div, 
    [data-testid="stBottomBlockContainer"] {
        background: transparent !important;
        background-color: transparent !important;
    }
    
    /* Academic Layout Engine */
    .readable-container {
        max-width: 850px;
        line-height: 1.8 !important;
        font-size: 1.05rem;
        color: #E2E8F0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    .readable-container p {
        margin-top: 0px;
        margin-bottom: 18px !important;
    }

    .readable-container strong, 
    .readable-container b {
        color: #4ADE80;
        display: inline-block;
        margin-top: 14px;
        margin-bottom: 6px;
    }

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

# Helper function to read from Streamlit Secrets or Environment Variables
def get_secret(key_name, default=None):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name, default)

PROJECT_ENDPOINT = get_secret("PROJECT_ENDPOINT")
AGENT_NAME = get_secret("AGENT_NAME")
AZURE_API_KEY = get_secret("AZURE_API_KEY")

st.title("Cambridge Past Paper Expert Agent (9618)")

if not PROJECT_ENDPOINT or not AGENT_NAME or not AZURE_API_KEY:
    st.error("❌ Missing `PROJECT_ENDPOINT`, `AGENT_NAME`, or `AZURE_API_KEY`. Please configure them in Streamlit Secrets.")
    st.stop()


# 2. Authentication with AzureKeyCredential
@st.cache_resource(show_spinner="Connecting to Azure AI Services...")
def get_azure_clients():
    try:
        credential = AzureKeyCredential(AZURE_API_KEY)

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
    st.stop()


# 3. Sidebar Footer
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


# 6. Render Message History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(f'<div class="readable-container">{msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("citations"):
            with st.expander("📚 View Citations"):
                for cite in msg["citations"]:
                    st.write(f"- {cite}")


# 7. Human-in-the-Loop Approval Widget
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
    st.rerun()


# 9. Response Streaming
if st.session_state.awaiting_response and not st.session_state.pending_approval:
    with st.chat_message("assistant"):
        text_placeholder = st.empty()
        full_text = ""
        citations_list = []

        try:
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

            for event in response_stream:
                if getattr(event, "type", None) == "response.output_text.delta":
                    full_text += event.delta
                    
                    clean_display_text = full_text.replace(" ⊗ ", "\n\n")
                    clean_display_text = re.sub(r'【[^】]*】', '', clean_display_text)

                    text_placeholder.markdown(
                        f'<div class="readable-container">{clean_display_text}</div>', 
                        unsafe_allow_html=True
                    )

                if hasattr(event, "citations") and event.citations:
                    for citation in event.citations:
                        source_val = getattr(citation, "content", "Knowledge Base")
                        if source_val not in citations_list:
                            citations_list.append(source_val)

                if getattr(event, "type", None) == "mcp_approval_request":
                    st.session_state.pending_approval = event
                    break

        except Exception as e:
            st.error("Error streaming agent response.")
            st.exception(e)

    st.session_state.awaiting_response = False

    if st.session_state.pending_approval:
        st.rerun()

    if full_text:
        final_clean_text = re.sub(r'【[^】]*】', '', full_text).replace(" ⊗ ", "\n\n")
        st.session_state.messages.append({
            "role": "assistant",
            "content": final_clean_text,
            "citations": citations_list,
        })
        st.rerun()
