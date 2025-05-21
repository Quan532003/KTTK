// DOM Elements
const startCameraBtn = document.getElementById("startCameraBtn");

// lấy phần nội dung của option
const optionsSection = document.getElementById("optionsSection");
// lấy phần nội dung của detection
const detectionSection = document.getElementById("detectionSection");

//video camera
const cameraFeed = document.getElementById("cameraFeed");

const detectionCanvas = document.getElementById("detectionCanvas");
const startDetectBtn = document.getElementById("startDetectBtn");
const stopDetectBtn = document.getElementById("stopDetectBtn");
const backBtn = document.getElementById("backBtn");
const detectionStatus = document.getElementById("detectionStatus");
const detectionTime = document.getElementById("detectionTime");
const detectionCount = document.getElementById("detectionCount");
const objectCount = document.getElementById("objectCount");
const resultsList = document.getElementById("resultsList");
const modelSelect = document.getElementById("modelSelect");

// Global variables
let cameraStream = null;
let detectionInterval = null;
let phaseId = null;
let startTime = null;
let timerInterval = null;
let totalObjectsDetected = 0;
let detectionCounter = 0;
let detectionRate = 3;
let frameCounter = 0;
let processingDetection = false;

// Event listeners
startCameraBtn.addEventListener("click", initCameraDetection);
startDetectBtn.addEventListener("click", startDetection);
stopDetectBtn.addEventListener("click", stopDetection);
backBtn.addEventListener("click", goBack);

// Functions
function initCameraDetection() {
  //tat phan chon di, hien phan detect, có camera
  optionsSection.style.display = "none";
  detectionSection.style.display = "block";

  // Initialize camera
  navigator.mediaDevices
    .getUserMedia({ video: true })
    .then((stream) => {
      cameraStream = stream;
      cameraFeed.srcObject = stream;
      // Set up canvas dimensions after video is loaded
      cameraFeed.onloadedmetadata = () => {
        detectionCanvas.width = cameraFeed.videoWidth;
        detectionCanvas.height = cameraFeed.videoHeight;
      };
      detectionStatus.textContent =
        "Trạng thái: Camera đã sẵn sàng. Nhấn 'Bắt đầu' để phát hiện.";
    })
    .catch((err) => {
      console.error("Không thể truy cập camera:", err);
      detectionStatus.textContent =
        "Lỗi: Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.";
      detectionStatus.classList.add("status-stopped");
    });
}

async function startDetection() {
  if (!cameraStream) {
    alert("Camera chưa được khởi tạo!");
    return;
  }
  const modelId = modelSelect.value;
  try {
    // Create new detection phase
    const response = await fetch("/api/phase_detection/start", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        modelId: modelId,
        description: "Phát hiện gian lận qua camera",
      }),
    });
    const data = await response.json();
    if (data.success) {
      phaseId = data.phaseId;
      // Update UI
      startDetectBtn.disabled = true;
      stopDetectBtn.disabled = false;
      modelSelect.disabled = true;

      detectionStatus.textContent = "Trạng thái: Đang phát hiện...";
      detectionStatus.classList.remove("status-stopped");
      detectionStatus.classList.add("status-running");

      // Reset counters
      startTime = new Date();
      detectionCounter = 0;
      totalObjectsDetected = 0;
      detectionCount.textContent = "0";
      objectCount.textContent = "0";
      resultsList.innerHTML = "";

      // Start timer
      timerInterval = setInterval(updateTimer, 1000);

      // Start detection at 1-second intervals
      detectionInterval = setInterval(performDetection, 1000);
    } else {
      alert("Không thể bắt đầu phát hiện: " + data.message);
    }
  } catch (error) {
    console.error("Lỗi khi bắt đầu phát hiện:", error);
    alert("Đã xảy ra lỗi khi bắt đầu phát hiện. Vui lòng thử lại.");
  }
}

