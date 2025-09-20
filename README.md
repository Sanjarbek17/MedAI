# MedikAI Classifier - COVID-19 Chest X-Ray Analysis

A Flask web application for classifying chest X-ray images to detect COVID-19, pneumonia, and normal cases using AI.

## Features

- Web-based file upload interface
- Drag & drop support for X-ray images
- Real-time prediction results
- Responsive design with Tailwind CSS
- Support for JPG, JPEG, and PNG files (up to 10MB)

## Project Structure

```
MedikAI-Classifier/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main template
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── app.js        # Frontend JavaScript
└── uploads/              # Uploaded files storage
```

## Installation & Setup

1. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

1. Upload a chest X-ray image by:
   - Clicking "Browse Files" button
   - Dragging and dropping an image file
   
2. Click "Analyze X-Ray" to process the image

3. View the AI prediction results with confidence scores

## Development

### Running in Development Mode

The Flask app runs in debug mode by default when executed directly:

```bash
python app.py
```

### Production Deployment

For production, use a WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

- `GET /` - Main page
- `POST /upload` - Upload X-ray image
- `POST /predict` - Get AI prediction for uploaded image

## Technical Details

- **Backend**: Flask (Python)
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **File Handling**: Werkzeug for secure file uploads
- **Image Support**: JPG, JPEG, PNG (max 10MB)

## Medical Disclaimer

This tool is for research and educational purposes only. Results should not be used for medical diagnosis or treatment decisions. Always consult with qualified healthcare professionals.

## License

This project is for educational and research purposes.