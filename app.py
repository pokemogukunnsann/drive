from flask import Flask, request, send_from_directory, redirect, url_for, render_template
import os, uuid, json

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/uploads'
DATA_FILE = 'data.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    is_public = 'public' in request.form
    if file:
        file_id = str(uuid.uuid4())
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        file.save(filepath)

        data = load_data()
        data[file_id] = {
            'filename': filename,
            'public': is_public
        }
        save_data(data)

        if is_public:
            link = url_for('shared_file', file_id=file_id, _external=True)
            return f'共有リンク: <a href="{link}">{link}</a>'
        else:
            return 'アップロード成功（非公開）'

@app.route('/file/<file_id>')
def shared_file(file_id):
    data = load_data()
    if file_id in data and data[file_id]['public']:
        return send_from_directory(UPLOAD_FOLDER, file_id, as_attachment=True,
                                   download_name=data[file_id]['filename'])
    return 'ファイルが存在しないか非公開です。', 404

if __name__ == '__main__':
    app.run(debug=True)
