<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>COVID-19 Chest X-Ray Classifier</title>
<script src="https://cdn.tailwindcss.com/3.4.16"></script>
<script>tailwind.config={theme:{extend:{colors:{primary:'#2B6CB0',secondary:'#48BB78'},borderRadius:{'none':'0px','sm':'4px',DEFAULT:'8px','md':'12px','lg':'16px','xl':'20px','2xl':'24px','3xl':'32px','full':'9999px','button':'8px'}}}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/remixicon/4.6.0/remixicon.min.css">
<style>
:where([class^="ri-"])::before { content: "\f3c2"; }
body { font-family: 'Inter', sans-serif; }
.upload-zone { transition: all 0.3s ease; }
.upload-zone:hover { border-color: #2B6CB0; background-color: #EBF8FF; }
.upload-zone.dragover { border-color: #2B6CB0; background-color: #EBF8FF; transform: scale(1.02); }
.prediction-card { animation: slideIn 0.5s ease-out; }
@keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.loading-spinner { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.confidence-bar { transition: width 0.8s ease-out; }
.result-covid { background: linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%); }
.result-normal { background: linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%); }
.result-pneumonia { background: linear-gradient(135deg, #FEEBC8 0%, #F6AD55 100%); }
</style>
</head>
<body class="bg-gray-50 min-h-screen">
<nav class="bg-white shadow-sm border-b border-gray-200">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
<div class="flex justify-between items-center h-16">
<div class="flex items-center space-x-2">
<div class="w-8 h-8 flex items-center justify-center bg-primary rounded-lg">
<i class="ri-lungs-line text-white text-lg"></i>
</div>
<span class="text-xl font-semibold text-gray-900">MedAI Classifier</span>
</div>
<div class="flex items-center space-x-6">
<a href="#about" class="text-gray-600 hover:text-primary transition-colors">About</a>
<a href="#" class="flex items-center space-x-1 text-gray-600 hover:text-primary transition-colors">
<div class="w-4 h-4 flex items-center justify-center">
<i class="ri-github-line"></i>
</div>
<span>GitHub</span>
</a>
</div>
</div>
</div>
</nav>
<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
<div id="homepage" class="text-center mb-12">
<div class="max-w-3xl mx-auto">
<h1 class="text-4xl font-bold text-gray-900 mb-6">COVID-19 Chest X-Ray Classifier</h1>
<p class="text-xl text-gray-600 mb-8">Upload chest X-ray images to receive AI-powered classification results for COVID-19, pneumonia, and normal cases using advanced deep learning technology.</p>
<div class="bg-white rounded-2xl shadow-lg p-8 mb-8">
<div id="upload-section">
<div class="upload-zone border-2 border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer" id="uploadZone">
<div class="w-16 h-16 flex items-center justify-center mx-auto mb-4 bg-gray-100 rounded-full">
<i class="ri-cloud-line text-2xl text-gray-400"></i>
</div>
<h3 class="text-lg font-medium text-gray-900 mb-2">Drop your X-ray image here</h3>
<p class="text-gray-500 mb-4">or click to browse files</p>
<button class="bg-primary text-white px-6 py-3 !rounded-button font-medium hover:bg-blue-700 transition-colors whitespace-nowrap" id="browseBtn">
Browse Files
</button>
<p class="text-sm text-gray-400 mt-4">Supports JPG, JPEG, PNG files up to 10MB</p>
</div>
<input type="file" id="fileInput" class="hidden" accept=".jpg,.jpeg,.png">
</div>
<div id="preview-section" class="hidden mt-8">
<div class="flex items-start space-x-6 p-6 bg-gray-50 rounded-xl">
<div class="flex-shrink-0">
<img id="previewImage" class="w-32 h-32 object-cover rounded-lg shadow-md" alt="Preview">
</div>
<div class="flex-1">
<h4 class="font-medium text-gray-900 mb-2" id="fileName">chest-xray.jpg</h4>
<p class="text-sm text-gray-500 mb-4" id="fileSize">2.4 MB</p>
<div class="flex space-x-3">
<button class="bg-primary text-white px-6 py-2 !rounded-button font-medium hover:bg-blue-700 transition-colors whitespace-nowrap" id="predictBtn">
Analyze X-Ray
</button>
<button class="text-gray-600 px-4 py-2 border border-gray-300 !rounded-button hover:bg-gray-50 transition-colors whitespace-nowrap" id="removeBtn">
Remove
</button>
</div>
</div>
</div>
</div>
<div id="loading-section" class="hidden text-center py-12">
<div class="w-12 h-12 flex items-center justify-center mx-auto mb-4">
<i class="ri-loader-4-line text-3xl text-primary loading-spinner"></i>
</div>
<h3 class="text-lg font-medium text-gray-900 mb-2">Processing X-Ray Image</h3>
<p class="text-gray-500">Our AI model is analyzing your image...</p>
</div>
</div>
</div>
</div>
<div id="results-section" class="hidden">
<div class="grid lg:grid-cols-5 gap-8">
<div class="lg:col-span-2">
<div class="bg-white rounded-2xl shadow-lg p-6">
<h3 class="text-lg font-semibold text-gray-900 mb-4">Uploaded X-Ray</h3>
<img id="resultImage" class="w-full rounded-xl shadow-md mb-4" alt="X-Ray Result">
<div class="text-sm text-gray-500">
<p id="resultFileName">chest-xray-001.jpg</p>
<p id="resultFileSize">2.4 MB • 1024×1024 pixels</p>
</div>
</div>
</div>
<div class="lg:col-span-3">
<div class="prediction-card bg-white rounded-2xl shadow-lg p-8">
<div class="mb-6">
<div class="flex items-center justify-between mb-4">
<h3 class="text-2xl font-bold text-gray-900">Classification Result</h3>
<div class="w-8 h-8 flex items-center justify-center bg-green-100 rounded-full">
<i class="ri-check-line text-green-600"></i>
</div>
</div>
<div id="predictionResult" class="result-normal p-6 rounded-xl mb-6">
<div class="flex items-center justify-between mb-3">
<h4 class="text-2xl font-bold text-gray-900" id="predictionClass">Normal</h4>
<span class="text-3xl font-bold text-gray-900" id="confidenceScore">94%</span>
</div>
<div class="w-full bg-white bg-opacity-50 rounded-full h-3">
<div class="confidence-bar bg-white h-3 rounded-full" id="confidenceBar" style="width: 94%"></div>
</div>
<p class="text-sm text-gray-700 mt-2">Confidence Level</p>
</div>
<div class="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-6">
<div class="flex items-start space-x-3">
<div class="w-5 h-5 flex items-center justify-center flex-shrink-0 mt-0.5">
<i class="ri-alert-line text-yellow-600"></i>
</div>
<div>
<h5 class="font-medium text-yellow-800 mb-1">Medical Disclaimer</h5>
<p class="text-sm text-yellow-700">This tool is for research and educational purposes only. Results should not be used for medical diagnosis or treatment decisions. Always consult with qualified healthcare professionals.</p>
</div>
</div>
</div>
<div class="grid grid-cols-3 gap-4 mb-6">
<div class="text-center p-4 bg-gray-50 rounded-xl">
<div class="w-8 h-8 flex items-center justify-center mx-auto mb-2 bg-red-100 rounded-full">
<i class="ri-virus-line text-red-600"></i>
</div>
<p class="text-sm font-medium text-gray-900">COVID-19</p>
<p class="text-xs text-gray-500" id="covidProb">3%</p>
</div>
<div class="text-center p-4 bg-gray-50 rounded-xl">
<div class="w-8 h-8 flex items-center justify-center mx-auto mb-2 bg-green-100 rounded-full">
<i class="ri-heart-pulse-line text-green-600"></i>
</div>
<p class="text-sm font-medium text-gray-900">Normal</p>
<p class="text-xs text-gray-500" id="normalProb">94%</p>
</div>
<div class="text-center p-4 bg-gray-50 rounded-xl">
<div class="w-8 h-8 flex items-center justify-center mx-auto mb-2 bg-orange-100 rounded-full">
<i class="ri-lungs-line text-orange-600"></i>
</div>
<p class="text-sm font-medium text-gray-900">Pneumonia</p>
<p class="text-xs text-gray-500" id="pneumoniaProb">3%</p>
</div>
</div>
<button class="w-full bg-primary text-white py-3 !rounded-button font-medium hover:bg-blue-700 transition-colors whitespace-nowrap" id="tryAnotherBtn">
Try Another X-Ray
</button>
</div>
</div>
</div>
</div>
</div>
<section id="about" class="mt-20 py-16 bg-white rounded-2xl shadow-lg">
<div class="max-w-4xl mx-auto px-8">
<h2 class="text-3xl font-bold text-gray-900 text-center mb-8">About This Tool</h2>
<div class="grid md:grid-cols-2 gap-8">
<div>
<h3 class="text-xl font-semibold text-gray-900 mb-4">Dataset & Model</h3>
<p class="text-gray-600 mb-4">Our AI model is trained on a comprehensive dataset of over 15,000 chest X-ray images, including COVID-19 positive cases, pneumonia cases, and normal healthy lungs.</p>
<p class="text-gray-600">The deep learning model uses advanced convolutional neural networks (CNN) architecture optimized for medical image classification with 94% accuracy on validation data.</p>
</div>
<div>
<h3 class="text-xl font-semibold text-gray-900 mb-4">Research Purpose</h3>
<p class="text-gray-600 mb-4">This tool demonstrates the potential of AI in medical imaging analysis and serves as an educational resource for understanding machine learning applications in healthcare.</p>
<p class="text-gray-600">Built with PyTorch and deployed using modern web technologies for fast, reliable predictions.</p>
</div>
</div>
</div>
</section>
</main>
<footer class="bg-white border-t border-gray-200 mt-20">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
<div class="flex justify-between items-center">
<div class="flex items-center space-x-2">
<div class="w-6 h-6 flex items-center justify-center bg-primary rounded">
<i class="ri-lungs-line text-white text-sm"></i>
</div>
<span class="text-gray-600">MedAI Classifier</span>
</div>
<div class="flex items-center space-x-6">
<a href="#" class="text-gray-500 hover:text-primary transition-colors">Privacy</a>
<a href="#" class="text-gray-500 hover:text-primary transition-colors">Terms</a>
<a href="#" class="text-gray-500 hover:text-primary transition-colors">Contact</a>
</div>
</div>
</div>
</footer>
<script id="file-upload">
document.addEventListener('DOMContentLoaded', function() {
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const uploadSection = document.getElementById('upload-section');
const previewSection = document.getElementById('preview-section');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const homepage = document.getElementById('homepage');
let currentFile = null;

function showErrorMessage(message) {
  const errorDiv = document.createElement('div');
  errorDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg shadow-lg z-50';
  errorDiv.innerHTML = `
    <div class="flex items-center">
      <div class="w-5 h-5 flex items-center justify-center mr-2">
        <i class="ri-error-warning-line"></i>
      </div>
      <p>${message}</p>
    </div>
  `;
  document.body.appendChild(errorDiv);
  setTimeout(() => {
    errorDiv.remove();
  }, 3000);
}

function validateFile(file) {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
  const maxSize = 10 * 1024 * 1024; // 10MB

  if (!allowedTypes.includes(file.type)) {
    showErrorMessage('Please select a valid image file (JPG, JPEG, or PNG)');
    return false;
  }

  if (file.size > maxSize) {
    showErrorMessage('File size must be less than 10MB');
    return false;
  }

  return true;
}

function handleFileSelect(file) {
  if (!validateFile(file)) {
    return;
  }

  currentFile = file;
  const reader = new FileReader();
  
  reader.onload = (e) => {
    const img = new Image();
    img.onload = function() {
      document.getElementById('previewImage').src = e.target.result;
      document.getElementById('fileName').textContent = file.name;
      document.getElementById('fileSize').textContent = `${(file.size / (1024 * 1024)).toFixed(1)} MB`;
      uploadSection.classList.add('hidden');
      previewSection.classList.remove('hidden');
      
      previewSection.style.opacity = '0';
      previewSection.style.transform = 'translateY(20px)';
      previewSection.style.transition = 'all 0.3s ease-out';
      
      setTimeout(() => {
        previewSection.style.opacity = '1';
        previewSection.style.transform = 'translateY(0)';
      }, 50);
    };
    img.src = e.target.result;
  };

  reader.onerror = () => {
    showErrorMessage('Error reading file. Please try again.');
  };

  reader.readAsDataURL(file);
}

browseBtn.addEventListener('click', (e) => {
  e.preventDefault();
  fileInput.click();
});

uploadZone.addEventListener('click', (e) => {
  e.preventDefault();
  fileInput.click();
});

uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  e.stopPropagation();
  uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', (e) => {
  e.preventDefault();
  e.stopPropagation();
  uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  e.stopPropagation();
  uploadZone.classList.remove('dragover');
  
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFileSelect(files[0]);
  }
});

fileInput.addEventListener('change', (e) => {
  if (e.target.files.length > 0) {
    handleFileSelect(e.target.files[0]);
  }
});
});
</script>
<script id="prediction-handler">
document.addEventListener('DOMContentLoaded', function() {
const predictBtn = document.getElementById('predictBtn');
const removeBtn = document.getElementById('removeBtn');
const tryAnotherBtn = document.getElementById('tryAnotherBtn');
predictBtn.addEventListener('click', handlePrediction);
removeBtn.addEventListener('click', resetUpload);
tryAnotherBtn.addEventListener('click', resetUpload);
function handlePrediction() {
const previewSection = document.getElementById('preview-section');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const homepage = document.getElementById('homepage');
previewSection.classList.add('hidden');
loadingSection.classList.remove('hidden');
setTimeout(() => {
const mockResults = [
{ class: 'Normal', confidence: 94, covid: 3, normal: 94, pneumonia: 3, color: 'normal' },
{ class: 'COVID-19', confidence: 87, covid: 87, normal: 8, pneumonia: 5, color: 'covid' },
{ class: 'Pneumonia', confidence: 91, covid: 4, normal: 5, pneumonia: 91, color: 'pneumonia' }
];
const result = mockResults[Math.floor(Math.random() * mockResults.length)];
displayResults(result);
loadingSection.classList.add('hidden');
homepage.classList.add('hidden');
resultsSection.classList.remove('hidden');
}, 3000);
}
function displayResults(result) {
const previewImage = document.getElementById('previewImage');
const fileName = document.getElementById('fileName');
document.getElementById('resultImage').src = previewImage.src;
document.getElementById('resultFileName').textContent = fileName.textContent;
document.getElementById('resultFileSize').textContent = document.getElementById('fileSize').textContent + ' • 1024×1024 pixels';
document.getElementById('predictionClass').textContent = result.class;
document.getElementById('confidenceScore').textContent = result.confidence + '%';
document.getElementById('confidenceBar').style.width = result.confidence + '%';
document.getElementById('covidProb').textContent = result.covid + '%';
document.getElementById('normalProb').textContent = result.normal + '%';
document.getElementById('pneumoniaProb').textContent = result.pneumonia + '%';
const predictionResult = document.getElementById('predictionResult');
predictionResult.className = `result-${result.color} p-6 rounded-xl mb-6`;
}
function resetUpload() {
const uploadSection = document.getElementById('upload-section');
const previewSection = document.getElementById('preview-section');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const homepage = document.getElementById('homepage');
const fileInput = document.getElementById('fileInput');
uploadSection.classList.remove('hidden');
previewSection.classList.add('hidden');
loadingSection.classList.add('hidden');
resultsSection.classList.add('hidden');
homepage.classList.remove('hidden');
fileInput.value = '';
currentFile = null;
}
});
</script>
</body>
</html>