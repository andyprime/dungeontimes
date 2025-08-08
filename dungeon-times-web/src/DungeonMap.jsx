import { useRef, useEffect } from 'react'

const SOLID = 1;
const ROOM = 2;
const PASSAGE = 3;
const DOORWAY = 4;
const ENTRANCE = 5;

const HORIZONTAL_MARGIN = 2;
const VERTICAL_MARGIN = 2;
const GRID_SIZE = 20;

const DUNGEON_CELL_COLORS = {
  1: '#000000',
  2: '#9a9a9a',
  3: '#9a9a9a',
  4: '#915b0f',
  5: '#b8b8b8'
}
const DUNGEON_CURSOR_COLOR = '#18910f';

function DungeonMap({dungeon, cursors}) {

  const canvasRef = useRef(null)

  const draw = (canvas) => {
    // console.log('Dungeon draw: ', dungeon, cursors);

    if (dungeon != null) {

      canvas.setAttribute('width', (dungeon['width'] * GRID_SIZE) + (dungeon['width'] - 1) + (2 * HORIZONTAL_MARGIN) );
      canvas.setAttribute('height', (dungeon['height'] * GRID_SIZE) + (dungeon['height'] - 1) + (2 * VERTICAL_MARGIN) );

      let grid = [...Array(dungeon['width'])];

      for (let i in grid) {
        grid[i] = [...Array(dungeon['height'])];
        grid[i].fill(1);
      }

      for (let code in dungeon['cells']) {
        let type = +code.substring(1);
        for (let coords of dungeon['cells'][code]) {
          grid[coords[1]][coords[0]] = type;
        }
      }

      let ctx = canvas.getContext("2d");

      for (let x = 0; x < grid.length; x++) {
        for (let y = 0; y < grid[x].length; y++) {


          let inCursors = false;
          for (let c in cursors) {
            // console.log('Check: ', [x, y], ' vs ', c);
            if (cursors[c][0] == y && cursors[c][1] == x) {
              inCursors = true;
            }
          }

          if (inCursors) {
            ctx.fillStyle = DUNGEON_CURSOR_COLOR;
          } else {
            ctx.fillStyle = DUNGEON_CELL_COLORS[grid[x][y]];
          }

          let xpos = HORIZONTAL_MARGIN + x + (x * GRID_SIZE);
          let ypos = VERTICAL_MARGIN + y + (y * GRID_SIZE);
          switch (grid[x][y]) {
          case ENTRANCE:
            ctx.fillRect(xpos, ypos, GRID_SIZE, GRID_SIZE);

            let cursorx = xpos
            let cursory = ypos
            ctx.fillStyle = '#000000';
            ctx.beginPath();
            ctx.moveTo(cursorx, cursory);

            for (let i = 0; i < 4; i++) {
              cursorx += 5;
              ctx.lineTo(cursorx, cursory);
              cursory += 5;
              ctx.lineTo(cursorx, cursory);
            }
            ctx.closePath();
            ctx.fill();

            break;
          default:
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

export default DungeonMap