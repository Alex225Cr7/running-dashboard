import os
import requests
import json
import base64
from datetime import datetime, timedelta
from dateutil import parser
import google.generativeai as genai

# Cấu hình từ Biến môi trường
INTERVALS_ID = os.environ.get("INTERVALS_ATHLETE_ID")
INTERVALS_KEY = os.environ.get("INTERVALS_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_PAGES_URL = os.environ.get("GITHUB_PAGES_URL", "https://your-github-username.github.io/running-dashboard")

def fetch_intervals_data():
    if not INTERVALS_ID or not INTERVALS_KEY:
        print("Thiếu thông tin Intervals.icu")
        # Trả về dữ liệu mẫu để test giao diện nếu không có API
        return [
            {"id": "1", "name": "Morning Easy Run", "start_date_local": datetime.now().isoformat(), "distance": 10500, "moving_time": 3600, "average_heartrate": 142, "average_cadence": 172, "type": "Run"},
            {"id": "2", "name": "Tempo Run", "start_date_local": (datetime.now() - timedelta(days=2)).isoformat(), "distance": 12000, "moving_time": 3300, "average_heartrate": 158, "average_cadence": 175, "type": "Run"}
        ]
        
    url = f"https://intervals.icu/api/v1/athlete/{INTERVALS_ID}/activities"
    auth_string = f"API_KEY:{INTERVALS_KEY}"
    b64_auth = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    
    headers = {
        'Authorization': f'Basic {b64_auth}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Lỗi API Intervals: {response.status_code}")
        return []

def format_pace(speed_m_s):
    if not speed_m_s or speed_m_s <= 0: return "0:00"
    pace_min_km = 1000 / speed_m_s / 60
    mins = int(pace_min_km)
    secs = int((pace_min_km - mins) * 60)
    return f"{mins}:{secs:02d}"

def analyze_with_ai(run_data):
    if not GEMINI_KEY:
        return "<p>Cập nhật API Key của Gemini để xem nhận xét AI.</p>"
    
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro') # Dùng 1.5 pro cho phân tích sâu
    
    dist = round(run_data.get('distance', 0) / 1000, 2)
    pace = format_pace(run_data.get('distance', 0) / run_data.get('moving_time', 1))
    hr = run_data.get('average_heartrate', 0)
    cadence = run_data.get('average_cadence', 0)
    
    prompt = f"""
    Đóng vai một huấn luyện viên chạy bộ chuyên nghiệp. 
    Hãy nhận xét ngắn gọn (dưới 150 chữ) về bài chạy này của tôi. Khích lệ và đưa ra 1 điểm lưu ý.
    Thông số:
    - Quãng đường: {dist} km
    - Pace trung bình: {pace} /km
    - Nhịp tim trung bình: {hr} bpm
    - Guồng chân (Cadence): {cadence} spm
    
    Trả về định dạng HTML cơ bản (chỉ dùng thẻ <p>, <strong>, <ul>, <li> nếu cần). Không dùng markdown ```html.
    """
    
    try:
        response = model.generate_content(prompt)
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
    msg += f"❤️ Nhịp tim: {run_data.get('average_heartrate', 0)} bpm\n\n"
    msg += f"👉 Xem phân tích chi tiết tại: {GITHUB_PAGES_URL}"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT,
        "text": msg,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def main():
    activities = fetch_intervals_data()
    runs = [a for a in activities if a.get('type') == 'Run']
    
    if not runs:
        print("Không tìm thấy bài chạy nào.")
        return
        
    latest_run = runs[0]
    history_runs = runs[1:6] # Lấy 5 bài cũ hơn
    
    # 1. Chuẩn bị thông số mới nhất
    dist_km = round(latest_run.get('distance', 0) / 1000, 2)
    pace = format_pace(latest_run.get('distance', 0) / latest_run.get('moving_time', 1))
    hr = latest_run.get('average_heartrate', 0)
    cadence = latest_run.get('average_cadence', 0)
    
    run_date_obj = parser.isoparse(latest_run['start_date_local'])
    run_date_str = run_date_obj.strftime("%d/%m/%Y %H:%M")
    
    # 2. Phân tích AI
    ai_html = analyze_with_ai(latest_run)
    
    # 3. Tạo HTML cho lịch sử
    history_html = ""
    for r in history_runs:
        h_dist = round(r.get('distance', 0) / 1000, 2)
        h_pace = format_pace(r.get('distance', 0) / r.get('moving_time', 1))
        h_date = parser.isoparse(r['start_date_local']).strftime("%d/%m")
        h_name = r.get('name', 'Run')
        
        history_html += f"""
        <div class="history-item">
            <div class="hist-main">
                <span class="hist-name">{h_name}</span>
                <span class="hist-date">{h_date}</span>
            </div>
            <div class="hist-stats">
                <div class="hist-stat"><span class="hist-val">{h_dist} km</span><span class="hist-label">Distance</span></div>
                <div class="hist-stat"><span class="hist-val">{h_pace}</span><span class="hist-label">Pace</span></div>
                <div class="hist-stat"><span class="hist-val">{r.get('average_heartrate', 0)}</span><span class="hist-label">HR</span></div>
            </div>
        </div>
        """
        
    # 4. Ghi đè vào HTML
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()
        
    html = html.replace('{{LAST_SYNC_TIME}}', datetime.now().strftime("%d/%m/%Y %H:%M"))
    html = html.replace('{{RUN_NAME}}', latest_run.get('name', 'Run'))
    html = html.replace('{{RUN_DATE}}', run_date_str)
    html = html.replace('{{RUN_DISTANCE}}', str(dist_km))
    html = html.replace('{{RUN_PACE}}', pace)
    html = html.replace('{{RUN_HR}}', str(hr))
    html = html.replace('{{RUN_CADENCE}}', str(cadence))
    html = html.replace('{{AI_ANALYSIS_HTML}}', ai_html)
    html = html.replace('{{HISTORY_ROWS_HTML}}', history_html)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Đã tạo file index.html thành công.")
    
    # 5. Gửi Telegram nếu bài chạy mới (trong vòng 24h)
    time_diff = datetime.now() - run_date_obj.replace(tzinfo=None)
    if time_diff < timedelta(hours=24):
        send_telegram(latest_run)
        print("Đã gửi tin nhắn Telegram.")
    else:
        print("Bài chạy cũ, bỏ qua Telegram.")

if __name__ == "__main__":
    main()
