import os
import uuid
from flask import Flask, request, redirect, render_template, send_file, abort
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# .envファイルをロードして環境変数を設定
load_dotenv()

# Flask設定
app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/uploads'  # Vercelのストレージに保存されるパス
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Supabase設定（環境変数から取得）
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or key not set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# アップロード画面
@app.route('/')
def index():
    return render_template('upload.html')

# ファイルアップロード
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        # 直接URLを開いたときなど
        return redirect('/')

    # POST処理（ファイルアップロード）
    file = request.files.get('file')
    public = 'public' in request.form

    if not file:
        return 'ファイルが選択されていません', 400

    print(request.files)  # これを追加！
    print(request.form)

    # ファイル保存
    filename = secure_filename(file.filename)
    file_id = str(uuid.uuid4())  # 一意なファイルID生成
    filepath = os.path.join(UPLOAD_FOLDER, file_id)
    file.save(filepath)

    # Supabaseにメタデータ保存
    supabase.table("files").insert({
        "file_id": file_id,
        "filename": filename,
        "public": public,
        "mimetype": file.mimetype
    }).execute()

    # 共有リンクを表示
    share_url = f"https://{request.host}/file/{file_id}"
    return f"アップロード成功！<br><a href='{share_url}'>{share_url}</a>"

# ファイル共有リンク
@app.route('/file/<file_id>')
def shared_file(file_id):
    # Supabaseからファイル情報を取得
    result = supabase.table("files").select("*").eq("file_id", file_id).execute()
    if not result.data:
        abort(404)

    file_data = result.data[0]
    if not file_data["public"]:
        return "このファイルは非公開です"

    # ファイル送信
    filepath = os.path.join(UPLOAD_FOLDER, file_id)
    if not os.path.exists(filepath):
        return "ファイルは一時的に消えました（再アップロードが必要）"
    
    return send_file(filepath, mimetype=file_data["mimetype"], download_name=file_data["filename"])

if __name__ == "__main__":
    app.run(debug=True)
