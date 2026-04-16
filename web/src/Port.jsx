import { useContext, useState, useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router';
import { useQueryClient } from '@tanstack/react-query'

import App from './App.jsx';
import { About } from './About.jsx';
import { Bands, Band, Delver } from './Bands.jsx';
import { City } from './City.jsx';
import { Dungeon, Dungeons } from './Dungeon.jsx';
import { rootUrl } from './fetching.js';
import { LogContext } from './context.js';

const REGION_EVENTS = ['REGION', 'DUNGEONS', 'DUNGEON-NEW', 'DUNGEON-DEL'];
const EXP_EVENTS = ['EXPEDITION-NEW', 'EXPEDITIOn-DEL'];
const BATTLE_EVENTS = ['BATTLE-START', 'BATTLE-END'];

function Port() {
  const socket = useRef(null);

  const queryClient = useQueryClient();

  const [logs, setLogs] = useState({'region': []});

  var receiveMessage = async function (event) {
    let msg = await event.data.text();
    let doc = JSON.parse(msg);

    // =====================================================================================
    if (doc['type'] == 'CURSOR') {
      let expId = doc['context']['expedition'];
      let loc = doc['coords'];

      queryClient.setQueryData(['expeditions'], (old) => {
        let update = (e) =>
          e.id == expId
            ? {...e, location: loc}
            : e
        return Array.isArray(old)
          ? old.map(update)
          : old
      });

    } 
    // =====================================================================================
    else if (REGION_EVENTS.includes(doc['type'])) {
      // region events are pretty uncommon, so we can probably safely eat the refetch costs
      queryClient.invalidateQueries(['region']);      
    } 
    // =====================================================================================
    else if (EXP_EVENTS.includes(doc['type'])) {
      queryClient.invalidateQueries(['expeditions']);
    } 
    // =====================================================================================
    else if (doc['type'] == 'NARRATIVE') {
      let index = 'region';
      if(!!doc['context']['dungeon']) {
        index = doc['context']['dungeon'];
      }

      setLogs(oldLogs => {
        let newLogs = {...oldLogs};
        if (newLogs[index] == undefined) {
          newLogs[index] = [];
        }

        newLogs[index] = newLogs[index].slice(0, 19);
        newLogs[index].unshift(doc['message']);
        return newLogs;
      });

    } 
    // =====================================================================================
    else if (BATTLE_EVENTS.includes(doc['type'])) {
      // this is very heavy for updating a single field but its fine for now
      queryClient.invalidateQueries(['expeditions']);
    } 
    // =====================================================================================
    else if (doc['type'] == 'BANDS') {
      // BANDS message indicates a change in the global list of bands, i.e. a new band has formed
      queryClient.invalidateQueries(['bands']);
    }
    else if (doc['type'] == 'BAND') {
      // currently the BAND message indicates a change to the band itself or a member
      queryClient.invalidateQueries(['bands', doc['context']['band']]);
      queryClient.invalidateQueries(['delvers', doc['context']['band']]);
    }
    // =====================================================================================
    else if (doc['type'] == 'BATTLE-UPDATE') {
      let body = doc['details'];

      if (body['target'][0] == 'm') {
        queryClient.setQueryData([ 'dungeons', doc['context']['dungeon'] ], (old) => {
          // monsters are currently indexed under their room so we gotta go through some extra hops here
          if (old == undefined || old['rooms'] == undefined) {
            return old;
          }
          let newDungeon = {...old};
          newDungeon['rooms'].forEach((room) => {
            room['occ'] = room['occ'].map( (occ) => {
              if (occ.id == body['target']) {
                return {...occ, chp: body['newhp'], status: body['status']}
              } else {
                return occ;
              }
            });
          });
          return newDungeon;
        });

      } else {
        queryClient.setQueryData([ 'delvers', doc['context']['band'] ], (old) => {
          let update = (d) =>
            d.id == body['target']
              ? {...d, currenthp: body['newhp'], status: body['status']}
              : d
          return Array.isArray(old)
            ? old.map(update)
            : old
        });
      }

    }

  }

  useEffect(() => {
    if (socket.current == null) {
      console.log('!!! Declaring websocket', Date.now());
      socket.current = new WebSocket('ws://' + rootUrl + '/feed/dungeon');
      socket.current.onmessage = receiveMessage;
    }
  }, []);

  return (
    <BrowserRouter>
      <div className="flex flex-col">
        <header className="flex flex-row">
          <Link to="/"><div className="py-2 px-4">Yon Dungeon Tymes</div></Link>
          <Link to="/city/"><button className="py-2 px-4">City</button></Link>
          <Link to="/bands/"><button className="py-2 px-4">Bands</button></Link>
          <Link to="/dungeons/"><button className="py-2 px-4">Dungeons</button></Link>
          <Link to="/about/"><button className="py-2 px-4">About</button></Link>
        </header>
        <main className="flex flex-grow p-4 justify-center">
          <div className="flex flex-col min-w-4xl">
            <LogContext value={logs}>
              
              <Routes>
                <Route path="/" element={<App />} />
                <Route path="bands" element={<Bands />}>
                  <Route path=":bid" element={<Band />} />
                </Route>
                <Route path="delvers/:did" element={<Delver />} />
                <Route path="dungeons" element={<Dungeons />}>
                  <Route path=":did" element={<Dungeon />} />
                </Route>
                <Route path="city" element={<City />} />
                <Route path="about" element={<About />} />
              </Routes>
              
            </LogContext>
          </div>
        </main>
      </div>
    </BrowserRouter>
    )
}

export default Port