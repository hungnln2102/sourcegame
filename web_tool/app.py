import os
import uuid
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from extractor_core import process_package

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Lịch sử và trạng thái của các tiến trình giải nén
jobs = {}

def background_extractor(job_id, file_path):
    def update_progress(msg, percent):
        jobs[job_id]['status'] = msg
        jobs[job_id]['percent'] = percent

    try:
        jobs[job_id]['state'] = 'processing'
        zip_path, total_files, decoded_astc = process_package(file_path, update_progress)
        
        # Di chuyển zip file sang thư mục output
        zip_filename = os.path.basename(zip_path)
        final_zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)
        if os.path.exists(final_zip_path):
            os.remove(final_zip_path)
        os.rename(zip_path, final_zip_path)
        
        # Dọn dẹp file apk tạm đã upload
        if os.path.exists(file_path):
            os.remove(file_path)

        jobs[job_id]['state'] = 'completed'
        jobs[job_id]['zip_file'] = zip_filename
        jobs[job_id]['total_files'] = total_files
        jobs[job_id]['decoded_astc'] = decoded_astc
        jobs[job_id]['percent'] = 100
        jobs[job_id]['status'] = 'Hoàn tất giải nén!'
    except Exception as e:
        jobs[job_id]['state'] = 'failed'
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['status'] = f'Lỗi: {str(e)}'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'Không tìm thấy file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Tên file rỗng'}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.apk', '.xapk', '.zip']:
        return jsonify({'error': 'Vui lòng chọn file định dạng .apk, .xapk hoặc .zip'}), 400

    job_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_{file.filename}")
    file.save(save_path)

    jobs[job_id] = {
        'id': job_id,
        'filename': file.filename,
        'state': 'queued',
        'status': 'Đang chuẩn bị...',
        'percent': 0,
        'zip_file': None
    }

    # Chạy ngầm tiến trình giải nén
    thread = threading.Thread(target=background_extractor, args=(job_id, save_path))
    thread.daemon = True
    thread.start()

    return jsonify({'job_id': job_id})

@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job không tồn tại'}), 404
    return jsonify(jobs[job_id])

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    print("==========================================================")
    print(">> App Crawl APK/XAPK dang chay tai: http://127.0.0.1:5000")
    print("==========================================================")
    app.run(host='0.0.0.0', port=5000, debug=False)
