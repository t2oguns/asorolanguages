'use client'

import React from 'react'
import NavLink from './NavLink'
import Link from 'next/link'
import Profile from "./Profile";
import { usePathname } from "next/navigation";

function Navbar() {

  const navItems = [
    { name: "Learn", path: "/dashboard/learn" },
    { name: "Review", path: "/dashboard/review" },
    { name: "Read", path: "/dashboard/read" },
    { name: "Media", path: "/dashboard/media" },
  ];
  const pathname = usePathname();
  return (
    <>
      <div className="left logo mt-3 mb-5">
        {/*<Image></Image>*/}
        <h2 className="text-5xl font-bold text-black">
          <Link href={"learn/"}>Asoro</Link>
        </h2>
      </div>

      <div className="flex items-center justify-end">
        <ul className="flex space-x-16 text-xl items-center mr-10">
          {navItems.map((item, key) => {
            const isCurrentPath = pathname === item.path;
            return <NavLink key={key} name={item.name} path={item.path} isCurrentPath={isCurrentPath} />;
          })}
        </ul>
        <Profile />
      </div>
    </>
  )
}

export default Navbar