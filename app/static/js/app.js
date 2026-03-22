/* ═══════════════════════════════════════════════════════
   HireIQ — Frontend Application
   Full SPA logic: API calls, rendering, charts, drag-drop
═══════════════════════════════════════════════════════ */

/* ── State ─────────────────────────────────────────── */
const state = {
  jobs: [],
  candidates: [],
  screeningResults: [],
  selectedJobId: null,
  recentHistory: [],
  charts: {},
};

/* ── API ───────────────────────────────────────────── */
const API = {
  base: '/api',
  async get(path) {
    const r = await fetch(this.base + path);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async post(path, data) {
    const r = await fetch(this.base + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ error: r.statusText }));
      throw new Error(err.error || r.statusText);
    }
    return r.json();
  },
  async patch(path, data) {
    const r = await fetch(this.base + path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async delete(path) {
    const r = await fetch(this.base + path, { method: 'DELETE' });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async uploadFiles(path, formData) {
    const r = await fetch(this.base + path, { method: 'POST', body: formData });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ error: r.statusText }));
      throw new Error(err.error || r.statusText);
    }
    return r.json();
  },
};

/* ── Navigation ────────────────────────────────────── */
function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(a => a.classList.remove('active'));
  document.getElementById(`page-${page}`).classList.add('active');
  const navEl = document.getElementById(`nav-${page}`);
  if (navEl) navEl.classList.add('active');

  if (page === 'dashboard') refreshDashboard();
  if (page === 'jobs') loadJobs();
  if (page === 'candidates') loadCandidates();
  if (page === 'screening') loadScreeningPage();
}

document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    navigate(link.dataset.page);
  });
});

/* ── Theme Toggle ──────────────────────────────────── */
(function initTheme() {
  const saved = localStorage.getItem('hireiq-theme');
  if (saved === 'light') {
    document.body.setAttribute('data-theme', 'light');
    const btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = '☀️';
  }
  // default is dark — no attribute needed
})();

document.getElementById('themeToggle').addEventListener('click', () => {
  const isLight = document.body.hasAttribute('data-theme');
  if (isLight) {
    document.body.removeAttribute('data-theme');
    document.getElementById('themeToggle').textContent = '🌙';
    localStorage.setItem('hireiq-theme', 'dark');
  } else {
    document.body.setAttribute('data-theme', 'light');
    document.getElementById('themeToggle').textContent = '☀️';
    localStorage.setItem('hireiq-theme', 'light');
  }
  if (document.getElementById('page-dashboard')?.classList.contains('active')) {
    refreshDashboard();
  }
});

/* ══════════════  DASHBOARD  ══════════════════════════ */
async function refreshDashboard() {
  try {
    const [stats, recent, skills] = await Promise.all([
      API.get('/dashboard/stats'),
      API.get('/dashboard/recent'),
      API.get('/dashboard/skills-gap'),
    ]);
    renderStats(stats);
    renderStatusChart(stats);
    renderSkillsChart(skills.skills_gap);
    state.recentHistory = recent.recent_screenings;
    renderRecentScreenings(state.recentHistory);
  } catch (e) {
    toast('Failed to load dashboard: ' + e.message, 'error');
  }
}

function renderStats(s) {
  document.getElementById('stat-jobs').textContent = s.jobs.active;
  document.getElementById('stat-candidates').textContent = s.candidates.total;
  document.getElementById('stat-shortlisted').textContent = s.screenings.shortlisted;
  document.getElementById('stat-avgscore').textContent = s.screenings.avg_score + '%';
  document.getElementById('stat-bias').textContent = s.bias.avg_bias_score + '%';
  document.getElementById('stat-screenings').textContent = s.screenings.total;

  const tooltipContent = document.getElementById('shortlist-tooltip-content');
  if (s.screenings.shortlisted_info && s.screenings.shortlisted_info.length > 0) {
    tooltipContent.innerHTML = s.screenings.shortlisted_info.map(cand => `
      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border); padding-bottom:6px; margin-bottom:2px;">
         <div style="display:flex; flex-direction:column; line-height:1.2;">
             <span style="font-weight:700; font-size:13px; color:var(--text-primary);">${cand.name}</span>
             <span style="font-size:11px; color:var(--text-secondary); max-width:180px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${cand.job}</span>
         </div>
         <span style="font-size:12px; font-weight:700; color:${scoreColor(cand.score)};">${cand.score}%</span>
      </div>
    `).join('');
  } else {
    tooltipContent.innerHTML = '<span class="text-muted" style="font-size:12px;">No candidates shortlisted yet...</span>';
  }
}

