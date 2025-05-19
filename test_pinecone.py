import sys
import time
from src.services.pinecone_service import PineconeService

def main():
    try:
        # Pineconeサービスの初期化
        print("Pineconeサービスを初期化中...")
        service = PineconeService()
        
        # インデックスの統計情報を取得
        print("\nインデックスの初期状態を確認...")
        stats = service.get_index_stats()
        print(f"ベクトル数: {stats['total_vector_count']}")
        
        # テストデータの作成
        test_chunks = [
            {
                "id": "test1",
                "text": "これはテストデータ1です。検索機能の確認に使用します。"
            },
            {
                "id": "test2",
                "text": "これはテストデータ2です。日本語の文章を含んでいます。"
            },
            {
                "id": "test3",
                "text": "テスト用の文章その3。検索とインデックスの動作確認。"
            },
            {
                "id": "test4",
                "text": "検索機能のテストを行います。日本語の文章で確認します。"
            },
            {
                "id": "test5",
                "text": "これは別の内容の文章です。検索には関係ありません。"
            }
        ]
        
        # テストデータのアップロード
        print("\nテストデータをアップロードします...")
        service.upload_chunks(test_chunks)
        
        # インデックスの更新を待機
        print("\nインデックスの更新を待機中...")
        time.sleep(5)
        
        # インデックスの統計情報を再取得
        stats = service.get_index_stats()
        print(f"\nインデックスの現在の状態:")
        print(f"ベクトル数: {stats['total_vector_count']}")
        print(f"次元数: {stats['dimension']}")
        
        # テスト検索（複数のクエリでテスト）
        test_queries = [
            "テストデータ",
            "検索機能",
            "日本語",
            "存在しない文章"
        ]
        
        for query in test_queries:
            print(f"\n検索クエリ: {query}")
            results = service.query(query, similarity_threshold=0.5)  # しきい値を下げる
            
            if results['matches']:
                print(f"\n検索結果 ({len(results['matches'])}件):")
                for match in results['matches']:
                    print(f"スコア: {match.score:.3f}")
                    print(f"テキスト: {match.metadata['text']}")
                    print("---")
            else:
                print("検索結果が見つかりませんでした。")
            
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main() 