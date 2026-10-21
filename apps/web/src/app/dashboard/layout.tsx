import React from 'react'
import Sidebar from "../../components/features/dashboard/Sidebar";
import Navbar from '../../components/features/dashboard/Navbar';


const Layout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => {

  return (
    <div className="min-h-screen bg-linear-to-br from-[#f5f0e8] to-[#f0a07a]">
      
      <div className="fixed inset-0 z-0 pointer-events-none">{/* characters, animations live here, can go anywhere */}</div>

      <nav className="flex justify-between sticky bg-linear-to-br from-[#f5f0e8] to-[#f3c1aa] top-0 z-30 px-6 pt-1 shadow-sm">
          <Navbar/>
      </nav>

      <aside className="fixed top-36 right-8 bottom-0 z-10 max-w-80 w-80 lg:w-1/4">
        <Sidebar/>
      </aside>

      <main className="px-6 py-6 overflow-y-auto snap-y snap-mandatory gap-28">
        {children}
      </main>

    </div>
  )
}

export default Layout