// =====================
// Charts
// =====================
if (document.getElementById("yearlyChart")) {
  new Chart(document.getElementById("yearlyChart"), {
    type: 'line',
    data: {
      labels: ["2021", "2022", "2023", "2024", "2025"],
      datasets: [{
        label: "Studies Published",
        data: [15, 22, 30, 45, 60],
        borderColor: "#22c55e",
        backgroundColor: "rgba(34,197,94,0.3)",
        tension: 0.4,
        pointBackgroundColor: "#22c55e"
      }]
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#e5e7eb" } } },
      scales: {
        x: { ticks: { color: "#9ca3af" }, grid: { color: "#374151" } },
        y: { ticks: { color: "#9ca3af" }, grid: { color: "#374151" } }
      }
    }
  });
}

if (document.getElementById("organismChart")) {
  new Chart(document.getElementById("organismChart"), {
    type: 'doughnut',
    data: {
      labels: ["Human Cells", "Arabidopsis", "E. coli"],
      datasets: [{
        data: [40, 35, 25],
        backgroundColor: ["#22c55e", "#10b981", "#059669"]
      }]
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#e5e7eb" } } }
    }
  });
}

// =====================
// Search Functionality
// =====================