async function stopDetection() {
  if (!phaseId) return;
  try {
    // Stop detection phase
    const response = await fetch("/api/phase_detection/stop", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        phaseId: phaseId,
      }),
    });

    const data = await response.json();

    if (data.success) {
      // Clear intervals
      clearInterval(detectionInterval);
      clearInterval(timerInterval);

      // Update UI
      startDetectBtn.disabled = false;
      stopDetectBtn.disabled = true;
      modelSelect.disabled = false;

      detectionStatus.textContent = "Trạng thái: Phát hiện đã dừng.";
      detectionStatus.classList.remove("status-running");
      detectionStatus.classList.add("status-stopped");

      // Clear canvas
      const ctx = detectionCanvas.getContext("2d");
      ctx.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);

      // Reset phase ID
      phaseId = null;
    } else {
      alert("Không thể dừng phát hiện: " + data.message);
    }
  } catch (error) {
    console.error("Lỗi khi dừng phát hiện:", error);
    alert("Đã xảy ra lỗi khi dừng phát hiện. Vui lòng thử lại.");
  }
}

function goBack() {
  // Make sure detection is stopped
  if (phaseId) {
    stopDetection();
  }

  // Stop camera stream
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }

  // Switch back to options view
  detectionSection.style.display = "none";
  optionsSection.style.display = "flex";
}

async function performDetection() {
  if (!phaseId || !cameraStream) return;

  frameCounter++;
  if (frameCounter % detectionRate !== 0) return;

  if (processingDetection) return;

  processingDetection = true;

  try {
    // Capture current frame
    const ctx = detectionCanvas.getContext("2d");

    // Đảm bảo canvas có cùng kích thước với video
    if (
      detectionCanvas.width !== cameraFeed.videoWidth ||
      detectionCanvas.height !== cameraFeed.videoHeight
    ) {
      detectionCanvas.width = cameraFeed.videoWidth;
      detectionCanvas.height = cameraFeed.videoHeight;
    }

    ctx.drawImage(
      cameraFeed,
      0,
      0,
      detectionCanvas.width,
      detectionCanvas.height
    );

    const imageData = detectionCanvas.toDataURL("image/jpeg", 0.8);

    const confidence = 0.8;

    const startTime = performance.now();

    const response = await fetch("/api/phase_detection/detect", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        phaseId: phaseId,
        imageData: imageData,
        confidence: confidence,
      }),
    });

    const data = await response.json();

    const endTime = performance.now();
    const detectionTime = endTime - startTime;

    if (detectionTime > 300) {
      detectionRate = Math.min(5, detectionRate + 1);
    } else if (detectionTime < 200 && detectionRate > 1) {
      detectionRate = Math.max(1, detectionRate - 1);
    }

    if (data.success) {
      // Vẽ bounding box trên canvas
      drawDetections(data.detections);

      // Cập nhật bộ đếm
      detectionCounter++;
      detectionCount.textContent = detectionCounter;

      totalObjectsDetected += data.detections.length;
      objectCount.textContent = totalObjectsDetected;

      // Thêm vào danh sách kết quả
      if (data.image_path) {
        addDetectionResult(data.resultId, data.detections, data.image_path);
      } else {
        addDetectionResult(data.resultId, data.detections);
      }
    } else {
      console.error("Error in detection:", data.message);
    }
  } catch (error) {
    console.error("Error during detection:", error);
  } finally {
    processingDetection = false;
  }
}
function initCameraDetection() {
  optionsSection.style.display = "none";
  detectionSection.style.display = "block";

  navigator.mediaDevices
    .getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 640 },
      },
    })
    .then((stream) => {
      cameraStream = stream;
      cameraFeed.srcObject = stream;

      cameraFeed.onloadedmetadata = () => {
        cameraFeed.play();
        // Đặt kích thước canvas khớp với video
        detectionCanvas.width = cameraFeed.videoWidth;
        detectionCanvas.height = cameraFeed.videoHeight;
      };

      detectionStatus.textContent =
        "Trạng thái: Camera đã sẵn sàng. Nhấn 'Bắt đầu' để phát hiện.";
    })
    .catch((err) => {
      console.error("Không thể truy cập camera:", err);
      detectionStatus.textContent =
        "Lỗi: Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.";
      detectionStatus.classList.add("status-stopped");
    });
}
function drawDetections(detections) {
  const ctx = detectionCanvas.getContext("2d");
  ctx.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);

  // Scale factor để chuyển đổi từ 640x640 về kích thước thực tế của canvas
  const scaleX = detectionCanvas.width / 640;
  const scaleY = detectionCanvas.height / 640;

  detections.forEach((detection) => {
    // Sử dụng tọa độ pixel đã được tính sẵn từ server
    if (detection.box) {
      const x1 = detection.box.x1 * scaleX;
      const y1 = detection.box.y1 * scaleY;
      const x2 = detection.box.x2 * scaleX;
      const y2 = detection.box.y2 * scaleY;

      const width = x2 - x1;
      const height = y2 - y1;

      // Chọn màu dựa trên nhãn
      let color;
      switch (detection.label) {
        case "normal":
          color = "green";
          break;
        case "phone":
          color = "red";
          break;
        case "huitou":
          color = "orange";
          break;
        case "zuobi":
          color = "red";
          break;
        default:
          color = "blue";
      }

      // Vẽ bounding box
      ctx.lineWidth = 3;
      ctx.strokeStyle = color;
      ctx.strokeRect(x1, y1, width, height);

      // Vẽ background cho text với nhãn tiếng Việt
      const displayLabel = detection.display_label || detection.label;
      const text = `${displayLabel} (${Math.round(
        detection.confidence * 100
      )}%)`;
      ctx.font = "bold 16px Arial";
      const textWidth = ctx.measureText(text).width;

      // Background với độ trong suốt
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.8;
      ctx.fillRect(x1, y1 - 25, textWidth + 10, 25);
      ctx.globalAlpha = 1.0;

      // Vẽ text
      ctx.fillStyle = "white";
      ctx.fillText(text, x1, y1);
    }
  });
}

