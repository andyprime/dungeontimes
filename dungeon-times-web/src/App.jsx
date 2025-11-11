import { useContext, useState, useEffect, useRef } from 'react'
import './App.css'
import RegionMap from './RegionMap.jsx'
import DungeonView from './DungeonView.jsx'
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

async function fetchBands() {
  let url = '//' + rootUrl + "/bands/";
  let resp = await fetch(url);
  let list = await resp.json();

  let bands = {};
  for (let i in list) {
    let band = list[i];

    url = url = '//' + rootUrl + '/band/' + band['id'] + '/delvers/';
    resp = await fetch(url);

    let members = await resp.json();
    band['members'] = {};
    for (let j in members) {
      let m = members[j];
      band['members'][m['id']] = m;
    }

    bands[band['id']] = band;
  }

  return bands;
}

async function fetchDungeons() {
  let url = '//' + rootUrl + "/dungeon/";
  let resp = await fetch(url);
  let list = await resp.json();

  let dungeons = {};
  for (let i in list) {
    let dungeon = list[i];
    dungeon['cells'] = JSON.parse(dungeon['cells']);
    dungeon['battling'] = false;
    dungeon['roomFocus'] = null;
    dungeons[dungeon['id']] = dungeon;
  }

  return dungeons;
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
  // console.log('Fetch expedition', eid);

  let resp = await fetch('//' + rootUrl + "/expedition/" + eid);
  let expedition = await resp.json();
  expedition['type'] = 'dungeon';
  // this is a convenience flag to avoid having to emit exp. state specifically yet
  expedition['inside'] = false;
  // console.log('Expedition', expedition);

  return expedition;
}


