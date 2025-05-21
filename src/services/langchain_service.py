from typing import List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
import os
from ..config.settings import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    OPENAI_API_KEY,
    DEFAULT_TOP_K,
    SIMILARITY_THRESHOLD,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_RESPONSE_TEMPLATE
)

class LangChainService:
    def __init__(self, callback_manager=None):
        """LangChainサービスの初期化"""
        # チャットモデルの初期化
        self.llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            callback_manager=callback_manager
        )
        
        # 埋め込みモデルの初期化
        self.embeddings = OpenAIEmbeddings(
            api_key=OPENAI_API_KEY,
            model="text-embedding-ada-002"
        )
        
        # PineconeのAPIキーを環境変数に設定
        os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
        
        # Pineconeベクトルストアの初期化
        self.vectorstore = PineconeVectorStore.from_existing_index(
            index_name=PINECONE_INDEX_NAME,
            embedding=self.embeddings
        )
        
        # チャット履歴の初期化
        self.message_history = ChatMessageHistory()
        
        # デフォルトのプロンプトテンプレート
        self.system_prompt = DEFAULT_SYSTEM_PROMPT
        self.response_template = DEFAULT_RESPONSE_TEMPLATE

    def get_relevant_context(self, query: str, top_k: int = DEFAULT_TOP_K) -> Tuple[str, List[Dict[str, Any]]]:
        """クエリに関連する文脈を取得"""
        # 類似度検索を実行
        results = self.vectorstore.similarity_search_with_score(
            query,
            k=top_k
        )
        
        # 類似度スコアでフィルタリング
        filtered_results = [
            (doc, score) for doc, score in results
            if score >= SIMILARITY_THRESHOLD
        ]
        
        if not filtered_results:
            return "関連する情報が見つかりませんでした。", []
        
        # 文脈の構築
        context_parts = []
        search_details = []
        
        for doc, score in filtered_results:
            # メタデータの取得
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            # 文脈の追加
            context_parts.append(f"情報: {doc.page_content}")
            if metadata:
                context_parts.append(f"メタデータ: {metadata}")
            
            # 検索詳細の記録
            search_details.append({
                "content": doc.page_content,
                "score": score,
                "metadata": metadata
            })
        
        return "\n\n".join(context_parts), search_details

    def analyze_question_type(self, query: str) -> str:
        """質問のタイプを分析"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """以下の質問のタイプを分析し、最も適切なカテゴリを選択してください。
利用可能なカテゴリ：
- facility: 施設に関する質問
- area: 地域情報に関する質問
- property: 物件情報に関する質問
- comparison: 物件比較に関する質問
- price_analysis: 価格分析に関する質問
- location: 立地条件に関する質問
- investment: 投資分析に関する質問

回答は、上記のカテゴリ名のみを返してください。"""),
            ("human", "{query}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"query": query})
        return response.content.strip().lower()

    def get_response(self, query: str, system_prompt: str = None, response_template: str = None, property_info: str = None, chat_history: list = None) -> Tuple[str, Dict[str, Any]]:
        """クエリに対する応答を生成"""
        # プロンプトの設定
        system_prompt = system_prompt or self.system_prompt
        response_template = response_template or self.response_template
        
        # 質問タイプの分析
        question_type = self.analyze_question_type(query)
        
        # メッセージリストの作成
        messages = [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("system", "参照文脈:\n{context}")
        ]
        
        # 物件情報がある場合は追加
        if property_info:
            messages.append(("system", "物件情報:\n{property_info}"))
        
        # 質問タイプの追加
        messages.append(("system", f"質問タイプ: {question_type}"))
        
        # ユーザー入力の追加
        messages.append(("human", "{input}"))
        
        # プロンプトテンプレートの設定
        prompt = ChatPromptTemplate.from_messages(messages)
        
        # チェーンの初期化
        chain = prompt | self.llm
        
        # 関連する文脈を取得
        context, search_details = self.get_relevant_context(query)
        
        # チャット履歴を設定
        if chat_history:
            self.message_history.messages = []
            for role, content in chat_history:
                if role == "human":
                    self.message_history.add_user_message(content)
                elif role == "ai":
                    self.message_history.add_ai_message(content)
        
        # 応答を生成
        response = chain.invoke({
            "chat_history": self.message_history.messages,
            "context": context,
            "property_info": property_info or "物件情報はありません。",
            "input": query
        })
        
        # メッセージを履歴に追加
        self.message_history.add_user_message(query)
        self.message_history.add_ai_message(response.content)
        
        # 詳細情報の作成
        details = {
            "モデル": "GPT-3.5-turbo",
            "会話履歴": "有効",
            "質問タイプ": question_type,
            "文脈検索": {
                "検索結果数": len(search_details),
                "マッチしたチャンク": search_details
            },
            "プロンプト": {
                "システムプロンプト": system_prompt,
                "応答テンプレート": response_template
            },
            "物件情報": property_info or "物件情報はありません。",
            "会話履歴数": len(chat_history) if chat_history else 0
        }
        
        return response.content, details

    def clear_memory(self):
        """会話メモリをクリア"""
        self.message_history.clear() 