function renderStatusChart(stats) {
  const ctx = document.getElementById('statusChart');
  if (!ctx) return;
  if (state.charts.status) state.charts.status.destroy();
  const s = stats.screenings;
  const textColor = getComputedStyle(document.body).getPropertyValue('--text-secondary').trim() || '#8B95B0';
  state.charts.status = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Shortlisted', 'Pending', 'Rejected'],
      datasets: [{
        data: [s.shortlisted, s.pending, s.rejected],
        backgroundColor: ['rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)', 'rgba(239,68,68,0.8)'],
        borderColor: 'transparent',
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: textColor, font: { size: 12 } } },
      },
      cutout: '65%',
    },
  });
}

function renderSkillsChart(gaps) {
  const ctx = document.getElementById('skillsChart');
  if (!ctx) return;
  if (state.charts.skills) state.charts.skills.destroy();
  if (!gaps || !gaps.length) return;
  const top = gaps.slice(0, 10);
  const textColor = getComputedStyle(document.body).getPropertyValue('--text-secondary').trim() || '#8B95B0';
  const gridColor = getComputedStyle(document.body).getPropertyValue('--border').trim() || 'rgba(255,255,255,0.04)';
  state.charts.skills = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top.map(g => g.skill),
      datasets: [
        { label: 'Demand', data: top.map(g => g.demand), backgroundColor: 'rgba(14,165,233,0.7)', borderRadius: 4 },
        { label: 'Supply', data: top.map(g => g.supply), backgroundColor: 'rgba(16,185,129,0.7)', borderRadius: 4 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: textColor } } },
      scales: {
        x: { ticks: { color: textColor, maxRotation: 40 }, grid: { color: gridColor } },
        y: { ticks: { color: textColor }, grid: { color: gridColor } },
      },
    },
  });
}

function renderRecentScreenings(screenings) {
  const tbody = document.getElementById('recentBody');
  if (!screenings || !screenings.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-row">No screenings yet. Post a job and upload resumes to start!</td></tr>';
    return;
  }
  tbody.innerHTML = screenings.map(s => `
    <tr>
      <td><strong>${s.candidate?.name || 'Unknown'}</strong></td>
      <td><span class="badge badge-blue" style="font-weight:600">${s.job_title}</span></td>
      <td><span style="color:${scoreColor(s.overall_score)};font-weight:700">${s.overall_score}%</span></td>
      <td>${statusBadge(s.status)}</td>
      <td>
        <span class="badge ${s.email_sent ? 'badge-green' : 'badge-gray'}" 
              style="font-size:11px; cursor:help;" 
              title="${s.email_status || 'No notification sent'}">
          ${s.email_sent ? '📧 Sent' : '⚪ None'}
        </span>
      </td>
      <td class="text-muted">${formatDate(s.screened_at)}</td>
    </tr>
  `).join('');
}

function filterRecentScreenings() {
  const query = document.getElementById('recentSearch').value.toLowerCase();
  const status = document.getElementById('recentStatus').value;

  const filtered = state.recentHistory.filter(s => {
    const matchesQuery = !query ||
      (s.candidate?.name?.toLowerCase().includes(query)) ||
      (s.job_title?.toLowerCase().includes(query));

    const matchesStatus = status === 'all' || s.status === status;

    return matchesQuery && matchesStatus;
  });

  renderRecentScreenings(filtered);
}

/* ══════════════  JOBS  ═══════════════════════════════ */
async function loadJobs() {
  const grid = document.getElementById('jobsGrid');
  grid.innerHTML = '<div class="loading-state"><span class="spinner"></span>&nbsp; Loading jobs...</div>';
  try {
    const data = await API.get('/jobs/?per_page=50');
    state.jobs = data.jobs;
    renderJobs(state.jobs);
    populateJobDropdown(state.jobs);
  } catch (e) {
    grid.innerHTML = `<div class="loading-state text-red">Error: ${e.message}</div>`;
  }
}

function renderJobs(jobs) {
  const grid = document.getElementById('jobsGrid');
  if (!jobs.length) {
    grid.innerHTML = '<div class="loading-state text-muted">No jobs posted yet. Click "Post New Job" to begin.</div>';
    return;
  }
  grid.innerHTML = jobs.map(job => `
    <div class="job-card" onclick="viewJobDetails(${job.id})">
      <div class="job-card-header">
        <div>
          <div class="job-card-title">${escHtml(job.title)}</div>
          <div class="job-card-dept">${escHtml(job.department || '')} ${job.location ? '· ' + escHtml(job.location) : ''}</div>
        </div>
        <span class="badge ${job.status === 'active' ? 'badge-green' : 'badge-gray'}">${job.status}</span>
      </div>
      <div class="job-card-meta">
        <span class="badge badge-blue">${escHtml(job.employment_type)}</span>
        <span class="badge badge-orange">${job.experience_years_min}–${job.experience_years_max} yrs</span>
        <span class="badge badge-purple">${escHtml(job.education_level || 'Any')}</span>
        ${job.bias_score > 30 ? `<span class="badge badge-red">⚠ Bias ${job.bias_score.toFixed(0)}%</span>` : ''}
      </div>
      <div class="job-card-skills">
        ${job.required_skills.slice(0, 5).map(s => `<span class="skill-tag">${escHtml(s)}</span>`).join('')}
        ${job.required_skills.length > 5 ? `<span class="skill-tag">+${job.required_skills.length - 5}</span>` : ''}
      </div>
      <div class="job-card-footer">
        <span class="text-muted" style="font-size:12px">${job.candidate_count} screened</span>
        <div style="display:flex;gap:6px">
          <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); quickScreen(${job.id})">🤖 Screen</button>
          <button class="btn btn-sm btn-danger" onclick="deleteJob(event, ${job.id})">🗑</button>
        </div>
      </div>
    </div>
  `).join('');
}

