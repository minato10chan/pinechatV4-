import streamlit as st
from src.services.pinecone_service import PineconeService
from src.services.question_classifier import QuestionClassifier
from src.services.response_templates import ResponseTemplates
from src.services.metadata_processor import MetadataProcessor
from src.utils.error_handler import ErrorHandler, ErrorType

def render_agent(pinecone_service: PineconeService):
    st.title("Agent Mode")
    
    # サービスの初期化
    question_classifier = QuestionClassifier()
    response_templates = ResponseTemplates()
    metadata_processor = MetadataProcessor()
    error_handler = ErrorHandler()
    
    # ユーザー入力
    user_input = st.text_input("質問を入力してください", key="agent_input")
    
    if user_input:
        # 思考プロセスの表示
        st.subheader("🤔 思考プロセス")
        
        # タスクの分析
        st.write("1. タスクの分析")
        st.write(f"- 入力された質問: {user_input}")
        
        # 質問タイプの初期化
        question_type = None
        
        try:
            # 質問タイプの判別
            st.write("2. 質問タイプの判別")
            question_type = question_classifier.get_question_type(user_input)
            
            if question_type:
                st.write(f"- 質問タイプ: {question_type}")
                
                # Pineconeから関連情報を検索
                st.write("3. 関連情報の検索")
                search_results = pinecone_service.query(user_input, top_k=3)
                
                if search_results["matches"]:
                    # メタデータの抽出と検証
                    st.write("4. メタデータの処理")
                    metadata = metadata_processor.extract_metadata(
                        question_type,
                        "\n".join([match.metadata["text"] for match in search_results["matches"]])
                    )
                    
                    if metadata_processor.validate_metadata(question_type, metadata):
                        # 回答の生成
                        st.write("5. 回答の生成")
                        response = response_templates.format_response(question_type, metadata)
                        
                        # 回答の表示
                        st.subheader("📝 回答")
                        st.write(response)
                        
                        # ベクトルデータの詳細情報を表示
                        st.subheader("🔍 参考情報")
                        for i, match in enumerate(search_results["matches"], 1):
                            with st.expander(f"参考情報 {i} (スコア: {match.score:.2f})"):
                                st.write("### テキスト")
                                st.write(match.metadata["text"])
                                
                                st.write("### メタデータ")
                                for key, value in match.metadata.items():
                                    if key != "text":  # テキストは既に表示済み
                                        st.write(f"- {key}: {value}")
                    else:
                        error = error_handler.handle_error(
                            ErrorType.INSUFFICIENT_INFORMATION,
                            {"question_type": question_type}
                        )
                        st.error(error_handler.format_error_response(error))
                else:
                    error = error_handler.handle_error(
                        ErrorType.INSUFFICIENT_INFORMATION,
                        {"message": "関連情報が見つかりませんでした。"}
                    )
                    st.error(error_handler.format_error_response(error))
            else:
                error = error_handler.handle_error(
                    ErrorType.UNKNOWN_QUESTION_TYPE,
                    {"question": user_input}
                )
                st.error(error_handler.format_error_response(error))
                
        except Exception as e:
            error = error_handler.handle_error(
                ErrorType.SYSTEM_ERROR,
                {"error": str(e)}
            )
            st.error(error_handler.format_error_response(error))
        
        # 実行結果の要約
        st.subheader("📊 実行結果の要約")
        st.write("- 質問の処理が完了しました")
        if question_type:
            st.write(f"- 質問タイプ: {question_type}")
        st.write("- エラーが発生した場合は、より具体的な質問を試してください") 