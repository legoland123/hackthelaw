import os
from dotenv import load_dotenv
from google.cloud import aiplatform_v1

load_dotenv()
project  = os.environ["GOOGLE_CLOUD_PROJECT"]
location = os.environ["VERTEX_AI_VECTOR_SEARCH_LOCATION"]
index_id = os.environ["VECTOR_SEARCH_INDEX_ID"]

client = aiplatform_v1.IndexServiceClient(
    client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
)
name = f"projects/{project}/locations/{location}/indexes/{index_id}"
idx = client.get_index(name=name)

print("Index name:", idx.name)
print("Metadata:", idx.metadata)  # look for a 'dimensions' field
