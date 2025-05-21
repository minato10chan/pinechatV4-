from typing import Dict, Any, List
from dataclasses import dataclass
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json
import os

@dataclass
class MetadataField:
    """メタデータフィールドの定義"""
    name: str
    description: str
    required: bool = False
    type: str = "string"
    example: str = ""

class MetadataProcessor:
    def __init__(self):
        """メタデータプロセッサの初期化"""
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="gpt-3.5-turbo",
            temperature=0
        )
        
        # メタデータフィールドの定義
        self.metadata_fields = {
            "facility": [
                MetadataField("name", "施設名", True),
                MetadataField("address", "住所", True),
                MetadataField("distance", "最寄り駅からの距離", True),
                MetadataField("category", "施設カテゴリ", False),
                MetadataField("business_hours", "営業時間", False),
                MetadataField("contact", "連絡先", False),
                MetadataField("additional_info", "追加情報", False)
            ],
            "area": [
                MetadataField("area_name", "地域名", True),
                MetadataField("safety", "治安状況", True),
                MetadataField("transportation", "交通アクセス", True),
                MetadataField("education", "教育環境", False),
                MetadataField("population", "人口", False),
                MetadataField("crime_rate", "犯罪率", False),
                MetadataField("additional_info", "追加情報", False)
            ],
            "property": [
                MetadataField("property_name", "物件名", True),
                MetadataField("price", "価格", True),
                MetadataField("layout", "間取り", True),
                MetadataField("area", "面積", False),
                MetadataField("facilities", "設備", False),
                MetadataField("age", "築年数", False),
                MetadataField("additional_info", "追加情報", False)
            ],
            "comparison": [
                MetadataField("property1_name", "物件1の名前", True),
                MetadataField("property2_name", "物件2の名前", True),
                MetadataField("property1_price", "物件1の価格", True),
                MetadataField("property2_price", "物件2の価格", True),
                MetadataField("property1_layout", "物件1の間取り", True),
                MetadataField("property2_layout", "物件2の間取り", True),
                MetadataField("differences", "主な違い", True),
                MetadataField("additional_info", "追加情報", False)
            ],
            "price_analysis": [
                MetadataField("area_name", "地域名", True),
                MetadataField("average_price", "平均価格", True),
                MetadataField("price_distribution", "価格帯分布", True),
                MetadataField("market_trend", "市場動向", True),
                MetadataField("price_history", "価格推移", False),
                MetadataField("additional_info", "追加情報", False)
            ],
            "location": [
                MetadataField("property_name", "物件名", True),
                MetadataField("nearest_station", "最寄り駅", True),
                MetadataField("walking_time", "徒歩時間", True),
                MetadataField("facilities", "周辺施設", True),
                MetadataField("access", "アクセス", True),
                MetadataField("additional_info", "追加情報", False)
            ],
            "investment": [
                MetadataField("property_name", "物件名", True),
                MetadataField("expected_yield", "想定利回り", True),
                MetadataField("risk_level", "投資リスク", True),
                MetadataField("market_potential", "市場性", True),
                MetadataField("investment_points", "投資のポイント", True),
                MetadataField("additional_info", "追加情報", False)
            ]
        }

    def extract_metadata(self, question_type: str, text: str) -> Dict[str, Any]:
        """テキストからメタデータを抽出"""
        if question_type not in self.metadata_fields:
            raise ValueError(f"Unknown question type: {question_type}")
        
        fields = self.metadata_fields[question_type]
        field_examples = "\n".join([
            f'    "{field.name}": "{field.example or "値の例"}"'
            for field in fields
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""以下のテキストから、{question_type}に関する情報を抽出してください。
必要なフィールド:
{chr(10).join([f"- {field.name}: {field.description} {'(必須)' if field.required else ''}" for field in fields])}

以下の形式のJSONで出力してください：
{{
{field_examples}
}}

注意：
- 必須フィールドは必ず含めてください
- 値が不明な場合は空文字列（""）を使用してください
- 追加情報は additional_info フィールドに含めてください
- 複数の情報がある場合は、最初の情報のみを抽出してください
- 数値データは適切な単位を含めてください（例：㎡、万円、分など）"""),
            ("human", "{text}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"text": text})
        
        try:
            # AIMessageからテキストを取得してJSONをパース
            response_text = response.content
            
            # 最初のJSONオブジェクトのみを抽出
            first_json_start = response_text.find("{")
            first_json_end = response_text.find("}", first_json_start) + 1
            if first_json_start == -1 or first_json_end == 0:
                raise ValueError("No JSON object found in response")
            
            json_text = response_text[first_json_start:first_json_end]
            metadata = json.loads(json_text)
            
            # 必須フィールドの検証
            missing_fields = [
                field.name for field in fields
                if field.required and (field.name not in metadata or not metadata[field.name])
            ]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            return metadata
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse metadata: {str(e)}\nResponse text: {response_text}")

    def validate_metadata(self, question_type: str, metadata: Dict[str, Any]) -> bool:
        """メタデータの検証"""
        if question_type not in self.metadata_fields:
            raise ValueError(f"Unknown question type: {question_type}")
        
        fields = self.metadata_fields[question_type]
        
        # 必須フィールドの検証
        for field in fields:
            if field.required and (field.name not in metadata or not metadata[field.name]):
                return False
        
        return True

    def format_metadata(self, question_type: str, metadata: Dict[str, Any]) -> str:
        """メタデータを整形して文字列として返す"""
        if question_type not in self.metadata_fields:
            raise ValueError(f"Unknown question type: {question_type}")
        
        fields = self.metadata_fields[question_type]
        formatted_parts = []
        
        for field in fields:
            if field.name in metadata and metadata[field.name]:
                formatted_parts.append(f"{field.description}: {metadata[field.name]}")
        
        return "\n".join(formatted_parts) 