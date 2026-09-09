import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Set your project endpoint
endpoint = "https://34150040-2851-resource.services.ai.azure.com/api/projects/34150040-2851"

# Authenticate via Entra ID (Ensure you ran `az login` in your terminal)
credential = DefaultAzureCredential()

# Initialize AIProjectClient using endpoint
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=credential
)

# Verify project connections
print("Successfully connected to Azure AI Foundry Project!")
print("Active Connections:")
for conn in project_client.connections.list():
    print(f" - {conn.name} ({conn.type})")