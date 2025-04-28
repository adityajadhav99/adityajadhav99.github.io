// last-updated.js

document.addEventListener('DOMContentLoaded', function () {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const today = new Date();
    document.getElementById('last-updated').innerHTML = `Last Updated: ${today.toLocaleDateString('en-GB', options)}`;
});