function filterJobs() {
  const q = document.getElementById('jobSearch').value.toLowerCase();
  const status = document.getElementById('jobStatusFilter').value;
  const filtered = state.jobs.filter(j => {
    const matchQ = !q || j.title.toLowerCase().includes(q) || (j.department || '').toLowerCase().includes(q);
    const matchStatus = status === 'all' || j.status === status;
    return matchQ && matchStatus;
  });
  renderJobs(filtered);
}

async function viewJobDetails(jobId) {
  try {
    const job = await API.get(`/jobs/${jobId}`);
    state.selectedJobId = jobId;
    document.getElementById('jobDetailsTitle').textContent = job.title;
    document.getElementById('jobDetailsBody').innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
        <div><span class="form-label">Department</span><br><span>${escHtml(job.department || '—')}</span></div>
        <div><span class="form-label">Location</span><br><span>${escHtml(job.location || '—')}</span></div>
        <div><span class="form-label">Type</span><br><span>${escHtml(job.employment_type)}</span></div>
        <div><span class="form-label">Experience</span><br><span>${job.experience_years_min}–${job.experience_years_max} years</span></div>
        <div><span class="form-label">Education</span><br><span>${escHtml(job.education_level || 'Any')}</span></div>
        <div><span class="form-label">Candidates Screened</span><br><span>${job.candidate_count}</span></div>
      </div>
      <div style="margin-bottom:16px">
        <span class="form-label">Required Skills</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">
          ${job.required_skills.map(s => `<span class="skill-tag">${escHtml(s)}</span>`).join('') || '<span class="text-muted">None detected</span>'}
        </div>
      </div>
      <div style="margin-bottom:16px">
        <span class="form-label">Preferred Skills</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">
          ${job.preferred_skills.map(s => `<span class="skill-tag">${escHtml(s)}</span>`).join('') || '<span class="text-muted">None detected</span>'}
        </div>
      </div>
      ${job.bias_score > 0 ? `
        <div class="bias-preview" style="display:block">
          <h4>⚖️ Bias Analysis — Score: ${job.bias_score}%</h4>
          ${job.bias_flags.map(f => `<div class="bias-flag ${f.severity}">${f.description}</div>`).join('')}
        </div>
      ` : ''}
      <div style="margin-top:16px">
        <span class="form-label">Description</span>
        <p style="margin-top:8px;color:var(--text-secondary);font-size:14px;white-space:pre-wrap;max-height:250px;overflow:auto">
          ${escHtml(job.description)}
        </p>
      </div>
    `;
    openModal('jobDetailsModal');
  } catch (e) {
    toast('Failed to load job: ' + e.message, 'error');
  }
}

function screenThisJob() {
  closeModal('jobDetailsModal');
  navigate('screening');
  setTimeout(() => {
    const sel = document.getElementById('screeningJob');
    if (sel) { sel.value = state.selectedJobId; loadJobDetails(); }
  }, 300);
}

async function quickScreen(jobId) {
  navigate('screening');
  setTimeout(async () => {
    const sel = document.getElementById('screeningJob');
    if (sel) { sel.value = jobId; await loadJobDetails(); await runScreening(); }
  }, 300);
}

async function deleteJob(event, jobId) {
  if (event) event.stopPropagation();
  if (!confirm('Delete this job posting? All its screening results will also be deleted.')) return;
  try {
    const r = await API.delete(`/jobs/${jobId}`);
    toast('Job deleted', 'success');
    loadJobs();
  } catch (e) {
    toast('Error: ' + e.message, 'error');
  }
}

async function previewBiasJob() {
  const desc = document.getElementById('jDesc').value.trim();
  if (!desc) { toast('Enter a job description first', 'warning'); return; }
  try {
    const result = await API.post('/jobs/analyze', { description: desc });
    const bias = result.bias;
    const preview = document.getElementById('biasPreview');
    const content = document.getElementById('biasContent');
    content.innerHTML = `
      <p style="font-size:13px;margin-bottom:8px">Bias Score: <strong style="color:${bias.score > 30 ? 'var(--red)' : 'var(--green)'}">${bias.score}%</strong> — ${bias.summary}</p>
      ${bias.flags.map(f => `<div class="bias-flag ${f.severity}">${f.description}</div>`).join('')}
      ${bias.suggestions.map(s => `<div class="badge badge-orange" style="margin:4px 0;display:inline-block;border-radius:6px;font-size:11px">
        Tip: Replace "<strong>${escHtml(s.term)}</strong>" with "<strong>${escHtml(s.suggestion)}</strong>"
      </div>`).join('')}
    `;
    preview.style.display = 'block';
  } catch (e) {
    toast('Bias check failed: ' + e.message, 'error');
  }
}

async function submitJob() {
  const title = document.getElementById('jTitle').value.trim();
  const desc = document.getElementById('jDesc').value.trim();
  if (!title || !desc) { toast('Title and description are required', 'warning'); return; }

  const payload = {
    title, description: desc,
    department: document.getElementById('jDept').value,
    location: document.getElementById('jLocation').value,
    employment_type: document.getElementById('jType').value,
    experience_years_min: parseInt(document.getElementById('jExpMin').value) || 0,
    experience_years_max: parseInt(document.getElementById('jExpMax').value) || 5,
    education_level: document.getElementById('jEdu').value,
    salary_min: parseInt(document.getElementById('jSalMin').value) || 0,
    salary_max: parseInt(document.getElementById('jSalMax').value) || 0,
  };

  try {
    const result = await API.post('/jobs/', payload);
    toast('Job posted successfully!', 'success');
    closeModal('jobModal');
    clearJobForm();
    loadJobs();

    // Show bias warning if high
    if (result.bias && result.bias.score > 30) {
      setTimeout(() => toast(`⚠️ Bias detected in JD (${result.bias.score}%). Consider reviewing the language.`, 'warning'), 500);
    }
  } catch (e) {
    toast('Error posting job: ' + e.message, 'error');
  }
}

function clearJobForm() {
  ['jTitle', 'jDept', 'jLocation', 'jDesc', 'jSalMin', 'jSalMax'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  document.getElementById('biasPreview').style.display = 'none';
  document.getElementById('jExpMin').value = 2;
  document.getElementById('jExpMax').value = 6;
}

/* ══════════════  CANDIDATES  ═════════════════════════ */
async function loadCandidates() {
  const tbody = document.getElementById('candidatesBody');
  tbody.innerHTML = '<tr><td colspan="7" class="empty-row"><span class="spinner"></span> Loading...</td></tr>';
  try {
    const data = await API.get('/candidates/?per_page=100');
    state.candidates = data.candidates;

    const count = data.total;
    document.getElementById('candidateCount').textContent = count;
    document.getElementById('pool-total').textContent = count;

    // Calculate Stats
    if (count > 0) {
      const masters = state.candidates.filter(c => (c.education_level || '').toLowerCase().includes('master') || (c.education_level || '').toLowerCase().includes('phd')).length;

      const skillFreq = {};
      state.candidates.forEach(c => {
        c.skills.forEach(s => { const sk = s.trim(); skillFreq[sk] = (skillFreq[sk] || 0) + 1; });
      });
      const topSkill = Object.entries(skillFreq).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A';

      const techKeywords = ['python', 'java', 'sql', 'react', 'javascript', 'aws', 'docker', 'cloud', 'git', 'c++', 'ml', 'ai'];
      const techCount = state.candidates.filter(c =>
        c.skills.some(s => techKeywords.includes(s.toLowerCase()))
      ).length;
      const techDensity = Math.round((techCount / count) * 100);

      document.getElementById('pool-top-skill').textContent = topSkill;
      document.getElementById('pool-masters').textContent = masters;
      document.getElementById('pool-tech').textContent = techDensity + '%';
    }

    renderCandidates(state.candidates);
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-row text-red">Error: ${e.message}</td></tr>`;
  }
}

