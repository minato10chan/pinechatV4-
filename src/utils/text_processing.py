from typing import List, Dict, Any
from janome.tokenizer import Tokenizer
from ..config.settings import CHUNK_SIZE
import time

class JapaneseTextProcessor:
    def __init__(self):
        self.tokenizer = Tokenizer()

    def split_into_sentences(self, text: str) -> List[str]:
        """テキストを文単位に分割"""
        sentences = []
        current_sentence = []
        
        for token in self.tokenizer.tokenize(text):
            current_sentence.append(token.surface)
            if token.surface in ['。', '！', '？', '!', '?']:
                sentences.append(''.join(current_sentence))
                current_sentence = []
        
        if current_sentence:
            sentences.append(''.join(current_sentence))
        
        return sentences

    def is_sentence_boundary(self, text: str) -> bool:
        """文の区切りかどうかを判定"""
        if not text:
            return False
        return text[-1] in ['。', '！', '？', '!', '?']

    def process_text_file(self, file_content: str, filename: str, chunk_size: int = CHUNK_SIZE) -> List[Dict[str, Any]]:
        """テキストファイルを文脈を考慮したチャンクに分割"""
        chunks = []
        current_chunk = ""
        current_length = 0
        chunk_id = 0
        
        # 文単位に分割
        sentences = self.split_into_sentences(file_content)
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # 現在のチャンクに文を追加できる場合
            if current_length + sentence_size <= chunk_size:
                current_chunk += sentence + "\n"
                current_length += sentence_size + 1
            else:
                # 現在のチャンクが空でない場合、新しいチャンクを作成
                if current_chunk:
                    chunks.append({
                        "id": f"{filename}_chunk_{chunk_id}",  # ファイル名を含めたID
                        "text": current_chunk.strip(),
                        "metadata": {
                            "filename": filename,
                            "chunk_id": chunk_id
                        }
                    })
                    chunk_id += 1
                    current_chunk = ""
                    current_length = 0
                
                # 文がチャンクサイズを超える場合は、強制的に分割
                if sentence_size > chunk_size:
                    # 文を適切なサイズに分割
                    for i in range(0, len(sentence), chunk_size):
                        sub_chunk = sentence[i:i + chunk_size]
                        chunks.append({
                            "id": f"{filename}_chunk_{chunk_id}",  # ファイル名を含めたID
                            "text": sub_chunk,
                            "metadata": {
                                "filename": filename,
                                "chunk_id": chunk_id
                            }
                        })
                    current_chunk = ""
                    current_length = 0
                else:
                    current_chunk = sentence + "\n"
                    current_length = sentence_size + 1
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append({
                "id": f"{filename}_chunk_{chunk_id}",  # ファイル名を含めたID
                "text": current_chunk.strip(),
                "metadata": {
                    "filename": filename,
                    "chunk_id": chunk_id
                }
            })
        
        return chunks

# 後方互換性のための関数
def process_text_file(file_content: str, filename: str, chunk_size: int = CHUNK_SIZE) -> List[Dict[str, Any]]:
    processor = JapaneseTextProcessor()
    return processor.process_text_file(file_content, filename, chunk_size)