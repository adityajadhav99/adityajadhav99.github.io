// include.js - Dynamic component loader with path resolution and error fallback

window.addEventListener("DOMContentLoaded", () => {
    const includes = document.querySelectorAll('[id^="contact-card"]');
    if (!includes.length) return;

    // Detect if current page is inside a subdirectory
    const pathname = window.location.pathname.replace(/\\/g, '/');
    const isSubfolder = pathname.includes('/projects/') || pathname.includes('/research/');
    const basePath = isSubfolder ? '../' : './';

    fetch(basePath + "contact-details/contact-card.html")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(data => {
            // Adjust image path based on current page location
            const adjustedData = isSubfolder 
                ? data 
                : data.replace('src="../images/', 'src="./images/');

            includes.forEach(include => {
                include.innerHTML = adjustedData;
            });
        })
        .catch(err => {
            console.warn("Contact card asynchronous load note:", err.message);
        });
});
