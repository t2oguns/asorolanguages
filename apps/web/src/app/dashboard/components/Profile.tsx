'use client'

import LogoutButton from '@/app/(auth)/logout/components/LogoutButton'
import { api } from '@/lib/api'
import React, { useEffect, useState } from 'react'
const Profile = () => {
    const [user, setUser] = useState({
        name: "John",
        email: "john.doe@example.com",
        avatar: "/api/placeholder/32/32",
    })
    
    useEffect(()=>{
        async function getUser(){
            const data = await api("/api/me/")
            setUser(data)
        }

        getUser()
    }, [])

    return (
        <div>
            <p>{user.display_name}</p>
            <LogoutButton/>    
        </div>
    )
}

export default Profile