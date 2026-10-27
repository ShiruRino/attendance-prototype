// State App
let currentAttendanceType = "CHECK_IN";
let activeTab = "tab-attendance";
let webcamStream = null;
let currentPendingAttendance = null; // Data sementara yang menunggu konfirmasi modal
let registrationSnapshotBase64 = null;
let activeCandidates = [];
let selectedCandidateIndex = 0;
let activeRecognitionData = null;

// DOM Elements
const videoStream = document.getElementById("video-stream");
const regVideo = document.getElementById("reg-video");
const regPreview = document.getElementById("reg-preview");
const cameraPlaceholder = document.getElementById("camera-placeholder");
const scanningOverlay = document.getElementById("scanning-overlay");
const hiddenCanvas = document.getElementById("hidden-canvas");

// Modal Elements
const modalConfirm = document.getElementById("modal-confirm");
const modalSinglePreview = document.getElementById("modal-single-preview");
const modalMultiPreview = document.getElementById("modal-multi-preview");
const modalMultiCountLabel = document.getElementById("modal-multi-count-label");
const modalCandidatesList = document.getElementById("modal-candidates-list");
const modalConfirmQuestion = document.getElementById("modal-confirm-question");
const modalSnapshotImg = document.getElementById("modal-snapshot-img");
const modalUserName = document.getElementById("modal-user-name");
const modalEmployeeId = document.getElementById("modal-employee-id");
const modalAttendanceType = document.getElementById("modal-attendance-type");
const modalSimilarity = document.getElementById("modal-similarity");
const modalFallbackBadge = document.getElementById("modal-fallback-badge");
const btnModalConfirm = document.getElementById("btn-modal-confirm");

// Initialize on Load
document.addEventListener("DOMContentLoaded", () => {
  updateClock();
  setInterval(updateClock, 1000);
  startWebcam();
  loadLogs();
  loadUsers();
  if (window.lucide) {
    lucide.createIcons();
  }
});

// Real-time Clock
function updateClock() {
  const now = new Date();
  const timeStr = now.toLocaleTimeString("id-ID", { hour12: false });
  const dateStr = now.toLocaleDateString("id-ID", {
    weekday: "long",
    day: "numeric",
    month: "short",
    year: "numeric"
  });
  const clockEl = document.getElementById("current-clock");
  const dateEl = document.getElementById("current-date");
  if (clockEl) clockEl.innerText = timeStr;
  if (dateEl) dateEl.innerText = dateStr;
}

// Tab Switcher
function switchTab(tabId) {
  activeTab = tabId;
  const tabs = ["tab-attendance", "tab-registration", "tab-logs"];
  tabs.forEach(t => {
    const el = document.getElementById(t);
    const btn = document.getElementById("btn-" + t);
    if (t === tabId) {
      el.classList.remove("hidden");
      btn.className = "px-4 py-3 text-sm font-medium border-b-2 border-blue-500 text-zinc-100 flex items-center gap-2 transition-colors";
    } else {
      el.classList.add("hidden");
      btn.className = "px-4 py-3 text-sm font-medium border-b-2 border-transparent text-zinc-400 hover:text-zinc-200 flex items-center gap-2 transition-colors";
    }
  });

  // Switch webcam source
  if (tabId === "tab-attendance" && webcamStream) {
    videoStream.srcObject = webcamStream;
    videoStream.play().catch(e => console.log(e));
  } else if (tabId === "tab-registration" && webcamStream) {
    regVideo.srcObject = webcamStream;
    regVideo.play().catch(e => console.log(e));
  }
  
  if (window.lucide) {
    lucide.createIcons();
  }
}

