import { useState, useContext } from 'react'
import { LogContext } from './context.js';
import { Link, Outlet, useParams } from 'react-router';
import reactStringReplace from 'react-string-replace';

const LinkableTypes = ['delver', 'dungeon', 'band'];

function cap(val) {
    return String(val).charAt(0).toUpperCase() + String(val).slice(1);
}

function EventLog({location}) {
  let logs = useContext(LogContext);
  const [filter, setFilter] = useState('all');

  let messages = [];
  let count = 0;
  if (!!logs[location]) {
    logs[location].forEach((log) => {
      if (count < 20) {
        if (filter == 'all') {
          messages.push(log);
          count += 1;
        } else if (filter == 'major' && log['level'] == 'major') {
          messages.push(log);
          count += 1;
        } else {
          if (log['type'] == filter) {
            messages.push(log);
            count += 1;
          }
        }
        
      }
    });
  }

  let buttons = location == 'region' ? ['major', 'city'] : ['major', 'combat'];

  let onStyle = 'bg-gray-300 hover:bg-gray-400 mx-1 py-1 px-2 rounded';
  let offStyle = 'bg-gray-400 hover:bg-gray-500 mx-1 py-1 px-2 rounded';
  
  if (!!logs[location]) {
    return (
      <div id="event-log">
        <div className="flex">
          <h2>Event Log ({location})</h2>
          <button key="all" className={filter == 'all' ? onStyle : offStyle} onClick={(x) => setFilter('all')}>All</button>
          { buttons.map( (button, i) => <button key={i} className={filter == button ? onStyle : offStyle} onClick={(x) => setFilter(button)}>{cap(button)}</button>) }
        </div>
        { messages.map( (doc, i) => <Message key={i} doc={doc} /> ) }
      </div>
    )
  }
}

function Message({doc}) {
  
  let replaced = doc['message'].slice(0);
  // React treats the links as children that need unique keys
  // a simple counter is predictable enough
  let j = 1;
  LinkableTypes.forEach((t) => {
    let id = doc['context'][t];
    if (!!id) {
      let name = doc['names'][id];
      // by complete chance the url is just the pluralized type, fine enough for now
      let url = '/' + t + 's/' + id;
      replaced = reactStringReplace(replaced, name, (match, i) => (<Link key={j} to={url} className="bg-gray-400 px-2 rounded-full">{match}</Link> ), 1);
      j += 1;
    }
  });

  return (<p>{replaced}</p>)
}

export default EventLog