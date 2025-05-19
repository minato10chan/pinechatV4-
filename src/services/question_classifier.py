from typing import Literal, Optional
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from src.config.settings import OPENAI_API_KEY

class QuestionType(BaseModel):
    """質問タイプを表すモデル"""
    type: Literal["facility", "area", "property"] = Field(
        description="質問のタイプ: facility(施設情報), area(地域情報), property(物件情報)"
    )
    confidence: float = Field(
        description="判別の確信度（0.0-1.0）",
        ge=0.0,
        le=1.0
    )
    reason: str = Field(
        description="判別理由の説明"
    )

class QuestionClassifier:
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in settings")
        
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=OPENAI_API_KEY
        )
        self.parser = PydanticOutputParser(pydantic_object=QuestionType)
        
        # フォーマット指示を取得
        format_instructions = self.parser.get_format_instructions()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは質問のタイプを判別する専門家です。
以下の3つのカテゴリーに分類してください：

1. facility (施設情報)
- コンビニ、スーパー、病院などの施設に関する質問
- 位置情報や距離情報が重要な場合
- 例：「最寄りのコンビニはどこ？」「近くに病院はある？」

2. area (地域情報)
- 治安、交通、教育などの地域特性に関する質問
- 定性的な情報が重要な場合
- 例：「この地域の治安はどう？」「交通の便は良い？」

3. property (物件情報)
- 価格、間取り、設備などの物件特性に関する質問
- 数値情報と定性的情報の両方が重要な場合
- 例：「この物件の価格は？」「間取りはどうなってる？」

{format_instructions}"""),
            ("human", "{question}")
        ])

    def classify(self, question: str) -> QuestionType:
        """質問のタイプを判別する"""
        chain = self.prompt | self.llm | self.parser
        return chain.invoke({
            "question": question,
            "format_instructions": self.parser.get_format_instructions()
        })

    def get_question_type(self, question: str) -> Optional[str]:
        """質問タイプを取得（確信度が0.7以上の場合のみ）"""
        result = self.classify(question)
        if result.confidence >= 0.7:
            return result.type
        return None 