function addDetectionResult(resultId, detections, imagePath = null) {
  // Tạo kết quả
  const resultItem = document.createElement("div");
  resultItem.className = "result-item";

  // Lấy thời gian hiện tại
  const now = new Date();
  const timeString = now.toLocaleTimeString();

  // Nhóm theo nhãn
  const labelCounts = {};
  detections.forEach((detection) => {
    const label = detection.label;
    labelCounts[label] = (labelCounts[label] || 0) + 1;
  });

  // Tạo header
  let resultHTML = `
            <div class="result-header">
                <span>ID: ${resultId}</span>
                <span>${timeString}</span>
            </div>
        `;

  // Thêm ảnh thumbnail nếu có
  if (imagePath) {
    resultHTML += `<div class="result-image"><img src="${imagePath}" alt="Detection Result" style="max-width:100%; max-height:100px;"></div>`;
  }

  // Thêm nhãn
  if (detections.length > 0) {
    resultHTML += "<div>";

    for (const [label, count] of Object.entries(labelCounts)) {
      const badgeClass = label === "normal" ? "bg-success" : "bg-danger";
      resultHTML += `<span class="badge ${badgeClass} badge-label">${label}: ${count}</span>`;
    }

    resultHTML += "</div>";
  } else {
    resultHTML += '<div class="text-muted">Không phát hiện đối tượng nào</div>';
  }

  resultItem.innerHTML = resultHTML;

  // Thêm vào danh sách
  resultsList.insertBefore(resultItem, resultsList.firstChild);

  // Giới hạn 10 kết quả
  if (resultsList.children.length > 10) {
    resultsList.removeChild(resultsList.lastChild);
  }
}

function updateTimer() {
  if (!startTime) return;

  const now = new Date();
  const elapsed = now - startTime;

  // Format as mm:ss
  const minutes = Math.floor(elapsed / 60000);
  const seconds = Math.floor((elapsed % 60000) / 1000);

  detectionTime.textContent = `${minutes.toString().padStart(2, "0")}:${seconds
    .toString()
    .padStart(2, "0")}`;
}

// Clean up resources when leaving page
window.addEventListener("beforeunload", () => {
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
  }

  if (detectionInterval) {
    clearInterval(detectionInterval);
  }

  if (timerInterval) {
    clearInterval(timerInterval);
  }

  if (phaseId) {
    // Try to stop detection phase
    fetch("/api/phase_detection/stop", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        phaseId: phaseId,
      }),
      keepalive: true,
    });
  }
});
