import { useQuery } from '@tanstack/react-query'
import { Link, Outlet, useParams } from 'react-router';

import { getBands, getBand, getDelvers, getDelver } from './fetching.js'

const rootUrl = window.location.hostname + ':8081';

const Bands = function() {
  
  let query = useQuery({ queryKey: ['bands'], queryFn: getBands });

  return (
    <>
      <Link to="/">Back</Link>

      <h1>Band List</h1>

      <ul>
      { query.data?.map((band) => (
        <li key={band.id}><Link to={"/bands/" + band.id}>{band.name}</Link> <p>{band.riches}</p></li>
        )) }
      </ul>

      <Outlet />
    </>
    );
}

const Band = function() {
  
  let params = useParams();
  
  let bandQuery = useQuery({ queryKey: ['bands', params.bid], queryFn: getBands });
  let delverQuery = useQuery({ queryKey: ['delvers', params.bid], queryFn: getDelvers})


  if (bandQuery.isPending) {
    return <span>Hang on .... </span>
  }

  if (bandQuery.isSuccess) {

    let band = bandQuery.data.find((b) => b.id ==params.bid);
    
    if (!!band) {
      
      return (
        <>
          <h1>{ band.name }</h1>

          { delverQuery.data?.map((delver) => (
            <Link key={delver.id} to={"/delvers/" + delver.id}><DelverCard id={delver.id} d={delver} /></Link>
            )) }

        </>
        )
    } else {
      return <span>That ain't no Band</span>
    }
  }
}

const DelverCard = function({ d }) {
  return (
    <div style={{margin: '5px', border: '1px solid black'}}>
      {d.name}
      <br />

      { d.stock } { d.job}
    </div>
    )
}

const Delver = function({ d }) {
  let params = useParams();
  let delverQuery = useQuery({ queryKey: ['delver', params.did], queryFn: getDelver})

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
          <h3>Inventory</h3>
          { delver.inventory.length > 0 && <ul>{delver.inventory.map((item) => (<li>{item.name}</li>))}</ul> }
        </div>
      </>
      )
  } else {
    return <span>Who are you referring to?</span>
  }
}

export {Bands, Band, Delver}

