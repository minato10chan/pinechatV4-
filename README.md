# 地域情報案内チャットシステム

このプロジェクトは、特定の地域の周辺情報を自然言語で検索・案内できるチャットシステムです。不動産購入や賃貸の意思決定を支援することを目的としており、物件情報だけでなく、その地域で生活する上で必要な様々な情報を提供します。

## 主な機能

### 1. 地域情報の検索・案内
- 物件情報（間取り、価格、設備など）
- 教育環境（学校、保育園、塾など）
- 交通アクセス（駅、バス、道路など）
- 生活インフラ（スーパー、病院、公共施設など）
- 安全・防災情報
- 地域コミュニティの状況
- 行政情報（都市計画、再開発など）

### 2. 自然言語での対話
- 日本語での質問応答
- 文脈を考慮した応答生成
- 詳細な情報の提供
- 関連情報の提案

### 3. ファイル管理機能
- テキストファイルのアップロード
- メタデータによる情報分類
- 自動的なテキスト処理
- データベースへの保存

### 4. カスタマイズ機能
- プロンプトテンプレートの編集
- 検索条件の調整
- 表示形式の変更

## ローカル環境でのセットアップ

### 1. 仮想環境の作成と有効化

```shell
# Windowsの場合
# PowerShellを開いて以下のコマンドを順番に実行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS/Linuxの場合
# ターミナルを開いて以下のコマンドを順番に実行
python -m venv .venv
source .venv/bin/activate
```

### 2. 必要なパッケージのインストール

```shell
# 仮想環境が有効化されていることを確認（プロンプトの先頭に(.venv)が表示されているはず）
# 以下のコマンドを実行
pip install -r requirements.txt
```

### 3. 環境変数の設定

```shell
# Windowsの場合
copy .env.template .env

# macOS/Linuxの場合
cp .env.template .env
```

