import { useQuery } from '@tanstack/react-query'
import { Link, Outlet, useParams } from 'react-router';

const rootUrl = window.location.hostname + ':8081';

const getBands = async function() {
  let response = await fetch('//' + rootUrl + '/bands');
  if (!response.ok) {
    throw new Error('Bands fetch failed.');
  }
  return response.json();
}

const getBand = async function({ queryKey }) {
  let [_key, bId] = queryKey;
  let response = await fetch('//' + rootUrl + '/band/' + bId);
  if (!response.ok) {
    throw new Error('Band fetch failed.');
  }
  return response.json();
}

const getDelvers = async function({ queryKey }) {
  let [_key, bId] = queryKey;
  let response = await fetch('//' + rootUrl + '/band/' + bId + '/delvers');
  if (!response.ok) {
    throw new Error('Delver fetch failed.');
  }
  return response.json();
}


const Bands = function() {
  
  let query = useQuery({ queryKey: ['bands'], queryFn: getBands });

  return (
    <>
      <h1>Band List</h1>

      <ul>
      { query.data?.map((band) => (
        <li key={band.id}><Link to={"/bands/" + band.id}>{band.name}</Link></li>
        )) }
      </ul>

      <Outlet />
    </>
    );
}

const Band = function() {
  
  let params = useParams();
  // let bb = params.bid;

  console.log('bb', params.bid);
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
          <h1>Band Detail</h1>

          {
            band.name
          }

          { delverQuery.data?.map((delver) => (
            <Delver id={delver.id} d={delver} />
            )) }

        </>
        )
    } else {
      return <span>That ain't no Band</span>
    }
  }
}

const Delver = function({ d }) {
  console.log(d)
  return (
    <>
      {d.name}
    </>
    )
}

export {Bands, Band}

