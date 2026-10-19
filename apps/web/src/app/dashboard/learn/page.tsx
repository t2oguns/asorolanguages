import React from 'react'
import Profile from '../components/Profile'
import LogoutButton from '@/app/(auth)/logout/components/LogoutButton'
import Unit from './components/Unit'
import { serverFetch } from '@/lib/server-api';

const Page = async () => {
  let units;
  try{
    units = await serverFetch("/api/v1/courses/units/");

    if (!Array.isArray(units)) {
      throw new Error("Invalid units response");
    }
  }catch (error){
    console.error("Failed to fetch units:", error);

    return;
  }

  return (
    <div> 
      {units.map((unit, id)=>{
        return  <Unit key={id} unit={unit}/>
      })}
    </div>
  )
}

export default Page