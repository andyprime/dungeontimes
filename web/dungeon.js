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

const CITY = 1;
const FARMLAND = 2;
const ROAD = 3;
const FOREST = 4;
const RIVER = 5;
const WATER = 6;
const HILLS = 7;
const MOUNTAIN = 8;
const DESERT = 9;
const PLAIN = 10;
const TOWN = 11;

const REGION_CELL_COLORS = {
    1: '#3855f4',
    2: '#b6ee3b',
    3: '#c8c8c8',
    4: '#236405',
    5: '#000000',
    6: '#000000',
    7: '#cbd02c',
    8: '#6a6a6a',
    9: '#ffa14f',
    10: '#20a61c',
    11: '#3855f4'
}

const DUNGEON_CELL_COLORS = {
    1: '#000000',
    2: '#9a9a9a',
    3: '#9a9a9a',
    4: '#915b0f',
    5: '#b8b8b8'
}

const REGION_CURSOR_COLOR = '#ff79cb';
const REGION_DUNGEON_COLOR = '#000000';
const DUNGEON_CURSOR_COLOR = '#18910f';

const JOB_NAMES = {
    'MUSCLE': 'Muscle Man',
    'ETHICIST': 'Ethicist',
    'SWORDLORD': 'Swordlord',
    'NEERDOWELL': 'Neerdowell',
    'MAGICIAN': 'Magician'
}

region = null;
expeditions = {};
selectedView = null;

rootUrl = window.location.hostname + ':8081';

document.addEventListener('DOMContentLoaded', async function(event) {
    var socket = new WebSocket('ws://' + rootUrl + '/feed/dungeon');
    socket.onmessage = receiveMessage;

    panel1 = document.querySelector('#region-buttons');
    panel1.addEventListener('click', onRegionSelect);

    panel2 = document.querySelector('#dungeon-buttons');
    panel2.addEventListener('click', onDungeonSelect);

    fetchExisting();
});

async function receiveMessage(event) {
    msg = await event.data.text();
    console.log(msg);
    bits = msg.split(';');

    // for expedition specific updates, ignore them if its not for the one we're looking at

    relevant = selectedView != null && bits[1] == selectedView['id'];
    // if(['NARR', 'BTLS', 'BTLE', 'BTL-UPD'].includes(bits[0])) {
    //     if(selectedView != null && bits[1] != selectedView['id']) {
    //         return;
    //     }
    // }

    if (bits[0] == 'CURSOR') {
        // we wanna track all coordinates but only draw if its the current one
        // [1] = ID, [2] = D/O, [3] = coords
        
        if (bits[2] == 'D') {
            expeditions[bits[1]]['inside'] = true;
            updateCoords(bits[1], bits[3]);
            if (relevant) {
                drawDungeon();
            }
        } else {
            expeditions[bits[1]]['inside'] = false;
            updateCoords(bits[1], bits[3]);
            if(selectedView['type'] == 'region') {
                drawRegion();
            }
        }        
    } else if (bits[0] == 'NARR') {
        if (relevant) {
            addEvent(bits[2]);
        }
    } else if (bits[0] == 'EXP-NEW') {
        fetchExpedition(bits[1]);
    } else if (bits[0] == 'EXP-DEL') {
        removeExpedition(bits[1]);
    } else if (bits[0] == 'BTLS') {
        expeditions[bits[1]]['battling'] = bits[2];
        if (relevant) {
            toggleFoes(bits[2], true);
        }
    } else if (bits[0] == 'BTLE') {
        expeditions[bits[1]]['battling'] = null;
        if (relevant) {
            toggleFoes(bits[2], false);
        }
    } else if (bits[0] == 'BTL-UPD') {
        if (relevant) {
            battleUpdate(JSON.parse(bits[2]));
        }
    } else if (bits[0] == 'DNGS') {
        entrances = []
        for (i = 1; i < bits.length; i++) {
            entrances.push(JSON.parse(bits[i]));  
        }
        region.dungeons = entrances;
        if(selectedView['type'] == 'region') {
            drawRegion();
        }  
    } 
}

async function fetchExisting() {

    url = '//' + rootUrl + '/region/';
    resp = await fetch(url);
    region = await resp.json();

    grid = [...Array(region['width'])];
    for (i in grid) {
        grid[i] = [...Array(region['height'])];
        grid[i].fill(1);
    }
    for (i =0; i < region.cells.length; i++) {
        c = region.cells[i];
        // backend does y,x so we reverse that when loading in
        grid[c[2]][c[1]] = c[0];
    }
    region['grid'] = grid;
    region['type'] = 'region';
    delete region['cells'];

    console.log('Region', region);

    createButton('region', region['id'], region['name']);
    selectRegion();

    url = '//' + rootUrl + "/expeditions/";
    resp = await fetch(url);
    json = await resp.json();

    for (i in json) {
        fetchExpedition(json[i]['id']);
    }
}

