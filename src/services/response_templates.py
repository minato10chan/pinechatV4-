from typing import Dict, Any, List
from dataclasses import dataclass
from langchain.prompts import ChatPromptTemplate

@dataclass
class ResponseTemplate:
    """回答テンプレートの基本クラス"""
    template: str
    required_fields: List[str]

class ResponseTemplates:
    def __init__(self):
        self.templates = {
            "facility": ResponseTemplate(
                template="""{name}についてお調べしました。

場所は{address}にあります。
{distance}の場所にあります。

{additional_info}

他に気になることはありますか？""",
                required_fields=["name", "address", "distance"]
            ),
            "area": ResponseTemplate(
                template="""{area_name}の地域情報についてお伝えします。

治安状況は{safety}です。
交通アクセスは{transportation}です。
教育環境は{education}です。

{additional_info}

他に気になることはありますか？""",
                required_fields=["area_name", "safety", "transportation"]
            ),
            "property": ResponseTemplate(
                template="""{property_name}の物件情報についてお伝えします。

価格は{price}です。
間取りは{layout}です。
面積は{area}です。
設備は{facilities}です。

{additional_info}

他に気になることはありますか？""",
                required_fields=["property_name", "price", "layout"]
            )
        }

    def get_template(self, question_type: str) -> ResponseTemplate:
        """質問タイプに応じたテンプレートを取得"""
        if question_type not in self.templates:
            raise ValueError(f"Unknown question type: {question_type}")
        return self.templates[question_type]

    def format_response(self, question_type: str, data: Dict[str, Any]) -> str:
        """テンプレートを使用して回答を生成"""
        template = self.get_template(question_type)
        
        # 必須フィールドのチェック
        missing_fields = [field for field in template.required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # テンプレートにデータを適用
        return template.template.format(**data) 