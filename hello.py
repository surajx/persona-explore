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
    # CSS for the body, canvas, and grid cells
    css = """
    body {
        margin: 0;
        padding: 0;
        overflow: hidden;
        background: linear-gradient(to bottom, #000000, #1a1a1a);
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
    }

    canvas {
        display: block;
        position: absolute;
        top: 0;
        left: 0;
    }

    .grid-cell img {
        border: 2px solid white;
        box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        opacity: 0.8;
        transition: opacity 0.3s ease, transform 0.3s ease;
    }

    .grid-cell img:hover {
        opacity: 1;
        transform: scale(1.1);
    }
    """

    # Load all image file names from the directory
    img_files = [f for f in os.listdir(IMAGE_DIR) if f.endswith(".jpg")]

    # JavaScript array to hold the image paths
    js_img_array = f"const images = {str([f'/image/{os.path.splitext(img)[0]}' for img in img_files])};"

    # Canvas element
    canvas = Canvas(id="grid-canvas")

    # JavaScript to draw the grid and randomly place images in each cell with margins and random sizes
    js_code = f"""
    const canvas = document.getElementById('grid-canvas');
    const ctx = canvas.getContext('2d');
    const gridSize = 50;
    const sizes = [50, 75, 100];  // Different cell sizes
    {js_img_array}  // Image array

    // Function to resize the canvas based on window size
    function resizeCanvas() {{
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        drawGrid();
    }}

    // Function to draw the grid with images in each cell
    function drawGrid() {{
        const numCellsX = Math.ceil(canvas.width / gridSize);
        const numCellsY = Math.ceil(canvas.height / gridSize);

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Randomly draw images in each grid cell
        for (let x = 0; x <= numCellsX * gridSize; x += gridSize + 5) {{  // Adding 5px margin
            for (let y = 0; y <= numCellsY * gridSize; y += gridSize + 5) {{  // Adding 5px margin
                const img = new Image();
                const randomSize = sizes[Math.floor(Math.random() * sizes.length)];
                img.src = images[Math.floor(Math.random() * images.length)];
                img.onload = () => {{
                    ctx.drawImage(img, x, y, randomSize, randomSize);
                }};
            }}
        }}
    }}

    // Initialize canvas and set event listener for window resizing
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();  // Call this initially to set the canvas size
    """

    return Titled(
        "Grid Canvas with Random Images",
        Style(css),  # Inline CSS
        canvas,  # The canvas element
        Script(js_code),  # Inline JavaScript
    )


# Serve static files dynamically using a custom route
serve()
