import streamlit as st
from src.utils.text_processing import process_text_file
from src.services.pinecone_service import PineconeService
from src.config.settings import METADATA_CATEGORIES, CATEGORY_KEYWORDS, CHUNK_SIZE
from datetime import datetime
import pandas as pd
import json
import traceback
import io
import re

# デフォルトの作成日時を設定
DEFAULT_CREATION_DATE = datetime.now().isoformat()

def split_text_into_chunks(text: str, max_chunk_size: int = None) -> list:
    """
    テキストを適切なサイズのチャンクに分割する関数
    
    Args:
        text (str): 分割するテキスト
        max_chunk_size (int): チャンクの最大サイズ（文字数）
    
    Returns:
        list: 分割されたテキストチャンクのリスト
    """
    # セッション状態からチャンクサイズを取得、なければデフォルト値を使用
    chunk_size = max_chunk_size or st.session_state.get("chunk_size", CHUNK_SIZE)
    
    # テキストが空の場合は空のリストを返す
    if not text:
        return []
    
    # テキストを行ごとに分割
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for line in lines:
        line = line.strip()
        if not line:  # 空行をスキップ
            continue
            
        # 現在のチャンクに追加した場合のサイズを計算
        line_size = len(line)
        
        # 現在のチャンクが最大サイズを超える場合は新しいチャンクを開始
        if current_size + line_size > chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
        
        # 行を現在のチャンクに追加
        current_chunk.append(line)
        current_size += line_size
    
    # 最後のチャンクを追加
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def read_file_content(file) -> str:
    """ファイルの内容を適切なエンコーディングで読み込む"""
    encodings = ['utf-8', 'shift-jis', 'cp932', 'euc-jp']
    content = file.getvalue()
    
    for encoding in encodings:
        try:
            # バイト列を文字列にデコード
            decoded_content = content.decode(encoding)
            # デコードした文字列を再度エンコードして元のバイト列と比較
            if decoded_content.encode(encoding) == content:
                return decoded_content
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    
    # すべてのエンコーディングで失敗した場合
    try:
        # UTF-8で強制的にデコードを試みる（一部の文字が化ける可能性あり）
        return content.decode('utf-8', errors='replace')
    except Exception as e:
        raise ValueError(f"ファイルのエンコーディングを特定できませんでした。エラー: {str(e)}")

def process_csv_file(file):
    """CSVファイルを処理してチャンクに分割"""
    try:
        # エンコーディングのリスト（日本語のCSVで一般的なエンコーディング）
        encodings = ['utf-8', 'shift-jis', 'cp932', 'euc-jp']
        
        # 各エンコーディングで試行
        for encoding in encodings:
            try:
                # ファイルの内容をバイト列として読み込む
                content = file.getvalue()
                # 指定したエンコーディングでデコード
                decoded_content = content.decode(encoding)
                # デコードした内容をStringIOに変換
                file_like = io.StringIO(decoded_content)
                # CSVとして読み込む
                df = pd.read_csv(file_like, header=None, names=[
                    "大カテゴリ", "中カテゴリ", "施設名", "緯度", "経度", "徒歩距離", "徒歩分数", "直線距離"
                ])
                break  # 成功したらループを抜ける
            except (UnicodeDecodeError, pd.errors.EmptyDataError):
                continue  # 失敗したら次のエンコーディングを試す
        
        if 'df' not in locals():
            raise ValueError("CSVファイルのエンコーディングを特定できませんでした。")
        
        # デバッグ情報の表示
        st.write("CSVファイルの内容:")
        st.dataframe(df)
        
        # 各列を結合してテキストを作成
        chunks = []
        for index, row in df.iterrows():
            try:
                # 各行をテキストに変換
                text = f"{row['施設名']}は{row['大カテゴリ']}の{row['中カテゴリ']}です。"
                if text.strip():
                    # NaN値を適切に処理し、型変換を確実に行う
                    metadata = {
                        "main_category": str(row['大カテゴリ']) if pd.notna(row['大カテゴリ']) else "",
                        "sub_category": str(row['中カテゴリ']) if pd.notna(row['中カテゴリ']) else "",
                        "facility_name": str(row['施設名']) if pd.notna(row['施設名']) else "",
                        "latitude": float(row['緯度']) if pd.notna(row['緯度']) else 0.0,
                        "longitude": float(row['経度']) if pd.notna(row['経度']) else 0.0,
                        "walking_distance": int(float(row['徒歩距離'])) if pd.notna(row['徒歩距離']) else 0,
                        "walking_minutes": int(float(row['徒歩分数'])) if pd.notna(row['徒歩分数']) else 0,
                        "straight_distance": int(float(row['直線距離'])) if pd.notna(row['直線距離']) else 0
                    }
                    
                    # デバッグ情報の表示
                    st.write(f"行 {index + 1} のメタデータ:")
                    st.json(metadata)
                    
                    chunks.append({
                        "id": f"csv_{index}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "text": text,
                        "metadata": metadata
                    })
            except Exception as e:
                st.error(f"行 {index + 1} の処理中にエラーが発生しました: {str(e)}")
                continue
        
        if not chunks:
            raise ValueError("有効なデータが1件も見つかりませんでした。")
            
        return chunks
    except Exception as e:
        raise ValueError(f"CSVファイルの処理に失敗しました: {str(e)}")

