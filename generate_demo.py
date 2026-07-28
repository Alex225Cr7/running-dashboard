import os, datetime

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('{{LAST_SYNC_TIME}}', datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
html = html.replace('{{RUN_NAME}}', 'Sunday Long Run')
html = html.replace('{{RUN_DATE}}', '26/07/2026 05:00')
html = html.replace('{{RUN_DISTANCE}}', '21.1')
html = html.replace('{{RUN_PACE}}', '5:30')
html = html.replace('{{RUN_HR}}', '152')
html = html.replace('{{RUN_CADENCE}}', '175')
html = html.replace('{{AI_ANALYSIS_HTML}}', '<p>Bài chạy Half Marathon rất tốt. Pace ổn định ở 5:30/km và nhịp tim kiểm soát tốt trong vùng Zone 2-3. Cadence 175 spm là mức tối ưu. <strong>Lưu ý:</strong> Hãy nhớ giãn cơ kỹ sau bài chạy dài để tránh căng cơ bắp chân nhé!</p>')

history_html = '''
<div class="history-item">
    <div class="hist-main">
        <span class="hist-name">Tempo Thursday</span>
        <span class="hist-date">23/07</span>
    </div>
    <div class="hist-stats">
        <div class="hist-stat"><span class="hist-val">12.0 km</span><span class="hist-label">Distance</span></div>
        <div class="hist-stat"><span class="hist-val">5:15</span><span class="hist-label">Pace</span></div>
        <div class="hist-stat"><span class="hist-val">160</span><span class="hist-label">HR</span></div>
    </div>
</div>
<div class="history-item">
    <div class="hist-main">
        <span class="hist-name">Recovery Tuesday</span>
        <span class="hist-date">21/07</span>
    </div>
    <div class="hist-stats">
        <div class="hist-stat"><span class="hist-val\">8.0 km</span><span class="hist-label">Distance</span></div>
        <div class="hist-stat"><span class="hist-val\">6:10</span><span class="hist-label">Pace</span></div>
        <div class="hist-stat"><span class="hist-val\">135</span><span class="hist-label">HR</span></div>
    </div>
</div>
'''
html = html.replace('{{HISTORY_ROWS_HTML}}', history_html)

with open('demo.html', 'w', encoding='utf-8') as f:
    f.write(html)
