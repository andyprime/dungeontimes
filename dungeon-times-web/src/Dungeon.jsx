import { Link, Outlet, useParams } from 'react-router';
import { useQuery } from '@tanstack/react-query'

import DungeonMap from './DungeonMap.jsx'
import Portrait from './Portrait.jsx'

import { getDungeon, getBand, getExpeditions, getDelvers } from './fetching.js'

function Dungeon() {
  let params = useParams();

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

    let cursor = null;
    if (!!exp) {
      cursor = exp.cursor;
      console.log('c', cursor);
    }

    let delvers = [];
    if (delverQuery.isSuccess) {
      delvers = Object.values(delverQuery.data).map( d => {
        return <Portrait key={d.id} type="delver" person={d} />
      });
    }

    let inBattle = false;
    let monsters = '';
    if (inBattle) {
      let room = dungeon.rooms.find( room => room.n == dungeon.roomFocus );
    
      monsters = room.occ.map( (monster, index) => 
        <Portrait key={index} type="monster" person={monster} />
      );
    }
    
    return (
      <>
        <Link to="/">Back</Link>
        <h1>{dungeon.name}</h1>
        <DungeonMap dungeon={dungeon} cursor={[cursor]} />
        { band != null && <div id="theparty" className="group" ><b>{band.name}</b><ul>{delvers}</ul></div> }
        { inBattle && <div id="thefoes" className="group" ><b>Lurking Foes!</b><ul>{monsters}</ul></div> }
      </>
      );
  } else {
    return <span>That's not a real dungeon</span>
  }
}

export { Dungeon }