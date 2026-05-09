const API_BASE = "";

let cooldownTimer = null;
let cooldownEndsAt = 0;

async function search() {
  if (cooldownTimer) return;

  const query = document.getElementById("query").value.trim();
  if (!query) return;

  setLoading(true);
  hideAll();

  try {
    const res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: 5 }),
    });

    if (res.status === 429) {
      const err = await res.json();
      const detail = err.detail || {};
      startCooldown(detail);
      return;
    }

    if (!res.ok) {
      const err = await res.json();
      const detail = err.detail;
      const msg = typeof detail === "string" ? detail : (detail?.message || "오류 발생");
      throw new Error(msg);
    }

    showResult(await res.json());
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
}

function showResult(data) {
  document.getElementById("answer").textContent = data.answer;
  document.getElementById("sources").textContent = `출처: ${data.sources.join(", ")}`;
  document.getElementById("elapsed").textContent = `${data.elapsed_ms}ms`;
  document.getElementById("result").classList.remove("hidden");
}

function showError(msg) {
  const box = document.getElementById("error");
  box.innerHTML = "";
  box.textContent = `오류: ${msg}`;
  box.classList.remove("hidden");
}

function startCooldown(detail) {
  const seconds = Math.max(1, parseInt(detail.retry_seconds, 10) || 60);
  cooldownEndsAt = Date.now() + seconds * 1000;

  const box = document.getElementById("error");
  box.classList.remove("hidden");
  box.classList.add("cooldown");

  const title = detail.is_daily_limit
    ? "오늘 무료 할당량 소진"
    : "요청이 너무 많습니다";

  const desc = detail.is_daily_limit
    ? "Gemini API 무료 일일 할당량(1,000건)을 모두 사용했습니다. 아래 시간 후 다시 시도할 수 있습니다."
    : "API rate limit에 도달했습니다. 아래 시간 후 다시 시도할 수 있습니다.";

  box.innerHTML = `
    <div class="cooldown-title">${title}</div>
    <div class="cooldown-desc">${desc}</div>
    <div class="cooldown-timer" id="cooldownTimer"></div>
    <div class="cooldown-hint">잠시만 기다려 주세요. 검색 버튼은 자동으로 다시 활성화됩니다.</div>
  `;

  setSearchDisabled(true);
  updateCooldownTimer();
  cooldownTimer = setInterval(updateCooldownTimer, 1000);
}

function updateCooldownTimer() {
  const remaining = Math.max(0, Math.ceil((cooldownEndsAt - Date.now()) / 1000));
  const el = document.getElementById("cooldownTimer");
  if (el) el.textContent = formatRemaining(remaining);

  if (remaining <= 0) {
    clearInterval(cooldownTimer);
    cooldownTimer = null;
    const box = document.getElementById("error");
    box.classList.remove("cooldown");
    box.classList.add("hidden");
    box.innerHTML = "";
    setSearchDisabled(false);
  }
}

function formatRemaining(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  const pad = (n) => String(n).padStart(2, "0");
  if (h > 0) return `${h}시간 ${pad(m)}분 ${pad(s)}초 남음`;
  if (m > 0) return `${m}분 ${pad(s)}초 남음`;
  return `${s}초 남음`;
}

function setSearchDisabled(disabled) {
  const btn = document.querySelector(".search-box button");
  const input = document.getElementById("query");
  if (btn) {
    btn.disabled = disabled;
    btn.textContent = disabled ? "대기 중…" : "검색";
  }
  if (input) input.disabled = disabled;
}

function setLoading(show) {
  document.getElementById("loading").classList.toggle("hidden", !show);
}

function hideAll() {
  document.getElementById("result").classList.add("hidden");
  if (!cooldownTimer) {
    const box = document.getElementById("error");
    box.classList.add("hidden");
    box.classList.remove("cooldown");
  }
}

document.getElementById("query").addEventListener("keydown", e => {
  if (e.key === "Enter") search();
});
