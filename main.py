import os
import requests
import json
import base64
import time
from datetime import datetime, timedelta
from dateutil import parser
import google.genai as genai

INTERVALS_ID = os.environ.get("INTERVALS_ATHLETE_ID", "").strip()
INTERVALS_KEY = os.environ.get("INTERVALS_API_KEY", "").strip()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GITHUB_PAGES_URL = os.environ.get("GITHUB_PAGES_URL", "https://your-github-username.github.io/running-dashboard")

DATA_FILE = "data.json"

def fetch_intervals_data():
    if not INTERVALS_ID or not INTERVALS_KEY:
        error_msg = f"Lỗi: Thiếu ID hoặc API Key của Intervals. ID: {'Có' if INTERVALS_ID else 'Không'}, Key: {'Có' if INTERVALS_KEY else 'Không'}"
        print(error_msg)
        return [{"id": "error-1", "name": error_msg, "type": "Run", "distance": 0, "moving_time": 1, "start_date_local": datetime.now().isoformat()}]
        
    oldest_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00")
    newest_date = datetime.now().strftime("%Y-%m-%dT23:59:59")
    url = f"https://intervals.icu/api/v1/athlete/{INTERVALS_ID}/activities?oldest={oldest_date}&newest={newest_date}"
    auth_string = f"API_KEY:{INTERVALS_KEY}"
    b64_auth = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    
    headers = {
        'Authorization': f'Basic {b64_auth}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return [a for a in response.json() if a.get('type') == 'Run']
        else:
            error_msg = f"Lỗi API Intervals: Mã {response.status_code}. Vui lòng kiểm tra lại API Key hoặc ID."
            print(error_msg)
            return [{"id": "error-2", "name": error_msg, "type": "Run", "distance": 0, "moving_time": 1, "start_date_local": datetime.now().isoformat()}]
    except Exception as e:
        error_msg = f"Lỗi kết nối mạng khi tải dữ liệu Intervals: {str(e)}"
        print(error_msg)
        return [{"id": "error-3", "name": error_msg, "type": "Run", "distance": 0, "moving_time": 1, "start_date_local": datetime.now().isoformat()}]

def format_pace(speed_m_s):
    if not speed_m_s or speed_m_s <= 0: return "0:00"
    pace_min_km = 1000 / speed_m_s / 60
    mins = int(pace_min_km)
    secs = int((pace_min_km - mins) * 60)
    return f"{mins}:{secs:02d}"

def analyze_with_ai(run_data):
    if not GEMINI_KEY:
        return "<p>Cập nhật API Key của Gemini để xem nhận xét AI.</p>"
    
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        
        dist = round(run_data.get('distance', 0) / 1000, 2)
        pace = format_pace(run_data.get('distance', 0) / run_data.get('moving_time', 1))
        hr = run_data.get('average_heartrate', 0)
        cadence = run_data.get('average_cadence', 0)
        if cadence > 0 and cadence <= 130:
            cadence = round(cadence * 2)
        
        prompt = f"""
        Đóng vai một huấn luyện viên chạy bộ marathon chuyên nghiệp đang kèm một học viên chuẩn bị giải Full Marathon (Sub-4h30).
        Hãy phân tích thật chi tiết và chuyên sâu bài chạy này:
        - Quãng đường: {dist} km
        - Pace trung bình: {pace} /km
        - Nhịp tim trung bình: {hr} bpm
        - Guồng chân (Cadence): {cadence} spm
        
        Yêu cầu cấu trúc bài phân tích:
        1. **Đánh giá Hiệu suất & Nỗ lực**: Nhận xét về tương quan giữa Pace và Nhịp tim. Bài chạy này đạt mục tiêu (phục hồi, duy trì hay phát triển) chưa?
        2. **Động lực học chạy bộ (Running Dynamics)**: Phân tích về Cadence {cadence} spm. Đã tối ưu chưa? Có dấu hiệu lê chân hay sải quá dài không?
        3. **Lời khuyên & Đề xuất**: Rút kinh nghiệm gì cho bài chạy tiếp theo trong giáo án?
        
        Lưu ý: 
        - Phân tích mang tính chuyên môn cao, có chiều sâu giống như các bài phân tích dài trước đây.
        - Trả về định dạng HTML (dùng <h4>, <p>, <ul>, <li>, <strong>). 
        - Tuyệt đối KHÔNG dùng markdown ```html ở đầu và cuối.
        """
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text.replace("```html", "").replace("```", "").strip()
    except Exception as e:
        print("Lỗi Gemini API:", e)
        return "<p>Không thể phân tích lúc này.</p>"

def send_telegram(run_data):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return
        
    dist = round(run_data.get('distance', 0) / 1000, 2)
    pace = format_pace(run_data.get('distance', 0) / run_data.get('moving_time', 1))
    
    msg = f"🏃‍♂️ **Bài chạy mới hoàn thành!**\n\n"
    msg += f"📍 Tên: {run_data.get('name', 'Run')}\n"
    msg += f"📏 Quãng đường: {dist} km\n"
    msg += f"⏱️ Pace: {pace} /km\n"
    msg += f"👉 Xem phân tích chi tiết tại: {GITHUB_PAGES_URL}"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT,
        "text": msg,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def load_local_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_local_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    runs_api = fetch_intervals_data()
    runs_local = load_local_data()
    
    # Tạo set các ID đã có
    existing_ids = {str(r['id']) for r in runs_local}
    
    new_runs = []
    
    # Lọc ra các bài chạy mới hoặc bài chưa được phân tích thành công
    for r in runs_api:
        rid = str(r['id'])
        existing_run = next((item for item in runs_local if str(item["id"]) == rid), None)
        
        # Thêm vào danh sách xử lý nếu là bài mới, hoặc bài cũ nhưng AI bị lỗi
        if not existing_run or "Không thể phân tích" in existing_run.get("ai_analysis", ""):
            new_runs.append(r)
            
    if not new_runs:
        print("Không có bài chạy mới nào.")
        return
        
    print(f"Phát hiện {len(new_runs)} bài chạy mới!")
    
    # Xử lý các bài mới (Phân tích AI)
    new_entries = []
    for r in new_runs:
        print(f"Đang phân tích bài chạy: {r.get('name')}")
        
        dist_km = round(r.get('distance', 0) / 1000, 2)
        pace = format_pace(r.get('distance', 0) / r.get('moving_time', 1))
        hr = r.get('average_heartrate', 0)
        cadence = r.get('average_cadence', 0)
        if cadence > 0 and cadence <= 130:
            cadence = round(cadence * 2)
        
        run_date_obj = parser.isoparse(r['start_date_local'])
        run_date_str = run_date_obj.strftime("%d/%m/%Y %H:%M")
        
        ai_html = analyze_with_ai(r)
        
        entry = {
            "id": str(r['id']),
            "name": r.get('name', 'Run'),
            "date": run_date_str,
            "distance": dist_km,
            "pace": pace,
            "hr": hr,
            "cadence": cadence,
            "elevation": r.get('total_elevation_gain', 0),
            "load": r.get('icu_training_load', 0),
            "calories": r.get('calories', 0),
            "max_hr": r.get('max_heartrate', 0),
            "stride": r.get('average_stride', 0),
            "hr_zones": r.get('icu_hr_zone_times', []),
            "ai_analysis": ai_html,
            "raw_date": r['start_date_local']
        }
        new_entries.append(entry)
        
        # Gửi Telegram
        send_telegram(r)
        
        # Đợi 5 giây để tránh lỗi Rate Limit của Gemini (15 requests/minute)
        time.sleep(5)
        
    # Nối dữ liệu mới vào danh sách cũ (cập nhật nếu đã tồn tại)
    updated_data = runs_local.copy()
    for new_entry in new_entries:
        # Tìm xem có bài cũ trùng ID không (trường hợp phân tích lại)
        idx = next((i for i, item in enumerate(updated_data) if item["id"] == new_entry["id"]), -1)
        if idx >= 0:
            updated_data[idx] = new_entry
        else:
            updated_data.insert(0, new_entry)
    
    # Cắt giữ lại tối đa 50 bài chạy gần nhất để file ko quá lớn
    updated_data = updated_data[:50]
    
    save_local_data(updated_data)
    print("Đã cập nhật data.json thành công!")

if __name__ == "__main__":
    main()
