const canvas = document.getElementById("bgWave");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let lines = [];

for (let i = 0; i < 40; i++) {
    lines.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        speed: Math.random() * 1 + 0.5
    });
}

function animate() {
    ctx.fillStyle = "rgba(15, 32, 39, 0.9)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = "rgba(118, 187, 177, 0.82)";
    ctx.lineWidth = 2;

    lines.forEach(line => {
        ctx.beginPath();
        ctx.moveTo(line.x, line.y);
        ctx.lineTo(line.x + 100, line.y + 20);
        ctx.stroke();

        line.x += line.speed;

        if (line.x > canvas.width) {
            line.x = 0;
            line.y = Math.random() * canvas.height;
        }
    });

    requestAnimationFrame(animate);
}

animate();