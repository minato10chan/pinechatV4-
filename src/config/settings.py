"""
アプリケーションの設定を管理するモジュール
"""

import streamlit as st
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# 環境変数の読み込み
load_dotenv()

# API Keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") or st.secrets.get("pinecone_key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("openai_api_key")

# Pinecone Settings
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME") or st.secrets.get("index_name")
PINECONE_ASSISTANT_NAME = os.getenv("PINECONE_ASSISTANT_NAME") or st.secrets.get("assistant_name")

# Text Processing Settings
CHUNK_SIZE = 500  # テキストを分割する際の1チャンクあたりの文字数
BATCH_SIZE = 100  # Pineconeへのアップロード時のバッチサイズ

# OpenAI Settings
EMBEDDING_MODEL = "text-embedding-ada-002"  # 使用する埋め込みモデル

# Search Settings
DEFAULT_TOP_K = 10  # デフォルトの検索結果数
SIMILARITY_THRESHOLD = 0.7  # 類似度のしきい値（0-1の範囲）

# Metadata Settings
DEFAULT_CREATION_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # メタデータの作成日が空の場合のデフォルト値

def get_metadata_creation_date(metadata):
    """
    メタデータの作成日を取得する関数
    作成日が空の場合は現在の日時を返す
    """
    if not metadata or "creation_date" not in metadata or not metadata["creation_date"]:
        return DEFAULT_CREATION_DATE
    return metadata["creation_date"]

# Prompt Settings
# プロンプトテンプレートの保存と読み込み
PROMPT_TEMPLATES_FILE = "prompt_templates.json"

def save_prompt_templates(templates):
    """プロンプトテンプレートを保存"""
    with open(PROMPT_TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)

def load_prompt_templates():
    """プロンプトテンプレートを読み込み"""
    if os.path.exists(PROMPT_TEMPLATES_FILE):
        with open(PROMPT_TEMPLATES_FILE, "r", encoding="utf-8") as f:
            templates = json.load(f)
            # デフォルトテンプレートを取得
            default_template = next((t for t in templates if t["name"] == "デフォルト"), None)
            if default_template:
                return templates, default_template["system_prompt"], default_template["response_template"]
    return [], "", ""

# プロンプトテンプレートの読み込み
PROMPT_TEMPLATES, DEFAULT_SYSTEM_PROMPT, DEFAULT_RESPONSE_TEMPLATE = load_prompt_templates()

# メタデータ設定
METADATA_CATEGORIES = {
    "市区町村": [
        "川越市",
        "さいたま市",
        "千葉市",
        "横浜市",
        "川崎市",
        "相模原市",
    ]
}

