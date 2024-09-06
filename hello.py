from fasthtml.common import *
from fasthtml.xtend import Titled, Script, Style

app = FastHTML()


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

    # Canvas element
    canvas = Canvas(id="grid-canvas")

    # JavaScript to draw the grid and handle resizing
    js_code = """
    const canvas = document.getElementById('grid-canvas');
    const ctx = canvas.getContext('2d');
    const gridSize = 50;

    // Function to resize the canvas based on window size
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        drawGrid();
    }

    // Function to draw the grid with 50x50 cells
    function drawGrid() {
        const numCellsX = Math.ceil(canvas.width / gridSize);
        const numCellsY = Math.ceil(canvas.height / gridSize);

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';

        // Draw vertical grid lines
        for (let x = 0; x <= numCellsX * gridSize; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }

        // Draw horizontal grid lines
        for (let y = 0; y <= numCellsY * gridSize; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }
    }

    // Initialize canvas and set event listener for window resizing
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas(); // Call this initially to set the canvas size
    """

    return Titled(
        "Large Grid Canvas",
        Style(css),  # Inline CSS
        canvas,  # The canvas element
        Script(js_code),  # Inline JavaScript
    )


# Serving the app
serve()
