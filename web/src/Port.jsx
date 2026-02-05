import { useContext, useState, useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router';
import { useQueryClient } from '@tanstack/react-query'

import App from './App.jsx';
import { Bands, Band } from './Bands.jsx';
import { Dungeon } from './Dungeon.jsx';
import { rootUrl } from './fetching.js';
import { LogContext } from './context.js';

const DUNGEON_EVENTS = ['DUNGEONS', 'DUNGEON-NEW', 'DUNGEON-DEL'];
const EXP_EVENTS = ['EXPEDITION-NEW', 'EXPEDITIOn-DEL'];
const BATTLE_EVENTS = ['BATTLE-START', 'BATTLE-END'];

function Port() {
  const socket = useRef(null);

  const queryClient = useQueryClient();

  const [logs, setLogs] = useState({'region': []});

  var receiveMessage = async function (event) {
    let msg = await event.data.text();
    let doc = JSON.parse(msg);

    // ====================================================
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

    } else if (DUNGEON_EVENTS.includes(doc['type'])) {
      // console.log('Dungeon event: ', doc);
      queryClient.invalidateQueries(['region']);      
    } else if (EXP_EVENTS.includes(doc['type'])) {
      // console.log('Expedition event: ', doc);
      queryClient.invalidateQueries(['expeditions']);
    } else if (doc['type'] == 'NARRATIVE') {
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
    else if (BATTLE_EVENTS.includes(doc['type'])) {
      // this is very heavy for updating a single field but its fine for now
      queryClient.invalidateQueries(['expeditions']);
    } 

    else if (doc['type'] == 'BANDS') {
      queryClient.invalidateQueries(['bands']);
    }

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
    <>
      <LogContext value={logs}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<App />} />
            <Route path="bands" element={<Bands />}>
              <Route path=":bid" element={<Band />} />
            </Route>
            <Route path="dungeons/:did" element={<Dungeon />} />
          </Routes>
        </BrowserRouter>
      </LogContext>
    </>
    )
}

export default Port