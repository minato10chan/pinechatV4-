import sys
from src.services.pinecone_service import PineconeService

def main():
    try:
        # Pineconeサービスの初期化
        service = PineconeService()
        
        # インデックスの統計情報を取得
        stats = service.get_index_stats()
        print(f"インデックス名: {stats['index_name']}")
        print(f"ベクトル数: {stats['total_vector_count']}")
        print(f"次元数: {stats['dimension']}")
        print(f"メトリック: {stats['metric']}")
        
        # テスト検索
        test_query = "テスト検索"
        print(f"\nテスト検索: {test_query}")
        results = service.query(test_query)
        print(f"検索結果数: {results['filtered_matches']}/{results['total_matches']}")
        
        if results['matches']:
            print("\n検索結果:")
            for match in results['matches']:
                print(f"スコア: {match.score:.3f}")
                print(f"テキスト: {match.metadata['text'][:100]}...")
                print("---")
        else:
            print("検索結果が見つかりませんでした。")
            
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main() 