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
    const elAi = document.getElementById('detail-ai');

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

        // Toggle visibility
        emptyStateEl.classList.add('hidden');
        runDetailsEl.classList.remove('hidden');
        
        // Retrigger animation
        runDetailsEl.classList.remove('fade-in');
        void runDetailsEl.offsetWidth; // trigger reflow
        runDetailsEl.classList.add('fade-in');
    }
});
