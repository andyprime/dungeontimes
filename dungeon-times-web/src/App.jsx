import { useContext, useState, useEffect, useRef } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './App.css'
import RegionMap from './RegionMap.jsx'

const rootUrl = window.location.hostname + ':8081';




async function fetchExisting() {
  const url = '//' + rootUrl + '/region/';
  var resp = await fetch(url);
  var region = await resp.json();

  var cells = JSON.parse(region['cells']);
  var grid = [...Array(region['width'])];
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
  region['type'] = 'region';
  delete region['cells'];

  console.log('Region fetch: ', region);

  return region;

    // createButton('region', region['id'], region['name']);
    // selectRegion();

//     url = '//' + rootUrl + "/expeditions/";
//     resp = await fetch(url);
//     json = await resp.json();

//     for (i in json) {
//         fetchExpedition(json[i]['id']);
//     }
}


function App() {

  var expeditions = {};

  const [region, setRegion] = useState(null);
  
  var region2 = region;

  const [regionCursors, setRegionCursors] = useState([[]]);
  const [inBattle, setInBattle] = useState(false);

  var receiveMessage = async function (event) {
    let msg = await event.data.text();
    let bits = msg.split(';');

    if (bits[0] == 'CURSOR') {
      // console.log(msg);
      // we wanna track all coordinates but only draw if its the current one
      // [1] = ID, [2] = D/O, [3] = coords
      
      if (bits[2] == 'D') {
        // expeditions[bits[1]]['inside'] = true;
        // updateCoords(bits[1], bits[3]);
        // if (relevant) {
        //     drawDungeon();
        // }
      } else {
        expeditions[bits[1]] = bits[3].split(',');;

        setRegionCursors(Object.values(expeditions));
        // note for later: this would be array.map(o => o[key]) if expeditions was the full object

      }        
    } else if (bits[0] == 'DNGS') {
      let entrances = []
      for (let i = 1; i < bits.length; i++) {
          entrances.push(JSON.parse(bits[i]));  
      }

      // region is null here but if we set with a function we can get the current value handed off
      setRegion(oldRegion => ({
        ...oldRegion, 
        dungeons: entrances
      }));
    } else if (bits[0] == 'EXP-NEW') {
        // don't need to do anything since we don't fetch exp objects yet
    } else if (bits[0] == 'EXP-DEL') {
        delete expeditions[bits[1]];
    }


  }

  // cheating the effect system to aprroximate an onMount event, but this will need proper handling
  useEffect(() => {
    console.log('INITIAL', region, setRegion);
    var socket = new WebSocket('ws://' + rootUrl + '/feed/dungeon');
    socket.onmessage = receiveMessage;

    // this isn't the best way to do this but auntil I get a moment to decide on a state/query manager it'll do
    fetchExisting().then((r) => { 
      setRegion(r);
    });
    

    // return () => { socket.close(); };
  }, []);

  

  return (
    <>
      <h1>Yon Dungeon Tymes</h1>
      Regions
      <ul id="region-buttons"></ul>
      Dungeons
      <ul id="dungeon-buttons"></ul>

      <RegionMap region={region} cursors={regionCursors} />

      <div id="theparty"><b>Our Party</b><ul></ul></div>

      { inBattle && <div id="thefoes"><b>Lurking Foes!</b><ul></ul></div> }
      

      <p><b>Event Log</b></p>
      <div id="event-log">
          <p>The past is a mystery.</p>
      </div>
    </>
  )
}

export default App
