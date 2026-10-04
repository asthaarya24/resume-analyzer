"use strict";

const API = "http://127.0.0.1:5001";

// ── DOM ──────────────────────────────────────────────────
const dropZone    = document.getElementById("dropZone");
const fileInput   = document.getElementById("fileInput");
const fileTag     = document.getElementById("fileTag");
const jobDesc     = document.getElementById("jobDesc");
const charCount   = document.getElementById("charCount");
const wordCount   = document.getElementById("wordCount");
const runBtn      = document.getElementById("runBtn");
const errBar      = document.getElementById("errBar");
const logPanel    = document.getElementById("logPanel");
const logLines    = document.getElementById("logLines");
const inputGrid   = document.getElementById("inputGrid");
const results     = document.getElementById("results");
const resetBtn    = document.getElementById("resetBtn");
const statusDot   = document.getElementById("statusDot");
const statusLabel = document.getElementById("statusLabel");

let pickedFile = null;

// ── HEALTH CHECK ─────────────────────────────────────────
async function checkHealth() {
  try {
    const r = await fetch(`${API}/health`);
    if (r.ok) {
      statusDot.classList.add("online");
      statusLabel.textContent = "FLASK ONLINE";
    }
  } catch {
    statusLabel.textContent = "OFFLINE";
  }
}
checkHealth();
setInterval(checkHealth, 10000);

// ── FILE HANDLING ─────────────────────────────────────────
dropZone.addEventListener("dragover",  e => { e.preventDefault(); dropZone.classList.add("over"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault(); dropZone.classList.remove("over");
  const f = e.dataTransfer.files[0];
  f?.type === "application/pdf" ? setFile(f) : showErr("PDF files only.");
});
dropZone.addEventListener("click", e => {
  if (!e.target.classList.contains("browse-btn")) fileInput.click();
});
fileInput.addEventListener("change", () => fileInput.files[0] && setFile(fileInput.files[0]));

function setFile(f) {
  pickedFile = f;
  fileTag.textContent = `[ ${f.name} — ${(f.size/1024).toFixed(1)} KB ]`;
  clearErr();
}

// ── JD COUNTERS ──────────────────────────────────────────
jobDesc.addEventListener("input", () => {
  const v = jobDesc.value;
  charCount.textContent = `${v.length} chars`;
  wordCount.textContent = `${v.trim() ? v.trim().split(/\s+/).length : 0} words`;
});

// ── ANALYSE ──────────────────────────────────────────────
runBtn.addEventListener("click", run);

async function run() {
  clearErr();
  if (!pickedFile)            return showErr("No PDF selected.");
  if (!jobDesc.value.trim())  return showErr("Job description is empty.");

  const fd = new FormData();
  fd.append("resume",   pickedFile);
  fd.append("job_desc", jobDesc.value.trim());

  // Switch UI to log view
  inputGrid.style.display = "none";
  runBtn.disabled = true;
  logPanel.style.display  = "block";
  results.style.display   = "none";
  buildLog();

  try {
    const res  = await fetch(`${API}/analyze`, { method: "POST", body: fd });
    const data = await res.json();

    if (!res.ok || data.error) {
      restoreInput();
      return showErr(data.error || `Server error ${res.status}`);
    }

    await sleep(400);
    finishLog();
    await sleep(300);
    render(data);

  } catch (err) {
    console.error(err);
    restoreInput();
    showErr("Cannot reach Flask. Make sure `python app.py` is running on port 5000.");
  }
}

// ── LOG ANIMATION ─────────────────────────────────────────
const LOG_STEPS = [
  "Extracting PDF text …",
  "Matching skills against database …",
  "Running spaCy NLP analysis …",
  "Computing BERT semantic similarity …",
  "Generating Gemini AI insights …",
];

function buildLog() {
  logLines.innerHTML = "";
  LOG_STEPS.forEach((txt, i) => {
    const d = document.createElement("div");
    d.className = "log-line";
    d.id = `log${i}`;
    d.textContent = txt;
    logLines.appendChild(d);
    setTimeout(() => {
      if (i > 0) document.getElementById(`log${i-1}`)?.classList.replace("active","done");
      d.classList.add("active");
    }, i * 1300);
  });
}

function finishLog() {
  LOG_STEPS.forEach((_, i) => {
    const el = document.getElementById(`log${i}`);
    el?.classList.remove("active");
    el?.classList.add("done");
  });
}

// ── RENDER RESULTS ────────────────────────────────────────
function render(d) {
  logPanel.style.display = "none";
  results.style.display  = "block";

  // Arc score
  const score = d.score ?? 0;
  const arc   = document.getElementById("arcFill");
  const circ  = 251.2;
  setTimeout(() => {
    arc.style.strokeDashoffset = circ - (score / 100) * circ;
    if      (score >= 70) arc.style.stroke = "var(--green)";
    else if (score >= 45) arc.style.stroke = "#ffcc00";
    else                  arc.style.stroke = "var(--warn)";
    countUp("bigScore", 0, score, 1200);
  }, 100);

  // Sub-bars
  bar("sbarBert",  "valBert",  d.bert_score);
  bar("sbarSkill", "valSkill", d.skill_score);
  bar("sbarKw",    "valKw",    d.keyword_score);

  // Skills
  chips("matchedChips", d.matched_skills  || [], "chip-ok");
  chips("missingChips", d.missing_skills  || [], "chip-bad");
  chips("resumeKwChips",d.resume_keywords || [], "chip-kw");
  chips("jdKwChips",    d.job_keywords    || [], "chip-kw");

  // Education & Experience
  const eduRow = document.getElementById("educationRow");
  const expRow = document.getElementById("experienceRow");
  if (eduRow) eduRow.innerHTML = "";
  if (expRow) expRow.innerHTML = "";
  const entPanel = document.getElementById("entitiesPanel");
  const hasEdu = d.education && d.education.length;
  const hasExp = d.experience && d.experience.length;
  if (hasEdu || hasExp) {
    entPanel.style.display = "block";
    chips("educationRow", d.education || [], "chip");
    chips("experienceRow", d.experience || [], "chip");
  } else {
    entPanel.style.display = "none";
  }

  // Insights
  const insightsEl = document.getElementById("insightsPre");
  insightsEl.innerHTML = formatInsights(d.insights || "No AI insights returned.");
}

// ── INSIGHTS FORMATTING ───────────────────────────────────
function formatInsights(text) {
  if (!text) return "No AI insights returned.";
  
  // Split into lines
  const lines = text.split('\n');
  let html = '';
  let inList = false;
  
  lines.forEach(line => {
    const trimmed = line.trim();
    
    // Empty line
    if (!trimmed) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      html += '<br>';
      return;
    }
    
    // Check for headers (lines that start with ** or are all caps/short)
    if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      const headerText = trimmed.replace(/\*\*/g, '').trim();
      html += `<h3>${headerText}</h3>`;
      return;
    }
    
    // Check for list items (lines starting with - or *)
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      if (!inList) {
        html += '<ul>';
        inList = true;
      }
      const itemText = trimmed.replace(/^[-*]\s+/, '').replace(/\*/g, '').trim();
      html += `<li>${itemText}</li>`;
      return;
    }
    
    // Regular paragraph - remove asterisks but keep bold
    if (inList) {
      html += '</ul>';
      inList = false;
    }
    
    // Convert **text** to <strong>text</strong> and remove other asterisks
    let formatted = trimmed
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*/g, '');
    
    html += `<p>${formatted}</p>`;
  });
  
  // Close any open list
  if (inList) {
    html += '</ul>';
  }
  
  return html;
}

