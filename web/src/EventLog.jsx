import { useContext } from 'react'
import { LogContext } from './context.js';

function EventLog({location}) {
  let logs = useContext(LogContext);
  let messages = [];

  // console.log(location, logs);
  
  if (!!logs[location]) {
    messages = logs[location].map( (msg, i) => <p key={i}>{msg}</p> );
  }

  return (
    <div id="event-log">
      <h2>Event Log ({location})</h2>
      { messages }
    </div>
  )
}

export default EventLog