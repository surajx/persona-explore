from fasthtml.common import *
from fasthtml.xtend import Titled, Script, Style
import os
import random
from starlette.responses import FileResponse

# Set your image directory
IMAGE_DIR = "data/st-agent-images-local"

app = FastHTML()


# Route to serve images dynamically
@app.get("/image/{persona_id}")
def get_image(persona_id: str):
    image_path = os.path.join(IMAGE_DIR, f"{persona_id}.jpg")
    if os.path.exists(image_path):
        return FileResponse(image_path)
    else:
        return "Image not found", 404


@app.route("/")
def get():
    # CSS for body and canvas
    css = """
    body {
        margin: 0;
        padding: 0;
        overflow: hidden;
        background: linear-gradient(to bottom, #000000, #1a1a1a);
    }

    canvas {
        display: block;
        position: absolute;
        top: 0;
        left: 0;
    }

    .grid-cell img {
        border-radius: 10px;
        border: 2px solid white;
        box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        opacity: 0.9;
        transition: opacity 0.3s ease, transform 0.3s ease;
        width: 100px;
        height: 100px;  /* Fixed size */
    }

    .grid-cell img:hover {
        opacity: 1;
        transform: scale(1.1);
    }

    .focused {
        transform: scale(1.5) !important;  /* Zoom effect */
        box-shadow: 5px 5px 15px rgba(255, 255, 255, 0.8);
        z-index: 10;  /* Ensure focused cell is above others */
    }
    """

    # Load all image file names from the directory
    img_files = [f for f in os.listdir(IMAGE_DIR) if f.endswith(".jpg")]

    # JavaScript array to hold the image paths
    js_img_array = f"const images = {str([f'/image/{os.path.splitext(img)[0]}' for img in img_files])};"

    # Canvas element
    canvas = Canvas(id="grid-canvas")

    # JavaScript for canvas, scrolling, and drawing images
    js_code = f"""
    const canvas = document.getElementById('grid-canvas');
    const ctx = canvas.getContext('2d');
    const gridSize = 100;  // Fixed size for images
    const scrollSpeed = 20;  // Scrolling speed

    {js_img_array}  // Image array

    // Set canvas size to be much larger than the viewport
    const canvasWidth = 5000;  // Example width
    const canvasHeight = 5000;  // Example height

    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    // Function to draw the grid with images in each cell
    function drawGrid() {{
        const numCellsX = Math.ceil(canvasWidth / gridSize);
        const numCellsY = Math.ceil(canvasHeight / gridSize);

        ctx.clearRect(0, 0, canvasWidth, canvasHeight);

        // Draw images in each grid cell
        for (let x = 0; x <= numCellsX * gridSize; x += gridSize + 5) {{
            for (let y = 0; y <= numCellsY * gridSize; y += gridSize + 5) {{
                const img = new Image();
                img.src = images[Math.floor(Math.random() * images.length)];
                img.onload = () => {{
                    ctx.drawImage(img, x, y, gridSize, gridSize);
                }};
            }}
        }}
    }}

    // Variables to track scroll position
    let scrollX = 0;
    let scrollY = 0;

    // Scroll canvas with arrow keys
    window.addEventListener('keydown', function(e) {{
        switch (e.key) {{
            case 'ArrowUp':
                scrollY = Math.max(scrollY - scrollSpeed, 0);
                break;
            case 'ArrowDown':
                scrollY = Math.min(scrollY + scrollSpeed, canvasHeight - window.innerHeight);
                break;
            case 'ArrowLeft':
                scrollX = Math.max(scrollX - scrollSpeed, 0);
                break;
            case 'ArrowRight':
                scrollX = Math.min(scrollX + scrollSpeed, canvasWidth - window.innerWidth);
                break;
        }}
        window.scrollTo(scrollX, scrollY);
        focusCenterCell();
    }});

    // Swipe handling for touch devices
    let touchStartX = 0;
    let touchStartY = 0;

    window.addEventListener('touchstart', function(e) {{
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    }});

    window.addEventListener('touchmove', function(e) {{
        let touchEndX = e.touches[0].clientX;
        let touchEndY = e.touches[0].clientY;

        let diffX = touchStartX - touchEndX;
        let diffY = touchStartY - touchEndY;

        if (Math.abs(diffX) > Math.abs(diffY)) {{
            // Horizontal swipe
            scrollX = Math.min(Math.max(scrollX + diffX, 0), canvasWidth - window.innerWidth);
        }} else {{
            // Vertical swipe
            scrollY = Math.min(Math.max(scrollY + diffY, 0), canvasHeight - window.innerHeight);
        }}

        window.scrollTo(scrollX, scrollY);
        touchStartX = touchEndX;
        touchStartY = touchEndY;
        focusCenterCell();
    }});

    // Function to focus on the center grid cell and zoom it
    function focusCenterCell() {{
        const centerX = window.innerWidth / 2 + window.scrollX;
        const centerY = window.innerHeight / 2 + window.scrollY;

        const nearestCellX = Math.round(centerX / gridSize) * gridSize;
        const nearestCellY = Math.round(centerY / gridSize) * gridSize;

        const allImages = document.querySelectorAll('.grid-cell img');
        allImages.forEach(img => img.classList.remove('focused'));

        const img = document.elementFromPoint(window.innerWidth / 2, window.innerHeight / 2);
        if (img && img.tagName === 'IMG') {{
            img.classList.add('focused');
        }}
    }}

    // Initialize the grid and set up focus
    drawGrid();
    focusCenterCell();
    window.addEventListener('scroll', focusCenterCell);
    """

    return Titled(
        "Scrollable Grid Canvas with Focus Effect",
        Style(css),  # Inline CSS
        canvas,  # The canvas element
        Script(js_code),  # Inline JavaScript
    )


# Serve static files dynamically using a custom route
serve()
