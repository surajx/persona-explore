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
    # CSS for the body and canvas
    css = """
    body {
        margin: 0;
        padding: 0;
        overflow: hidden;
        background-color: black;
    }

    canvas {
        display: block;
        position: absolute;
        top: 0;
        left: 0;
    }
    """

    # Load all image file names from the directory
    img_files = [f for f in os.listdir(IMAGE_DIR) if f.endswith(".jpg")]

    # Create a JavaScript array to hold the image paths (using dynamic routes)
    js_img_array = f"const images = {str([f'/image/{os.path.splitext(img)[0]}' for img in img_files])};"

    # Canvas element
    canvas = Canvas(id="grid-canvas")

    # JavaScript to draw the grid and randomly place images in each cell
    # Corrected JavaScript code inside the f-string
    js_code = f"""
    const canvas = document.getElementById('grid-canvas');
    const ctx = canvas.getContext('2d');
    const gridSize = 50;
    const images = {str([f'/image/{os.path.splitext(img)[0]}' for img in img_files])};  // Image array

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
        for (let x = 0; x <= numCellsX * gridSize; x += gridSize) {{
            for (let y = 0; y <= numCellsY * gridSize; y += gridSize) {{
                const img = new Image();
                img.src = images[Math.floor(Math.random() * images.length)];
                img.onload = () => {{
                    ctx.drawImage(img, x, y, gridSize, gridSize);
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