// Attendance Type Toggle
function setAttendanceType(type) {
  currentAttendanceType = type;
  const btnIn = document.getElementById("btn-type-in");
  const btnOut = document.getElementById("btn-type-out");

  if (type === "CHECK_IN") {
    btnIn.className = "px-3 py-1 rounded-lg text-xs font-semibold bg-blue-600 text-white shadow-sm transition-all flex items-center gap-1.5";
    btnOut.className = "px-3 py-1 rounded-lg text-xs font-medium text-zinc-400 hover:text-zinc-200 transition-all flex items-center gap-1.5";
  } else {
    btnOut.className = "px-3 py-1 rounded-lg text-xs font-semibold bg-blue-600 text-white shadow-sm transition-all flex items-center gap-1.5";
    btnIn.className = "px-3 py-1 rounded-lg text-xs font-medium text-zinc-400 hover:text-zinc-200 transition-all flex items-center gap-1.5";
  }
}

// Webcam Management
async function startWebcam() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
      audio: false
    });
    webcamStream = stream;
    videoStream.srcObject = stream;
    regVideo.srcObject = stream;
    cameraPlaceholder.classList.add("hidden");
  } catch (err) {
    console.warn("Kamera tidak dapat diakses:", err);
    cameraPlaceholder.classList.remove("hidden");
    showToast("Kamera tidak dapat diakses. Gunakan upload foto sebagai alternatif.", "warning");
  }
}

// Capture Snapshot from Video Stream
function captureFrame(sourceVideo) {
  if (!sourceVideo || !sourceVideo.videoWidth) {
    throw new Error("Video stream belum aktif");
  }
  hiddenCanvas.width = sourceVideo.videoWidth;
  hiddenCanvas.height = sourceVideo.videoHeight;
  const ctx = hiddenCanvas.getContext("2d");
  ctx.drawImage(sourceVideo, 0, 0, hiddenCanvas.width, hiddenCanvas.height);
  return hiddenCanvas.toDataURL("image/jpeg", 0.9);
}

// Attendance Check
async function captureAndRecognize() {
  let imageBase64 = null;
  try {
    imageBase64 = captureFrame(videoStream);
  } catch (e) {
    showToast("Silakan aktifkan kamera atau pilih file foto terlebih dahulu.", "warning");
    return;
  }
  processRecognition(imageBase64);
}

async function handleAttendanceFile(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async (e) => {
    processRecognition(e.target.result);
  };
  reader.readAsDataURL(file);
}

async function processRecognition(imageBase64) {
  scanningOverlay.classList.remove("hidden");

  try {
    const response = await fetch("/api/recognize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image: imageBase64,
        attendance_type: currentAttendanceType
      })
    });

    const data = await response.json();
    scanningOverlay.classList.add("hidden");

    if (!data.detected || !data.candidates || data.candidates.length === 0) {
      showToast(data.message || "Wajah tidak terdeteksi. Posisikan wajah di kamera.", "warning");
      return;
    }

    // Buka Modal Konfirmasi dengan data kandidat yang terdeteksi
    openConfirmModal(data, imageBase64);

  } catch (err) {
    scanningOverlay.classList.add("hidden");
    console.error(err);
    showToast("Terjadi kendala menghubungi server.", "error");
  }
}

