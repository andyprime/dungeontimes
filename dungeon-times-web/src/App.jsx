import { useContext, useState, useEffect, useRef } from 'react'
import './App.css'
import RegionMap from './RegionMap.jsx'
import DungeonMap from './DungeonMap.jsx'

const rootUrl = window.location.hostname + ':8081';


// this function and several more to follow are a legacy of the pre-React prototype and 
// replacement with a robust Query or data management module should be considered a priority
async function fetchRegion() {
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

  return region;
}

async function fetchExpeditions() {
  let url = '//' + rootUrl + "/expeditions/";
  let resp = await fetch(url);
  let list = await resp.json();

  let expeditions = {};
  for (let i in list) {
    expeditions[list[i]['id']] = await fetchExpedition(list[i]['id']);
  }

  return expeditions;
}

async function fetchExpedition(eid) {
  console.log('Fetch expedition', eid);
   
  let resp = await fetch('//' + rootUrl + "/expedition/" + eid);
  let expedition = await resp.json();
  expedition['type'] = 'dungeon';
  // console.log('Expedition', expedition);

  let url = '//' + rootUrl + "/dungeon/" + expedition['dungeon'];
  resp = await fetch(url);
  let dungeon = await resp.json();
  // var dungeonName = dungeon['name'];
  dungeon['cells'] = JSON.parse(dungeon['cells']);
  dungeon['battling'] = null;
  // console.log('Dungeon', dungeon);

  url = '//' + rootUrl + "/expedition/" + expedition['id'] + "/delvers";
  resp = await fetch(url);
  let json = await resp.json();
  let delvers = [];
  for (let i in json) {
    delvers.push(json[i]);
  }

  // this is a convenience flag to avoid having to emit exp. state specifically yet
  expedition['inside'] = false;
  expedition['dungeon'] = dungeon;
  expedition['delvers'] = delvers;

  return expedition;
}


function App() {

  const [region, setRegion] = useState(null);
  const [expeditions, setExpeditions] = useState([]);
  const [selectedDungeon, setSelectedDungeon] = useState(null);

  const [view, setView] = useState('region');
  // view will get closured in receiveMessage so we gotta set up a ref and an effect to keep it fresh
  const viewRef = useRef(view);

  var region2 = region;

  const [regionCursors, setRegionCursors] = useState([]);
  const [dungeonCursors, setDungeonCursors] = useState([]);
  const [inBattle, setInBattle] = useState(false);

  var receiveMessage = async function (event) {
    let msg = await event.data.text();
    let bits = msg.split(';');

    let relevant = view != null && bits[1] == selectedView['id'];

    if (bits[0] == 'CURSOR') {
      // we wanna track all coordinates but only draw if its the current one
      // [1] = ID, [2] = D/O, [3] = coords
      
      if (bits[2] == 'D') {
        if (bits[1] == viewRef.current) {
          setDungeonCursors([bits[3].split(',')]);
        }
      } else {
        expeditions[bits[1]] = bits[3].split(',');;
        setRegionCursors(Object.values(expeditions));
      }        
    } else if (bits[0] == 'NARR') {
        if (relevant) {
            addEvent(bits[2]);
        }
    } else if (bits[0] == 'DNGS') {
      let entrances = []
      for (let i = 1; i < bits.length; i++) {
          entrances.push(JSON.parse(bits[i]));  
      }

      // we can avoid having to ref/effect region here by using the function param of our state
      setRegion(oldRegion => ({
        ...oldRegion, 
        dungeons: entrances
      }));
    } else if (bits[0] == 'EXP-NEW') {
      fetchExpeditions().then((exs) => {
        setExpeditions(exs);
      });
    } else if (bits[0] == 'EXP-DEL') {
      delete expeditions[bits[1]];
    }

  }

  const selectDungeon = function(event) {
    // console.log('Select', event.target.getAttribute('eid'));
    let id = event.target.getAttribute('eid');
    setSelectedDungeon(expeditions[id].dungeon);
    setDungeonCursors([]);
    setView(id);
  }

  // cheating the effect system to aprroximate an onMount event, but this will need proper handling
  useEffect(() => {
    var socket = new WebSocket('ws://' + rootUrl + '/feed/dungeon');
    socket.onmessage = receiveMessage;

    // this isn't the best way to do this but auntil I get a moment to decide on a state/query manager it'll do
    fetchRegion().then((r) => { 
      setRegion(r);
    });

    fetchExpeditions().then((exs) => {
      setExpeditions(exs);
    });

    // return () => { socket.close(); };
  }, []);

  useEffect(() => {
    viewRef.current = view;
  }, [view]);

  let expButtons = '';
  if (expeditions != {}) {
    expButtons = Object.values(expeditions).map(exp =>
      <li key={exp.id}><button eid={exp.id} onClick={selectDungeon}>{exp.dungeon.name}</button></li>
    );
  } 

  return (
    <>
      <h1>Yon Dungeon Tymes</h1>
      <ul id="region-buttons">
        Regions
        { region != null && <li><button onClick={() => setView('region')} >{region['name']}</button></li> }
      </ul>
      <ul id="dungeon-buttons">Dungeons {expButtons}</ul>

      { view == 'region' && <RegionMap region={region} cursors={regionCursors} /> }

      { view != 'region' && <>
        <DungeonMap dungeon={selectedDungeon} cursors={dungeonCursors} /> }

        <div id="theparty"><b>Our Party</b><ul></ul></div> 

        { inBattle && <div id="thefoes"><b>Lurking Foes!</b><ul></ul></div> } 
        </>
      }
      
      <p><b>Event Log</b></p>
      <div id="event-log">
          <p>The past is a mystery.</p>
      </div>
    </>
  )
}

export default App
