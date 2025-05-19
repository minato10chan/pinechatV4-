from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
import time
from ..config.settings import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    BATCH_SIZE,
    DEFAULT_TOP_K,
    SIMILARITY_THRESHOLD
)
import json

class PineconeService:
    def __init__(self):
        """Pineconeサービスの初期化"""
        try:
            # OpenAIクライアントの初期化
            if not OPENAI_API_KEY:
                raise ValueError("OpenAI APIキーが設定されていません")
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Pineconeの初期化
            if not PINECONE_API_KEY:
                raise ValueError("Pinecone APIキーが設定されていません")
            if not PINECONE_INDEX_NAME:
                raise ValueError("Pineconeインデックス名が設定されていません")
            
            self.pc = Pinecone(api_key=PINECONE_API_KEY)
            
            # インデックスの存在確認と初期化
            self._initialize_index()
            
            # インデックスの次元数を取得
            stats = self.index.describe_index_stats()
            self.dimension = stats.dimension
            print(f"インデックスの次元数: {self.dimension}")
            
        except Exception as e:
            raise Exception(f"Pineconeサービスの初期化に失敗しました: {str(e)}")

    def _initialize_index(self):
        """インデックスの初期化"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # インデックスの存在確認
                existing_indexes = self.pc.list_indexes().names()
                print(f"既存のインデックス: {existing_indexes}")
                
                if PINECONE_INDEX_NAME not in existing_indexes:
                    print(f"インデックス '{PINECONE_INDEX_NAME}' が存在しないため、新規作成します")
                    # インデックスが存在しない場合は作成
                    spec = ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                    self.pc.create_index(
                        name=PINECONE_INDEX_NAME,
                        dimension=1536,  # OpenAIの埋め込みモデルの次元数
                        metric="cosine",
                        spec=spec
                    )
                    print(f"インデックス '{PINECONE_INDEX_NAME}' の作成を開始しました")
                    # インデックスの作成完了を待機
                    time.sleep(10)
                
                # インデックスの取得
                self.index = self.pc.Index(PINECONE_INDEX_NAME)
                print(f"インデックス '{PINECONE_INDEX_NAME}' に接続しました")
                
                # インデックスの状態を確認
                stats = self.index.describe_index_stats()
                print(f"インデックスの状態: {stats.total_vector_count}件のベクトル")
                
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"インデックスの初期化に失敗しました（試行 {attempt + 1}/{max_retries}）: {str(e)}")
                    print(f"{retry_delay}秒後に再試行します...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 待機時間を倍増
                else:
                    raise Exception(f"インデックスの初期化に失敗しました（最大試行回数到達）: {str(e)}")

    def get_embedding(self, text: str) -> List[float]:
        """テキストの埋め込みベクトルを取得"""
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                response = self.openai_client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"埋め込みベクトルの生成に失敗しました（試行 {attempt + 1}/{max_retries}）: {str(e)}")
                    print(f"{retry_delay}秒後に再試行します...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise Exception(f"埋め込みベクトルの生成に失敗しました（最大試行回数到達）: {str(e)}")

    def upload_chunks(self, chunks: List[Dict[str, Any]], namespace: str = None, batch_size: int = BATCH_SIZE) -> None:
        """チャンクをPineconeにアップロード"""
        if not chunks:
            print("アップロードするチャンクがありません")
            return

        try:
            total_chunks = len(chunks)
            print(f"アップロード開始: 合計{total_chunks}件のチャンク")
            
            # チャンクをバッチに分割
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_num = i // batch_size + 1
                print(f"\nバッチ {batch_num} を処理中... ({len(batch)}件)")
                
                # バッチ内の各チャンクの埋め込みベクトルを取得
                vectors = []
                retry_chunks = []  # 再試行が必要なチャンク
                
                for j, chunk in enumerate(batch, 1):
                    try:
                        print(f"  チャンク {j}/{len(batch)} の埋め込みベクトルを生成中...")
                        vector = self.get_embedding(chunk["text"])
                        
                        # メタデータの設定（CSVファイルのメタデータを含める）
                        metadata = {
                            "text": chunk["text"],
                            "filename": chunk.get("filename", ""),
                            "chunk_id": chunk.get("chunk_id", ""),
                            "main_category": chunk.get("metadata", {}).get("main_category", ""),
                            "sub_category": chunk.get("metadata", {}).get("sub_category", ""),
                            "city": chunk.get("metadata", {}).get("city", ""),
                            "created_date": chunk.get("metadata", {}).get("created_date", ""),
                            "upload_date": chunk.get("metadata", {}).get("upload_date", ""),
                            "source": chunk.get("metadata", {}).get("source", ""),
                            # CSVファイルのメタデータ
                            "facility_name": chunk.get("metadata", {}).get("facility_name", ""),
                            "latitude": chunk.get("metadata", {}).get("latitude", 0.0),
                            "longitude": chunk.get("metadata", {}).get("longitude", 0.0),
                            "walking_distance": chunk.get("metadata", {}).get("walking_distance", 0),
                            "walking_minutes": chunk.get("metadata", {}).get("walking_minutes", 0),
                            "straight_distance": chunk.get("metadata", {}).get("straight_distance", 0)
                        }
                        
                        # デバッグ情報の表示
                        print(f"  メタデータ: {json.dumps(metadata, ensure_ascii=False)}")
                        
                        vectors.append({
                            "id": chunk["id"],
                            "values": vector,
                            "metadata": metadata
                        })
                    except Exception as e:
                        print(f"  チャンク {chunk['id']} の処理中にエラーが発生しました: {str(e)}")
                        retry_chunks.append(chunk)
                        continue
                
                if vectors:
                    max_retries = 3
                    retry_delay = 2
                    
                    for attempt in range(max_retries):
                        try:
                            # バッチをアップロード（namespaceを指定）
                            print(f"  {len(vectors)}件のベクトルをアップロード中...")
                            self.index.upsert(vectors=vectors, namespace=namespace)
                            print(f"  バッチ {batch_num} のアップロードが完了しました")
                            break
                        except Exception as e:
                            if attempt < max_retries - 1:
                                print(f"  バッチ {batch_num} のアップロードに失敗しました（試行 {attempt + 1}/{max_retries}）: {str(e)}")
                                print(f"  {retry_delay}秒後に再試行します...")
                                time.sleep(retry_delay)
                                retry_delay *= 2
                            else:
                                raise Exception(f"バッチ {batch_num} のアップロードに失敗しました（最大試行回数到達）: {str(e)}")
                
                # 失敗したチャンクを再試行
                if retry_chunks:
                    print(f"\n失敗したチャンク {len(retry_chunks)}件 を再試行します...")
                    self.upload_chunks(retry_chunks, namespace, batch_size)
            
            print("\nアップロード完了")
            
        except Exception as e:
            raise Exception(f"チャンクのアップロードに失敗しました: {str(e)}")

    def query(self, query_text: str, namespace: str = None, top_k: int = DEFAULT_TOP_K, similarity_threshold: float = SIMILARITY_THRESHOLD) -> Dict[str, Any]:
        """クエリに基づいて類似チャンクを検索"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # より多くの候補を取得
                query_vector = self.get_embedding(query_text)
                print(f"検索クエリ: {query_text}")
                print(f"類似度しきい値: {similarity_threshold}")
                print(f"取得する候補数: {top_k * 2}")
                
                # より多くの候補を取得（フィルタリング用）
                results = self.index.query(
                    vector=query_vector,
                    top_k=top_k * 2,  # フィルタリング用に2倍取得
                    include_metadata=True,
                    namespace=namespace  # namespaceを指定
                )
                
                print(f"取得した候補数: {len(results.matches)}")
                if results.matches:
                    print("候補のスコア:")
                    for match in results.matches:
                        print(f"スコア: {match.score:.3f}")
                
                # 類似度でフィルタリング
                filtered_matches = [
                    match for match in results.matches
                    if match.score >= similarity_threshold
                ]
                
                print(f"フィルタリング後の候補数: {len(filtered_matches)}")
                
                # 上位K件に制限
                filtered_matches = filtered_matches[:top_k]
                
                print(f"最終的な検索結果数: {len(filtered_matches)}")
                for match in filtered_matches:
                    print(f"スコア: {match.score:.3f}, テキスト: {match.metadata['text'][:100]}...")
                
                return {
                    "matches": filtered_matches,
                    "total_matches": len(results.matches),
                    "filtered_matches": len(filtered_matches)
                }
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"検索クエリの実行に失敗しました（試行 {attempt + 1}/{max_retries}）: {str(e)}")
                    print(f"{retry_delay}秒後に再試行します...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise Exception(f"検索クエリの実行に失敗しました（最大試行回数到達）: {str(e)}")

    def get_index_stats(self, namespace: str = None) -> Dict[str, Any]:
        """インデックスの統計情報を取得"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                stats = self.index.describe_index_stats(namespace=namespace)
                return {
                    "total_vector_count": stats.total_vector_count,
                    "namespaces": stats.namespaces
                }
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"統計情報の取得に失敗しました（試行 {attempt + 1}/{max_retries}）: {str(e)}")
                    print(f"{retry_delay}秒後に再試行します...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise Exception(f"統計情報の取得に失敗しました（最大試行回数到達）: {str(e)}")

    def clear_index(self, namespace: str = None) -> None:
        """インデックスをクリア"""
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            print(f"インデックスをクリアしました（namespace: {namespace if namespace else 'default'}）")
        except Exception as e:
            raise Exception(f"インデックスのクリアに失敗しました: {str(e)}")

    def get_index_data(self) -> List[Dict]:
        """インデックスのデータを取得"""
        try:
            # デフォルトnamespaceのデータを取得
            results = self.index.query(
                vector=[0] * 1536,  # ダミーベクトル
                top_k=1000,
                include_metadata=True,
                namespace=""
            )
            
            data = []
            for match in results.matches:
                if 'metadata' in match:
                    metadata = match['metadata']
                    # 必要なメタデータを抽出
                    item = {
                        'filename': metadata.get('filename', ''),
                        'chunk_id': metadata.get('chunk_id', ''),
                        'main_category': metadata.get('main_category', ''),
                        'sub_category': metadata.get('sub_category', ''),
                        'city': metadata.get('city', ''),
                        'created_date': metadata.get('created_date', ''),
                        'upload_date': metadata.get('upload_date', ''),
                        'source': metadata.get('source', '')
                    }
                    data.append(item)
            
            return data
        except Exception as e:
            raise Exception(f"インデックスデータの取得に失敗しました: {str(e)}")

    def get_stats(self, namespace: str = None) -> dict:
        """指定されたnamespaceの統計情報を取得"""
        try:
            stats = self.index.describe_index_stats()
            if namespace:
                return stats.get('namespaces', {}).get(namespace, {})
            return stats
        except Exception as e:
            raise Exception(f"統計情報の取得に失敗しました: {str(e)}")

    def list_vectors(self, namespace: str = None, limit: int = 1000) -> list:
        """指定されたnamespaceのベクトルを取得"""
        try:
            # 空のクエリで全ベクトルを取得
            results = self.index.query(
                vector=[0] * 1536,  # ダミーベクトル（次元数はモデルに依存）
                top_k=limit,
                include_metadata=True,
                namespace=namespace
            )
            return results.matches
        except Exception as e:
            raise Exception(f"ベクトルの取得に失敗しました: {str(e)}")

    def get_by_id(self, vector_id: str, namespace: str = None) -> Dict[str, Any]:
        """指定されたIDのベクトルを取得"""
        try:
            # ベクトルを取得
            result = self.index.fetch(ids=[vector_id], namespace=namespace)
            
            if not result.vectors:
                return None
                
            # 最初のベクトルを取得
            vector = result.vectors[vector_id]
            
            # 結果を整形
            return {
                "id": vector.id,
                "values": vector.values,
                "metadata": vector.metadata,
                "text": vector.metadata.get("text", "")
            }
        except Exception as e:
            print(f"ベクトルの取得中にエラーが発生しました: {str(e)}")
            return None 