import React from 'react'
import Profile from '../components/Profile'
import LogoutButton from '@/app/(auth)/logout/components/LogoutButton'

const Page = () => {
  return (
    <div>Learn Page 
      <Profile/>
      <LogoutButton/>
    </div>
    
  )
}

export default Page