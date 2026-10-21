import React from 'react'
import Link from "next/link";

type Props = { 
  name: string; 
  path: string; 
  isCurrentPath: boolean 
}

const NavLink = ({ name, path, isCurrentPath }: Props) => {
  return (
    <li>
      <Link
        className={`flex space-x-4 w-20 justify-center items-center p-1 text-gray-800 font-medium rounded-lg hover:bg-ewe-50 hover:text-gray-500 transition-colors duration-200 ${
          isCurrentPath ? "font-extrabold bg-ewe-300 text-white hover:text-white hover:bg-ewe-500" : "hover:bg-ewe-50"
        }`}
        href={path}
      >
        <span>{name}</span>
      </Link>
    </li>
  )
}

export default NavLink