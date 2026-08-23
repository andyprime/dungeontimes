import { useState, useContext } from 'react'
import { LogContext } from './context.js';
import { Link, Outlet, useParams } from 'react-router';
import reactStringReplace from 'react-string-replace';

const LinkableTypes = ['delver', 'dungeon', 'band'];

function EventLog({location}) {
  let logs = useContext(LogContext);
  const [filter, setFilter] = useState(true);

  let messages = [];
  let count = 0;
  if (!!logs[location]) {
    logs[location].forEach((log) => {
      if (count < 20) {
        if (filter || log['level'] == 'major') {
          messages.push(log);
        }
        count += 1;
      }
    });
  }

  let style = filter ? 'bg-gray-300 hover:bg-gray-400' : 'bg-gray-400 hover:bg-gray-500';
  style += 'py-2 px-2 rounded-1';

  if (!!logs[location]) {
    return (
      <div id="event-log">
        <div className="online-flex">
          <h2>Event Log ({location})</h2>
          <button className={style} onClick={(x) => setFilter(!filter)}>All</button>
        </div>
        { messages.map( (doc, i) => <Message key={i} doc={doc} /> ) }
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