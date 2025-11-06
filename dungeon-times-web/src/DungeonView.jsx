import DungeonMap from './DungeonMap.jsx'
import Portrait from './Portrait.jsx'

function DungeonView({dungeon, band, cursors}) {
  
  // console.log('dv', dungeon);

  let delvers = [];
  if (band) {
    delvers = Object.values(band.members).map( d => {
      return <Portrait key={d.id} type="delver" person={d} />
    });
  }

  
  // let bandName = 'BAND NAME HERE';

  let inBattle = dungeon.battling;
  let monsters = '';
  if (inBattle) {
    let room = dungeon.rooms.find( room => room.n == dungeon.roomFocus );
  
    monsters = room.occ.map( (monster, index) => 
      <Portrait key={index} type="monster" person={monster} />
    );
  }
  
  return (
    <>
      <DungeonMap dungeon={dungeon} cursors={cursors} />
      { band != null && <div id="theparty" className="group" ><b>{band.name}</b><ul>{delvers}</ul></div> }
      { inBattle && <div id="thefoes" className="group" ><b>Lurking Foes!</b><ul>{monsters}</ul></div> }
    </>
    );
}

export default DungeonView