// ── HELPERS ──────────────────────────────────────────────
function bar(trackId, valId, val) {
  setTimeout(() => {
    document.getElementById(trackId).style.width = `${val ?? 0}%`;
    document.getElementById(valId).textContent   = `${val ?? 0}%`;
  }, 350);
}

function chips(id, items, cls) {
  const el = document.getElementById(id);
  el.innerHTML = "";
  if (!items.length) {
    el.innerHTML = `<span class="none-note">— none found</span>`;
    return;
  }
  items.forEach(s => {
    const sp = document.createElement("span");
    sp.className = `chip ${cls}`;
    sp.textContent = s;
    el.appendChild(sp);
  });
}

function countUp(id, from, to, ms) {
  const el = document.getElementById(id);
  const t0 = performance.now();
  const tick = now => {
    const p = Math.min((now - t0) / ms, 1);
    el.textContent = Math.round(from + (to - from) * easeOut(p));
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
const easeOut = t => 1 - Math.pow(1 - t, 3);

function showErr(msg) { errBar.textContent = `ERROR: ${msg}`; }
function clearErr()   { errBar.textContent = ""; }
function sleep(ms)    { return new Promise(r => setTimeout(r, ms)); }

function restoreInput() {
  inputGrid.style.display = "";
  logPanel.style.display  = "none";
  runBtn.disabled = false;
  LOG_STEPS.forEach((_, i) => {
    const el = document.getElementById(`log${i}`);
    el?.classList.remove("active","done");
  });
}

// ── RESET ─────────────────────────────────────────────────
resetBtn.addEventListener("click", () => {
  pickedFile = null;
  fileInput.value = "";
  fileTag.textContent = "";
  jobDesc.value = "";
  charCount.textContent = "0 chars";
  wordCount.textContent = "0 words";
  clearErr();
  restoreInput();
  results.style.display = "none";
});
