import os
import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from dotenv import load_dotenv

load_dotenv()

region = "us-east-2"
index_name = "feast-vectorial-db-app"

mapping = {
    "settings": {"index": {"knn": True}},
    "mappings": {
        "properties": {
            "nombre": {"type": "text"},
            "descripcion": {"type": "text"},
            "vector": {"type": "knn_vector", "dimension": 1024}
        }
    }
}


class VectorRepository:

    def __init__(self):
        self.bedrock = boto3.client("bedrock-runtime", region_name=region)
        self.client = self._build_client()
        self._ensure_index()

    def _build_client(self):
        credentials = boto3.Session().get_credentials().get_frozen_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            "aoss",
            session_token=credentials.token
        )
        return OpenSearch(
            hosts=[{"host": os.getenv("VECTOR_HOST"), "port": 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )

    def _ensure_index(self):
        if not self.client.indices.exists(index=index_name):
            self.client.indices.create(index=index_name, body=mapping)

    def _generar_embedding(self, texto: str) -> list | None:
        response = self.bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({"inputText": texto}),
            contentType="application/json"
        )
        return json.loads(response["body"].read())["embedding"]

    def crear(self, id: int, nombre: str, descripcion: str) -> None:
        embedding = self._generar_embedding(f"{nombre}. {descripcion}")
        self.client.index(
            index=index_name,
            id=id,
            body={"nombre": nombre, "descripcion": descripcion, "vector": embedding}
        )

    def buscar(self, query: str) -> list:
        embedding = self._generar_embedding(query)
        response = self.client.search(
            index=index_name,
            body={
                "size": 5,
                "query": {
                    "knn": {
                        "vector": {"vector": embedding, "k": 5}
                    }
                }
            }
        )
        return response["hits"]["hits"]

    def actualizar(self, id: int, nombre: str, descripcion: str) -> None:
        embedding = self._generar_embedding(f"{nombre}. {descripcion}")
        self.client.update(
            index=index_name,
            id=id,
            body={"doc": {"nombre": nombre, "descripcion": descripcion, "vector": embedding}}
        )

    def eliminar(self, id: int) -> None:
        self.client.delete(index=index_name, id=id)