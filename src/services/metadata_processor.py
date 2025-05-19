from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from src.config.settings import OPENAI_API_KEY
import json

@dataclass
class MetadataField:
    """メタデータフィールドの定義"""
    name: str
    description: str
    required: bool = False

class MetadataProcessor:
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in settings")
        
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=OPENAI_API_KEY
        )
        
        # 質問タイプごとのメタデータフィールド定義
        self.metadata_fields = {
            "facility": [
                MetadataField("name", "施設名", True),
                MetadataField("address", "住所", True),
                MetadataField("distance", "距離", True),
                MetadataField("additional_info", "その他の情報")
            ],
            "area": [
                MetadataField("area_name", "地域名", True),
                MetadataField("safety", "治安状況", True),
                MetadataField("transportation", "交通アクセス", True),
                MetadataField("education", "教育環境"),
                MetadataField("additional_info", "その他の特徴")
            ],
            "property": [
                MetadataField("property_name", "物件名", True),
                MetadataField("price", "価格", True),
                MetadataField("layout", "間取り", True),
                MetadataField("area", "面積"),
                MetadataField("facilities", "設備"),
                MetadataField("additional_info", "その他の特徴")
            ]
        }

    def extract_metadata(self, question_type: str, text: str) -> Dict[str, Any]:
        """テキストからメタデータを抽出"""
        if question_type not in self.metadata_fields:
            raise ValueError(f"Unknown question type: {question_type}")
        
        fields = self.metadata_fields[question_type]
        field_examples = "\n".join([f'    "{field.name}": "値の例"' for field in fields])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""以下のテキストから、{question_type}に関する情報を抽出してください。
必要なフィールド:
{chr(10).join([f"- {field.name}: {field.description} {'(必須)' if field.required else ''}" for field in fields])}

以下の形式のJSONで出力してください：
{{{{
{field_examples}
}}}}

注意：
- 必須フィールドは必ず含めてください
- 値が不明な場合は空文字列（""）を使用してください
- 追加情報は additional_info フィールドに含めてください
- 複数の情報がある場合は、最初の情報のみを抽出してください"""),
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
            return metadata
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse metadata: {str(e)}\nResponse text: {response_text}")

    def validate_metadata(self, question_type: str, metadata: Dict[str, Any]) -> bool:
        """メタデータの検証"""
        if question_type not in self.metadata_fields:
            return False
        
        fields = self.metadata_fields[question_type]
        required_fields = [field.name for field in fields if field.required]
        
        return all(field in metadata for field in required_fields)

    def get_metadata_fields(self, question_type: str) -> List[MetadataField]:
        """質問タイプに応じたメタデータフィールドを取得"""
        if question_type not in self.metadata_fields:
            raise ValueError(f"Unknown question type: {question_type}")
        return self.metadata_fields[question_type] 