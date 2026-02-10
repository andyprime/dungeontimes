import { useQuery } from '@tanstack/react-query'
import { Link, Outlet, useParams } from 'react-router';

import { getBands, getBand, getDelvers } from './fetching.js'

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
            <Delver id={delver.id} key={delver.id} d={delver} />
            )) }

        </>
        )
    } else {
      return <span>That ain't no Band</span>
    }
  }
}

const Delver = function({ d }) {
  return (
    <div>
      {d.name}
      <br />

      { d.inventory.length > 0 && <ul>{d.inventory.map((item) => (<li>{item.name}</li>))}</ul> }
    </div>
    )
}

export {Bands, Band}

