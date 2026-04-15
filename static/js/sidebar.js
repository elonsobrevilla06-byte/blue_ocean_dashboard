const sidebarHTML = `
    <div id="mobile-sidebar-overlay" class="fixed inset-0 bg-gray-900 bg-opacity-50 z-40 hidden lg:hidden transition-opacity"></div>

    <aside id="main-sidebar" class="fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 flex flex-col transform -translate-x-full lg:translate-x-0 transition-transform duration-300 ease-in-out lg:static lg:inset-auto lg:h-screen">
        <div class="h-16 flex items-center justify-between px-6 border-b border-gray-100 shrink-0">
            <span class="font-bold text-lg text-blue-600">Blue Ocean Bar</span>
            <button id="close-sidebar" class="lg:hidden text-gray-500 hover:text-gray-700 focus:outline-none">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        </div>
        <div class="p-4 flex-1 overflow-y-auto">
            <p class="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wider">Dashboard</p>
            <a href="/" class="sidebar-link flex items-center px-4 py-2 rounded-lg mb-6 transition-colors">
                <svg class="sidebar-icon w-5 h-5 mr-3 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
                Dashboard
            </a>

            <p class="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wider">Performance</p>
            <nav class="space-y-1 mb-6">
                <a href="/sales-overview" class="sidebar-link flex items-center px-4 py-2 rounded-lg transition-colors">
                    <svg class="sidebar-icon w-5 h-5 mr-3 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
                    Sales Overview
                </a>
                <a href="/revenue-streams" class="sidebar-link flex items-center px-4 py-2 rounded-lg transition-colors">
                    <svg class="sidebar-icon w-5 h-5 mr-3 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    Revenue Streams
                </a>
                <a href="/food-beverage" class="sidebar-link flex items-center px-4 py-2 rounded-lg transition-colors">
                    <svg class="sidebar-icon w-5 h-5 mr-3 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>
                    Food & Beverage
                </a>
            </nav>

            <p class="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wider">Management</p>
            <nav class="space-y-1">
                <a href="/cash-operations" class="sidebar-link flex items-center px-4 py-2 rounded-lg transition-colors">
                    <svg class="sidebar-icon w-5 h-5 mr-3 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
                    Cash Operations
                </a>
                <a href="/drawer-assignment" class="sidebar-link flex items-center px-4 py-2 rounded-lg transition-colors">
                    <svg class="sidebar-icon w-5 h-5 mr-3 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"></path></svg>
                    Drawer Assignment
                </a>
                <a href="/shift-logs" class="sidebar-link flex items-center px-4 py-2 rounded-lg transition-colors">
                    <svg class="sidebar-icon w-5 h-5 mr-3 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    Shift Logs
                </a>
                <a href="/user-management" class="sidebar-link flex items-center px-4 py-2 rounded-lg transition-colors">
                    <svg class="sidebar-icon w-5 h-5 mr-3 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
                    User Management
                </a>
            </nav>
        </div>
    </aside>
`;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('sidebar-container').innerHTML = sidebarHTML;

    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    const activeClasses = ['bg-blue-600', 'text-white', 'shadow-sm'];
    const inactiveClasses = ['text-gray-600', 'hover:bg-gray-100', 'hover:text-blue-600'];

    sidebarLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        const icon = link.querySelector('.sidebar-icon');

        if (linkPath === currentPath) {
            link.classList.remove(...inactiveClasses);
            link.classList.add(...activeClasses);
            if (icon) {
                icon.classList.remove('text-gray-400');
                icon.classList.add('text-white');
            }
        } else {
            link.classList.remove(...activeClasses);
            link.classList.add(...inactiveClasses);
            if (icon) {
                icon.classList.remove('text-white');
                icon.classList.add('text-gray-400');
            }
        }
    });

    const sidebar = document.getElementById('main-sidebar');
    const overlay = document.getElementById('mobile-sidebar-overlay');
    const openBtn = document.getElementById('open-sidebar-btn');
    const closeBtn = document.getElementById('close-sidebar');

    function toggleSidebar() {
        if (sidebar && overlay) {
            sidebar.classList.toggle('-translate-x-full');
            overlay.classList.toggle('hidden');
        }
    }

    if (openBtn) openBtn.addEventListener('click', toggleSidebar);
    if (closeBtn) closeBtn.addEventListener('click', toggleSidebar);
    if (overlay) overlay.addEventListener('click', toggleSidebar);
});

/* <a href="/tax-summary" class="sidebar-link flex items-center px-4 py-2 rounded-lg transition-colors">
    <svg class="sidebar-icon w-5 h-5 mr-3 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5.5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2zM10 8.5a.5.5 0 11-1 0 .5.5 0 011 0zm5 5a.5.5 0 11-1 0 .5.5 0 011 0z"></path></svg>
    Tax Summary
</a> */