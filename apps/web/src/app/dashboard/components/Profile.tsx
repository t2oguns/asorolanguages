import { getUser } from '@/lib/session'
import React from 'react'
const Profile = async () => {
    const profile = await getUser()
    return (
        <div><p>{profile.display_name}</p></div>
    )
}

export default Profile