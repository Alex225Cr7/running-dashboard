document.addEventListener('DOMContentLoaded', () => {
    const runListEl = document.getElementById('run-list');
    const emptyStateEl = document.getElementById('empty-state');
    const runDetailsEl = document.getElementById('run-details');
    
    // Elements to update
    const elName = document.getElementById('detail-name');
    const elDate = document.getElementById('detail-date');
    const elDist = document.getElementById('detail-dist');
    const elPace = document.getElementById('detail-pace');
    const elHr = document.getElementById('detail-hr');
    const elCadence = document.getElementById('detail-cadence');
    const elAi = document.getElementById('aiAnalysis');

    let runsData = [];

    // Fetch data
    fetch('data.json')
        .then(response => {
            if (!response.ok) throw new Error("Network error");
            return response.json();
        })
        .then(data => {
            runsData = data;
            renderList();
        })
        .catch(err => {
            console.error(err);
            runListEl.innerHTML = '<div class="loading">Không thể tải dữ liệu. Hãy chắc chắn bạn đã tạo file data.json!</div>';
        });

    function renderList() {
        runListEl.innerHTML = '';
        if (runsData.length === 0) {
            runListEl.innerHTML = '<div class="loading">Chưa có bài chạy nào.</div>';
            return;
        }

        runsData.forEach((run, index) => {
            const li = document.createElement('li');
            li.className = 'run-item';
            li.dataset.index = index;
            
            li.innerHTML = `
                <span class="run-item-name">${run.name}</span>
                <div class="run-item-meta">
                    <span class="run-item-date">${run.date.split(' ')[0]}</span>
                    <span class="run-item-stats">${run.distance}km • ${run.pace}</span>
                </div>
            `;
            
            li.addEventListener('click', () => selectRun(index));
            runListEl.appendChild(li);
        });
        
        // Auto select first run
        if(runsData.length > 0) {
            selectRun(0);
        }
    }

    function selectRun(index) {
        // Update active class
        document.querySelectorAll('.run-item').forEach(el => el.classList.remove('active'));
        const targetLi = document.querySelector(`.run-item[data-index="${index}"]`);
        if (targetLi) targetLi.classList.add('active');

        // Show details
        const run = runsData[index];
        elName.textContent = run.name;
        elDate.textContent = run.date;
        elDist.textContent = run.distance;
        elPace.textContent = run.pace;
        elHr.textContent = run.hr;
        elCadence.textContent = run.cadence;
        elAi.innerHTML = run.ai_analysis || "<p>Chưa có phân tích cho bài chạy này.</p>";

        // Hiển thị Advanced Stats
        const advGrid = document.getElementById('advancedStatsGrid');
        advGrid.innerHTML = `
            <div class="adv-stat-item">
                <span class="adv-stat-label">Độ dốc (Elev)</span>
                <span class="adv-stat-value">${run.elevation || 0} <small>m</small></span>
            </div>
            <div class="adv-stat-item">
                <span class="adv-stat-label">Training Load</span>
                <span class="adv-stat-value">${run.load || 0}</span>
            </div>
            <div class="adv-stat-item">
                <span class="adv-stat-label">Calories</span>
                <span class="adv-stat-value">${run.calories || 0} <small>kcal</small></span>
            </div>
            <div class="adv-stat-item">
                <span class="adv-stat-label">Max HR</span>
                <span class="adv-stat-value">${run.max_hr || 0} <small>bpm</small></span>
            </div>
        `;

        // Vẽ biểu đồ HR Zones
        const zoneChart = document.getElementById('zoneChart');
        const zoneLegend = document.getElementById('zoneLegend');
        zoneChart.innerHTML = '';
        zoneLegend.innerHTML = '';

        if (run.hr_zones && run.hr_zones.length > 0) {
            const totalTime = run.hr_zones.reduce((a, b) => a + b, 0);
            const zoneNames = ['Z1 (Phục hồi)', 'Z2 (Sức bền)', 'Z3 (Tempo)', 'Z4 (Threshold)', 'Z5 (Tối đa)'];
            
            if (totalTime > 0) {
                run.hr_zones.forEach((time, index) => {
                    if (index >= 5) return; // Chỉ lấy 5 zones chính
                    const percentage = (time / totalTime) * 100;
                    if (percentage > 0) {
                        // Vẽ thanh ngang
                        const bar = document.createElement('div');
                        bar.className = \`zone-bar zone-\${index + 1}\`;
                        bar.style.width = \`\${percentage}%\`;
                        bar.title = \`\${zoneNames[index]}: \${Math.round(percentage)}%\`;
                        zoneChart.appendChild(bar);
                        
                        // Thêm chú thích
                        const legend = document.createElement('div');
                        legend.className = 'legend-item';
                        legend.innerHTML = \`<div class="legend-color zone-\${index + 1}"></div> \${zoneNames[index]} (\${Math.round(percentage)}%)\`;
                        zoneLegend.appendChild(legend);
                    }
                });
            }
        }

        // Toggle visibility
        emptyStateEl.classList.add('hidden');
        runDetailsEl.classList.remove('hidden');
        
        // Retrigger animation
        runDetailsEl.classList.remove('fade-in');
        void runDetailsEl.offsetWidth; // trigger reflow
        runDetailsEl.classList.add('fade-in');
    }
});
