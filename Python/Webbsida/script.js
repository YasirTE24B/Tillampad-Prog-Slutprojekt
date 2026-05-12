const canvas = document.getElementById('spelCanvas');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score');

canvas.width = 640;
canvas.height = 800;

let ballX = 320; 
let smoothedX = 320;
let score = 0;
let obstacles = [];
let canDie = true;
let gameActive = true;

async function fetchBall() {
    try {
        const res = await fetch('http://localhost:5000/get_ball');
        const data = await res.json();
        ballX = data.ball_x;
    } catch(e) {
        // Om servern inte är igång händer inget
    }
    setTimeout(fetchBall, 15);
}

function createObstacle() {
    const gapWidth = 180;
    const gapPos = Math.random() > 0.5 ? 0 : (canvas.width - gapWidth);
    
    if (obstacles.length > 0 && obstacles[obstacles.length-1].y < 250) return;

    obstacles.push({
        y: -30,
        gapX: gapPos,
        gapW: gapWidth,
        passed: false
    });
}

function update() {
    if (!gameActive) return;
    
    smoothedX += (ballX - smoothedX) * 0.15;

    if(Math.random() < 0.02) createObstacle();

    obstacles.forEach((obs, index) => {
        obs.y += 2;

        // Poäng
        if(!obs.passed && obs.y > 600) {
            score++;
            scoreElement.innerText = score;
            obs.passed = true;
            fetch('http://localhost:5000/trigger_point').catch(e => {}); 
        }

        // Krock
        if(canDie && obs.y > 580 && obs.y < 620) {
            if(smoothedX < obs.gapX || smoothedX > (obs.gapX + obs.gapW)) {
                triggerDeath();
            }
        }

        if(obs.y > canvas.height) obstacles.splice(index, 1);
    });
}

function draw() {
    if (!gameActive) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Centerlinje (svag)
    ctx.strokeStyle = "rgba(255, 255, 255, 1)";
    ctx.beginPath(); 
    ctx.moveTo(320, 0); 
    ctx.lineTo(320, canvas.height); 
    ctx.stroke();

    // Hinder (Väggar)
    ctx.fillStyle = "#ff0000";
    obstacles.forEach(obs => {
        ctx.fillRect(0, obs.y, obs.gapX, 25);
        ctx.fillRect(obs.gapX + obs.gapW, obs.y, canvas.width, 25);
    });

    // Spelaren (Boll)
    ctx.fillStyle = "#fff000";
    ctx.beginPath();
    ctx.arc(smoothedX, 600, 15, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    update();
    requestAnimationFrame(draw);
}

function triggerDeath() {
    if (!gameActive) return;
    
    gameActive = false;
    scoreElement.innerText = "DU DOG :(";
    
    fetch('http://localhost:5000/set_status?dead=1').catch(e => {});
    
    setTimeout(() => {
        score = 0;
        obstacles = [];
        scoreElement.innerText = "0";
        gameActive = true;
        fetch('http://localhost:5000/set_status?dead=0').catch(e => {});
        requestAnimationFrame(draw);
    }, 5000);
}

fetchBall();
draw();