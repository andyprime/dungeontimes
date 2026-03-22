import { Link, Outlet, useParams } from 'react-router';
import { useQuery, useQueryClient } from '@tanstack/react-query'

import DungeonMap from './DungeonMap.jsx'
import Portrait from './Portrait.jsx'
import EventLog from './EventLog.jsx'

import { getDungeon, getDungeons, getBand, getExpeditions, getDelvers } from './fetching.js'

function Dungeons() {
  let dungeonQuery = useQuery({ queryKey: ['dungeons'], queryFn: getDungeons });

  return (
    <>
      <div><h1>Dungeons</h1></div>
      <div className="grid grid-cols-4 gap-4">
        { dungeonQuery.data?.map((dungeon) => (
          <div key={dungeon.id}><Link to={"/dungeons/" + dungeon.id}>{dungeon.name}</Link></div>
          )) }
      </div>
      <Outlet />
    </>
    );
}

function Dungeon() {
  let params = useParams();
  const queryClient = useQueryClient()

  // this is gross but it'll work for now
  let dungeonQuery = useQuery({ queryKey: ['dungeons', params.did], queryFn: getDungeon });
  let expeditionQuery = useQuery({ queryKey: ['expeditions'], queryFn: getExpeditions });
  
  let bandId = null;
  let exp = null;
  if (dungeonQuery.isSuccess && expeditionQuery.isSuccess) {
    exp = expeditionQuery.data.find( (ex) => ex.dungeon == dungeonQuery.data.id );
    if (!!exp) {
      bandId = exp.band;
    }
  }

  let bandQuery = useQuery({ queryKey: ['bands', bandId], queryFn: getBand, enabled: !!bandId });
  let delverQuery = useQuery({ queryKey: ['delvers', bandId], queryFn: getDelvers, enabled: !!bandId });

  if (dungeonQuery.isPending) {
    return <span>Hang on .... </span>
  }

  if (dungeonQuery.isSuccess) {

    let dungeon = dungeonQuery.data;
    
    let band = null;
    if (bandQuery.isSuccess) {
      band = bandQuery.data;
    }

    let cursors = [];
    let inBattle = false;
    if (!!exp) {
      if (!!exp.location.dungeon) {
        cursors = [exp.location.dungeon];
      }
      inBattle = exp['state'] == 'bat'; // this should be a constant but its the only state check we doing atm
    }

    let delvers = [];
    if (delverQuery.isSuccess) {
      delvers = Object.values(delverQuery.data).map( d => {
        return <Portrait key={d.id} type="delver" person={d} />
      });
    }

    
    let monsters = '';
    if (inBattle) {
      // just use the cursor to figure out which room they're in
      let cursor = cursors[0];      
      let room = dungeon.rooms.find( room => (cursor[0] >= room['c'][0] && cursor[0] < room['c'][0] + room['d'][0]) && (cursor[1] >= room['c'][1] && cursor[1] < room['c'][1] + room['d'][1]) );
      
      monsters = room.occ.map( (monster, index) => 
        <Portrait key={index} type="monster" person={monster} />
      );
    }
    
    return (
      <>
        <h1>{dungeon.name}</h1>
        <DungeonMap dungeon={dungeon} cursors={cursors} />

        { band != null && <div id="theparty"><div><h2>{band.name}</h2></div> <div className="grid grid-cols-4 gap-4"> {delvers} </div></div> }

        { inBattle && <div id="thefoes" className="group" ><h2>Lurking Foes!</h2><div className="grid grid-cols-4 gap-4">{monsters}</div></div> }

        <EventLog location={dungeon.id} />
      </>
      );
  } else {
    return <span>That's not a real dungeon</span>
  }
}

export { Dungeon, Dungeons }