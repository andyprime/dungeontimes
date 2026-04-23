import { JOB_NAMES } from './constants.js'

function Portrait({type, person}) {
  

  let statusLine = '';
  if (person.status != undefined) {
    statusLine = person.status.map( status => status['code']).join(', ');
  }


  if(type=='delver') {
    return (
      <div>
        <p>{person.name}</p>
        <p>{person.stock} {JOB_NAMES[person.job]}</p>
        <p>{person.currenthp} / {person.maxhp} {statusLine}</p>
      </div>
      );
  } else {
    // monster field names are super abbreviated from old attempts to minimize transmit size
    return (
      <div>
        <p>{person.n}</p>
        <p>{person.t}</p>
        <p>{person.chp} / {person.mhp} {statusLine}</p>
      </div>
      );
  }
}

export default Portrait