import { useRef, useEffect } from 'react'

const HORIZONTAL_MARGIN = 2;
const VERTICAL_MARGIN = 2;
const GRID_SIZE = 20;

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

function RegionMap({region, cursors}) {
  cursors = Object.values(cursors);
  const canvasRef = useRef(null)

  const draw = (canvas) => {
    // console.log('Canvas draw: ', cursors);

    if (region != null && region.grid != null) {
      canvas.setAttribute('width', (region['width'] * GRID_SIZE) + (region['width'] - 1) + (2 * HORIZONTAL_MARGIN) );
      canvas.setAttribute('height', (region['height'] * GRID_SIZE) + (region['height'] - 1) + (2 * VERTICAL_MARGIN) );
      let ctx = canvas.getContext("2d");

      for (let x = 0; x < region.grid.length; x++) {
        for (let y = 0; y < region.grid[x].length; y++) {

          let inCursors = false;
          let inDungeons = false;
          for (let c in cursors) {
            if (cursors[c][0] == y && cursors[c][1] == x) {
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

  // using an effect here because you need this code to run after the canvas element has been rendered
  useEffect(() => {
    const canvas = canvasRef.current;
    draw(canvas);
  }, [draw])

  return (
    <canvas ref={canvasRef} />
    )

}

export default RegionMap