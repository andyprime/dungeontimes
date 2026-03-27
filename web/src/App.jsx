import { useState } from 'react'
import { Link, NavLink } from 'react-router'
import { useQuery } from '@tanstack/react-query'

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
    bands = bandsQuery.data;
  }
  if (dungeonsQuery.isSuccess) {
    dungeons = dungeonsQuery.data;
  }

  if (regionQuery.isSuccess) {
    let region = regionQuery.data;
    let regionCursors = [];
    let messageIndex = {};

    if (expeditionsQuery.isSuccess) {
      expeditionsQuery.data.forEach(e => regionCursors.push({band: e['band'], location: e['location']['region']}));
    }
    
    return (
      <div className="flex flex-col content-center">
        <RegionMap region={region} cursors={regionCursors} bands={bands} dungeons={dungeons} />

        <EventLog location='region' />
      </div>
        )
  }
}

export default App