`.env`ファイルを開いて、以下の環境変数を設定してください：
```
PINECONE_API_KEY=your_api_key_here
PINECONE_ASSISTANT_NAME=your_assistant_name_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. アプリケーションの実行

```shell
# 以下のコマンドを実行
streamlit run streamlit_app.py
```

アプリケーションが起動したら、ブラウザで http://localhost:8501 にアクセスしてください。

## 使用方法

### 1. ファイルのアップロード
1. 「ファイルアップロード」タブを選択
2. テキストファイルをアップロード
3. メタデータを入力（大カテゴリ、中カテゴリ、市区町村など）
4. 「データベースに保存」をクリック

### 2. チャットでの質問
1. 「チャット」タブを選択
2. 質問を入力（例：「この地域の小学校について教えてください」）
3. システムが関連情報を検索し、回答を生成

### 3. 設定のカスタマイズ
1. 「設定」タブを選択
2. プロンプトテンプレートの編集
3. 検索条件の調整
4. 表示形式の変更

## 技術スタック

- フロントエンド: Streamlit
- バックエンド: Python
- データベース: Pinecone
- 言語モデル: OpenAI GPT-3.5-turbo
- テキスト処理: Janome（日本語形態素解析）

## 注意事項

1. 日本語テキストの処理に特化しています
2. 対応エンコーディング: UTF-8、Shift-JIS、CP932、EUC-JP
3. 大量のテキストデータを処理する場合は、適切なチャンクサイズの設定が必要です
4. APIキーは適切に管理してください

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## Configuration

### Install packages

1. For best results, create a [Python virtual environment](https://realpython.com/python-virtual-environments-a-primer/) with 3.10 or 3.11 and reuse it when running any file in this repo.
2. Run

```shell
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.template` to `.env` and `.streamlit/secrets.toml.template` to `.streamlit/secrets.toml`. Fill in your [Pinecone API key](https://app.pinecone.io/organizations/-/projects/-/keys) and the name you want to call your Assistant. The `.env` file will be used by the Jupyter notebook for processing the data and upserting it to Pinecone, whereas `secrets.toml` will be used by Streamlit when running locally.

## Setup Assistant

1. In the [console](https://app.pinecone.io/organizations/-/projects/-/assistant), accept the Terms of Service for Pinecone Assistant.

2. Run all cells in the "assistant-starter" Jupyter notebook to create an assistant and upload files to it.
> [!NOTE]
> If you prefer to create an assistant and upload your files via the UI, skip the notebook and continue to the next section.

## Test the app locally

### [OPTIONAL] Configure the app

In the `streamlit_app.py` file:

- Set your preferred title on [line 18](https://github.com/pinecone-field/assistant-streamlit-starter/blob/f5091cbe5a9bb0fc31f327cda47830824d7a168b/streamlit_app.py#L18)
- Set your preferred prompt on [line 21](https://github.com/pinecone-field/assistant-streamlit-starter/blob/f5091cbe5a9bb0fc31f327cda47830824d7a168b/streamlit_app.py#L21)
- Set your preferred button label on [line 24](https://github.com/pinecone-field/assistant-streamlit-starter/blob/f5091cbe5a9bb0fc31f327cda47830824d7a168b/streamlit_app.py#L24)
- Set your preferred success message on [line 49](https://github.com/pinecone-field/assistant-streamlit-starter/blob/f5091cbe5a9bb0fc31f327cda47830824d7a168b/streamlit_app.py#L49)
- Set your preferred failure message on [line 53](https://github.com/pinecone-field/assistant-streamlit-starter/blob/f5091cbe5a9bb0fc31f327cda47830824d7a168b/streamlit_app.py#L53)

### Run the app

1. Validate that Streamlit is [installed](#install-packages) correctly by running

```shell
streamlit hello
```

You should see a welcome message and the demo should automatically open in your browser. If it doesn't open automatically, manually go to the **Local URL** listed in the terminal output.

2. If the demo ran correctly, run

```shell
streamlit run streamlit_app.py
```

3. Confirm that your app looks good and test queries return successful responses. If so, move on to deployment!

## Deploy the app

1. Create and login to a [Streamlit Community Cloud](https://share.streamlit.io) account.
2. Link your Github account in Workspace settings.
3. On the dashboard, click "New app".
4. Select your Github repo and branch, then enter the filename `streamlit_app.py`.
5. [OPTIONAL] Set your preferred app URL.
6. In "Advanced settings...":
   - Change the Python version to match the one you tested locally
   - Copy the contents of your `secrets.toml` file into "Secrets"
   - Click "Save"
7. Click "Deploy"



## memo
このサービスは地域情報案内チャットシステムで、以下の主要な機能を提供しています：
・チャット機能
自然言語での質問応答
文脈を考慮した応答生成
地域に関する様々な情報の提供
日本語での対話インターフェース
・物件情報管理
物件情報の登録・管理
間取り、価格、設備などの詳細情報
物件情報の検索・表示
・ファイル管理機能
テキストファイルのアップロード
複数のエンコーディング対応（UTF-8、Shift-JIS、CP932、EUC-JP）
メタデータによる情報分類
Pineconeデータベースへの保存
・地域情報検索
教育環境（学校、保育園、塾など）
交通アクセス（駅、バス、道路など）
生活インフラ（スーパー、病院、公共施設など）
安全・防災情報
地域コミュニティの状況
行政情報（都市計画、再開発など）
・設定・カスタマイズ機能
プロンプトテンプレートの編集
検索条件の調整
表示形式の変更
システム設定の管理
・エージェント機能
自動化された情報収集
インテリジェントな情報処理
タスクの自動実行

・技術スタック:
フロントエンド: Streamlit
バックエンド: Python
データベース: Pinecone
言語モデル: OpenAI GPT-3.5-turbo
テキスト処理: Janome（日本語形態素解析）

##チャット機能について、より詳細に説明させていただきます：
・基本機能
自然言語での質問応答
文脈を考慮した会話の継続
物件情報との連携
チャット履歴の管理
・チャットインターフェース
メッセージ入力欄
チャット履歴の表示
詳細情報の展開表示
サイドバーでの設定管理
・プロンプト管理機能
カスタマイズ可能なプロンプトテンプレート
システムプロンプトの設定
応答テンプレートの設定
複数のテンプレートの切り替え
・物件情報連携
物件の選択機能
物件詳細情報の表示
物件情報を考慮した応答生成
物件情報の動的更新
・チャット履歴管理
履歴の保存（CSV形式）
履歴の読み込み
履歴のクリア
タイムスタンプ付きの記録
・高度な応答生成
LangChainを使用した文脈理解
GPT-3.5-turboによる応答生成
関連情報の検索と統合
詳細情報の提供
・エラー処理とフィードバック
エラーメッセージの表示
処理状態の表示
ユーザーフィードバック
システム状態の通知
・セキュリティ機能
APIキーの管理
セッション管理
データの暗号化
アクセス制御
・カスタマイズオプション
応答形式のカスタマイズ
検索パラメータの調整
表示設定の変更
テンプレートの編集
・パフォーマンス最適化
非同期処理
キャッシュ管理
効率的なデータ検索
レスポンス時間の最適化
このチャット機能は、地域情報の提供に特化しており、物件情報や地域の詳細情報を自然な会話形式で提供することができます。ユーザーは直感的なインターフェースを通じて、必要な情報を簡単に取得することができます。

[フロントエンド (Streamlit)]
        ↓
[バックエンド (Python)]
        ↓
[外部サービス]
- OpenAI (GPT-3.5-turbo)
- Pinecone (ベクトルDB)

src/
├── components/          # UIコンポーネント
│   ├── chat.py         # チャット機能
│   ├── file_upload.py  # ファイルアップロード
│   ├── settings.py     # 設定管理
│   └── agent.py        # エージェント機能
├── services/           # ビジネスロジック
│   ├── langchain_service.py    # LangChain処理
│   ├── pinecone_service.py     # Pinecone操作
│   └── question_classifier.py  # 質問分類
└── config/             # 設定ファイル
    └── settings.py     # システム設定

##チャット機能の処理フロー

[ユーザー入力]
      ↓
[入力処理]
- テキストの前処理
- 質問の分類
      ↓
[コンテキスト検索]
- Pineconeでの類似文書検索
- 関連情報の抽出
      ↓
[応答生成]
- プロンプトの構築
- GPT-3.5-turboによる生成
      ↓
[応答処理]
- フォーマット整形
- 詳細情報の付加
      ↓
[履歴管理]
- メッセージの保存
- セッション状態の更新

##データフロー
[ユーザー入力]
      ↓
[Pinecone検索]
- ベクトル化
- 類似度検索
      ↓
[コンテキスト構築]
- 関連文書の抽出
- メタデータの統合
      ↓
[GPT-3.5-turbo処理]
- プロンプトの構築
- 応答の生成
      ↓
[結果の整形]
- フォーマット適用
- 詳細情報の付加
      ↓
[UI表示]
- メッセージの表示
- 詳細情報の展開