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
from typing import List

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

def analyze_text_category(text: str) -> dict:
    """
    テキストの内容からカテゴリを分析する関数
    
    Args:
        text (str): 分析するテキスト
    
    Returns:
        dict: カテゴリ分析結果（カテゴリと信頼度スコアを含む）
    """
    # カテゴリごとのスコアを初期化
    category_scores = {
        "物件概要": 0,
        "地域特性・街のプロフィール": 0
    }
    
    # サブカテゴリごとのスコアを初期化
    subcategory_scores = {
        "物件概要": {
            "概要・エリア区分": 0,
            "価格・費用": 0,
            "間取り・設備": 0,
            "契約・手続き": 0
        },
        "地域特性・街のプロフィール": {
            "概要・エリア区分": 0,
            "交通アクセス": 0,
            "街の歴史・地域史": 0,
            "自然・環境": 0,
            "観光・グルメ": 0
        }
    }
    
    # テキストを行ごとに分割
    lines = text.split('\n')
    
    # 時刻表特有のキーワード（より具体的な表現に）
    timetable_keywords = [
        "時刻表", "発車", "到着", "上り", "下り", "平日", "土休日", "号",
        "始発", "終電", "運行", "ダイヤ", "列車", "電車", "快速", "普通",
        "各駅停車", "区間", "方面", "行き", "駅", "バス停", "停留所"
    ]
    
    # 歴史・文化関連のキーワードを追加
    history_culture_keywords = [
        "歴史", "史跡", "文化財", "重要文化財", "国宝", "遺跡",
        "城", "神社", "寺院", "仏閣", "古墳", "博物館", "資料館",
        "伝統", "文化", "祭り", "行事", "風習", "伝説", "物語",
        "偉人", "人物", "発祥", "起源", "由来", "地名", "街道",
        "市制", "施行", "周年", "記念", "制定", "答申", "告示",
        "和歌", "歌人", "伝説", "逸話", "故事", "由来", "歴史的",
        "文化的", "伝統的", "風習", "習俗", "慣習", "風俗", "民俗"
    ]
    
    # キーワードマッピング
    keyword_mapping = {
        "物件概要": {
            "概要・エリア区分": [
                "物件", "マンション", "アパート", "一戸建て", "土地", "駐車場",
                "エリア", "地区", "地域", "区画", "街区", "敷地", "建物",
                "構造", "階数", "築年数", "新築", "中古", "リフォーム"
            ],
            "価格・費用": [
                "価格", "費用", "家賃", "管理費", "敷金", "礼金", "仲介手数料",
                "共益費", "光熱費", "水道代", "電気代", "ガス代", "保険料",
                "税金", "固定資産税", "都市計画税", "修繕積立金", "更新料"
            ],
            "間取り・設備": [
                "間取り", "LDK", "DK", "K", "設備", "家具", "家電", "エアコン",
                "バス", "トイレ", "キッチン", "洗面所", "収納", "クローゼット",
                "ベランダ", "バルコニー", "ロフト", "地下室", "屋上", "庭",
                "駐車場", "駐輪場", "宅配ボックス", "インターホン", "セキュリティ"
            ],
            "契約・手続き": [
                "契約", "入居", "退去", "更新", "手続き", "書類", "保証人",
                "連帯保証人", "審査", "内見", "申込", "入居審査", "契約書",
                "重要事項説明", "火災保険", "家財保険", "原状回復", "明渡し"
            ]
        },
        "地域特性・街のプロフィール": {
            "概要・エリア区分": [
                "エリア", "地区", "地域", "区画", "街区", "町", "丁目",
                "住宅地", "商業地", "工業地", "文教地区", "オフィス街",
                "再開発", "都市計画", "用途地域", "容積率", "建蔽率"
            ],
            "交通アクセス": [
                "JR", "線", "駅", "所要時間", "分", "直通", "運転", "急行", "特急",
                "バス", "車", "アクセス", "交通", "路線", "新宿", "池袋", "渋谷",
                "横浜", "大宮", "川越", "本川越", "新木場", "八王子", "海老名",
                "元町", "中華街", "新横浜", "Fライナー", "小江戸号", "バス停",
                "高速道路", "IC", "JCT", "空港", "港", "フェリー", "タクシー"
            ] + timetable_keywords,
            "街の歴史・地域史": history_culture_keywords,
            "自然・環境": [
                "公園", "緑地", "庭園", "植物園", "森林", "山", "川", "湖",
                "海", "海岸", "砂浜", "岬", "渓谷", "滝", "温泉", "湧水",
                "自然", "環境", "生態系", "動植物", "野鳥", "昆虫", "花",
                "桜", "紅葉", "四季", "気候", "天気", "風", "光", "空気"
            ],
            "観光・グルメ": [
                "観光", "観光地", "名所", "旧跡", "見所", "スポット",
                "レジャー", "遊園地", "水族館", "動物園", "美術館", "博物館",
                "ショッピング", "商業施設", "モール", "商店街", "市場",
                "グルメ", "飲食店", "レストラン", "カフェ", "居酒屋", "バー",
                "特産品", "名物", "郷土料理", "スイーツ", "お土産", "物産"
            ]
        }
    }
    
    # 時刻表判定のためのフラグ
    is_timetable = False
    
    # 時刻表の特徴的なパターン（より厳密な条件に）
    timetable_patterns = [
        r'^\d{1,2}:\d{2}$',  # 時刻のパターン（例：6:02）- 行全体が時刻の場合のみ
        r'発車|到着',        # 発着の表示
        r'上り|下り',        # 上り下りの表示
        r'平日|土休日',      # 運行区分
        r'^\d+号$'          # 列車番号 - 行全体が番号の場合のみ
    ]
    
    # 各行を分析
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 歴史・文化関連のキーワードチェック（優先度を上げる）
        history_culture_count = sum(1 for keyword in history_culture_keywords if keyword in line)
        if history_culture_count > 0:
            category_scores["地域特性・街のプロフィール"] += history_culture_count * 2
            subcategory_scores["地域特性・街のプロフィール"]["街の歴史・地域史"] += history_culture_count * 2
            continue
        
        # 時刻表特有のキーワードチェック（より厳密に）
        if any(keyword in line for keyword in timetable_keywords):
            # 時刻表のパターンも同時に確認
            pattern_matches = sum(1 for pattern in timetable_patterns if re.search(pattern, line))
            if pattern_matches >= 2:  # 2つ以上のパターンが一致した場合のみ
                is_timetable = True
                category_scores["地域特性・街のプロフィール"] += 3
                subcategory_scores["地域特性・街のプロフィール"]["交通アクセス"] += 3
            continue
        
        # 通常のキーワードチェック
        for main_category, subcategories in keyword_mapping.items():
            for subcategory, keywords in subcategories.items():
                keyword_count = sum(1 for keyword in keywords if keyword in line)
                if keyword_count > 0:
                    # サブカテゴリごとに重み付けを調整
                    weight = 2 if subcategory == "街の歴史・地域史" else 1
                    category_scores[main_category] += keyword_count * weight
                    subcategory_scores[main_category][subcategory] += keyword_count * weight
    
    # 時刻表と判定された場合でも、歴史・文化関連のスコアが高い場合はそちらを優先
    if is_timetable and subcategory_scores["地域特性・街のプロフィール"]["街の歴史・地域史"] > subcategory_scores["地域特性・街のプロフィール"]["交通アクセス"]:
        is_timetable = False
    
    # 時刻表と判定された場合は、交通アクセスカテゴリに設定
    if is_timetable:
        return {
            "main_category": "地域特性・街のプロフィール",
            "sub_category": "交通アクセス",
            "confidence_score": 0.9
        }
    
    # 通常の判定
    main_category = max(category_scores.items(), key=lambda x: x[1])[0]
    subcategory = max(subcategory_scores[main_category].items(), key=lambda x: x[1])[0]
    
    # 信頼度スコアの計算
    total_score = sum(category_scores.values())
    if total_score == 0:
        confidence_score = 0.0
    else:
        # 選択されたカテゴリのスコアを全体のスコアで割って信頼度を計算
        confidence_score = category_scores[main_category] / total_score
    
    return {
        "main_category": main_category,
        "sub_category": subcategory,
        "confidence_score": confidence_score
    }

