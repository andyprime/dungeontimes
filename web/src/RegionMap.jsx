import { useRef, useState, useEffect } from 'react'
import { useNavigate } from "react-router";

const HORIZONTAL_MARGIN = 2;
const VERTICAL_MARGIN = 2;
const GRID_SIZE = 20;
const GRID_GAP = 1;

const CITY = 1;
const FARMLAND = 2;
const ROAD = 3;
const FOREST = 4;
const RIVER = 5;
const WATER = 6;
const HILLS = 7;
const MOUNTAIN = 8;
const DESERT = 9;
const PLAIN = 10;
const TOWN = 11;

const TERRAIN = {
  1: 'City',
  2: 'Farmland',
  3: 'Road',
  4: 'Forest',
  5: 'River',
  6: 'Sea',
  7: 'Hills',
  8: 'Mountain',
  9: 'Desert',
  10: 'Plain',
  11: 'Town'
}

const REGION_CURSOR_COLOR = '#ff79cb';
const REGION_DUNGEON_COLOR = '#000000';

const REGION_CELL_COLORS = {
  1: '#3855f4',
  2: '#b6ee3b',
  3: '#c8c8c8',
  4: '#236405',
  5: '#000000',
  6: '#000000',
  7: '#cbd02c',
  8: '#6a6a6a',
  9: '#ffa14f',
  10: '#20a61c',
  11: '#3855f4'
}

const match = function(coord, dungeons) {
  for (const id in dungeons) {
    if (dungeons[id][0] == coord[0] && dungeons[id][1] == coord[1]) {
      return id;
    }
  }
  return null;
}

function RegionMap({region, cursors, bands, dungeons}) {
  let rawCursors = cursors.map((c) => c['location'])
  const canvasRef = useRef(null)

  const [info, setInfo] = useState('|');

  let navigate = useNavigate();

  let width = (region['width'] * GRID_SIZE) + (region['width'] - 1) * GRID_GAP + (2 * HORIZONTAL_MARGIN)
  let height = (region['height'] * GRID_SIZE) + (region['height'] - 1) * GRID_GAP + (2 * VERTICAL_MARGIN)

  const draw = (canvas) => {
    if (region != null && region.grid != null) {
      canvas.setAttribute('width', width);
      canvas.setAttribute('height', height);
      let ctx = canvas.getContext("2d");

      for (let x = 0; x < region.grid.length; x++) {
        for (let y = 0; y < region.grid[x].length; y++) {

          let inCursors = false;
          let inDungeons = false;
          for (let c in rawCursors) {
            if (rawCursors[c][0] == y && rawCursors[c][1] == x) {
              inCursors = true;
            }
          }
          for (let d in region.dungeons) {
            if (region.dungeons[d][0] == y && region.dungeons[d][1] == x) {
              inDungeons = true;
            }
          }

          if (inCursors) {
            ctx.fillStyle = REGION_CURSOR_COLOR;
          } else if(inDungeons) {
            ctx.fillStyle = REGION_DUNGEON_COLOR;
          } else {
            ctx.fillStyle = REGION_CELL_COLORS[region.grid[x][y]];
          }

          switch (region.grid[x][y]) {
          default:
            let xpos = HORIZONTAL_MARGIN + x + (x * GRID_SIZE);
            let ypos = VERTICAL_MARGIN + y + (y * GRID_SIZE);

            ctx.fillRect(xpos, ypos, GRID_SIZE, GRID_SIZE);
          }
        }
      }
    }
  }

  let withinMargins = function(x, y) {
    return x > HORIZONTAL_MARGIN && x <= width - HORIZONTAL_MARGIN && y > VERTICAL_MARGIN && y <= height - VERTICAL_MARGIN;
  }

  let getGrids = function(x, y) {
    return [Math.floor( (x - HORIZONTAL_MARGIN) / (GRID_SIZE + GRID_GAP) ), Math.floor( (y - VERTICAL_MARGIN) / (GRID_SIZE + GRID_GAP) )]
  }

  let handleMouse = function(ev) {
    // offsets aren't in the React event wrapper because they used to be not universally supported but they should be fine now
    let x = ev.nativeEvent.offsetX;
    let y = ev.nativeEvent.offsetY;

    if (withinMargins(x, y)) {
      let [gridX, gridY] = getGrids(x, y);
      
      let terrainType = region.grid[gridX][gridY];
      let terrainName = TERRAIN[terrainType];
      
      let dMatch = match([gridY, gridX], region['dungeons']);
      
      let info = '| ';
      if (gridX == region.homebase[1] && gridY == region.homebase[0]) {
        info += 'The city of ' + region['city']['name'];
      } else if(!!dMatch) {
        let d = dungeons.find((d) => d['id'] == dMatch);
        if (!!d) {
          info += 'The terrible dungeon known as ' + d['name'];
        } else {
          // This should only happen if the dungeon query hasn't loaded yet
          info += 'A dungeon!';
        }
      } else {
        info += terrainName;
      }

      let c = cursors.find((c) => gridX == c['location'][1] && gridY == c['location'][0]);
      if (!!c) {
        let b = bands.find((b) => b['id'] == c['band']);
        if (!!b) {
          info += ', ' + b['name'] + ' are here';
        }
      }
      
      setInfo(info)
    }
  }

  let clearMsg = function(ev) {
    setInfo('|');
  }

  let handleClick = function(ev) {
    let x = ev.nativeEvent.offsetX;
    let y = ev.nativeEvent.offsetY;

    if (withinMargins(x, y)) {
      let [gridX, gridY] = getGrids(x, y);
      let dMatch = match([gridY, gridX], region['dungeons']);

      if (gridX == region.homebase[1] && gridY == region.homebase[0]) {
        navigate('/city')
      } else if(!!dMatch) {
        navigate('dungeons/'+dMatch)
      }
    }
  }

  // using an effect here because you need this code to run after the canvas element has been rendered
  useEffect(() => {
    const canvas = canvasRef.current;
    draw(canvas);
  }, [draw])

  return (
    <div>
      <h2>{region['name']}</h2>
      <div>{info}</div>
      <canvas onMouseMove={handleMouse} onMouseOut={clearMsg} onClick={handleClick} ref={canvasRef} />
    </div>
    )

}

export default RegionMap