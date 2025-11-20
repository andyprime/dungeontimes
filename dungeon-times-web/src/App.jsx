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

// in both of these haystack is a document NOT the context index itself
function hasContext(haystack, needle) {
  return haystack['context'][needle] != undefined;
}
// function getContext(haystack, needle) {
//   return haystack['context'].find(c => {c[needle] != undefined});
// }

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
    let doc = JSON.parse(msg);

    if (doc['context'] == undefined) {
      console.log('!!! Message missing a context field: ', doc);
    }

    if (doc['type'] == 'NARRATIVE') {
      let index = null;
      
      if (hasContext(doc, 'dungeon')) {
        index = doc['context']['dungeon'];
      } else if (hasContext(doc, 'region')) {
        // we technically have the region id here but we'll stick with the legacy constant for now
        index = 'region';
      }

      if (index != null) {
        setMessages(oldMessages => {
          let newMessages = {...oldMessages};
          let old = newMessages[index];
          if (old == undefined) {
            old = [];
          }

          let fresh = old.slice(0, 9);
          fresh.unshift(doc['message']);
          newMessages[index] = fresh;
          return newMessages;
        });
      }
    } else if (doc['type'] == 'CURSOR') {

      if (hasContext(doc, 'dungeon')) {
        if (doc['context']['dungeon'] == viewRef.current) {
          setDungeonCursors([doc['coords']]);
        }
      } else if (hasContext(doc, 'region')) {

        setRegionCursors(oldCursors => {
            let newCursors = {...oldCursors};
            newCursors[doc['context']['expedition']] = doc['coords'];
            return newCursors;
          });
      }    

    } else if (doc['type'] == 'DUNGEONS') {
      setRegion(oldRegion => ({
        ...oldRegion, 
        dungeons: doc['coords']
      }));
    } else if (doc['type'] == 'DUNGEON-NEW') {
      fetchDungeons().then((d) => {
        setDungeons(d);
      });
    } else if (doc['type'] == 'DUNGEON-DEL') {
      fetchDungeons().then((d) => {
        setDungeons(d);
      });
    } else if (doc['type'] == 'EXPEDITION-NEW') {
      fetchExpeditions().then((exs) => {
        setExpeditions(exs);
      });
    } else if (doc['type'] == 'EXPEDITION-DEL') {
      let exp = doc['context']['expedition'];
      setExpeditions(oldExpeditions => {
        let newExpeditions = {...oldExpeditions};
        delete newExpeditions[exp];
        return newExpeditions;
      });

      setRegionCursors(oldCursors => {
        let newCursors = {...oldCursors};
        delete newCursors[exp];
        return newCursors;
      });
    } else if (doc['type'] == 'BATTLE-START') {
      let dungeonId = doc['context']['dungeon'];
      
      setDungeons(oldDungeons => {
        let newDungeons = {...oldDungeons};
        newDungeons[dungeonId].battling = true;
        newDungeons[dungeonId].roomFocus = doc['room'];

        return newDungeons;
      });

    } else if (doc['type'] == 'BATTLE-END') {
      let dungeonId = doc['context']['dungeon'];
      
      setDungeons(oldDungeons => {
        let newDungeons = {...oldDungeons};

        newDungeons[dungeonId].battling = false;
        return newDungeons;
      });
    }

    else if (doc['type'] == 'BATTLE-UPDATE') {
      // this is going to be exceptionally janky for the moment since monsters are not top level objects

      let exp = expRef.current[doc['context']['expedition']];
      let update = doc['details'];
      
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