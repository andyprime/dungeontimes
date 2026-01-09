const rootUrl = window.location.hostname + ':8081';

// async function fetchRegion() {
//   const url = '//' + rootUrl + '/region/';
//   var resp = await fetch(url);
//   var region = await resp.json();

//   var cells = JSON.parse(region['cells']);
//   var grid = [...Array(region['width'])];
//   for (var i in grid) {
//     grid[i] = [...Array(region['height'])];
//     grid[i].fill(1);
//   }
//   for (i =0; i < cells.length; i++) {
//     var c = cells[i];
//     // backend does y,x so we reverse that when loading in
//     grid[c[2]][c[1]] = c[0];
//   }
//   region['grid'] = grid;
//   region['type'] = 'region';
//   delete region['cells'];

//   return region;
// }

const getRegion = async function({ queryKey }) {
  console.log('Start');
  let response = await fetch('//' + rootUrl + '/region');
  if (!response.ok) {
    console.log('Oops', response);
    throw new Error('Region fetch failed');
  }

  // region cells are stored funny at the moment
  let region = await response.json();

  let cells = JSON.parse(region['cells']);
  let grid = [...Array(region['width'])];
  for (var i in grid) {
    grid[i] = [...Array(region['height'])];
    grid[i].fill(1);
  }
  for (i =0; i < cells.length; i++) {
    var c = cells[i];
    // backend does y,x so we reverse that when loading in
    grid[c[2]][c[1]] = c[0];
  }
  region['grid'] = grid;

  return region;
}

const getDungeon = async function({ queryKey }) {
  let [_key, dId] = queryKey;
  let url = '//' + rootUrl + '/dungeon/' + dId;
  let response = await fetch(url);
  if (!response.ok) {
    throw new Error('Dungeon fetch failed.');
  }

  let dungeon = await response.json();
  dungeon['cells'] = JSON.parse(dungeon['cells']);
  
  return dungeon;
}

const getDungeons = async function({ queryKey }) {
  let url = '//' + rootUrl + '/dungeon';
  let response = await fetch(url);
  if (!response.ok) {
    throw new Error('Dungeon fetch failed.');
  }
  let dungeons = await response.json();

  for (var i in dungeons) {
    dungeons[i]['cells'] = JSON.parse(dungeons[i]['cells']);
  }
  return dungeons;
}

const getBands = async function() {
  let response = await fetch('//' + rootUrl + '/bands');
  if (!response.ok) {
    throw new Error('Bands fetch failed.');
  }
  return response.json();
}

const getBand = async function({ queryKey }) {
  let [_key, bId] = queryKey;
  let response = await fetch('//' + rootUrl + '/band/' + bId);
  if (!response.ok) {
    throw new Error('Band fetch failed.');
  }
  return response.json();
}

const getDelvers = async function({ queryKey }) {
  let [_key, bId] = queryKey;
  let response = await fetch('//' + rootUrl + '/band/' + bId + '/delvers');
  if (!response.ok) {
    throw new Error('Delver fetch failed.');
  }
  return response.json();
}

const getExpeditions = async function({ queryKey }) {
  let response = await fetch('//' + rootUrl + '/expeditions');
  if (!response.ok) {
    throw new Error('expeditions fetch failed.');
  }
  return response.json();
}

export { rootUrl, getRegion, getDungeon, getDungeons, getBands, getBand, getDelvers, getExpeditions }