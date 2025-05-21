from typing import Dict, Any, List
from dataclasses import dataclass
from langchain.prompts import ChatPromptTemplate

@dataclass
class ResponseTemplate:
    """回答テンプレートの基本クラス"""
    template: str
    required_fields: List[str]
    description: str

class ResponseTemplates:
    def __init__(self):
        self.templates = {
            "facility": ResponseTemplate(
                template="""{name}についてお調べしました。

場所は{address}にあります。
{distance}の場所にあります。

{additional_info}

他に気になることはありますか？""",
                required_fields=["name", "address", "distance"],
                description="施設に関する質問への回答テンプレート"
            ),
            "area": ResponseTemplate(
                template="""{area_name}の地域情報についてお伝えします。

治安状況は{safety}です。
交通アクセスは{transportation}です。
教育環境は{education}です。

{additional_info}

他に気になることはありますか？""",
                required_fields=["area_name", "safety", "transportation"],
                description="地域情報に関する質問への回答テンプレート"
            ),
            "property": ResponseTemplate(
                template="""{property_name}の物件情報についてお伝えします。

価格は{price}です。
間取りは{layout}です。
面積は{area}です。
設備は{facilities}です。

{additional_info}

他に気になることはありますか？""",
                required_fields=["property_name", "price", "layout"],
                description="物件情報に関する質問への回答テンプレート"
            ),
            "comparison": ResponseTemplate(
                template="""{property1_name}と{property2_name}の比較情報をお伝えします。

価格比較：
{property1_name}: {property1_price}
{property2_name}: {property2_price}

間取り比較：
{property1_name}: {property1_layout}
{property2_name}: {property2_layout}

主な違い：
{differences}

{additional_info}

他に気になることはありますか？""",
                required_fields=["property1_name", "property2_name", "property1_price", "property2_price", "property1_layout", "property2_layout", "differences"],
                description="物件比較に関する質問への回答テンプレート"
            ),
            "price_analysis": ResponseTemplate(
                template="""{area_name}の価格分析についてお伝えします。

平均価格：{average_price}
価格帯分布：
{price_distribution}

市場動向：
{market_trend}

{additional_info}

他に気になることはありますか？""",
                required_fields=["area_name", "average_price", "price_distribution", "market_trend"],
                description="価格分析に関する質問への回答テンプレート"
            ),
            "location": ResponseTemplate(
                template="""{property_name}の立地条件についてお伝えします。

最寄り駅：{nearest_station}（徒歩{walking_time}分）
周辺施設：
{facilities}

アクセス：
{access}

{additional_info}

他に気になることはありますか？""",
                required_fields=["property_name", "nearest_station", "walking_time", "facilities", "access"],
                description="立地条件に関する質問への回答テンプレート"
            ),
            "investment": ResponseTemplate(
                template="""{property_name}の投資分析についてお伝えします。

想定利回り：{expected_yield}
投資リスク：{risk_level}
市場性：{market_potential}

投資のポイント：
{investment_points}

{additional_info}

他に気になることはありますか？""",
                required_fields=["property_name", "expected_yield", "risk_level", "market_potential", "investment_points"],
                description="投資分析に関する質問への回答テンプレート"
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

    def get_available_templates(self) -> Dict[str, str]:
        """利用可能なテンプレートの一覧を取得"""
        return {name: template.description for name, template in self.templates.items()} 