// Modal Konfirmasi
function openConfirmModal(data, imageBase64) {
  activeRecognitionData = data;
  activeCandidates = data.candidates || [];

  // Update badge tipe absensi
  modalAttendanceType.innerText = data.attendance_type;
  modalAttendanceType.className = "px-2 py-0.5 rounded text-xs font-mono font-medium bg-zinc-800 text-zinc-200 border border-zinc-700";

  // Fallback badge
  if (data.fallback_used) {
    modalFallbackBadge.classList.remove("hidden");
  } else {
    modalFallbackBadge.classList.add("hidden");
  }

  if (activeCandidates.length <= 1) {
    // Mode Single Face (1 orang)
    modalSinglePreview.classList.remove("hidden");
    modalMultiPreview.classList.add("hidden");
    modalSnapshotImg.src = activeCandidates[0]?.crop_image || imageBase64;
    selectCandidate(0);
  } else {
    // Mode Multi Face (>1 orang): Manual Selection
    modalSinglePreview.classList.add("hidden");
    modalMultiPreview.classList.remove("hidden");
    modalMultiCountLabel.innerText = `Terdeteksi ${activeCandidates.length} Orang`;

    // Render list kandidat wajah
    modalCandidatesList.innerHTML = activeCandidates.map((c, idx) => {
      let badgeHtml = '';
      let subTitle = '';
      let titleName = '';

      if (c.recognized) {
        titleName = escapeHtml(c.name);
        subTitle = `<p class="text-[11px] font-mono text-zinc-400">${c.employee_id ? escapeHtml(c.employee_id) : '-'}</p>`;
        badgeHtml = `<span class="inline-block mt-0.5 px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">${c.confidence_pct}% Cocok</span>`;
      } else if (c.is_suspected) {
        titleName = "Belum Terdaftar";
        subTitle = `<p class="text-[11px] text-zinc-400 truncate italic">Diduga: ${escapeHtml(c.suspected_name)}</p>`;
        badgeHtml = `<span class="inline-block mt-0.5 px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">Diduga (${c.confidence_pct}%)</span>`;
      } else {
        titleName = "Belum Terdaftar";
        subTitle = `<p class="text-[11px] font-mono text-zinc-500">Tanpa ID</p>`;
        badgeHtml = `<span class="inline-block mt-0.5 px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-zinc-800 text-zinc-500 border border-zinc-700">Belum Terdaftar</span>`;
      }

      return `
        <div onclick="selectCandidate(${idx})" id="candidate-card-${idx}" class="cursor-pointer rounded-xl border p-2.5 flex items-center space-x-2.5 transition select-none">
          <img src="${c.crop_image}" class="w-12 h-12 rounded-lg object-cover border border-zinc-700 shrink-0 bg-black" />
          <div class="overflow-hidden text-left flex-1 min-w-0">
            <p class="text-xs font-semibold truncate text-zinc-100">${titleName}</p>
            ${subTitle}
            ${badgeHtml}
          </div>
        </div>
      `;
    }).join("");

    // Prioritaskan pilihan default pada kandidat pertama yang dikenali (terdaftar)
    let initialIdx = activeCandidates.findIndex(c => c.recognized);
    if (initialIdx === -1) initialIdx = 0;
    selectCandidate(initialIdx);
  }

  modalConfirm.classList.remove("hidden");
  if (window.lucide) lucide.createIcons();
}

