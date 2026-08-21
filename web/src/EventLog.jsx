import { useContext } from 'react'
import { LogContext } from './context.js';
import { Link, Outlet, useParams } from 'react-router';
import reactStringReplace from 'react-string-replace';

const LinkableTypes = ['delver', 'dungeon', 'band'];

function EventLog({location}) {
  let logs = useContext(LogContext);
  let messages = [];

  if (!!logs[location]) {
    return (
      <div id="event-log">
        <h2>Event Log ({location})</h2>
        { logs[location].map( (doc, i) => <Message key={i} doc={doc} /> ) }
      </div>
    )
  }
}

function Message({doc}) {
  
  let replaced = doc['message'];;

  LinkableTypes.forEach((t) => {
    let id = doc['context'][t];
    if (!!id) {
      let name = doc['names'][id];
      // by complete chance the url is just the pluralized type, fine enough for now
      let url = '/' + t + 's/' + id;
      replaced = reactStringReplace(replaced, name, (match, i) => (<Link to={url}>{match}</Link> ));
    }
  });

  return (<p>{replaced}</p>)
}

export default EventLog