from logging import Logger, getLogger
from typing import List
from uuid import UUID

from src.infrastructure.postgres.repositories import DocumentRepository
from src.infrastructure import AiHubClient
from src.applications.dtos.search import SearchMode, SimilarityMetric


class SearchService:
    """Service for handling different search modes."""
    
    def __init__(
        self,
        document_repository: DocumentRepository,
        aihub_client: AiHubClient
    ) -> None:
        self.document_repository = document_repository
        self.aihub_client = aihub_client
        self._logger: Logger = getLogger(__name__)
    
    async def search(
        self,
        datasource_ids: List[UUID],
        query: str,
        search_mode: SearchMode,
        similarity_metric: SimilarityMetric = SimilarityMetric.COSINE,
        top_k: int = 5
    ) -> List[dict]:
        """Execute search based on the specified mode.
        
        Args:
            datasource_ids: List of datasource UUIDs to search in
            query: User query text
            search_mode: Search mode (semantic, full_text, or hybrid)
            similarity_metric: Distance metric for vector search
            top_k: Number of results to return
            
        Returns:
            List of search results with chunk information and scores
        """
        self._logger.info(
            f"Searching with mode={search_mode.value}, metric={similarity_metric.value}, "
            f"query='{query}', datasources={len(datasource_ids)}, top_k={top_k}"
        )
        
        # Switch case based on search mode
        if search_mode == SearchMode.SEMANTIC:
            return await self._semantic_search(
                datasource_ids, query, similarity_metric, top_k
            )
        elif search_mode == SearchMode.FULL_TEXT:
            return await self._full_text_search(datasource_ids, query, top_k)
        elif search_mode == SearchMode.HYBRID:
            return await self._hybrid_search(
                datasource_ids, query, similarity_metric, top_k
            )
        else:
            raise ValueError(f"Unsupported search mode: {search_mode}")
    
    async def _semantic_search(
        self,
        datasource_ids: List[UUID],
        query: str,
        similarity_metric: SimilarityMetric,
        top_k: int
    ) -> List[dict]:
        """Vector similarity search using embeddings."""
        self._logger.info(f"Performing semantic search with {similarity_metric.value}")
        
        # Get embedding model from first datasource
        embedding_model = await self.document_repository.get_datasource_embedding_model(
            datasource_ids[0]
        )
        if not embedding_model:
            raise ValueError(f"No embedding model found for datasource {datasource_ids[0]}")
        
        # Generate query embedding
        embedding_response = await self.aihub_client.embedding(
            inputs=query,
            model=embedding_model
        )
        query_embedding = embedding_response["data"][0]["embedding"]
        
        # Convert embedding to PostgreSQL array format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Map similarity metric to pgvector operator
        operator_map = {
            SimilarityMetric.COSINE: "<=>",  # Cosine distance
            SimilarityMetric.L2: "<->",      # L2 distance
            SimilarityMetric.INNER_PRODUCT: "<#>",  # Negative inner product
        }
        operator = operator_map[similarity_metric]
        
        # Build SQL query for vector similarity search
        datasource_ids_str = ", ".join([f"'{str(ds_id)}'" for ds_id in datasource_ids])
        
        sql_query = f"""
            SELECT 
                c.id as chunk_id,
                c.document_id,
                c.datasource_id,
                c.content,
                c.chunk_index,
                d.title as document_title,
                (1 - (c.embedding {operator} '{embedding_str}'::vector)) as score
            FROM chunks_384dimensions c
            JOIN documents d ON c.document_id = d.id
            WHERE c.datasource_id IN ({datasource_ids_str})
                AND c.embedding IS NOT NULL
            ORDER BY c.embedding {operator} '{embedding_str}'::vector
            LIMIT :top_k
        """
        
        results = await self.document_repository.execute_raw_sql(
            sql_query,
            {
                "top_k": top_k
            }
        )
        
        self._logger.info(f"Semantic search returned {len(results)} results")
        return results
    
    async def _full_text_search(
        self,
        datasource_ids: List[UUID],
        query: str,
        top_k: int
    ) -> List[dict]:
        """Full-text search using PostgreSQL tsvector."""
        self._logger.info("Performing full-text search")
        
        datasource_ids_str = ", ".join([f"'{str(ds_id)}'" for ds_id in datasource_ids])
        
        sql_query = f"""
            SELECT 
                c.id as chunk_id,
                c.document_id,
                c.datasource_id,
                c.content,
                c.chunk_index,
                d.title as document_title,
                ts_rank(c.tcontent, query) as score
            FROM chunks_384dimensions c
            JOIN documents d ON c.document_id = d.id,
            plainto_tsquery('english', :search_text) query
            WHERE c.datasource_id IN ({datasource_ids_str})
                AND c.tcontent @@ query
            ORDER BY score DESC
            LIMIT :top_k
        """
        
        results = await self.document_repository.execute_raw_sql(
            sql_query,
            {
                "search_text": query,
                "top_k": top_k
            }
        )
        
        self._logger.info(f"Full-text search returned {len(results)} results")
        return results
    
    async def _hybrid_search(
        self,
        datasource_ids: List[UUID],
        query: str,
        similarity_metric: SimilarityMetric,
        top_k: int,
        text_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[dict]:
        """Hybrid search combining full-text and vector similarity."""
        self._logger.info(
            f"Performing hybrid search (text_weight={text_weight}, vector_weight={vector_weight})"
        )
        
        # Get embedding model from first datasource
        embedding_model = await self.document_repository.get_datasource_embedding_model(
            datasource_ids[0]
        )
        if not embedding_model:
            raise ValueError(f"No embedding model found for datasource {datasource_ids[0]}")
        
        # Generate query embedding
        embedding_response = await self.aihub_client.embedding(
            inputs=query,
            model=embedding_model
        )
        query_embedding = embedding_response["data"][0]["embedding"]
        
        # Convert embedding to PostgreSQL array format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Map similarity metric to pgvector operator
        operator_map = {
            SimilarityMetric.COSINE: "<=>",
            SimilarityMetric.L2: "<->",
            SimilarityMetric.INNER_PRODUCT: "<#>",
        }
        operator = operator_map[similarity_metric]
        
        datasource_ids_str = ", ".join([f"'{str(ds_id)}'" for ds_id in datasource_ids])
        
        sql_query = f"""
            WITH text_search AS (
                SELECT 
                    c.id,
                    ts_rank(c.tcontent, query) as text_score
                FROM chunks_384dimensions c,
                plainto_tsquery('english', :search_text) query
                WHERE c.datasource_id IN ({datasource_ids_str})
                    AND c.tcontent @@ query
            ),
            vector_search AS (
                SELECT 
                    c.id,
                    (1 - (c.embedding {operator} '{embedding_str}'::vector)) as vector_score
                FROM chunks_384dimensions c
                WHERE c.datasource_id IN ({datasource_ids_str})
                    AND c.embedding IS NOT NULL
            )
            SELECT 
                c.id as chunk_id,
                c.document_id,
                c.datasource_id,
                c.content,
                c.chunk_index,
                d.title as document_title,
                (COALESCE(ts.text_score, 0) * :text_weight + 
                 COALESCE(vs.vector_score, 0) * :vector_weight) as score
            FROM chunks_384dimensions c
            JOIN documents d ON c.document_id = d.id
            LEFT JOIN text_search ts ON c.id = ts.id
            LEFT JOIN vector_search vs ON c.id = vs.id
            WHERE c.datasource_id IN ({datasource_ids_str})
                AND (ts.text_score IS NOT NULL OR vs.vector_score IS NOT NULL)
            ORDER BY score DESC
            LIMIT :top_k
        """
        
        results = await self.document_repository.execute_raw_sql(
            sql_query,
            {
                "search_text": query,
                "text_weight": text_weight,
                "vector_weight": vector_weight,
                "top_k": top_k
            }
        )
        
        self._logger.info(f"Hybrid search returned {len(results)} results")
        return results