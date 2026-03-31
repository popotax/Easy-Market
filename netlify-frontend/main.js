const form = document.getElementById("estimate-form");
const tagInput = document.getElementById("tag");
const errorBox = document.getElementById("error");
const resultSection = document.getElementById("result");

const playerName = document.getElementById("playerName");
const playerTag = document.getElementById("playerTag");
const valueMain = document.getElementById("valueMain");
const valueRange = document.getElementById("valueRange");
const statTrophies = document.getElementById("statTrophies");
const statBrawlers = document.getElementById("statBrawlers");
const statAvg = document.getElementById("statAvg");
const statProgress = document.getElementById("statProgress");

// Fixed backend URL. Only the owner runs this backend when needed.
const BACKEND_BASE_URL = "http://192.168.0.102:5001";

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function clearError() {
  errorBox.textContent = "";
  errorBox.classList.add("hidden");
}

function showResult(data) {
  playerName.textContent = data.name;
  playerTag.textContent = data.tag;
  valueMain.textContent = `$${Number(data.estimated_value).toFixed(2)}`;
  valueRange.textContent = `Range: $${Number(data.range_low).toFixed(2)} - $${Number(data.range_high).toFixed(2)}`;
  statTrophies.textContent = String(data.trophies);
  statBrawlers.textContent = String(data.num_brawlers);
  statAvg.textContent = String(data.avg_level);
  statProgress.textContent = String(data.account_progress_score);
  resultSection.classList.remove("hidden");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  resultSection.classList.add("hidden");

  const backendUrl = backendUrlInput.value.trim().replace(/\/$/, "");
  const tag = tagInput.value.trim();

  if (!tag) {
    showError("Please enter a player tag.");
    return;
  }

  if (BACKEND_BASE_URL.includes("replace-with-your-backend-url")) {
    showError("Backend URL is not configured by the owner.");
    return;
  }

  try {
    const resp = await fetch(`${BACKEND_BASE_URL.replace(/\/$/, "")}/api/estimate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ tag }),
    });

    const payload = await resp.json().catch(() => ({}));

    if (!resp.ok || !payload.ok) {
      showError(payload.error || `Request failed (${resp.status})`);
      return;
    }

    showResult(payload.result);
  } catch (error) {
    showError(`Cannot reach backend: ${error}`);
  }
});
