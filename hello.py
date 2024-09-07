from fasthtml.common import *
from fasthtml.xtend import Titled, Script, Style
import boto3
import os

import random

app = FastHTML()

# Define the S3 bucket name and folder
S3_BUCKET_NAME = "st-public-assets"
S3_FOLDER = "images/agents/"
S3_BUCKET_URL = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{S3_FOLDER}"

# Initialize the boto3 client for S3
s3 = boto3.client("s3")

# In-memory list to hold image filenames from S3
image_filenames = []


# Function to fetch all image filenames from the S3 bucket
def fetch_image_filenames():
    global image_filenames
    response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=S3_FOLDER)

    if "Contents" in response:
        # Extract the filenames from the S3 folder
        image_filenames = [
            obj["Key"].replace(S3_FOLDER, "")
            for obj in response["Contents"]
            if obj["Key"].endswith(".jpg")
        ]


# Fetch filenames from S3 when the app starts
fetch_image_filenames()


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
        transition: transform 0.2s ease-in-out, opacity 0.2s ease-in-out;
        opacity: 0.5;  /* Initially dim all images */
    }

    .zoomed {
        transform: scale(1.5);
        z-index: 1;
        opacity: 1;  /* Full opacity for focused image */
    }
    """

    # Create a JavaScript array to hold the S3 image paths (randomize order)
    random_images = [
        S3_BUCKET_URL + img
        for img in random.sample(image_filenames, len(image_filenames))
    ]

    js_img_array = f"const images = {random_images};"

    # JavaScript for creating the grid and applying zoom and opacity effect
    js_code = f"""
    const grid = document.createElement('div');
    grid.id = 'grid';
    document.body.appendChild(grid);

    {js_img_array}  // Image array

    const gridSize = 100;  // Fixed size for images
    const gridGap = 20;  // Space between cells
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

    // Function to handle zoom and opacity adjustment
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

        // Add zoom and full opacity to the closest item, and dim others
        if (closestItem && closestItem !== currentZoomedItem) {{
            closestItem.classList.add('zoomed');
            currentZoomedItem = closestItem;
        }}
    }}

    // Function to scroll to the center of the entire grid on page load
    function scrollToCanvasCenter() {{
        const gridWidth = numCellsX * (gridSize + gridGap);
        const gridHeight = numCellsY * (gridSize + gridGap);
        
        const scrollX = (gridWidth - window.innerWidth) / 2;
        const scrollY = (gridHeight - window.innerHeight) / 2;

        window.scrollTo({{
            top: scrollY,
            left: scrollX,
            behavior: 'auto'  // Scroll to the center immediately on load
        }});
    }}

    // Initial call to scroll to the center of the large grid and align the centered item
    scrollToCanvasCenter();
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


# Serve the FastHTML app
serve()
