import DungeonMap from './DungeonMap.jsx'
import Portrait from './Portrait.jsx'

function ExpeditionView({expedition, cursors}) {
  let delvers = expedition.delvers.map( d => {
      return <Portrait key={d.id} type="delver" person={d} />
    });

  let inBattle = expedition.dungeon.battling;
  let monsters = '';
  if (inBattle) {
    let room = expedition.dungeon.rooms.find( room => room.n == expedition.dungeon.roomFocus );
  
    monsters = room.occ.map( (monster, index) => 
      <Portrait key={index} type="monster" person={monster} />
    );
  }
  
  return (
    <>
      <DungeonMap dungeon={expedition.dungeon} cursors={cursors} />
      <div id="theparty" className="group" ><b>{expedition.band.name}</b><ul>{delvers}</ul></div> 
      { inBattle && <div id="thefoes" className="group" ><b>Lurking Foes!</b><ul>{monsters}</ul></div> }
    </>
    );
}

export default ExpeditionView