def process_text_file(file_content: str, metadata: dict) -> List[dict]:
    """
    テキストファイルを処理してチャンクに分割し、メタデータを付与する関数
    
    Args:
        file_content (str): テキストファイルの内容
        metadata (dict): メタデータ
    
    Returns:
        List[dict]: チャンクとメタデータのリスト
    """
    # テキストをチャンクに分割
    chunks = split_text_into_chunks(file_content)
    
    # 各チャンクにメタデータを付与
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        # チャンクのカテゴリを分析
        category_analysis = analyze_text_category(chunk)
        
        # チャンクのIDを生成
        chunk_id = f"{metadata.get('id', 'chunk')}_{i}"
        
        # チャンクのメタデータを作成
        chunk_metadata = {
            "id": chunk_id,
            "chunk_id": chunk_id,
            "filename": metadata.get("filename", ""),
            "main_category": category_analysis["main_category"],
            "sub_category": category_analysis["sub_category"],
            "confidence_score": category_analysis["confidence_score"],
            "city": metadata.get("municipality", ""),
            "source": metadata.get("source", ""),
            "created_date": metadata.get("creation_date", ""),
            "upload_date": metadata.get("upload_date", datetime.now().isoformat())
        }
        
        processed_chunks.append({
            "id": chunk_id,
            "text": chunk,
            "metadata": chunk_metadata
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
                        # ファイルの一意のIDを生成
                        file_id = f"{uploaded_file.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        chunks = process_text_file(file_content, {
                            "id": file_id,
                            "municipality": city,
                            "source": source,
                            "creation_date": upload_date.isoformat(),
                            "upload_date": upload_date.isoformat(),
                            "filename": uploaded_file.name
                        })
                        
                        st.write(f"ファイルを{len(chunks)}個のチャンクに分割しました")
                        
                        # デバッグ情報の表示
                        st.write("メタデータの例:")
                        if chunks:
                            st.json(chunks[0]["metadata"])
                        
                        with st.spinner("Pineconeにアップロード中..."):
                            pinecone_service.upload_chunks(chunks)
                            st.success("アップロードが完了しました！")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}") 