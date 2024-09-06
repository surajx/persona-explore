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

    #grid {
        position: relative;
        width: 5000px;  /* Large grid size */
        height: 5000px;
    }

    .grid-item {
        position: absolute;
        width: 100px;  /* Fixed size for images */
        height: 100px;
        border-radius: 10px;
        transition: transform 0.2s ease-in-out;
    }

    .zoomed {
        transform: scale(1.5);
        z-index: 1;
    }

    """

    # Load all image file names from the directory
    img_files = [f for f in os.listdir(IMAGE_DIR) if f.endswith(".jpg")]

    # Create a JavaScript array to hold the image paths
    js_img_array = f"const images = {str([f'/image/{os.path.splitext(img)[0]}' for img in img_files])};"

    # JavaScript for creating the grid and applying zoom effect
    js_code = f"""
    const grid = document.createElement('div');
    grid.id = 'grid';
    document.body.appendChild(grid);

    {js_img_array}  // Image array

    const gridSize = 100;  // Fixed size for images
    const gridGap = 5;  // Space between cells
    const numCellsX = Math.ceil(5000 / (gridSize + gridGap));  // Number of cells horizontally
    const numCellsY = Math.ceil(5000 / (gridSize + gridGap));  // Number of cells vertically

    // Create grid items and append to grid
    for (let x = 0; x < numCellsX; x++) {{
        for (let y = 0; y < numCellsY; y++) {{
            const img = new Image();
            img.src = images[Math.floor(Math.random() * images.length)];
            img.classList.add('grid-item');
            img.style.left = `${{x * (gridSize + gridGap)}}px`;
            img.style.top = `${{y * (gridSize + gridGap)}}px`;
            grid.appendChild(img);
        }}
    }}

    let currentZoomedItem = null;

    // Function to handle zoom and scroll adjustment
    function zoomOnCenter() {{
        const centerX = window.innerWidth / 2 + window.scrollX;
        const centerY = window.innerHeight / 2 + window.scrollY;

        let closestItem = null;
        let closestDistance = Infinity;

        const items = document.querySelectorAll('.grid-item');
        items.forEach(item => {{
            const itemRect = item.getBoundingClientRect();
            const itemCenterX = itemRect.left + itemRect.width / 2 + window.scrollX;
            const itemCenterY = itemRect.top + itemRect.height / 2 + window.scrollY;

            const distance = Math.sqrt(Math.pow(centerX - itemCenterX, 2) + Math.pow(centerY - itemCenterY, 2));
            if (distance < closestDistance) {{
                closestDistance = distance;
                closestItem = item;
            }}
        }});

        // Remove zoom from the previous item
        if (currentZoomedItem && closestItem !== currentZoomedItem) {{
            currentZoomedItem.classList.remove('zoomed');
        }}

        // Add zoom to the closest item and scroll only if the closest item has changed
        if (closestItem && closestItem !== currentZoomedItem) {{
            closestItem.classList.add('zoomed');
            currentZoomedItem = closestItem;
        }}
    }}

    // Initial call to align the first centered item
    zoomOnCenter();

    // Event listener for scroll to adjust zoom on the center item
    window.addEventListener('scroll', zoomOnCenter);

    // Arrow keys for scrolling
    window.addEventListener('keydown', function(e) {{
        switch (e.key) {{
            case 'ArrowUp':
                window.scrollBy(0, -20);
                break;
            case 'ArrowDown':
                window.scrollBy(0, 20);
                break;
            case 'ArrowLeft':
                window.scrollBy(-20, 0);
                break;
            case 'ArrowRight':
                window.scrollBy(20, 0);
                break;
        }}
        zoomOnCenter();
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

        window.scrollBy(diffX, diffY);
        zoomOnCenter();

        touchStartX = touchEndX;
        touchStartY = touchEndY;
    }});
    """

    return Titled(
        "Scrollable Grid with Focus Effect",
        Style(css),  # Inline CSS
        Script(js_code),  # Inline JavaScript
    )


# Serve static files dynamically using a custom route
serve()
