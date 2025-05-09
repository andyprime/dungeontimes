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

const JOB_NAMES = {
    'MUSCLE': 'Muscle Man',
    'ETHICIST': 'Ethicist',
    'SWORDLORD': 'Swordlord',
    'NEERDOWELL': 'Neerdowell',
    'MAGICIAN': 'Magician'
}

// dungeon = null;
// cursor = null;
// grid = [];

expeditions = [];

rootUrl = window.location.hostname + ':8081';

/*
        <canvas id="thedungeon"></canvas>

        <div id="theparty"><b>Our Party</b><ul style="padding-left: 0; background-color: e6e6e6;"></ul></div>

        <div id="thefoes" style="display: none;"><b>Lurking Foes!</b><ul style="padding-left: 0; background-color: e6e6e6;"></ul></div>

        <p><b>Event Log</b></p>
        <div id="event-log" style="padding: 10px 20px; background-color: e6e6e6;">
            <p>The past is a mystery.</p>
        </div>
*/



document.addEventListener('DOMContentLoaded', async function(event) {
    var socket = new WebSocket('ws://' + rootUrl + '/feed/dungeon');
    socket.onmessage = receiveMessage;

    panel = document.querySelector('#thebuttons');
    panel.addEventListener('click', onDungeonSelect)


    // fetchExistingExpeditions();
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
    } else if (bits[0] == 'EXP-NEW') {
        fetchExpedition(bits[1]);
    } else if (bits[0] == 'EXP-DEL') {
        removeExpedition(bits[1]);
    } else if (bits[0] == 'BTLS') {
        toggleFoes(bits[1], true);
    } else if (bits[0] == 'BTLE') {
        toggleFoes(bits[1], false);
    } else if (bits[0] == 'BTL-UPD') {
        battleUpdate(JSON.parse(bits[1]));
    }
}

// async function fetchExistingExpeditions() {
//     url = '//' + rootUrl + "/expeditions/";
//     resp = await fetch(url);
//     json = await resp.json();

//     console.log(json);
//     pizza.ham()

// }

async function fetchExpedition(eid, initial=false) {
    // if (!initial) {
    //     log = document.querySelector('#event-log');
    //     newbie = document.createElement('p');
    //     newbie.innerHTML = 'The world is cast anew.';
    //     log.textContent = '';
    //     log.prepend(newbie);   
    // }

    for(pack in expeditions) {
        if(pack['exp']['id'] == eid) {
            console.log('We already know about expedition ', eid);
            return;
        }
    }

    resp = await fetch('//' + rootUrl + "/expedition/" + eid);
    expedition = await resp.json();
    console.log('Expedition', expedition);

    url = '//' + rootUrl + "/dungeon/" + expedition['dungeon'];
    resp = await fetch(url);
    json = await resp.json();

    dungeon = JSON.parse(json['body']);
    cursor = expedition['cursor'];
    console.log('Dungeon', dungeon);

    // toggleFoes(false);
    // draw();

    url = '//' + rootUrl + "/expedition/" + expedition['id'] + "/delvers";
    resp = await fetch(url);
    json = await resp.json();
    delvers = [];
    for (i in json) {
        delvers.push(json[i]);
    }

    package = {
        exp: expedition,
        dungeon: dungeon,
        delvers: delvers
    };

    expeditions.push(package)

    createButton(eid);

    console.log(expeditions);

    // console.log('Delvers: ', json);
    // partyEl = document.querySelector('#theparty ul');
    // partyEl.textContent = '';
    // for (i in json) {
    //     delver = json[i];
    //     partyEl.append(characterBox('delver', delver));
    // }
}

function createButton(eid) {
    but = document.createElement('button');
    but.innerHTML = 'Dungeon ' + eid;
    but.style['margin-right'] = '20px';
    but.setAttribute('eid', eid);

    panel = document.querySelector('#thebuttons');
    panel.append(but)
}

function onDungeonSelect(event) {
    console.log('Click');
    console.log(event.target);

    if(event.target.tagName == 'BUTTON') {
        console.log(event.target.getAttribute('eid'));
    }
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

function toggleFoes(roomNo, visible) {
    console.log('Toggle Foes', roomNo, visible);
    if (visible) {

        room = null;
        for (i = 0; i < dungeon.rooms.length; i++) {
            r = dungeon.rooms[i];
            if (r['n'] == roomNo) {
                room = r;
            }
        }

        document.getElementById('thefoes').style.display = 'block';
        foesEl = document.querySelector('#thefoes ul');
        console.log('Room occupants', room.occ)
        for (i in room.occ) {
            monster = room.occ[i];
            foesEl.append(characterBox('monster', monster));
        }
    } else {
        document.getElementById('thefoes').style.display = 'none';
        document.querySelector('#thefoes ul').textContent = '';
    }
}

function battleUpdate(info) {
    content = '';
    sel = '#c' + info['target'] + ' .hp';
    hpEl = document.querySelector(sel);
    content += info['newhp'] + '/' + info['maxhp'];
    if (info['dam'] != null && info['dam'] > 0) {
        animate(hpEl);
    }
    if (Array.isArray(info['status']) && info['status'].length > 0) {
        s = ' ';
        for (i = 0; i < info['status'].length; i++) {
            s += info['status'][i]['code'] + ' ';
        }
        content += s;
    }
    hpEl.textContent = content

}

function animate(element) {
    element.style.color = 'red';
    swapfn = function() {
        element.style.color = 'black';
    }
    setTimeout(swapfn, 400);
}

function characterBox(type, fellah) {
    d = document.createElement('li');
    // uuids can start with numbers so we need to prepend a letter to make sure the ID is valid
    d.id = 'c' + fellah['id'];
    d.style.display = 'inline-block';
    d.style.padding = '10px 20px';

    nameEl = document.createElement('div');
    nameEl.classList.add('name');
    if (type == 'delver') {
        nameEl.textContent = fellah['name'];
    } else{
        nameEl.textContent = fellah['n'];
    }
    d.append(nameEl);

    titleEl = document.createElement('div');
    titleEl.classList.add('title');
    if (type == 'delver') {
        titleEl.textContent = fellah['stock'] + " " + JOB_NAMES[fellah['job']]; 
    } else {
        // monster data is currently very abbreviated
        titleEl.textContent = fellah['t']; 
    }
    d.append(titleEl);

    hpEl = document.createElement('div');
    hpEl.classList.add('hp');
    if (type == 'delver') {
        hpEl.textContent = fellah['currenthp'] + '/' + fellah['maxhp'];
    } else{
        hpEl.textContent = fellah['chp'] + '/' + fellah['mhp'];
    }
    d.append(hpEl);

    return d;
}

function draw() {
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

    canvas = document.getElementById("thedungeon");
    ctx = canvas.getContext("2d");

    for (x = 0; x < grid.length; x++) {
        for (y = 0; y < grid[i].length; y++) {
            if (cursor != null && x == cursor[1] && y == cursor[0]) {
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