import { useContext, useState, useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router';

import App from './App.jsx';
import { Bands, Band } from './Bands.jsx';
import { Dungeon } from './Dungeon.jsx';
import { rootUrl } from './fetching.js';

var receiveMessage = async function (event) {
  
}

function Port() {
  const socket = useRef(null);

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