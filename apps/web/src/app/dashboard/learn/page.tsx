import React from 'react'
import Profile from '../../../components/features/dashboard/Profile'
import LogoutButton from '@/components/features/logout/LogoutButton'
import Unit from '../../../components/features/learn/Unit'
import { serverFetch } from '@/lib/api/server-api';

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