function selectCandidate(idx) {
  selectedCandidateIndex = idx;
  const candidate = activeCandidates[idx];
  if (!candidate) return;

  // Update highlight card terpilih
  activeCandidates.forEach((_, i) => {
    const card = document.getElementById(`candidate-card-${i}`);
    if (card) {
      if (i === idx) {
        card.className = "cursor-pointer rounded-xl border border-blue-500 bg-zinc-900 ring-2 ring-blue-500/40 p-2.5 flex items-center space-x-2.5 transition select-none";
      } else {
        card.className = "cursor-pointer rounded-xl border border-zinc-800 bg-zinc-950/60 hover:border-zinc-700 p-2.5 flex items-center space-x-2.5 transition select-none opacity-60 hover:opacity-100";
      }
    }
  });

  // Update info teks di modal
  if (candidate.recognized) {
    modalUserName.innerText = candidate.name;
    modalEmployeeId.innerText = candidate.employee_id || "-";
    modalSimilarity.innerText = `${candidate.confidence_pct}% (Skor: ${candidate.similarity})`;
    modalSimilarity.className = "font-mono text-blue-400 font-semibold text-xs";

    modalConfirmQuestion.innerText = "Apakah data identitas di atas sudah benar?";
    modalConfirmQuestion.className = "text-center text-xs font-medium text-zinc-300 mb-4";

    btnModalConfirm.disabled = false;
    btnModalConfirm.className = "py-2.5 px-4 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl text-sm transition flex items-center justify-center gap-1.5 cursor-pointer shadow-sm";
    btnModalConfirm.innerHTML = `<i data-lucide="check" class="w-4 h-4"></i> Ya, Benar`;

    currentPendingAttendance = {
      employee_id: candidate.employee_id,
      name: candidate.name,
      attendance_type: activeRecognitionData.attendance_type,
      similarity: candidate.similarity
    };
  } else {
    // Wajah belum terdaftar / confidence kurang
    if (candidate.is_suspected) {
      modalUserName.innerHTML = `<span class="text-zinc-300 font-semibold">Belum Terdaftar</span> <span class="text-xs text-zinc-500 font-normal block sm:inline sm:ml-1">(Diduga: ${escapeHtml(candidate.suspected_name)})</span>`;
      modalEmployeeId.innerText = "-";
      modalSimilarity.innerText = `${candidate.confidence_pct}% (Diduga mirip, skor kurang)`;
      modalSimilarity.className = "font-mono text-zinc-400 font-medium text-xs";

      modalConfirmQuestion.innerHTML = `Wajah belum terdaftar resmi (<span class="text-zinc-300">diduga mirip ${escapeHtml(candidate.suspected_name)}</span>). Tidak dapat melakukan absensi.`;
      modalConfirmQuestion.className = "text-center text-xs font-medium text-zinc-400 mb-4";
    } else {
      modalUserName.innerText = "Belum Terdaftar";
      modalEmployeeId.innerText = "-";
      modalSimilarity.innerText = `${candidate.confidence_pct}% (Di Bawah Ambang Batas)`;
      modalSimilarity.className = "font-mono text-zinc-500 font-medium text-xs";

      modalConfirmQuestion.innerText = "Wajah ini belum terdaftar di database. Silakan pilih wajah lain yang terdaftar.";
      modalConfirmQuestion.className = "text-center text-xs font-medium text-zinc-500 mb-4";
    }

    btnModalConfirm.disabled = true;
    btnModalConfirm.className = "py-2.5 px-4 bg-zinc-800 text-zinc-500 font-medium rounded-xl text-sm cursor-not-allowed border border-zinc-700/60 flex items-center justify-center gap-1.5";
    btnModalConfirm.innerHTML = `<i data-lucide="x" class="w-4 h-4"></i> Belum Terdaftar`;

    currentPendingAttendance = null;
  }

  if (window.lucide) lucide.createIcons();
}

function closeConfirmModal() {
  modalConfirm.classList.add("hidden");
  currentPendingAttendance = null;
}

// Submit Konfirmasi Absensi
async function submitAttendanceConfirmation() {
  if (!currentPendingAttendance) return;

  btnModalConfirm.disabled = true;
  btnModalConfirm.innerHTML = `<span class="inline-block animate-spin mr-2">🔄</span> Menyimpan...`;

  try {
    const res = await fetch("/api/confirm_attendance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        employee_id: currentPendingAttendance.employee_id,
        name: currentPendingAttendance.name,
        attendance_type: currentPendingAttendance.attendance_type,
        similarity: currentPendingAttendance.similarity
      })
    });

    const result = await res.json();
    btnModalConfirm.disabled = false;
    btnModalConfirm.innerHTML = `<i data-lucide="check" class="w-4 h-4"></i> Ya, Benar`;

    if (result.success) {
      showToast(`Absensi ${currentPendingAttendance.attendance_type} berhasil dicatat!`, "success");
      closeConfirmModal();
      loadLogs();
    } else {
      showToast(result.message || "Gagal mencatat absensi", "error");
    }
  } catch (e) {
    btnModalConfirm.disabled = false;
    btnModalConfirm.innerHTML = `<i data-lucide="check" class="w-4 h-4"></i> Ya, Benar`;
    showToast("Gagal menyimpan konfirmasi absensi", "error");
  }
  if (window.lucide) lucide.createIcons();
}

