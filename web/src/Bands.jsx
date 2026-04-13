import { useQuery } from '@tanstack/react-query'
import { Link, Outlet, useParams } from 'react-router';

import { getBands, getBand, getDelvers, getDelver, getDelverEvents, getBandEvents } from './fetching.js'

const rootUrl = window.location.hostname + ':8081';

const Bands = function() {
  
  let query = useQuery({ queryKey: ['bands'], queryFn: getBands });

  return (
    <>
      <div><h1>Registered Bands</h1></div>

      <div className="grid grid-cols-4 gap-4">
        { query.data?.map((band) => (
          <div key={band.id}><Link to={"/bands/" + band.id}>{band.name}</Link> <p>{band.riches}</p></div>
          )) }
      </div>
      
      <Outlet />
    </>
    );
}

const Band = function() {
  
  let params = useParams();
  
  let bandQuery = useQuery({ queryKey: ['bands', params.bid], queryFn: getBands });
  let delverQuery = useQuery({ queryKey: ['delvers', params.bid], queryFn: getDelvers})

  let eventQuery = useQuery({ queryKey: ['bands', params.bid, 'events'], queryFn: getBandEvents });

  if (bandQuery.isPending) {
    return <span>Hang on .... </span>
  }

  if (bandQuery.isSuccess) {

    let band = bandQuery.data.find((b) => b.id ==params.bid);
    
    if (!!band) {
      
      return (
        <>
          <div><h1>{ band.name }</h1></div>

          <div className="grid grid-cols-4 gap-4">
            { delverQuery.data?.map((delver) => (
              <Link key={delver.id} to={"/delvers/" + delver.id}><DelverCard id={delver.id} d={delver} /></Link>
              )) }
          </div>

          <div>
            <h2>History</h2>
            { !!eventQuery.data && <div>{eventQuery.data.map( (event) => (<p key={event.time}>{event.message}</p>)  )}</div> }
          </div>

        </>
        )
    } else {
      return <span>That ain't no Band</span>
    }
  }
}

const DelverCard = function({ d }) {
  return (
    <div className="p-4 bg-gray-200 rounded-lg">
      {d.name}
      <br />

      { d.stock } { d.job}
    </div>
    )
}

const Delver = function({ d }) {
  let params = useParams();
  let delverQuery = useQuery({ queryKey: ['delver', params.did], queryFn: getDelver});

  let eventQuery = useQuery({ queryKey: ['delver', params.did, 'events'], queryFn: getDelverEvents});

  if (delverQuery.isPending) {
    return <span>Hang on .... </span>
  }

  if (delverQuery.isSuccess) {

    let delver = delverQuery.data

    return (
      <>
        <h1>{delver.name}</h1>
        <div>{delver.stock} {delver.job}</div>
        <div>
          <table>
            <tbody>
              <tr><td>Muscularity</td><td>{delver.attributes['muscularity'].current}</td></tr>
              <tr><td>Prowess</td><td>{delver.attributes['prowess'].current}</td></tr>
              <tr><td>Pendantry</td><td>{delver.attributes['pendantry'].current}</td></tr>
              <tr><td>Diligence</td><td>{delver.attributes['diligence'].current}</td></tr>
              <tr><td>Cool</td><td>{delver.attributes['cool'].current}</td></tr>
              <tr><td>Guile</td><td>{delver.attributes['guile'].current}</td></tr>
              <tr><td>Obduracy</td><td>{delver.attributes['obduracy'].current}</td></tr>
              <tr><td>Pizazz</td><td>{delver.attributes['pizazz'].current}</td></tr>
            </tbody>
          </table>
        </div>
        <div>
          <h2>Inventory</h2>
          <ul>
            <li><b>Tools</b>
              { delver.tools.length > 0 && <div>{delver.tools.map((item) => (<p>{item.name}</p>))}</div>}
            </li>
            <li><b>Gear</b>
              { delver.gear.length > 0 && <div>{delver.gear.map((item) => (<p>{item.name}</p>))}</div> }
            </li>
            <li>
              <b>Loot</b>
              { delver.inventory.length > 0 && <div>{delver.inventory.map((item) => (<p>{item.name}</p>))}</div> }
            </li>
          </ul>
        </div>
        <div>
          <h2>History</h2>
          { !!eventQuery.data && <div>{eventQuery.data.map( (event) => (<p key={event.time}>{event.message}</p>)  )}</div> }
        </div>
      </>
      )
  } else {
    return <span>Who are you referring to?</span>
  }
}

export {Bands, Band, Delver}

