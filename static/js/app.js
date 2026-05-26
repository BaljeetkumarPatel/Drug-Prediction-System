AOS.init({ duration: 800, once: true });

const naSlider = document.getElementById('na_to_k');
const naLabel = document.getElementById('naLabel');
const form = document.getElementById('predictForm');
const loader = document.getElementById('loader');
const drugOutput = document.getElementById('drugOutput');
const confidenceOutput = document.getElementById('confidenceOutput');
const explainOutput = document.getElementById('explainOutput');

let confidenceChart;
let importanceChart;

naSlider.addEventListener('input', () => {
  naLabel.textContent = Number(naSlider.value).toFixed(2);
});

gsap.from('.hero-text h1', { y: 20, opacity: 0, duration: 1 });
gsap.from('.floating-cards .card', { y: 18, opacity: 0, duration: 0.8, stagger: 0.18 });

async function loadFeatureImportance() {
  const res = await fetch('/feature-importance');
  const data = await res.json();
  const ctx = document.getElementById('importanceChart');

  importanceChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.features,
      datasets: [{
        label: 'Feature Importance',
        data: data.importances,
        backgroundColor: ['#2de2e6', '#50f3a7', '#6ab7ff', '#68f5d2', '#9ed3ff']
      }]
    },
    options: {
      plugins: { legend: { labels: { color: '#eaf6ff' } } },
      scales: {
        x: { ticks: { color: '#cde5ff' } },
        y: { ticks: { color: '#cde5ff' }, beginAtZero: true }
      }
    }
  });
}

function drawConfidenceChart(confidenceBreakdown = {}) {
  const labels = Object.keys(confidenceBreakdown);
  const values = Object.values(confidenceBreakdown);
  const ctx = document.getElementById('confidenceChart');

  if (confidenceChart) confidenceChart.destroy();

  confidenceChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: ['#2de2e6', '#6ab7ff', '#50f3a7', '#87ffe0', '#2f7fbd']
      }]
    },
    options: {
      plugins: {
        legend: { labels: { color: '#eaf6ff' } },
        title: { display: true, text: 'Drug Prediction Confidence %', color: '#eaf6ff' }
      }
    }
  });
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  loader.classList.remove('hidden');

  const payload = {
    age: document.getElementById('age').value,
    sex: document.getElementById('sex').value,
    bp: document.getElementById('bp').value,
    cholesterol: document.getElementById('cholesterol').value,
    na_to_k: document.getElementById('na_to_k').value
  };

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Prediction failed');

    drugOutput.textContent = `Recommended Drug: ${data.recommended_drug}`;
    confidenceOutput.textContent = `Confidence: ${data.confidence}%`;
    explainOutput.textContent = data.explanation;
    drawConfidenceChart(data.confidence_breakdown);

    gsap.fromTo('.result-card', { scale: 0.97, opacity: 0.6 }, { scale: 1, opacity: 1, duration: 0.55 });
  } catch (error) {
    drugOutput.textContent = 'Prediction error';
    confidenceOutput.textContent = '--';
    explainOutput.textContent = error.message;
  } finally {
    loader.classList.add('hidden');
  }
});

loadFeatureImportance();
