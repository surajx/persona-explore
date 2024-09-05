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
        id="infinite-canvas",
        hx_get="/load-images",
        hx_trigger="intersect once",
        hx_swap="beforeend",
    )


@app.get("/load-images")
def load_images(page: int = 1):
    images_per_page = 100
    start = (page - 1) * images_per_page
    end = start + images_per_page

    # Get the list of image files
    image_files = sorted(
        [f for f in os.listdir(IMAGE_DIR) if f.endswith(".png")],
        key=lambda x: int(x.split(".")[0]),
    )

    images = [
        Div(
            Img(
                src=f"/image/{os.path.splitext(file)[0]}",
                alt=f"Person {os.path.splitext(file)[0]}",
            ),
            cls="tile",
            data_id=os.path.splitext(file)[0],
        )
        for file in image_files[start:end]
    ]

    return Div(
        *images,
        hx_get=f"/load-images?page={page+1}",
        hx_trigger="intersect once",
        hx_swap="beforeend",
    )


@app.get("/image/{persona_id}")
def get_image(persona_id: str):
    image_path = os.path.join(IMAGE_DIR, f"{persona_id}.png")
    if os.path.exists(image_path):
        return FileResponse(image_path)
    else:
        return "Image not found", 404


def css_component():
    return Style(
        """
        #infinite-canvas {
            display: flex;
            flex-wrap: wrap;
            height: 100vh;
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
        .tile.center {
            transform: scale(1.5);
            z-index: 1;
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


@app.get("/person/{id}")
def person_detail(id: str):
    return Title(f"Person {id}"), Main(
        H1(f"Details for Person {id}"), Img(src=f"/image/{id}", alt=f"Person {id}")
    )


serve()