async function fetchExpedition(eid) {
    console.log('Fetch expedition', eid);
    
    if(expeditions[eid] != undefined) {
        console.log('We already know about expedition ', eid);
        return;
    }

    resp = await fetch('//' + rootUrl + "/expedition/" + eid);
    var expedition = await resp.json();
    expedition['type'] = 'dungeon';
    console.log('Expedition', expedition);

    url = '//' + rootUrl + "/dungeon/" + expedition['dungeon'];
    resp = await fetch(url);
    json = await resp.json();
    var dungeonName = json['name'];
    var dungeon = JSON.parse(json['body']);
    dungeon['battling'] = null;
    console.log('Dungeon', dungeon);

    url = '//' + rootUrl + "/expedition/" + expedition['id'] + "/delvers";
    resp = await fetch(url);
    json = await resp.json();
    var delvers = [];
    for (i in json) {
        delvers.push(json[i]);
    }

    // this is a convenience flag to avoid having to emit exp. state specifically yet
    expedition['inside'] = false;
    expedition['dungeon'] = dungeon;
    expedition['delvers'] = delvers;

    expeditions[eid] = expedition;

    createButton('dungeon', eid, dungeonName);
}

function createButton(type, id, name) {
    but = document.createElement('button');
    but.innerHTML = name;
    but.style['margin-right'] = '20px';
    but.setAttribute('id', id);

    li = document.createElement('li');
    if (type == 'dungeon') {
        li.id = 'd' + id;
    } else {
        li.id = 'r' + id;
    }
    li.className = 'btn-' + type;
    li.style['list-style-type'] = 'none';
    li.style['display'] = 'inline';
    li.append(but);

    panel = document.querySelector('#' + type + '-buttons');
    panel.append(li);
}

function onDungeonSelect(event) {
    if(event.target.tagName == 'BUTTON') {
        eid = event.target.getAttribute('id');
        selectExpedition(eid);
    }
}

function selectExpedition(id) {
    if (expeditions[id] != undefined) {
        selectedView = expeditions[id];
        
        clearLog();
        drawDungeon();
        drawParty();
        if (expeditions[id]['battling'] != null) {
            toggleFoes(expeditions[id]['battling'], true);
        }
    } else {
        throw new Error('Trying to select unknown expedition', id);
    }
}

function onRegionSelect(event) {
    if(event.target.tagName == 'BUTTON') {
        selectRegion()
    }
}

function selectRegion() {
    selectedView = region;
    clearLog();
    drawRegion();
}

function removeExpedition(eid) {
    button = document.querySelector('#d' + eid);
    button.remove();

    delete expeditions[eid];
    selectRegion();
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
    if(selectedView != null) {
        partyEl = document.querySelector('#theparty ul');
        partyEl.textContent = '';
        for (i in selectedView['delvers']) {
            delver = selectedView['delvers'][i];
            partyEl.append(characterBox('delver', delver));
        }
    }
}

function toggleFoes(roomNo, visible) {
    console.log('Toggle Foes', roomNo, visible);
    if (visible) {

        dungeon = selectedView['dungeon'];

        console.log(dungeon);

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

    if (expeditions[eid] != undefined) {
        expeditions[eid]['cursor'] = [coords[0], coords[1]];
    }
}

function drawRegion() {
    canvas = document.getElementById("themap");
    canvas.setAttribute('width', (region['width'] * GRID_SIZE) + (region['width'] - 1) + (2 * HORIZONTAL_MARGIN) );
    canvas.setAttribute('height', (region['height'] * GRID_SIZE) + (region['height'] - 1) + (2 * VERTICAL_MARGIN) );
    ctx = canvas.getContext("2d");

    cursors = [];
    for (i in expeditions) {
        if (!expeditions[i]['inside']) {
            cursors.push(expeditions[i]['cursor']);
        }
    }

    for (x = 0; x < region.grid.length; x++) {
        for (y = 0; y < region.grid[x].length; y++) {

            // tuples don't exist in javascript so we gotta do work to figure this out
            inCursors = false;
            inDungeons = false;
            for (c in cursors) {
                if (cursors[c][0] == y && cursors[c][1] == x) {
                    inCursors = true;
                }
            }
            for (d in region.dungeons) {
                if (region.dungeons[d][0] == y && region.dungeons[d][1] == x) {
                    inDungeons = true;
                }
            }

            if (inCursors) {
                ctx.fillStyle = REGION_CURSOR_COLOR;
            } else if(inDungeons) {
                ctx.fillStyle = REGION_DUNGEON_COLOR;
            } else {
                ctx.fillStyle = REGION_CELL_COLORS[region.grid[x][y]];
            }

            switch (region.grid[x][y]) {
                default:
                    xpos = HORIZONTAL_MARGIN + x + (x * GRID_SIZE);
                    ypos = VERTICAL_MARGIN + y + (y * GRID_SIZE);

                    ctx.fillRect(xpos, ypos, GRID_SIZE, GRID_SIZE);
            }
        }
    }

}

function drawDungeon(dungeon) {
    if (selectedView == null) {
        console.log('No one ever selected an expedition.');
        return;
    }

    dungeon = selectedView['dungeon'];
    cursor = selectedView['cursor'];

    canvas = document.getElementById("themap");

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

    canvas = document.getElementById("themap");
    ctx = canvas.getContext("2d");

    for (x = 0; x < grid.length; x++) {
        for (y = 0; y < grid[x].length; y++) {
            if (cursor != null && x == cursor[1] && y == cursor[0]) {
                ctx.fillStyle = DUNGEON_CURSOR_COLOR;
            } else {
                ctx.fillStyle = DUNGEON_CELL_COLORS[grid[x][y]];
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