function App() {
  const socket = useRef(null)

  const [region, setRegion] = useState(null);
  const [bands, setBands] = useState({});

  const [dungeons, setDungeons] = useState({});
  const [selectedDungeon, setSelectedDungeon] = useState(null);

  const [expeditions, setExpeditions] = useState({abc: 'test'});

  const [view, setView] = useState('region');

  const viewRef = useRef(view);
  const expRef = useRef(expeditions);
  const bandRef = useRef(bands);
  const dungeonRef = useRef(dungeons);

  const [regionCursors, setRegionCursors] = useState({});
  const [dungeonCursors, setDungeonCursors] = useState([]);
  const [messageIndex, setMessages] = useState({region: ['The past is a mystery']});

  // ================================

  var receiveMessage = async function (event) {
    let msg = await event.data.text();
    let bits = msg.split(';');

    // console.log(msg);

    if (bits[0] == 'CURSOR') {
      // we wanna track all coordinates but only draw if its the current one
      // [1] = ID, [2] = D/O, [3] = coords

      // console.log('Cursor update', bits, viewRef.current);

      if (bits[2] == 'D') {
        if (bits[1] == viewRef.current) {
          setDungeonCursors([bits[3].split(',')]);
        }
      } else {

        setRegionCursors(oldCursors => {
            let newCursors = {...oldCursors};
            newCursors[bits[1]] = bits[3].split(',');
            console.log('Region cursors: ', newCursors);
            return newCursors;
          });
      }        
    } else if (bits[0] == 'NARR') {
      // console.log(bits);
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
      // Dungeon entrances update message
      let entrances = []
      for (let i = 1; i < bits.length; i++) {
        if (bits[i]) {
          entrances.push(JSON.parse(bits[i]));  
        }
      }

      setRegion(oldRegion => ({
        ...oldRegion, 
        dungeons: entrances
      }));
    } else if (bits[0] == 'DNG-NEW') {
      fetchDungeons().then((d) => {
        setDungeons(d);
      });
    }  else if (bits[0] == 'DNG-DEL') {
      fetchDungeons().then((d) => {
        setDungeons(d);
      });
    } else if (bits[0] == 'EXP-NEW') {
      console.log('EXP-NEW ', bits[1]);
      fetchExpeditions().then((exs) => {
        setExpeditions(exs);
      });
    } else if (bits[0] == 'EXP-DEL') {
      console.log('EXP-DEL ', bits[1]);      
      setExpeditions(oldExpeditions => {
        let newExpeditions = {...oldExpeditions};
        delete newExpeditions[bits[1]];
        return newExpeditions;
      });

      setRegionCursors(oldCursors => {
        let newCursors = {...oldCursors};
        delete newCursors[bits[1]];
        return newCursors;
      });

    } else if (bits[0] == 'BTLS') {

      let exp = expRef.current[bits[1]];
      let dungeonId = exp.dungeon;

      if (exp != undefined) {
        setDungeons(oldDungeons => {
          let newDungeons = {...oldDungeons};
          newDungeons[dungeonId].battling = true;
          newDungeons[dungeonId].roomFocus = bits[2];

          return newDungeons;
        });

      } else {
        console.log('Did not find exp', bits[1]);
      }

    } else if (bits[0] == 'BTLE') {

      let exp = expRef.current[bits[1]];
      let dungeonId = exp.dungeon;

      if (exp != undefined) {
        setDungeons(oldDungeons => {
          let newDungeons = {...oldDungeons};

          newDungeons[dungeonId].battling = false;
          return newDungeons;
        });

      } else {
        console.log('Did not find exp', bits[1]);
      }      

    } else if (bits[0] == 'BTL-UPD') {
      // this is going to be exceptionally janky for the moment since monsters are not top level objects

      let exp = expRef.current[bits[1]];
      let update = JSON.parse(bits[2]);
      // console.log('BTL-UPD ', update);

      if (exp != undefined) {
        
        if (update.target[0] == 'm') {
          // monsters live inside the dungeon, so we update that state
          setDungeons(oldDungeons => {
            let newDungeons = {...oldDungeons};
            let dungeon = newDungeons[exp['dungeon']];
            
            let room = dungeon.rooms.find( room => room.n == dungeon.roomFocus );
            if (room) {
              let target = room.occ.find( monster => monster.id == update.target );
              target.chp = update.newhp;

              if (update['status'] !=  undefined) {
                target['status'] = update['status'];
              }
            }

            return newDungeons;
          });
        } else {
          setBands(oldBands => {
            let newBands = {...oldBands};

            let band = newBands[exp['band']];
            let target = Object.values(band.members).find(delver => delver.id == update.target)

            target.currenthp = update.newhp;
            if (update['status'] !=  undefined) {
              target['status'] = update['status'];
            }

            return newBands;
          });
        }

      } else {
        console.log('Did not find exp', bits[1]);
      }   

    }

  }

  const bandForDungeon = function(dungeon) {
    let ex = Object.values(expeditions).find((x) => x.dungeon == dungeon.id)
    if (ex) {
      return bands[ex.band];
    }
    return null;
  }

  const selectDungeon = function(event) {
    let id = event.target.getAttribute('eid');

    setDungeonCursors([]);
    setSelectedDungeon(dungeons[id]);
    setView(id);
  }

  // ================================

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

    fetchBands().then((bands) => {
      setBands(bands);
    });

    fetchExpeditions().then((exp) => {
      setExpeditions(exp);
    });

    fetchDungeons().then((d) => {
      setDungeons(d);
    });

    // returning a function is supposed to act as a cleanup when App is destroyed but this seems to be called immediately
    // return () => { socket.current.close(); };
  }, []);

  // since the handle message function is local we gotta maintain refs to avoid the stale closure problem
  useEffect(() => {
    expRef.current = expeditions;
  }, [expeditions]);

  useEffect(() => {
    bandRef.current = bands;
  }, [bands]);

  useEffect(() => {
    dungeonRef.current = dungeons;
  }, [dungeons]);

  useEffect(() => {
    viewRef.current = view;
  }, [view]);

  // ================================

  let bandButtons = '';
  let dungeonButtons = '';
  if (bands != {}) {
    bandButtons = Object.values(bands).map(band =>
      <li key={band.id}><button>{band.name}</button></li>
      );
  }
  if (dungeons != {}) {
    dungeonButtons = Object.values(dungeons).map(dungeon =>
      <li key={dungeon.id}><button eid={dungeon.id} onClick={selectDungeon}>{dungeon.name}</button></li>
      );
  } 


  return (
    <>
    <h1>Yon Dungeon Tymes</h1>
    <ul id="region-buttons">
      Regions
      { region != null && <li><button onClick={() => setView('region')} >{region['name']}</button></li> }
      </ul>
      <ul id="bands-buttons">Bands {bandButtons}</ul>
      <ul id="dungeon-buttons">Dungeons {dungeonButtons}</ul>

      { view == 'region' && <RegionMap region={region} cursors={regionCursors} /> }

      { view != 'region' && <DungeonView dungeon={selectedDungeon} band={bandForDungeon(selectedDungeon)} cursors={dungeonCursors} /> }

      <EventLog messages={messageIndex} view={view} />
      </>
      )
}

export default App