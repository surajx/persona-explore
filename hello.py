from fasthtml.common import *
from starlette.responses import FileResponse
import os

app = FastHTML()

# Define the path to our images
IMAGE_DIR = "data/st-agent-images-local"


@app.get("/")
def home():
    return Title("Community Mosaic"), Main(
        canvas_component(), css_component(), js_component()
    )


def canvas_component():
    return Div(
        Div(id="infinite-canvas"),
        Div(  # The sentinel element
            "Loading more images...",
            id="load-more",
            hx_get="/load-images?page=1",
            hx_trigger="intersect once",
            hx_swap="beforeend",
        ),
    )


@app.get("/load-images")
def load_images(page: int = 1):
    images_per_page = 100
    start = (page - 1) * images_per_page
    end = start + images_per_page

    # Get the list of image files
    image_files = [f for f in os.listdir(IMAGE_DIR) if f.endswith(".jpg")]

    images = [
        Div(
            Img(src=f"/image/{os.path.splitext(file)[0]}", alt=f"Person {file}"),
            cls="tile",
            data_id=os.path.splitext(file)[0],
        )
        for file in image_files[start:end]
    ]

    # If there are still more images to load, append a new load trigger
    if end < len(image_files):
        return Div(
            *images,
            Div(
                "Loading more images...",
                hx_get=f"/load-images?page={page+1}",
                hx_trigger="intersect once",
                hx_swap="beforeend",
            ),
        )
    else:
        # If no more images, just return the current set
        return Div(*images)


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
#infinite-canvas {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    grid-auto-rows: 100px;
    width: 300vw;  /* Expand horizontally */
    height: 300vh;  /* Expand vertically */
    overflow: auto;
}

.tile {
    width: 100px;
    height: 100px;
    transition: all 0.3s;
}

.tile img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
        """
    )


def js_component():
    return Script(
        """
        const canvas = document.getElementById('infinite-canvas');
        let centerTile = null;

        function updateCenterTile() {
            const rect = canvas.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            
            let closest = null;
            let closestDistance = Infinity;

            canvas.querySelectorAll('.tile').forEach(tile => {
                const tileRect = tile.getBoundingClientRect();
                const tileX = tileRect.left + tileRect.width / 2;
                const tileY = tileRect.top + tileRect.height / 2;
                
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

        canvas.addEventListener('scroll', updateCenterTile);
        window.addEventListener('resize', updateCenterTile);

        canvas.addEventListener('click', (e) => {
            if (e.target.closest('.tile')) {
                const tile = e.target.closest('.tile');
                if (tile === centerTile) {
                    window.location.href = `/person/${tile.dataset.id}`;
                } else {
                    tile.scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});
                }
            }
        });

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
