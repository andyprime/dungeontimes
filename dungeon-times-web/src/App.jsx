import { useContext, useState, useEffect } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './App.css'
import RegionMap from './RegionMap.jsx'

const rootUrl = window.location.hostname + ':8081';

async function receiveMessage(event) {
  var msg = await event.data.text();
  console.log(msg);
}


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

  const [region, setRegion] = useState(null);
  const [inBattle, setInBattle] = useState(false);

  // cheating the effect system to aprroximate an onMount event, but this will need proper handling
  useEffect(() => {
    // var socket = new WebSocket('ws://' + rootUrl + '/feed/dungeon');
    // socket.onmessage = receiveMessage;

    // this isn't the best way to do this but auntil I get a moment to decide on a state/query manager it'll do
    fetchExisting().then((r) => { 
      console.log('Inside effect: ', r);
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

      <RegionMap region={region} />

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
