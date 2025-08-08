import { useContext, useState, useEffect, useRef } from 'react'
import './App.css'
import RegionMap from './RegionMap.jsx'
import ExpeditionView from './ExpeditionView.jsx'
import EventLog from './EventLog.jsx'

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
  dungeon['battling'] = false;
  dungeon['roomFocus'] = null;
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
  const socket = useRef(null)

  const [region, setRegion] = useState(null);
  const [expeditions, setExpeditions] = useState([]);
  const [selectedExpedition, setSelectedExpedition] = useState(null);

  const [view, setView] = useState('region');
  // view will get closured in receiveMessage so we gotta set up a ref and an effect to keep it fresh
  const viewRef = useRef(view);

  var region2 = region;

  const [regionCursors, setRegionCursors] = useState([]);
  const [dungeonCursors, setDungeonCursors] = useState([]);
  const [messageIndex, setMessages] = useState({region: ['The past is a mystery']});

  var receiveMessage = async function (event) {
    let msg = await event.data.text();
    let bits = msg.split(';');

    // console.log(msg);

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
      setMessages(oldMessages => {

        let old = oldMessages[bits[1]];
        if (old == undefined) {
          old = [];
        }
        let fresh = old.slice (0, 9);
        fresh.unshift(bits[2]);
        let newMsg = {...oldMessages};
        newMsg[bits[1]] = fresh;
        return newMsg;
      });

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
    } else if (bits[0] == 'BTLS') {

      // the next three sections are kinda gross, need to sort out a better way than updating
      // the entire expeditions set
      setExpeditions(oldExpeditions => {
        if (oldExpeditions[bits[1]] != undefined) {
          let newExpeditions = Object.assign({}, oldExpeditions);
          newExpeditions[bits[1]].dungeon.battling = true;
          newExpeditions[bits[1]].dungeon.roomFocus = bits[2];
          return newExpeditions;
        } else {
          return oldExpeditions;
        }
      });      

    } else if (bits[0] == 'BTLE') {
      setExpeditions(oldExpeditions => {
        if (oldExpeditions[bits[1]] != undefined) {
          let newExpeditions = Object.assign({}, oldExpeditions);
          newExpeditions[bits[1]].dungeon.battling = false;
          return newExpeditions;
        } else {
          return oldExpeditions;
        }
      });     
    } else if (bits[0] == 'BTL-UPD') {
      let update = JSON.parse(bits[2]);
      setExpeditions(oldExpeditions => {
        if (oldExpeditions[bits[1]] != undefined) {
          let newExpeditions = Object.assign({}, oldExpeditions);
          
          let expedition = newExpeditions[bits[1]];
          if (update.target[0] == 'm') {
            // monsters have no id based lookup yet :(
            let room = expedition.dungeon.rooms.find( room => room.n == expedition.dungeon.roomFocus );
            
            if (room) {
              let target = room.occ.find( monster => monster.id == update.target );
              target.chp = update.newhp;

              if (update['status'] !=  undefined) {
                target['status'] = update['status'];
              }
            }

          } else {
            let target = expedition.delvers.find( delver => delver.id == update.target);
            target.currenthp = update.newhp;
            if (update['status'] !=  undefined) {
              target['status'] = update['status'];
            }
          }

          return newExpeditions;
        } else {
          return oldExpeditions;
        }
      });
    }

  }

  const selectExpedition = function(event) {
    let id = event.target.getAttribute('eid');
    setSelectedExpedition(expeditions[id]);
    setDungeonCursors([]);
    setView(id);
  }

  // cheating the effect system to aprroximate an onMount event, but this will need proper handling
  useEffect(() => {
    if (socket.current == null) {
      console.log('!!! Declaring websocket', Date.now());
      socket.current = new WebSocket('ws://' + rootUrl + '/feed/dungeon');
      socket.current.onmessage = receiveMessage;
    }

    // this isn't the best way to do this but auntil I get a moment to decide on a state/query manager it'll do
    fetchRegion().then((r) => { 
      setRegion(r);
    });

    fetchExpeditions().then((exs) => {
      setExpeditions(exs);
    });

    // returning a function is supposed to act as a cleanup when App is destroyed but this seems to be called immediately
    // return () => { socket.current.close(); };
  }, []);

  useEffect(() => {
    viewRef.current = view;
  }, [view]);

  let expButtons = '';
  if (expeditions != {}) {
    expButtons = Object.values(expeditions).map(exp =>
      <li key={exp.id}><button eid={exp.id} onClick={selectExpedition}>{exp.dungeon.name}</button></li>
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

      { view != 'region' && <ExpeditionView expedition={selectedExpedition} cursors={dungeonCursors} /> }

      <EventLog messages={messageIndex} view={view} />
      </>
      )
}

export default App