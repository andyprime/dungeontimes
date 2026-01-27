import { useState } from 'react'
import { Link, NavLink } from 'react-router'
import { useQuery } from '@tanstack/react-query'

import './App.css'
import RegionMap from './RegionMap.jsx'
import EventLog from './EventLog.jsx'
import { getRegion, getBands, getDungeons, getExpeditions } from './fetching.js'

function App() {

  let regionQuery = useQuery({ queryKey: ['region'], queryFn: getRegion });
  let bandsQuery = useQuery({ queryKey: ['bands'], queryFn: getBands });
  let dungeonsQuery = useQuery({ queryKey: ['dungeons'], queryFn: getDungeons });
  let expeditionsQuery = useQuery({ queryKey: ['expeditions'], queryFn: getExpeditions });

  if (regionQuery.isPending) {
    return <span>Hang on .... </span>
  }

  let bandButtons = '';
  let dungeonButtons = '';
  let bands = [];
  let dungeons = [];

  if (bandsQuery.isSuccess) {
    bandButtons = bandsQuery.data.map(band =>
      <li key={band.id}><Link to={"/bands/" + band.id}><button>{band.name}</button></Link></li>
      );
  }
  if (dungeonsQuery.isSuccess) {
    dungeonButtons = dungeonsQuery.data.map(dungeon =>
      <li key={dungeon.id}><Link to={"/dungeons/" + dungeon.id}><button eid={dungeon.id}>{dungeon.name}</button></Link></li>
      );
  } 

  if (regionQuery.isSuccess) {
    let region = regionQuery.data;
    let regionCursors = [];
    let messageIndex = {};

    if (expeditionsQuery.isSuccess) {
      expeditionsQuery.data.forEach(e => regionCursors.push(e['location']['region']));
    }
    
    return (
      <>
      <h1>Yon Dungeon Tymes</h1>
      
      <ul id="region-buttons">
        Regions
        <li><button>{region['name']}</button></li>
      </ul>
      <ul id="bands-buttons"><Link to="/bands">Bands</Link> {bandButtons}</ul>
      <ul id="dungeon-buttons">Dungeons {dungeonButtons}</ul>

      <RegionMap region={region} cursors={regionCursors} />

      <EventLog location='region' />
      </>
        )
  }
}

export default App