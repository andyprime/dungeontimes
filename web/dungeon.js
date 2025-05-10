// Andy, you ask, why are you writing all this raw javascript?
// Well, it started off as a time saving mechanism but now its kind of a novelty.

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

expeditions = [];
selectedExpedition = null;

rootUrl = window.location.hostname + ':8081';

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

    // for expedition specific updates, ignore them if its not for the one we're looking at
    if(['NARR', 'BTLS', 'BTLE', 'BTL-UPD'].includes(bits[0])) {
        if(selectedExpedition != null && bits[1] != selectedExpedition['exp']['id']) {
            return;
        }
    }

    if (bits[0] == 'CURSOR') {
        // we wanna track all coordinates but only draw if its the current one
        updateCoords(bits[1], bits[2]);
        if (bits[1] == selectedExpedition['exp']['id']) {
            drawMap();
        }
    } else if (bits[0] == 'NARR') {
        addEvent(bits[2]);
    } else if (bits[0] == 'EXP-NEW') {
        fetchExpedition(bits[1]);
    } else if (bits[0] == 'EXP-DEL') {
        removeExpedition(bits[1]);
    } else if (bits[0] == 'BTLS') {
        toggleFoes(bits[2], true);
    } else if (bits[0] == 'BTLE') {
        toggleFoes(bits[2], false);
    } else if (bits[0] == 'BTL-UPD') {
        battleUpdate(JSON.parse(bits[2]));
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

    console.log('Fetch expedition', eid);
    for(pack in expeditions) {
        if(pack['exp']['id'] == eid) {
            console.log('We already know about expedition ', eid);
            return;
        }
    }

    resp = await fetch('//' + rootUrl + "/expedition/" + eid);
    var expedition = await resp.json();
    console.log('Expedition', expedition);

    url = '//' + rootUrl + "/dungeon/" + expedition['dungeon'];
    resp = await fetch(url);
    json = await resp.json();
    var dungeon = JSON.parse(json['body']);
    console.log('Dungeon', dungeon);

    url = '//' + rootUrl + "/expedition/" + expedition['id'] + "/delvers";
    resp = await fetch(url);
    json = await resp.json();
    var delvers = [];
    for (i in json) {
        delvers.push(json[i]);
    }

    expeditions.push({
        exp: expedition,
        dungeon: dungeon,
        delvers: delvers
    });

    createButton(eid);
    if (expeditions.length == 1) {
        selectExpedition(eid);
    }    
}

function createButton(eid) {
    but = document.createElement('button');
    but.innerHTML = 'Dungeon ' + eid;
    but.id = 'd' + eid;
    but.style['margin-right'] = '20px';
    but.setAttribute('eid', eid);

    panel = document.querySelector('#thebuttons');
    panel.append(but)
}

function onDungeonSelect(event) {
    if(event.target.tagName == 'BUTTON') {
        eid = event.target.getAttribute('eid');
        selectExpedition(eid);
    }
}

function selectExpedition(eid) {
    for (i in expeditions) {
        package = expeditions[i];
        if(package['exp']['id'] == eid) {
            selectedExpedition = package;
        }
    }
    console.log('Exp. selected: ', selectedExpedition);
    
    clearLog();
    drawMap();
    drawParty();
}

function removeExpedition(eid) {
    if (selectedExpedition != null && selectedExpedition['exp']['id'] == eid) {
        replacement = null;
        for (i in expeditions) {
            if (expeditions[i]['exp']['id'] != eid) {
                replacement = expeditions[i];
            }
        }
    }

    button = document.querySelector('#d' + eid);
    button.remove();

    console.log('pre splice: ', expeditions.length);
    for (i in expeditions) {
        if (expeditions[i]['exp']['id'] == eid) {
            expeditions.splice(i, 1);
        }
    }
    console.log('post splice: ', expeditions.length);

    if (replacement != null) {
        selectExpedition(replacement['exp']['id']);
    } else {
        clearData();
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

function clearLog() {
    document.querySelector('#event-log').innerHTML = '';
    addEvent('The past is lost');
}

function drawParty() {
    if(selectedExpedition != null) {
        partyEl = document.querySelector('#theparty ul');
        partyEl.textContent = '';
        for (i in selectedExpedition['delvers']) {
            delver = selectedExpedition['delvers'][i];
            partyEl.append(characterBox('delver', delver));
        }
    }
}

function toggleFoes(roomNo, visible) {
    console.log('Toggle Foes', roomNo, visible);
    if (visible) {

        dungeon = selectedExpedition['dungeon'];

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
    hpEl.textContent = content;
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

function updateCoords(eid, coordString) {
    coords = coordString.split(',');
    for (i in expeditions) {
        if (expeditions[i]['exp']['id'] == eid) {
            console.log('Updating coords: ', eid, coords);
            expeditions[i]['exp']['cursor'] = [coords[0], coords[1]];
        }
    }
}

function drawMap(dungeon) {
    if (selectedExpedition == null) {
        console.log('No one ever selected an expedition.');
        return;
    }

    dungeon = selectedExpedition['dungeon'];
    cursor = selectedExpedition['exp']['cursor'];

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

function clearData() {
    // might not be strictly necessary if things happen fast enough
}