# カテゴリのキーワードマッピング
CATEGORY_KEYWORDS = {
    "物件概要": {
        "keywords": [
            "物件", "建物", "完成", "販売", "建築", "間取り", "設備", "価格", "契約",
            "マンション", "アパート", "一戸建て", "土地", "分譲", "賃貸", "新築", "中古",
            "リフォーム", "リノベーション", "デザイン", "仕様", "構造", "階数", "面積",
            "坪数", "専有面積", "敷地面積", "建蔽率", "容積率", "駐車場", "駐輪場"
        ],
        "sub_categories": {
            "完成時期": ["完成", "竣工", "入居", "引渡し", "引き渡し", "着工", "建設", "建築", "新築"],
            "販売開始": ["販売", "分譲", "募集", "受付", "先行", "先行販売", "先行分譲", "先行募集"],
            "建築確認": ["建築", "確認", "申請", "許可", "届出", "検査", "確認申請", "建築確認申請"],
            "間取り・仕様": [
                "間取り", "LDK", "部屋数", "寝室", "リビング", "ダイニング", "キッチン",
                "バスルーム", "トイレ", "洗面所", "クローゼット", "収納", "ロフト", "ベランダ",
                "バルコニー", "テラス", "庭", "ガレージ", "車庫"
            ],
            "設備・オプション": [
                "設備", "オプション", "仕様", "システムキッチン", "浴室", "洗面台", "トイレ",
                "エアコン", "床暖房", "温水", "給湯", "ガス", "電気", "インターネット",
                "宅配ボックス", "オートロック", "セキュリティ", "防犯", "防音", "断熱"
            ],
            "デザイン・外観": [
                "デザイン", "外観", "外装", "内装", "カラー", "素材", "タイル", "サイディング",
                "ガラス", "アルミ", "木目", "モダン", "クラシック", "和風", "洋風", "スタイル"
            ],
            "建築会社・デベロッパー": [
                "建築会社", "デベロッパー", "施工", "設計", "監理", "工事", "請負", "ゼネコン",
                "ハウスメーカー", "不動産会社", "分譲会社", "販売会社"
            ],
            "価格・費用": [
                "価格", "費用", "コスト", "総額", "坪単価", "平米単価", "頭金", "ローン",
                "金利", "返済", "諸費用", "手数料", "税金", "固定資産税", "都市計画税",
                "管理費", "修繕積立金", "共益費"
            ],
            "資産価値・売却": [
                "資産価値", "売却", "投資", "利回り", "キャピタルゲイン", "インカムゲイン",
                "相場", "時価", "査定", "評価", "担保", "融資", "ローン", "借入"
            ],
            "契約・手続き": [
                "契約", "手続き", "申込", "申し込み", "予約", "内定", "決済", "引渡し",
                "引き渡し", "登記", "名義変更", "ローン審査", "融資", "住宅ローン"
            ]
        }
    },
    "地域特性・街のプロフィール": {
        "keywords": [
            "地域", "街", "人口", "歴史", "地理", "自然", "イベント", "都市", "治安", "景観",
            "エリア", "地区", "町", "区", "市", "県", "都道府県", "近隣", "周辺", "環境",
            "生活", "文化", "伝統", "祭り", "行事", "施設", "インフラ", "交通", "アクセス",
            "商業", "産業", "経済", "発展", "開発", "整備", "計画", "政策", "行政"
        ],
        "sub_categories": {
            "概要・エリア区分": [
                "エリア", "地区", "地域", "町", "区", "市", "県", "都道府県", "近隣", "周辺",
                "中心部", "郊外", "住宅地", "商業地", "工業地", "文教地区", "オフィス街"
            ],
            "人口・居住特性": [
                "人口", "居住", "世帯", "家族", "単身", "高齢者", "若者", "子育て", "外国人",
                "転入", "転出", "増加", "減少", "密度", "構成", "年齢", "性別", "職業"
            ],
            "街の歴史・地域史": [
                "歴史", "由来", "発展", "変遷", "文化", "伝統", "史跡", "名所", "旧跡",
                "遺跡", "文化財", "保存", "継承", "発祥", "起源", "開拓", "開発"
            ],
            "地理的特性": [
                "地理", "地形", "立地", "位置", "標高", "傾斜", "河川", "山", "海", "湖",
                "平野", "丘陵", "台地", "谷", "盆地", "気候", "気象", "災害", "防災"
            ],
            "自然環境": [
                "自然", "公園", "緑", "樹木", "花", "草", "水辺", "川", "池", "森", "林",
                "動植物", "生態系", "環境", "景観", "眺望", "ビュー", "日当たり", "風通し"
            ],
            "地域イベント・伝統行事": [
                "イベント", "祭り", "行事", "催し", "お祭り", "伝統", "文化", "芸能",
                "パフォーマンス", "展示", "発表", "競技", "大会", "フェスティバル"
            ],
            "都市連携・姉妹都市情報": [
                "連携", "姉妹都市", "交流", "協力", "提携", "パートナー", "ネットワーク",
                "国際", "海外", "友好", "支援", "協定", "協働", "共同"
            ],
            "治安・騒音・環境整備": [
                "治安", "騒音", "環境", "安全", "防犯", "犯罪", "事故", "災害", "防災",
                "衛生", "清潔", "整備", "管理", "維持", "改善", "対策", "条例", "規制"
            ],
            "風景・景観・街並み": [
                "景観", "風景", "街並み", "建物", "建築", "デザイン", "外観", "眺望",
                "ビュー", "シンボル", "ランドマーク", "名所", "旧跡", "保存", "整備"
            ],
            "観光・地元特産品・名産・グルメ": [
                "観光", "特産", "グルメ", "名産", "名物", "料理", "食材", "農産物",
                "海産物", "工芸品", "お土産", "レストラン", "カフェ", "飲食店", "商店",
                "市場", "ショッピング", "買い物"
            ]
        }
    }
} 