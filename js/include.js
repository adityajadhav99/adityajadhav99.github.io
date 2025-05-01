window.addEventListener("DOMContentLoaded", () => {
    const includes = document.querySelectorAll('[id^="contact-card"]');

    includes.forEach(include => {
        fetch("contact-details/contact-card.html")
            .then(response => response.text())
            .then(data => {
                include.innerHTML = data;
            });
    });
});
