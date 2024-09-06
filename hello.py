from fasthtml.common import *
from fasthtml.xtend import Titled, Script, Style

app = FastHTML()


# Route to display the canvas with inline CSS and JavaScript
@app.route("/")
def get():
    # CSS for the body and canvas
    css = """
    body {
        margin: 0;
        padding: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        background-color: black;
    }

    canvas {
        display: block;
    }
    """

    # Canvas tag with its dimensions
    canvas = Canvas(id="grid-canvas", width="800", height="600")

    # JavaScript for creating a grid on the canvas
    js_code = """
    const canvas = document.getElementById('grid-canvas');
    const ctx = canvas.getContext('2d');
    const gridSize = 50;
    const canvasWidth = canvas.width;
    const canvasHeight = canvas.height;

    function drawGrid() {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        for (let x = 0; x <= canvasWidth; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvasHeight);
            ctx.stroke();
        }
        for (let y = 0; y <= canvasHeight; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvasWidth, y);
            ctx.stroke();
        }
    }

    function centerGrid() {
        const translateX = (canvasWidth % gridSize) / 2;
        const translateY = (canvasHeight % gridSize) / 2;
        ctx.translate(translateX, translateY);
        drawGrid();
    }

    centerGrid();
    """

    # Return the response with CSS and JavaScript
    return Titled(
        "Grid Canvas",
        Style(css),  # Inline CSS
        canvas,  # The canvas element
        Script(js_code),  # Inline JavaScript
    )


# Serving the app
serve()
