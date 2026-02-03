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
      <b>Event Log ({location}):</b>
      { messages }
    </div>
  )
}

export default EventLog