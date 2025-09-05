const JOB_NAMES = {
    'MUSCLE': 'Muscle Man',
    'ETHICIST': 'Ethicist',
    'SWORDLORD': 'Swordlord',
    'NEERDOWELL': 'Neerdowell',
    'MAGICIAN': 'Magician'
}

function Portrait({type, person}) {
  

  let statusLine = '';
  if (person.status != undefined) {
    statusLine = person.status.map( status => status['code']).join(', ');
  }


  if(type=='delver') {
    return (
      <li>
        <p>{person.name}</p>
        <p>{person.stock} {JOB_NAMES[person.job]}</p>
        <p>{person.currenthp} / {person.maxhp} {statusLine}</p>
      </li>
      );
  } else {
    // monster field names are super abbreviated from old attempts to minimize transmit size
    return (
      <li>
        <p>{person.n}</p>
        <p>{person.t}</p>
        <p>{person.chp} / {person.mhp} {statusLine}</p>
      </li>
      );
  }
}

export default Portrait