// Face Registration Handlers
function captureRegistrationSnapshot() {
  try {
    registrationSnapshotBase64 = captureFrame(regVideo);
    regPreview.src = registrationSnapshotBase64;
    regPreview.classList.remove("hidden");
    regVideo.classList.add("hidden");
    showToast("Foto wajah berhasil diambil dari webcam", "info");
  } catch (e) {
    showToast("Pastikan webcam aktif untuk mengambil foto", "warning");
  }
}

function handleRegistrationFile(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    registrationSnapshotBase64 = e.target.result;
    regPreview.src = registrationSnapshotBase64;
    regPreview.classList.remove("hidden");
    regVideo.classList.add("hidden");
    showToast("File foto berhasil dipilih", "info");
  };
  reader.readAsDataURL(file);
}

async function handleRegisterSubmit(event) {
  event.preventDefault();
  const employeeId = document.getElementById("reg-id").value.trim();
  const name = document.getElementById("reg-name").value.trim();

  if (!registrationSnapshotBase64) {
    showToast("Harap ambil foto webcam atau upload foto wajah terlebih dahulu.", "warning");
    return;
  }

  const btnSubmit = document.getElementById("btn-submit-register");
  btnSubmit.disabled = true;
  btnSubmit.innerHTML = `<span class="inline-block animate-spin mr-2">🔄</span> Memproses Pendaftaran Wajah...`;

  try {
    const res = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        employee_id: employeeId,
        name: name,
        image: registrationSnapshotBase64
      })
    });

    const data = await res.json();
    btnSubmit.disabled = false;
    btnSubmit.innerHTML = `<i data-lucide="save" class="w-4 h-4"></i> Simpan Data Karyawan`;

    if (data.success) {
      showToast(data.message, "success");
      document.getElementById("form-register").reset();
      registrationSnapshotBase64 = null;
      regPreview.classList.add("hidden");
      regVideo.classList.remove("hidden");
      loadUsers();
      switchTab("tab-attendance");
    } else {
      showToast(data.message || "Gagal mendaftarkan wajah", "error");
    }
  } catch (err) {
    btnSubmit.disabled = false;
    btnSubmit.innerHTML = `<i data-lucide="save" class="w-4 h-4"></i> Simpan Data Karyawan`;
    showToast("Terjadi kendala saat menghubungkan ke server.", "error");
  }
  if (window.lucide) lucide.createIcons();
}

// Load Attendance Logs
async function loadLogs() {
  try {
    const res = await fetch("/api/attendance_logs");
    const data = await res.json();
    const logs = data.logs || [];

    const logCountEl = document.getElementById("log-count");
    if (logCountEl) logCountEl.innerText = logs.length;

    // Mini log table in Attendance Tab
    const miniTbody = document.getElementById("mini-log-tbody");
    if (miniTbody) {
      if (logs.length === 0) {
        miniTbody.innerHTML = `<tr><td colspan="3" class="py-4 text-center text-zinc-500">Belum ada absensi hari ini.</td></tr>`;
      } else {
        miniTbody.innerHTML = logs.slice(0, 5).map(item => `
          <tr class="hover:bg-zinc-800/40 transition">
            <td class="py-2.5 px-2 font-medium text-zinc-200">${escapeHtml(item.name)}</td>
            <td class="py-2.5 px-2">
              <span class="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
                ${item.attendance_type}
              </span>
            </td>
            <td class="py-2.5 px-2 text-zinc-500 text-[11px] font-mono text-right">${item.timestamp.split(" ")[1] || item.timestamp}</td>
          </tr>
        `).join("");
      }
    }

    // Full log table in Logs Tab
    const logsTbody = document.getElementById("logs-tbody");
    if (logsTbody) {
      if (logs.length === 0) {
        logsTbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-zinc-500">Belum ada riwayat absensi.</td></tr>`;
      } else {
        logsTbody.innerHTML = logs.map((item, idx) => `
          <tr class="hover:bg-zinc-800/40 transition">
            <td class="py-3 px-4 font-mono text-zinc-500">${idx + 1}</td>
            <td class="py-3 px-4 font-mono text-zinc-300">${escapeHtml(item.employee_id)}</td>
            <td class="py-3 px-4 font-semibold text-zinc-100">${escapeHtml(item.name)}</td>
            <td class="py-3 px-4">
              <span class="px-2 py-0.5 rounded text-xs font-mono font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
                ${item.attendance_type}
              </span>
            </td>
            <td class="py-3 px-4 font-mono text-zinc-400">${(item.similarity * 100).toFixed(1)}%</td>
            <td class="py-3 px-4 font-mono text-zinc-500 text-right text-xs">${item.timestamp}</td>
          </tr>
        `).join("");
      }
    }

  } catch (err) {
    console.error("Gagal memuat log:", err);
  }
}

