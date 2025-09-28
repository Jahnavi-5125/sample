# from asyncio.log import logger
# from datetime import datetime
# import os
# from fastapi import HTTPException, Query
# from langchain_community.vectorstores import Qdrant
# from langchain_openai import AzureOpenAIEmbeddings
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.schema import Document
# from qdrant_client import QdrantClient
# from qdrant_client.http.models import Distance, VectorParams
# import asyncio
# from langchain.embeddings.base import Embeddings 
# from qdrant_client.models import Filter, FieldCondition, MatchText, SearchParams
# import hashlib
# from dotenv import dotenv_values
# from src.ai.ai_schemas.tool_structured_input import QueryRequest
# # Initialize Qdrant and embeddings
# env_vars = dotenv_values('.env')
# openai_api_key = env_vars.get('OPENAI_API_KEY')
# QDRANT_CLIENT_URL = env_vars.get('QDRANT_CLIENT_URL')
# embeddings = AzureOpenAIEmbeddings(api_key=os.getenv('AZURE_API_KEY'), model="text-embedding-3-small", azure_endpoint=os.getenv("AZURE_API_BASE"))
# qdrant_client = QdrantClient(host=QDRANT_CLIENT_URL, port=6333)

# # Ensure the collection exists (run this only once or check first)
# try:
#     qdrant_client.get_collection("file_storage")
# except Exception:
#     qdrant_client.create_collection(
#         collection_name="file_storage",
#         vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
#     )
# async def store_document_embeddings(file_id, filename, text_content, user_id):
#     try:
#         # Generate SHA-256 hash of the document content
#         content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
#         print(f"Document hash: {content_hash}")
        
#         # Check if document with this hash already exists
#         qdrant = Qdrant(
#             client=qdrant_client,
#             collection_name="file_storage",
#             embeddings=embeddings
#         )
        
#         # Search for existing document with same hash
#         try:
#             existing_docs = qdrant.similarity_search(
#                 query="dummy_query",  # We just need to check metadata, query doesn't matter
#                 k=1,
#                 filter={"content_hash": content_hash, "user_id": user_id}
#             )
            
#             if existing_docs:
#                 print(f"Document with hash {content_hash} already exists")
#                 return {
#                     "status": "success", 
#                     "message": "Document already exists",
#                     "file_id": existing_docs[0].metadata.get("file_id"),
#                     "existing_filename": existing_docs[0].metadata.get("filename"),
#                     "content_hash": content_hash
#                 }
#         except Exception as search_error:
#             # If search fails, assume document doesn't exist and continue
#             print(f"Search error : {search_error}")
        
#         # Document doesn't exist, proceed with storage
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,
#             chunk_overlap=200,
#             separators=["\n\n", "\n", ". ", " ", ""]
#         )
        
#         # Split the text into chunks
#         texts = text_splitter.split_text(text_content)
#         print(f"Number of chunks created: {len(texts)}")
        
#         # Create metadata for each chunk (including content hash)
#         metadatas = [
#             {
#                 "file_id": file_id,
#                 "user_id": user_id,
#                 "filename": filename,
#                 "chunk_index": i,
#                 "total_chunks": len(texts),
#                 "content_hash": content_hash  # Add hash to metadata
#             } for i in range(len(texts))
#         ]
        
#         # Convert to LangChain documents
#         documents = [
#             Document(page_content=text, metadata=metadata)
#             for text, metadata in zip(texts, metadatas)
#         ]
        
#         # Add documents to Qdrant
#         # This will be executed in a thread pool since it's a blocking operation
#         loop = asyncio.get_running_loop()
#         await loop.run_in_executor(
#             None,
#             lambda: qdrant.add_documents(documents)
#         )
        
#         return {
#             "status": "success", 
#             "chunks": len(texts),
#             "content_hash": content_hash,
#             "message": "Document stored successfully",
#             "file_id": file_id
#         }
    
#     except Exception as e:
#         print(f"Error storing embeddings: {str(e)}")
#         return {"status": "error", "message": str(e)}


# def search_file_storage(query: str, doc_ids: list, k: int = 5):
#     """
#     Perform a similarity search on the 'file_storage' collection in Qdrant for a given query and session ID.

