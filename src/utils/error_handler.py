from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class ErrorType(Enum):
    """エラーの種類を定義"""
    UNKNOWN_QUESTION_TYPE = "unknown_question_type"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    INVALID_METADATA = "invalid_metadata"
    TEMPLATE_ERROR = "template_error"
    SYSTEM_ERROR = "system_error"

@dataclass
class ErrorResponse:
    """エラーレスポンスの定義"""
    error_type: ErrorType
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorHandler:
    def __init__(self):
        self.error_messages = {
            ErrorType.UNKNOWN_QUESTION_TYPE: "申し訳ありませんが、質問の種類を特定できませんでした。",
            ErrorType.INSUFFICIENT_INFORMATION: "申し訳ありませんが、回答に必要な情報が不足しています。",
            ErrorType.INVALID_METADATA: "申し訳ありませんが、データの形式が正しくありません。",
            ErrorType.TEMPLATE_ERROR: "申し訳ありませんが、回答の生成中にエラーが発生しました。",
            ErrorType.SYSTEM_ERROR: "申し訳ありませんが、システムエラーが発生しました。"
        }

    def handle_error(self, error_type: ErrorType, details: Optional[Dict[str, Any]] = None) -> ErrorResponse:
        """エラーを処理してレスポンスを生成"""
        message = self.error_messages.get(error_type, "予期せぬエラーが発生しました。")
        return ErrorResponse(error_type=error_type, message=message, details=details)

    def format_error_response(self, error_response: ErrorResponse) -> str:
        """エラーレスポンスをフォーマット"""
        response = f"エラー: {error_response.message}\n"
        if error_response.details:
            response += "\n詳細情報:\n"
            for key, value in error_response.details.items():
                response += f"- {key}: {value}\n"
        return response

    def is_recoverable_error(self, error_type: ErrorType) -> bool:
        """エラーが回復可能かどうかを判定"""
        return error_type in [
            ErrorType.UNKNOWN_QUESTION_TYPE,
            ErrorType.INSUFFICIENT_INFORMATION
        ] 