function renderCandidates(candidates) {
  const tbody = document.getElementById('candidatesBody');
  if (!candidates.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-row">No candidates yet. Upload resumes to get started.</td></tr>';
    return;
  }
  tbody.innerHTML = candidates.map(c => `
    <tr class="candidate-row" style="cursor: pointer;" onclick="viewCandidate(${c.id})">
      <td>
        <div style="display:flex; align-items:center; gap:12px;">
          <div style="width:32px; height:32px; background:var(--bg-card); border:1px solid var(--border); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:14px;">👤</div>
          <div>
            <div style="font-weight:700; color:var(--text-primary);">${escHtml(c.name || 'Unknown')}</div>
            <div style="font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px;">${c.file_type?.toUpperCase() || ''} SOURCE</div>
          </div>
        </div>
      </td>
      <td style="font-size:13px; color:var(--text-secondary); font-family:monospace;">${escHtml(c.email || '—')}</td>
      <td>
        <div style="display:flex; gap:4px; flex-wrap:wrap">
          ${c.skills.slice(0, 3).map(s => `<span class="skill-tag" style="background:rgba(14, 165, 233, 0.1); color:#0EA5E9; border:none; padding:2px 8px; font-weight:600;">${escHtml(s)}</span>`).join('')}
          ${c.skills.length > 3 ? `<span class="skill-tag" style="background:var(--bg-card); color:var(--text-muted); border:1px dashed var(--border);">+${c.skills.length - 3}</span>` : ''}
        </div>
      </td>
      <td>
        <span class="badge ${c.experience_years >= 5 ? 'badge-purple' : 'badge-blue'}" style="font-weight:700;">
          ${c.experience_years ? c.experience_years + ' Years' : 'Fresher'}
        </span>
      </td>
      <td style="font-size:12px; font-weight:500; color:var(--text-secondary);">${escHtml(c.education_level || '—')}</td>
      <td style="font-size:11px; color:var(--text-muted); white-space:nowrap;">${formatDate(c.created_at)}</td>
      <td>
        <div style="display:flex; gap:6px" onclick="event.stopPropagation();">
          <button class="btn btn-sm btn-ghost" onclick="viewCandidate(${c.id})" title="View Professional Profile">👁️ Details</button>
          <button class="btn btn-sm btn-danger" onclick="deleteCandidate(event, ${c.id})" title="Remove from Pool">🗑️</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function filterCandidates() {
  const q = document.getElementById('candidateSearch').value.toLowerCase();
  const filtered = state.candidates.filter(c =>
    (c.name || '').toLowerCase().includes(q) ||
    (c.email || '').toLowerCase().includes(q)
  );
  renderCandidates(filtered);
}

async function viewCandidate(id) {
  try {
    state.viewingCandidateId = id;
    const c = await API.get(`/candidates/${id}`);

    // Check if this candidate has recent screening scores we can show
    const recentResult = state.screeningResults?.find(r => r.candidate_id === id);

    document.getElementById('candidateModalTitle').textContent = c.name || 'Unknown Candidate';

    // Fill the info panel (Left side)
    const infoPanel = document.getElementById('candidateInfoPanel');
    infoPanel.innerHTML = `
      <div style="overflow-y:auto;max-height:650px;padding-right:12px;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
          <div><span class="form-label">Email</span><br>${escHtml(c.email || '—')}</div>
          <div><span class="form-label">Phone</span><br>${escHtml(c.phone || '—')}</div>
          <div><span class="form-label">Experience</span><br>${c.experience_years ? c.experience_years + ' years' : '—'}</div>
          <div><span class="form-label">Education</span><br>${escHtml(c.education_level || '—')}</div>
        </div>
        ${c.job_titles.length ? `
          <div style="margin-bottom:16px">
            <span class="form-label">Previous Roles</span>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">
              ${c.job_titles.map(t => `<span class="badge badge-cyan">${escHtml(t)}</span>`).join('')}
            </div>
          </div>
        ` : ''}
        <div style="margin-bottom:16px">
          <span class="form-label">Skills (${c.skills.length})</span>
          <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">
            ${c.skills.map(s => `<span class="skill-tag">${escHtml(s)}</span>`).join('')}
          </div>
        </div>
        ${c.summary ? `
          <div style="margin-bottom:24px">
            <span class="form-label">AI Summary</span>
            <p style="margin-top:8px;font-size:13px;color:var(--text-secondary);line-height:1.7">
              ${escHtml(c.summary)}
            </p>
          </div>
        ` : ''}
        <div style="height:450px;background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
          <iframe src="/api/candidates/${c.id}/view" style="width:100%;height:100%;border:none;"></iframe>
        </div>
      </div>
    `;

    // Render/Manage the Radar Chart (Right side)
    const chartPanel = document.getElementById('candidateChartPanel');
    const legend = document.getElementById('fitLegend');

    if (recentResult) {
      chartPanel.style.display = 'block';
      renderFitChart(recentResult);
      legend.innerHTML = `
        <div style="background:rgba(16, 185, 129, 0.1); padding:10px; border-radius:8px; border-left:4px solid #10B981;">
          <strong>🎯 AI Insights:</strong> ${recentResult.explanation}
        </div>
      `;
    } else {
      // If viewed from candidates list (no screening context)
      chartPanel.style.display = 'block'; // Keep it visible but show "No data"
      renderFitChart({ semantic_score: 0, skill_match_score: 0, experience_score: 0, education_score: 0, location_score: 0 });
      legend.innerHTML = '<p class="text-muted" style="text-align:center">Run screening to see 5-point fit analysis (Semantic, Skills, Experience, Education, Location)</p>';
    }

    openModal('candidateModal');
  } catch (e) {
    toast('Error: ' + e.message, 'error');
  }
}

function renderFitChart(res) {
  const ctx = document.getElementById('candidateFitChart');
  if (!ctx) return;

  // Destroy existing chart if it exists
  if (state.charts.fitChart) state.charts.fitChart.destroy();

  state.charts.fitChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Semantic', 'Skills', 'Ex', 'Edu', 'Loc'],
      datasets: [{
        label: 'Candidate Score %',
        data: [res.semantic_score, res.skill_match_score, res.experience_score, res.education_score, res.location_score || 0],
        backgroundColor: 'rgba(14, 165, 233, 0.2)',
        borderColor: '#0EA5E9',
        borderWidth: 2,
        pointBackgroundColor: '#0EA5E9',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: '#0EA5E9'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0,
          max: 100,
          beginAtZero: true,
          ticks: { display: false, stepSize: 20 },
          grid: { color: 'rgba(255,255,255,0.05)' },
          angleLines: { color: 'rgba(255,255,255,0.05)' },
          pointLabels: { color: '#8B95B0', font: { size: 11, weight: 'bold' } }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

async function deleteCandidate(event, id) {
  if (event) event.stopPropagation();
  if (!confirm('Delete this candidate and their resume?')) return;
  try {
    await API.delete(`/candidates/${id}`);
    toast('Candidate removed', 'success');
    loadCandidates();
  } catch (e) {
    toast('Error: ' + e.message, 'error');
  }
}


/* ── Drag & Drop Upload ─────────────────────────────── */
const uploadZone = document.getElementById('uploadZone');
uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('dragging'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragging'));
uploadZone.addEventListener('drop', async e => {
  e.preventDefault();
  uploadZone.classList.remove('dragging');
  const files = Array.from(e.dataTransfer.files);
  await uploadFiles(files);
});
uploadZone.addEventListener('click', () => document.getElementById('fileInput').click());

function handleFileSelect(event) {
  const files = Array.from(event.target.files);
  uploadFiles(files);
  event.target.value = '';
}

async function uploadFiles(files) {
  if (!files.length) return;
  const progressDiv = document.getElementById('uploadProgress');
  progressDiv.style.display = 'block';
  progressDiv.innerHTML = files.map(f => `
    <div class="upload-progress-item" id="prog-${f.name.replace(/\W/g, '_')}">
      <span class="spinner"></span>
      <span>${escHtml(f.name)}</span>
      <span style="margin-left:auto;color:var(--text-muted);font-size:11px">${(f.size / 1024).toFixed(0)} KB</span>
    </div>
  `).join('');

  const formData = new FormData();
  files.forEach(f => formData.append('files', f));

  try {
    const result = await API.uploadFiles('/candidates/upload', formData);
    toast(`✅ ${result.count} resume(s) uploaded and parsed!`, 'success');
    if (result.errors.length) {
      result.errors.forEach(e => toast(e, 'error'));
    }
    progressDiv.style.display = 'none';
    loadCandidates();
  } catch (e) {
    toast('Upload failed: ' + e.message, 'error');
    progressDiv.style.display = 'none';
  }
}

/* ══════════════  SCREENING  ══════════════════════════ */
async function loadScreeningPage() {
  try {
    const data = await API.get('/jobs/?status=active&per_page=50');
    populateJobDropdown(data.jobs);
  } catch (e) {
    toast('Failed to load jobs: ' + e.message, 'error');
  }
}

function populateJobDropdown(jobs) {
  const sel = document.getElementById('screeningJob');
  if (!sel) return;
  sel.innerHTML = '<option value="">— Choose a job —</option>';
  jobs.filter(j => j.status === 'active').forEach(j => {
    const opt = document.createElement('option');
    opt.value = j.id;
    opt.textContent = j.title + (j.department ? ` (${j.department})` : '');
    sel.appendChild(opt);
  });
}

async function loadJobDetails() {
  const jobId = document.getElementById('screeningJob').value;
  const btn = document.getElementById('runScreenBtn');
  const hint = document.getElementById('screeningHint');
  const preview = document.getElementById('jobPreview');

  if (!jobId) {
    btn.disabled = true;
    hint.textContent = 'Select a job to screen candidates';
    preview.style.display = 'none';
    return;
  }

  try {
    const job = await API.get(`/jobs/${jobId}`);
    state.selectedJobId = jobId;
    btn.disabled = false;
    hint.textContent = `${job.candidate_count} candidates previously screened`;
    preview.style.display = 'block';
    document.getElementById('previewBadges').innerHTML = `
      <span class="badge badge-purple">${escHtml(job.title)}</span>
      <span class="badge badge-blue">${job.experience_years_min}–${job.experience_years_max} yrs</span>
      <span class="badge badge-orange">${job.required_skills.length} req. skills</span>
      ${job.bias_score > 30 ? `<span class="badge badge-red">⚠ Bias ${job.bias_score.toFixed(0)}%</span>` : ''}
    `;
  } catch (e) {
    toast('Error loading job: ' + e.message, 'error');
  }
}

function updateWeightDisplay() {
  const wsElem = document.getElementById('wSemantic');
  const wkElem = document.getElementById('wSkills');
  const wlElem = document.getElementById('wLocation');
  const ws = wsElem.value;
  const wk = wkElem.value;
  const wl = wlElem.value;

  wsElem.style.setProperty('--val', ws + '%');
  wkElem.style.setProperty('--val', wk + '%');
  wlElem.style.setProperty('--val', wl + '%');

  document.getElementById('wSemanticVal').textContent = ws + '%';
  document.getElementById('wSkillsVal').textContent = wk + '%';
  document.getElementById('wLocationVal').textContent = wl + '%';
}

async function runScreening() {
  const jobId = document.getElementById('screeningJob').value;
  if (!jobId) { toast('Please select a job first', 'warning'); return; }

  const progress = document.getElementById('screeningProgress');
  const progressBar = document.getElementById('progressBar');
  const progressText = document.getElementById('progressText');
  const runBtn = document.getElementById('runScreenBtn');

  runBtn.disabled = true;
  progress.style.display = 'block';
  document.getElementById('resultsSection').style.display = 'none';

  // Simulate progress stages
  const stages = [
    { pct: 10, text: '🔍 Fetching candidates...' },
    { pct: 30, text: '🧠 Computing semantic embeddings...' },
    { pct: 55, text: '📊 Matching skills and experience...' },
    { pct: 75, text: '⚖️ Applying bias-aware ranking...' },
    { pct: 90, text: '💾 Saving results...' },
  ];

  let stageIdx = 0;
  const stageInterval = setInterval(() => {
    if (stageIdx < stages.length) {
      const st = stages[stageIdx++];
      progressBar.style.width = st.pct + '%';
      progressText.textContent = st.text;
    }
  }, 500);

  const ws = parseInt(document.getElementById('wSemantic').value) / 100;
  const wk = parseInt(document.getElementById('wSkills').value) / 100;
  const wl = parseInt(document.getElementById('wLocation').value) / 100;
  const rem = 1.0 - (ws + wk + wl);

  const weights = {
    semantic: ws,
    skills: wk,
    location: wl,
    experience: Math.max(rem * 0.6, 0.0),
    education: Math.max(rem * 0.4, 0.0),
  };

  try {
    const result = await API.post('/screening/screen', {
      job_id: parseInt(jobId),
      refresh: true,
      weights,
    });

    clearInterval(stageInterval);
    progressBar.style.width = '100%';
    progressText.textContent = '✅ Screening complete!';

    setTimeout(() => {
      progress.style.display = 'none';
      runBtn.disabled = false;
      state.screeningResults = result.results;
      renderResults(result);
      toast(`Screening done! ${result.shortlisted} candidate(s) shortlisted.`, 'success');
    }, 600);

  } catch (e) {
    clearInterval(stageInterval);
    progress.style.display = 'none';
    runBtn.disabled = false;
    toast('Screening failed: ' + e.message, 'error');
  }
}

function renderResults(data) {
  const section = document.getElementById('resultsSection');
  section.style.display = 'block';
  document.getElementById('resultsTitle').textContent = `Results — ${data.job_title}`;

  const s = data;
  document.getElementById('resultsStats').innerHTML = `
    <span class="badge badge-green">✅ ${s.shortlisted || 0} Shortlisted</span>
    <span class="badge badge-gray">Total: ${s.total_screened || 0}</span>
  `;

  // Score distribution chart
  const scores = data.results.map(r => r.overall_score);
  renderScoreDistChart(scores);

  state.screeningResults = data.results;
  filterResults('all');
}

function renderScoreDistChart(scores) {
  const ctx = document.getElementById('scoreDistChart');
  if (!ctx) return;
  if (state.charts.scoreDist) state.charts.scoreDist.destroy();
  const buckets = new Array(10).fill(0);
  scores.forEach(s => { buckets[Math.min(Math.floor(s / 10), 9)]++; });
  state.charts.scoreDist = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['0-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90-100'],
      datasets: [{
        label: 'Candidates',
        data: buckets,
        backgroundColor: buckets.map((_, i) =>
          i >= 7 ? 'rgba(16,185,129,0.7)' : i >= 4 ? 'rgba(245,158,11,0.7)' : 'rgba(239,68,68,0.7)'
        ),
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#8B95B0' }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { ticks: { color: '#8B95B0', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.04)' } },
      },
    },
  });
}

function filterResults(filter) {
  state.currentResultFilter = filter;
  document.querySelectorAll('.status-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.status-tab').forEach(t => {
    if (t.textContent.toLowerCase().includes(filter) || (filter === 'all' && t.textContent === 'All')) {
      t.classList.add('active');
    }
  });

  const filtered = filter === 'all'
    ? state.screeningResults
    : state.screeningResults.filter(r => r.status === filter);

  const grid = document.getElementById('resultsGrid');
  if (!filtered.length) {
    grid.innerHTML = '<div class="loading-state text-muted">No candidates in this category.</div>';
    return;
  }

  grid.innerHTML = filtered.map(r => {
    const c = r.candidate;
    const isTop = r.rank <= 3;
    return `
      <div class="result-card ${r.status}">
        <div class="result-rank ${isTop ? 'top' : ''}">${r.rank}</div>
        <div class="result-info">
          <div class="result-name">${escHtml(c?.name || 'Unknown')}</div>
          <div class="result-meta">
            ${c?.email ? `📧 ${escHtml(c.email)}` : ''}
            ${c?.experience_years ? ` · ${c.experience_years} yrs exp` : ''}
            ${c?.education_level ? ` · ${escHtml(c.education_level)}` : ''}
          </div>
          <div class="result-skills">
            ${r.matched_skills.slice(0, 5).map(s => `<span class="skill-tag matched">✓ ${escHtml(s)}</span>`).join('')}
            ${r.missing_skills.slice(0, 3).map(s => `<span class="skill-tag missing">✗ ${escHtml(s)}</span>`).join('')}
          </div>
          <div class="result-explanation">${escHtml(r.explanation || '')}</div>
          <div style="margin-top:10px;display:flex;gap:8px">
            <select class="filter-select" style="font-size:11px;padding:4px 8px" onchange="updateStatus(${r.job_id}, ${r.candidate_id}, this.value)">
              <option value="shortlisted" ${r.status === 'shortlisted' ? 'selected' : ''}>✅ Shortlisted</option>
              <option value="pending"     ${r.status === 'pending' ? 'selected' : ''}>🕐 Pending</option>
              <option value="rejected"    ${r.status === 'rejected' ? 'selected' : ''}>❌ Rejected</option>
            </select>
            <button class="btn btn-sm btn-ghost" onclick="viewCandidate(${r.candidate_id})">View Profile</button>
          </div>
        </div>
        <div class="result-scores">
          <div class="overall-score">
            <div class="overall-score-val">${r.overall_score}%</div>
            <div class="overall-score-label">Overall Match</div>
          </div>
          ${statusBadge(r.status)}
          ${scoreBar('Semantic', r.semantic_score, '#0EA5E9')}
          ${scoreBar('Skills', r.skill_match_score, '#10B981')}
          ${scoreBar('Experience', r.experience_score, '#10B981')}
          ${scoreBar('Education', r.education_score, '#F59E0B')}
        </div>
      </div>
    `;
  }).join('');
}

async function updateStatus(jobId, candidateId, newStatus) {
  try {
    await API.patch(`/screening/results/${jobId}/candidate/${candidateId}`, { status: newStatus });
    toast(`Status updated to ${newStatus}`, 'success');
    if (newStatus === 'rejected') {
      alert(`An automated rejection email has been routed to the candidate.`);
    }
    const sr = state.screeningResults.find(r => r.job_id === jobId && r.candidate_id === candidateId);
    if (sr) sr.status = newStatus;
  } catch (e) {
    toast('Error: ' + e.message, 'error');
  }
}

async function downloadReport() {
  const jobId = state.selectedJobId;
  if (!jobId) {
    toast('No job selected', 'warning');
    return;
  }

  const btn = document.getElementById('downloadReportBtn');
  const originalText = btn.innerHTML;
  btn.innerHTML = '<span class="spinner"></span> Generating...';
  btn.disabled = true;

  try {
    const response = await fetch(`/api/screening/results/${jobId}/export/csv`);
    if (!response.ok) throw new Error('Export failed or no data available');

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    // Attempt to get filename from header or use default
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `HireIQ_Report_Job_${jobId}.csv`;
    if (contentDisposition && contentDisposition.indexOf('filename=') !== -1) {
      filename = contentDisposition.split('filename=')[1].replace(/"/g, '');
    }

    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();

    toast('Report downloaded successfully!', 'success');
  } catch (e) {
    toast('Error downloading report: ' + e.message, 'error');
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

/* ── Modals ─────────────────────────────────────────── */
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('open');
  });
});

/* ── Toasts ─────────────────────────────────────────── */
function toast(message, type = 'info', duration = 4000) {
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span>${icons[type]}</span><span>${message}</span>`;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(100px)'; el.style.transition = 'all 0.3s'; setTimeout(() => el.remove(), 300); }, duration);
}

/* ── Helpers ────────────────────────────────────────── */
function escHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function scoreColor(s) {
  if (s >= 70) return 'var(--green)';
  if (s >= 45) return 'var(--orange)';
  return 'var(--red)';
}

function statusBadge(status) {
  const map = { shortlisted: 'badge-green', pending: 'badge-orange', rejected: 'badge-red', active: 'badge-green', closed: 'badge-gray' };
  return `<span class="badge ${map[status] || 'badge-gray'}">${status}</span>`;
}

function scoreBar(label, value, color) {
  return `
    <div class="score-bar">
      <div class="score-bar-label">
        <span>${label}</span><span>${value}%</span>
      </div>
      <div class="score-bar-track">
        <div class="score-bar-fill" style="width:${value}%;background:${color}"></div>
      </div>
    </div>
  `;
}

/* ── Boot ───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  navigate('dashboard');
});