#     Args:
#         query (str): The query string to search.
#         session_id (str): The session ID to filter the search.
#         qdrant_client (QdrantClient): The Qdrant client instance.
#         embeddings (Embeddings): The embeddings model used for vector representation.
#         k (int): Number of top results to retrieve.

#     Returns:
#         List[Dict]: A list of dictionaries containing search results.
#     """
#     qdrant = Qdrant(
#         client=qdrant_client,
#         collection_name="file_storage",
#         embeddings=embeddings
#     )

#     results = qdrant.similarity_search(
#         query=query,
#         k=k,
#         filter={"file_id": doc_ids}
#     )
#     print(results)
#     formatted_results = []
#     for doc in results:
#         result_data = {
#             "content": doc.page_content,
#             "filename": doc.metadata.get("filename"),
#             "file_id": doc.metadata.get("file_id")
#         }
#         formatted_results.append(result_data)

#     return formatted_results

# def search_similar_company_name(
#     query: QueryRequest,
#     limit: int = 5
# ):
#     """
#     Search for similar stocks using optional exchange filter, exact match, and vector similarity.
#     """
#     try:
#         print(f"Searching for: {query.query} | Type: {query.type} | Exchange: {query.exchange_short_name}")
#         # ---- 1. Build Filter Conditions ----
#         filter_conditions_must = []
#         filter_conditions_should = []

#         if query.exchange_short_name:
#             query.exchange_short_name=query.exchange_short_name.strip().upper()
#             filter_conditions_must.append(
#                 FieldCondition(
#                     key="exchangeShortName",
#                     match=MatchText(text=query.exchange_short_name)
#                 )
#             )

#         query_to_embed = ""
#         if query.type == "ticker_symbol":
#             query_to_embed = f"Symbol: {query.query.upper()}"
#             filter_conditions_should.append(
#                 FieldCondition(
#                     key="symbol",
#                     match=MatchText(text=query.query.upper())
#                 )
#             )
#         elif query.type == "company_name":
#             query_to_embed = f"Name: {query.query}"
#             filter_conditions_should.append(
#                 FieldCondition(
#                     key="name",
#                     match=MatchText(text=query.query)
#                 )
#             )

#         # Primary filter (must + should)
#         query_filter = Filter(
#             must=filter_conditions_must,
#             should=filter_conditions_should
#         )

#         # Secondary fallback filter (only must)
#         fallback_filter = Filter(
#             must=filter_conditions_must
#         )

#         # ---- 2. Generate embedding ----
        
#         query_embedding = embeddings.embed_query(query_to_embed)

#         if not isinstance(query_embedding, list):
#             query_embedding = query_embedding.tolist() if hasattr(query_embedding, 'tolist') else list(query_embedding)

#         # ---- 3. Try vector search with full filter ----
#         print(f"Performing vector search with filter: {query_filter}")
#         hits = qdrant_client.search(
#             collection_name="company_embeddings",
#             query_vector=query_embedding,
#             limit=limit,
#             with_payload=True,
#             search_params=SearchParams(hnsw_ef=128),
#             query_filter=query_filter
#         )
#         print(f"hits: {hits}")
#         # ---- 4. Fallback: use only "must" filter if no results ----
#         if not hits:
#             print("Fallback: retrying with only 'must' filter")
#             hits = qdrant_client.search(
#                 collection_name="company_embeddings",
#                 query_vector=query_embedding,
#                 limit=limit,
#                 with_payload=True,
#                 search_params=SearchParams(hnsw_ef=128),
#                 query_filter=fallback_filter
#             )
#         print("Hits after fallback:", hits)
#         # ---- 5. Format the final response ----
#         results = []
#         for hit in hits:
#             payload = hit.payload
#             result_item = {
#                 "score": getattr(hit, "score", 1.0),
#                 "symbol": payload.get("symbol", ""),
#                 "name": payload.get("name", ""),
#                 "exchangeShortName": payload.get("exchangeShortName", ""),
#                 "type": payload.get("type", ""),
#             }
#             results.append(result_item)

#         response = {
#             "results": results[:limit],
#             "timestamp": datetime.now().isoformat()
#         }

#         return response

#     except Exception as e:
#         logger.error(f"Search error: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")   
# if __name__ == "__main__":
#     x = search_file_storage("GST Taxation in India", ["62a48b96-f03f-4576-a07a-b9a011d19d21"], k=5)
#     print(x)