def analyze_text_category(text):
    """
    テキストの内容からカテゴリを分析する関数
    """
    # 各カテゴリのスコアを初期化
    category_scores = {category: 0 for category in CATEGORY_KEYWORDS.keys()}
    
    # 各サブカテゴリのスコアを初期化
    subcategory_scores = {}
    for main_category, data in CATEGORY_KEYWORDS.items():
        for subcategory in data["sub_categories"].keys():
            subcategory_scores[subcategory] = 0
    
    # テキストを小文字に変換
    text_lower = text.lower()
    
    # 各カテゴリのキーワードをチェック
    for main_category, data in CATEGORY_KEYWORDS.items():
        # メインカテゴリのキーワードをチェック
        for keyword in data["keywords"]:
            if keyword.lower() in text_lower:
                category_scores[main_category] += 1
        
        # サブカテゴリのキーワードをチェック
        for subcategory, keywords in data["sub_categories"].items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    subcategory_scores[subcategory] += 1
    
    # 最もスコアの高いメインカテゴリを選択
    main_category = max(category_scores.items(), key=lambda x: x[1])[0]
    
    # 最もスコアの高いサブカテゴリを選択
    subcategory = max(subcategory_scores.items(), key=lambda x: x[1])[0]
    
    # 判定結果を返す
    return {
        "main_category": main_category,
        "subcategory": subcategory,
        "scores": {
            "main_categories": category_scores,
            "subcategories": subcategory_scores
        }
    }

def process_text_file(file_content, metadata):
    """
    テキストファイルを処理する関数
    """
    # テキストをチャンクに分割
    chunks = split_text_into_chunks(file_content)
    
    # 各チャンクを処理
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        # カテゴリを分析
        category_result = analyze_text_category(chunk)
        
        # 一意のIDを生成
        chunk_id = f"text_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
        
        # メタデータを更新（Pineconeの期待する形式に合わせる）
        chunk_metadata = {
            "city": metadata.get("municipality", ""),  # municipalityをcityとして保存
            "created_date": metadata.get("creation_date", DEFAULT_CREATION_DATE),
            "facility_name": "",
            "filename": metadata.get("filename", ""),  # ファイル名を追加
            "latitude": 0.0,
            "longitude": 0.0,
            "main_category": category_result["main_category"],
            "source": metadata.get("source", ""),
            "straight_distance": 0,
            "sub_category": category_result["subcategory"]  # subcategoryをsub_categoryとして保存
        }
        
        processed_chunks.append({
            "id": chunk_id,  # ルートレベルのid
            "text": chunk,
            "metadata": chunk_metadata,
            "category_result": category_result  # カテゴリ判定結果を追加
        })
    
    return processed_chunks

def render_file_upload(pinecone_service: PineconeService):
    """ファイルアップロード機能のUIを表示"""
    st.title("ファイルアップロード")
    st.write("テキストファイルをアップロードして、Pineconeデータベースに保存します。")
    
    uploaded_file = st.file_uploader("テキストファイルをアップロード", type=['txt', 'csv'])
    
    if uploaded_file is not None:
        # ファイルの種類に応じて処理を分岐
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            # CSVファイルの場合はメタデータ入力フォームを表示しない
            if st.button("データベースに保存"):
                try:
                    with st.spinner("ファイルを処理中..."):
                        chunks = process_csv_file(uploaded_file)
                        st.write(f"ファイルを{len(chunks)}個のチャンクに分割しました")
                        
                        with st.spinner("Pineconeにアップロード中..."):
                            pinecone_service.upload_chunks(chunks)
                            st.success("アップロードが完了しました！")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
        else:
            # テキストファイルの場合はメタデータ入力フォームを表示
            st.subheader("メタデータ入力")
            
            # 市区町村の選択
            city = st.selectbox(
                "市区町村",
                METADATA_CATEGORIES["市区町村"],
                index=None,
                placeholder="市区町村を選択してください（必須）"
            )
            
            # ソース元の入力
            source = st.text_input(
                "ソース元",
                placeholder="ソース元を入力してください（必須）"
            )
            
            # アップロード日（自動設定）
            upload_date = datetime.now()
            
            if st.button("データベースに保存"):
                try:
                    # 必須項目のチェック
                    if not all([city, source]):
                        st.error("市区町村とソース元は必須項目です。")
                        return
                        
                    with st.spinner("ファイルを処理中..."):
                        file_content = read_file_content(uploaded_file)
                        chunks = process_text_file(file_content, {
                            "municipality": city,
                            "source": source,
                            "creation_date": upload_date.isoformat(),
                            "filename": uploaded_file.name  # ファイル名を追加
                        })
                        
                        st.write(f"ファイルを{len(chunks)}個のチャンクに分割しました")
                        
                        # カテゴリ判定結果を表示
                        st.subheader("カテゴリ判定結果")
                        for i, chunk in enumerate(chunks, 1):
                            st.write(f"チャンク {i}:")
                            st.write(f"メインカテゴリ: {chunk['category_result']['main_category']}")
                            st.write(f"サブカテゴリ: {chunk['category_result']['subcategory']}")
                            st.write("---")
                        
                        # チャンクの内容を表示
                        st.subheader("チャンクの内容")
                        for i, chunk in enumerate(chunks, 1):
                            st.write(f"チャンク {i}:")
                            st.text(chunk["text"])
                            st.write("---")
                        
                        with st.spinner("Pineconeにアップロード中..."):
                            pinecone_service.upload_chunks(chunks)
                            st.success("アップロードが完了しました！")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}") 