// Navbar changing of active item
document.addEventListener('DOMContentLoaded', function () {
    var url = window.location.pathname;
    console.log(url);
    document.querySelector('li.nav-item a[href="'+ url +'"]').classList.add('active');
});
