# import os
# from datetime import datetime
# from azure.storage.blob import BlobServiceClient
# from dotenv import load_dotenv

# load_dotenv(dotenv_path=".env", override=True)
# #––– pull these from your env (or however you manage config) –––
# CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
# CONTAINER_NAME    = os.getenv("AZURE_CONTAINER_NAME")

# def get_blob_service_client():
#     return BlobServiceClient.from_connection_string(CONNECTION_STRING)

# def save_html_db(fig, filename: str) -> dict:
#     """
#     1) write the Plotly figure to `filename`
#     2) upload that file to Azure Blob
#     3) delete the local file
#     4) return {"filename": <name-without-.html>, "file_url": <azure-url>}
#     """
#     # 1) make sure the output folder exists
#     os.makedirs(os.path.dirname(filename), exist_ok=True)

#     # 2) write the HTML file
#     fig.write_html(filename)

#     # 3) prepare Azure client & container
#     blob_service_client = get_blob_service_client()
#     container_client    = blob_service_client.get_container_client(CONTAINER_NAME)
#     try:
#         container_client.create_container()
#     except Exception as e:
#         # ignore if it already exists
#         if "ContainerAlreadyExists" not in str(e):
#             raise

#     # 4) upload the file
#     blob_name   = os.path.basename(filename)                       
#     blob_client = container_client.get_blob_client(blob_name)
#     with open(filename, "rb") as data:
#         blob_client.upload_blob(
#             data,
#             overwrite=True,
#             content_type="text/html"
#         )

#     # 5) delete the local file
#     os.remove(filename)

#     # 6) return the base filename (minus ".html") and the URL
#     base_name = os.path.splitext(blob_name)[0]
#     return {
#         "filename": base_name,
#         "file_url": blob_client.url
#     }
