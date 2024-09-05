from fasthtml.common import *
from starlette.responses import FileResponse
import os

app = FastHTML()

# Define the path to our images
IMAGE_DIR = "data/st-agent-images-local"

import functools


@functools.lru_cache(maxsize=1)
def get_image_list():
    files = [f for f in os.listdir(IMAGE_DIR) if f.endswith(".jpg")]
    print(f"First 5 image files: {files[:5]}")
    return files


@app.get("/")
def home():
    return Title("Community Mosaic"), Main(
        canvas_component(), css_component(), js_component()
    )


def canvas_component():
    return Div(
        Div(
            id="infinite-canvas",
            hx_get="/load-images",
            hx_trigger="intersect once",
            hx_swap="beforeend",
        ),
        id="infinite-canvas-container",
    )


@app.get("/load-images")
def load_images(page: int = 1):
    images_per_page = 100  # Reduced for debugging
    start = (page - 1) * images_per_page
    end = start + images_per_page

    image_files = get_image_list()

    print(f"Loading images from {start} to {end}")
    print(f"Total images: {len(image_files)}")

    images = [
        Div(
            Img(src=f"/image/{file.split('.')[0]}", alt=f"Person {file}"),
            cls="tile",
            data_id=file.split(".")[0],
        )
        for file in image_files[start:end]
    ]

    return Div(
        *images,
        hx_get=f"/load-images?page={page+1}",
        hx_trigger="intersect once",
        hx_swap="beforeend",
    )


@app.get("/image/{sha_value}")
def get_image(sha_value: str):
    image_path = os.path.join(IMAGE_DIR, f"{sha_value}.jpg")
    if os.path.exists(image_path):
        return FileResponse(image_path)
    else:
        return "Image not found", 404


def css_component():
    return Style(
        """
body, html {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
}
#infinite-canvas-container {
    width: 100vw;
    height: 100vh;
    overflow: auto;  /* Ensure the container is scrollable */
}
#infinite-canvas {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    grid-auto-rows: 100px;
    width: 300vw;
    height: 300vh;
    background-color: #f0f0f0; /* Added for visibility */
}
.tile {
    width: 100px;
    height: 100px;
    transition: all 0.3s;
    overflow: hidden;
    border: 1px solid #ccc; /* Added for visibility */
}
.tile img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.tile.center {
    transform: scale(1.5);
    z-index: 1;
    border: 2px solid red; /* Added for visibility */
}
"""
    )


def js_component():
    return Script(
        """
        const container = document.getElementById('infinite-canvas-container');
        const canvas = document.getElementById('infinite-canvas');
        let centerTile = null;

        function updateCenterTile() {
            const rect = container.getBoundingClientRect();
            const centerX = rect.width / 2 + container.scrollLeft;
            const centerY = rect.height / 2 + container.scrollTop;
            
            let closest = null;
            let closestDistance = Infinity;

            canvas.querySelectorAll('.tile').forEach(tile => {
                const tileRect = tile.getBoundingClientRect();
                const tileX = tileRect.left + tileRect.width / 2 + container.scrollLeft - rect.left;
                const tileY = tileRect.top + tileRect.height / 2 + container.scrollTop - rect.top;
                
                const distance = Math.sqrt(Math.pow(centerX - tileX, 2) + Math.pow(centerY - tileY, 2));
                
                if (distance < closestDistance) {
                    closest = tile;
                    closestDistance = distance;
                }
            });

            if (centerTile !== closest) {
                if (centerTile) centerTile.classList.remove('center');
                closest.classList.add('center');
                centerTile = closest;
            }
        }

        container.addEventListener('scroll', updateCenterTile);
        window.addEventListener('resize', updateCenterTile);

        container.addEventListener('click', (e) => {
            if (e.target.closest('.tile')) {
                const tile = e.target.closest('.tile');
                if (tile === centerTile) {
                    window.location.href = `/person/${tile.dataset.id}`;
                } else {
                    const rect = tile.getBoundingClientRect();
                    container.scrollTo({
                        left: rect.left + container.scrollLeft - container.clientWidth / 2 + rect.width / 2,
                        top: rect.top + container.scrollTop - container.clientHeight / 2 + rect.height / 2,
                        behavior: 'smooth'
                    });
                }
            }
        });

        // Initial center
        container.scrollTo(container.scrollWidth / 2 - container.clientWidth / 2,
                           container.scrollHeight / 2 - container.clientHeight / 2);

        // Initial update
        updateCenterTile();
    """
    )


@app.get("/person/{sha_value}")
def person_detail(sha_value: str):
    return Title(f"Person {sha_value}"), Main(
        H1(f"Details for Person {sha_value}"),
        Img(src=f"/image/{sha_value}", alt=f"Person {sha_value}"),
    )


serve()
