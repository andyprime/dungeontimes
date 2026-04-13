import { useState } from 'react'
import { Link, NavLink } from 'react-router'
import { useQuery } from '@tanstack/react-query'

import RegionMap from './RegionMap.jsx'
import EventLog from './EventLog.jsx'
import { getRegion, getBands, getDungeons, getExpeditions } from './fetching.js'

function City() {
  let regionQuery = useQuery({ queryKey: ['region'], queryFn: getRegion });
  
  if (regionQuery.isPending) {
    return <span>Hang on .... </span>
  }

  if (regionQuery.isSuccess) {
    let city = regionQuery.data['city'];
    
    let shops = city.venues.filter((v) => v.type =='shop');
    let guilds = city.venues.filter((v) => v.type =='guild');

    return (
      <div>
        <h1>The City of {city['name']}</h1>
        
        <h3>Shops</h3>
        { shops.length > 0 && <div>{shops.map((shop) => (<Shop key={shop['id']} shop={shop} />))} </div> }

        
        <h3>Guilds</h3>
        { guilds.length > 0 && <div>{guilds.map((guild) => (<Guild key={guild['id']} guild={guild} />))} </div> }
      </div>
        )
  }
}

function Shop({shop}) {

  return (
    <div>
      <p><b>{shop['name']}</b></p>

      <div>
        Goods:
        { shop['stock'].length > 0 && shop['stock'].map((item) => (<p key={item.id}>{item['name']} ({item['value']})</p>)) }
        { shop['stock'].length == 0 && (<p>Out of stock</p>)}
      </div>

    </div>
    )
}

function Guild({guild}) {

  return (
    <div>
      <p><b>{guild['name']}</b></p>

      <div>
        Available Contractors:
        { guild['stock'].map((hireling) => (<p key={hireling.id}>{hireling['name']}</p>)) }
      </div>

    </div>
  )
}

export { City }