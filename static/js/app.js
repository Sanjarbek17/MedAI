document.addEventListener('DOMContentLoaded', function() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const uploadSection = document.getElementById('upload-section');
    const previewSection = document.getElementById('preview-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const homepage = document.getElementById('homepage');
    const predictBtn = document.getElementById('predictBtn');
    const removeBtn = document.getElementById('removeBtn');
    const tryAnotherBtn = document.getElementById('tryAnotherBtn');
    
    let currentFile = null;
    let uploadedFilename = null;
    let isProcessing = false; // Add flag to prevent double processing

    function showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
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

    function showSuccessMessage(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 right-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg shadow-lg z-50';
        successDiv.innerHTML = `
            <div class="flex items-center">
                <div class="w-5 h-5 flex items-center justify-center mr-2">
                    <i class="ri-check-line"></i>
                </div>
                <p>${message}</p>
            </div>
        `;
        document.body.appendChild(successDiv);
        setTimeout(() => {
            successDiv.remove();
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

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                uploadedFilename = result.filename;
                showSuccessMessage('File uploaded successfully!');
                return true;
            } else {
                showErrorMessage(result.error || 'Upload failed');
                return false;
            }
        } catch (error) {
            showErrorMessage('Network error. Please try again.');
            return false;
        }
    }

    async function handleFileSelect(file) {
        // Prevent double processing
        if (isProcessing) {
            console.log('Already processing a file, ignoring...');
            return;
        }

        console.log('handleFileSelect called with:', file.name);
        
        if (!validateFile(file)) {
            return;
        }

        isProcessing = true;
        currentFile = file;
        const reader = new FileReader();
        
        reader.onload = async (e) => {
            const img = new Image();
            img.onload = async function() {
                console.log('Image loaded, uploading to server...');
                // Upload file to server
                const uploadSuccess = await uploadFile(file);
                
                if (uploadSuccess) {
                    console.log('Upload successful, updating UI...');
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
                }
                isProcessing = false;
            };
            img.onerror = () => {
                showErrorMessage('Invalid image file. Please try again.');
                isProcessing = false;
            };
            img.src = e.target.result;
        };

        reader.onerror = () => {
            showErrorMessage('Error reading file. Please try again.');
            isProcessing = false;
        };

        reader.readAsDataURL(file);
    }

    async function handlePrediction() {
        if (!currentFile) {
            showErrorMessage('Please upload a file first');
            return;
        }

        previewSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');

        try {
            // Step 1: First check if the image is a chest X-ray
            const formDataChest = new FormData();
            formDataChest.append('file', currentFile);

            console.log('Step 1: Validating if image is a chest X-ray...');
            const chestResponse = await fetch('/chest', {
                method: 'POST',
                body: formDataChest
            });

            const chestResult = await chestResponse.json();

            if (!chestResponse.ok) {
                showErrorMessage(chestResult.error || 'Chest validation failed');
                loadingSection.classList.add('hidden');
                previewSection.classList.remove('hidden');
                return;
            }

            console.log('Chest validation result:', chestResult.prediction);

            // Check if the image is actually a chest X-ray
            // The model returns "chest_image" for chest X-rays and "not_chest" for non-chest images
            const isChestImage = chestResult.prediction.class.toLowerCase().includes('chest_image') ||
                               (chestResult.prediction.class.toLowerCase().includes('chest') && 
                                !chestResult.prediction.class.toLowerCase().includes('not_chest'));

            if (!isChestImage) {
                showErrorMessage(`This does not appear to be a chest X-ray image. Detected: ${chestResult.prediction.class} (${chestResult.prediction.confidence}% confidence). Please upload a valid chest X-ray.`);
                loadingSection.classList.add('hidden');
                previewSection.classList.remove('hidden');
                return;
            }

            // Step 2: Check if the chest image shows COVID
            const formData1 = new FormData();
            formData1.append('file', currentFile);

            console.log('Step 2: Checking for COVID...');
            const covidResponse = await fetch('/iscovid', {
                method: 'POST',
                body: formData1
            });

            const covidResult = await covidResponse.json();

            if (!covidResponse.ok) {
                showErrorMessage(covidResult.error || 'COVID check failed');
                loadingSection.classList.add('hidden');
                previewSection.classList.remove('hidden');
                return;
            }

            console.log('COVID check result:', covidResult.prediction);

            // Step 3: Use detailed classification for final results
            const formData2 = new FormData();
            formData2.append('file', currentFile);

            console.log('Step 3: Getting detailed classification...');
            const detailResponse = await fetch('/image', {
                method: 'POST',
                body: formData2
            });

            const detailResult = await detailResponse.json();

            if (detailResponse.ok) {
                // Combine results: use detailed classification but inform with COVID check
                const finalResult = detailResult.prediction;
                
                // Log all results for comparison
                console.log('Chest validation result:', chestResult.prediction);
                console.log('COVID-specific model result:', covidResult.prediction);
                console.log('4-class model result:', finalResult);
                
                displayResults(finalResult);
                loadingSection.classList.add('hidden');
                homepage.classList.add('hidden');
                resultsSection.classList.remove('hidden');
            } else {
                showErrorMessage(detailResult.error || 'Detailed classification failed');
                loadingSection.classList.add('hidden');
                previewSection.classList.remove('hidden');
            }
        } catch (error) {
            showErrorMessage('Network error. Please try again.');
            loadingSection.classList.add('hidden');
            previewSection.classList.remove('hidden');
        }
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
        const colorClass = result.class === 'COVID-19' ? 'covid' : 
                          result.class === 'Normal' ? 'normal' : 'pneumonia';
        predictionResult.className = `result-${colorClass} p-6 rounded-xl mb-6`;
    }

    function resetUpload() {
        uploadSection.classList.remove('hidden');
        previewSection.classList.add('hidden');
        loadingSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
        homepage.classList.remove('hidden');
        
        fileInput.value = '';
        currentFile = null;
        uploadedFilename = null;
        isProcessing = false; // Reset processing flag
        console.log('Upload reset');
    }

    // Event listeners with improved handling
    browseBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        fileInput.click();
    });

    uploadZone.addEventListener('click', (e) => {
        // Only trigger if clicking on the upload zone itself, not child elements
        if (e.target === uploadZone || uploadZone.contains(e.target)) {
            e.preventDefault();
            e.stopPropagation();
            fileInput.click();
        }
    });

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        // Only remove dragover if we're leaving the upload zone completely
        if (!uploadZone.contains(e.relatedTarget)) {
            uploadZone.classList.remove('dragover');
        }
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

    // Clear previous event listener and add new one
    fileInput.addEventListener('change', (e) => {
        console.log('File input changed:', e.target.files.length);
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    predictBtn.addEventListener('click', handlePrediction);
    removeBtn.addEventListener('click', resetUpload);
    tryAnotherBtn.addEventListener('click', resetUpload);
});