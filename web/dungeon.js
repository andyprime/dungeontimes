const HORIZONTAL_MARGIN = 2;
const VERTICAL_MARGIN = 2;
const GRID_SIZE = 20;

const SOLID = 1;
const ROOM = 2;
const PASSAGE = 3;
const DOORWAY = 4;
const ENTRANCE = 5;

const CELL_COLORS = {
    1: '#000000',
    2: '#9a9a9a',
    3: '#9a9a9a',
    4: '#915b0f',
    5: '#b8b8b8'
}

const CURSOR_COLOR = '#18910f';

dungeon = null;
cursor = null;
grid = [];


document.addEventListener('DOMContentLoaded', async function(event) {
    var socket = new WebSocket('ws://localhost:8081/feed/dungeon');
    socket.onmessage = receiveMessage;

    fetchExpedition();
});

async function receiveMessage(event) {
    msg = await event.data.text();
    console.log(msg);
    bits = msg.split(';');
    if (bits[0] == 'CURSOR') {
        coords = bits[1].split(',');
        
        cursor = [coords[0], coords[1]];
        draw();
    } else if (bits[0] == 'NARR') {
        addEvent(bits[1]);
    } else if (bits[0] == 'EXP') {
        fetchExpedition()
    }
}

async function fetchExpedition() {
    url = "http://localhost:8081/expedition/";
    resp = await fetch(url);
    json = await resp.json();
    expedition = json[0];
    console.log('Expedition', expedition);

    url = "http://localhost:8081/dungeon/" + expedition['dungeon'];
    resp = await fetch(url);
    json = await resp.json();

    dungeon = JSON.parse(json['body']);
    cursor = expedition['cursor'];
    console.log('Dungeon', dungeon)

    draw()
}

function addEvent(message) {
    newbie = document.createElement('p');
    newbie.innerHTML = message;
    document.querySelector('#event-log').prepend(newbie);

    events = document.querySelectorAll('#event-log p');
    if (events.length > 10) {
        events[events.length - 1].remove();
    }
}

function draw() {
    console.log('Drawing new dungeon')
    canvas = document.getElementById("thedungeon");

    canvas.setAttribute('width', (dungeon['width'] * GRID_SIZE) + (dungeon['width'] - 1) + (2 * HORIZONTAL_MARGIN) );
    canvas.setAttribute('height', (dungeon['height'] * GRID_SIZE) + (dungeon['height'] - 1) + (2 * VERTICAL_MARGIN) );

    grid = [...Array(dungeon['width'])];

    for (i in grid) {
        grid[i] = [...Array(dungeon['height'])];
        grid[i].fill(1);
    }

    for (code in dungeon['cells']) {
        type = +code.substring(1);
        for (coords of dungeon['cells'][code]) {
            grid[coords[1]][coords[0]] = type;
        }
    }

    console.log('Pre-draw cursor: ', cursor);
    canvas = document.getElementById("thedungeon");
    ctx = canvas.getContext("2d");

    for (x = 0; x < grid.length; x++) {
        for (y = 0; y < grid[i].length; y++) {

            if (cursor != null && x == cursor[1] && y == cursor[0]) {
                console.log('Found cursor', grid[x][y]);
                ctx.fillStyle = CURSOR_COLOR;
            } else {
                ctx.fillStyle = CELL_COLORS[grid[x][y]];
            }

            switch (grid[x][y]) {
                case ENTRANCE:
                    xpos = HORIZONTAL_MARGIN + x + (x * GRID_SIZE);
                    ypos = VERTICAL_MARGIN + y + (y * GRID_SIZE);

                    ctx.fillRect(xpos, ypos, GRID_SIZE, GRID_SIZE);

                    cursorx = xpos
                    cursory = ypos
                    ctx.fillStyle = '#000000';
                    ctx.beginPath();
                    ctx.moveTo(cursorx, cursory);

                    for (i = 0; i < 4; i++) {
                        cursorx += 5;
                        ctx.lineTo(cursorx, cursory);
                        cursory += 5;
                        ctx.lineTo(cursorx, cursory);
                    }
                    ctx.closePath();
                    ctx.fill();

                    break;
                default:
                    xpos = HORIZONTAL_MARGIN + x + (x * GRID_SIZE);
                    ypos = VERTICAL_MARGIN + y + (y * GRID_SIZE);

                    ctx.fillRect(xpos, ypos, GRID_SIZE, GRID_SIZE);
            }
        }
    }

}