// Load Users
async function loadUsers() {
  try {
    const res = await fetch("/api/users");
    const data = await res.json();
    const users = data.users || [];

    const regUserCountEl = document.getElementById("reg-user-count");
    if (regUserCountEl) regUserCountEl.innerText = users.length;

    const usersTbody = document.getElementById("users-tbody");
    if (usersTbody) {
      if (users.length === 0) {
        usersTbody.innerHTML = `<tr><td colspan="4" class="py-6 text-center text-zinc-500">Belum ada user terdaftar.</td></tr>`;
      } else {
        usersTbody.innerHTML = users.map(u => `
          <tr class="hover:bg-zinc-800/40 transition">
            <td class="py-3 px-4 font-mono text-zinc-300 font-semibold">${escapeHtml(u.employee_id)}</td>
            <td class="py-3 px-4 font-medium text-zinc-100">${escapeHtml(u.name)}</td>
            <td class="py-3 px-4 text-zinc-500 font-mono text-xs">${u.created_at}</td>
            <td class="py-3 px-4 text-right">
              <button onclick="deleteUser('${escapeHtml(u.employee_id)}')" class="px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-750 text-zinc-400 hover:text-zinc-200 border border-zinc-700 text-xs transition">
                Hapus
              </button>
            </td>
          </tr>
        `).join("");
      }
    }
  } catch (err) {
    console.error("Gagal memuat user:", err);
  }
}

// Delete User
async function deleteUser(employeeId) {
  if (!confirm(`Yakin ingin menghapus karyawan dengan ID ${employeeId}?`)) return;

  try {
    const res = await fetch(`/api/users/${employeeId}`, { method: "DELETE" });
    const data = await res.json();
    if (data.success) {
      showToast(`User ${employeeId} berhasil dihapus`, "info");
      loadUsers();
    }
  } catch (err) {
    showToast("Gagal menghapus user", "error");
  }
}

// Toast System
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");

  let borderAccent = "border-zinc-800";
  let iconName = "info";

  if (type === "success") {
    borderAccent = "border-blue-500/50";
    iconName = "check";
  } else if (type === "warning") {
    borderAccent = "border-zinc-700";
    iconName = "alert-circle";
  } else if (type === "error") {
    borderAccent = "border-zinc-700";
    iconName = "x";
  }

  toast.className = `flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-2xl border text-xs font-medium transition-all transform duration-300 ease-out translate-y-2 opacity-0 pointer-events-auto bg-zinc-900 text-zinc-200 ${borderAccent}`;
  toast.innerHTML = `<i data-lucide="${iconName}" class="w-4 h-4 text-blue-400 shrink-0"></i><span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  requestAnimationFrame(() => {
    toast.classList.remove("translate-y-2", "opacity-0");
  });

  setTimeout(() => {
    toast.classList.add("translate-y-2", "opacity-0");
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Utility
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
