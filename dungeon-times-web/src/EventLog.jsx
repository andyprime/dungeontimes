
function EventLog({messages, view}) {
  let relevant = '';
  if (messages[view] != undefined) {
    relevant = messages[view].map( (msg, i) => <p key={i}>{msg}</p> );
  }

  return (
    <div id="event-log">
      <b>Event Log: {view}</b>
      { relevant }
    </div>
  )
}

export default EventLog