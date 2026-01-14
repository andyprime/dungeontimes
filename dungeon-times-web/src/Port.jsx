import { useContext, useState, useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router';
import { useQueryClient } from '@tanstack/react-query'

import App from './App.jsx';
import { Bands, Band } from './Bands.jsx';
import { Dungeon } from './Dungeon.jsx';
import { rootUrl } from './fetching.js';

const DUNGEON_EVENTS = ['DUNGEONS', 'DUNGEON-NEW', 'DUNGEON-DEL'];
const EXP_EVENTS = ['EXPEDITION-NEW', 'EXPEDITIOn-DEL'];

function Port() {
  const socket = useRef(null);

  const queryClient = useQueryClient();

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
      console.log('Dungeon event: ', doc);
      queryClient.invalidateQueries(['region']);      
    } else if (EXP_EVENTS.includes(doc['type'])) {
      console.log('Expedition event: ', doc);
      queryClient.invalidateQueries(['expeditions']);
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
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="bands" element={<Bands />}>
            <Route path=":bid" element={<Band />} />
          </Route>
          <Route path="dungeons/:did" element={<Dungeon />} />
        </Routes>
      </BrowserRouter>
    </>
    )
}

export default Port