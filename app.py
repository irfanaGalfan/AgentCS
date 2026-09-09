import json
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment variables
load_dotenv()
project_endpoint = os.getenv("PROJECT_ENDPOINT")
agent_name = os.getenv("AGENT_NAME")

# Validate configuration
if not project_endpoint or not agent_name:
    raise ValueError("PROJECT_ENDPOINT and AGENT_NAME must be set in .env file")

print(f"Connecting to project: {project_endpoint}")
print(f"Using agent: {agent_name}\n")

# 1. Connect to the project and agent
credential = DefaultAzureCredential(
    exclude_environment_credential=True,
    exclude_managed_identity_credential=True,
)
project_client = AIProjectClient(
    credential=credential, endpoint=project_endpoint
)

# 2. Get the OpenAI client
openai_client = project_client.get_openai_client()

# 3. Get the agent reference
agent = project_client.agents.get(agent_name=agent_name)
print(f"Connected to agent: {agent.name} (id: {agent.id})\n")

# 4. Create a new conversation thread
conversation = openai_client.conversations.create(items=[])
print(f"Created conversation (id: {conversation.id})\n")

# Conversation history for context (client-side tracking)
conversation_history = []


def send_message_to_agent(user_message):
    """
    Send a message to the agent and handle the response using the conversations API.
    """
    try:
        print("\nAgent: ", end="", flush=True)

        # Step A: Add user message to the conversation thread
        openai_client.conversations.items.create(
            conversation_id=conversation.id,
            items=[
                {"type": "message", "role": "user", "content": user_message}
            ],
        )

        # Track in local history
        conversation_history.append(
            {"role": "user", "content": user_message}
        )

        # Step B: Request response from agent
        response = openai_client.responses.create(
            conversation=conversation.id,
            extra_body={
                "agent_reference": {
                    "name": agent.name,
                    "type": "agent_reference",
                }
            },
            input="",
        )

        # Step C: Loop to handle MCP Approval Requests if triggered
        while True:
            approval_request = None
            if hasattr(response, "output") and response.output:
                for item in response.output:
                    if getattr(item, "type", None) == "mcp_approval_request":
                        approval_request = item
                        break

            # If no approval is required, exit the approval loop
            if not approval_request:
                break

            print(f"\n[Approval required for: {approval_request.name}]")
            print(f"Server: {getattr(approval_request, 'server_label', 'Unknown')}")

            # Display formatted arguments
            try:
                args = json.loads(approval_request.arguments)
                print(f"Arguments:\n{json.dumps(args, indent=2)}\n")
            except Exception:
                print(f"Arguments: {approval_request.arguments}\n")

            # Prompt user
            approval_input = (
                input("Approve this action? (yes/no): ").strip().lower()
            )
            is_approved = approval_input in ["yes", "y"]

            if is_approved:
                print("Approving action...\n")
            else:
                print("Action denied.\n")

            approval_response = {
                "type": "mcp_approval_response",
                "approval_request_id": approval_request.id,
                "approve": is_approved,
            }

            # Submit approval/denial choice back to conversation
            openai_client.conversations.items.create(
                conversation_id=conversation.id, items=[approval_response]
            )

            # Re-trigger response creation to continue agent execution
            response = openai_client.responses.create(
                conversation=conversation.id,
                extra_body={
                    "agent_reference": {
                        "name": agent.name,
                        "type": "agent_reference",
                    }
                },
                input="",
            )

        # Step D: Render output and citations
        if response and getattr(response, "output_text", None):
            response_text = response.output_text
            print(f"{response_text}\n")

            if getattr(response, "citations", None):
                print("\nSources:")
                for citation in response.citations:
                    source_val = getattr(citation, "content", "Knowledge Base")
                    print(f"  - {source_val}")

            conversation_history.append(
                {"role": "assistant", "content": response_text}
            )
            return response_text
        else:
            print("No text response received from agent.\n")
            return None

    except Exception as e:
        print(f"\n\nError processing request: {str(e)}\n")
        return None


def display_conversation_history():
    """Display client-side tracked conversation history."""
    print("\n" + "=" * 60)
    print("CONVERSATION HISTORY")
    print("=" * 60 + "\n")

    for turn in conversation_history:
        role = turn["role"].upper()
        content = turn["content"]
        print(f"{role}: {content}\n")

    print("=" * 60 + "\n")


def main():
    """Main CLI execution loop."""
    print("Contoso Product Expert Agent")
    print("Ask questions about our outdoor and camping products.")
    print("Type 'history' to see conversation history, or 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("\nEnding conversation...")
                break

            if user_input.lower() == "history":
                display_conversation_history()
                continue

            send_message_to_agent(user_input)

        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            break
        except Exception as e:
            print(f"\nUnexpected CLI error: {str(e)}\n")

    print("\nConversation ended.")


if __name__ == "__main__":
    main()