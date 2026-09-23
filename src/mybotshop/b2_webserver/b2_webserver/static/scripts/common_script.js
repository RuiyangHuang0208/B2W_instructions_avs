/*
Software License Agreement (BSD)

@author    Salman Omar Sohail <support@mybotshop.de>
@copyright (c) 2025, MYBOTSHOP GmbH, Inc., All rights reserved.
*/

// Dynamically load the navbar 
const nav = document.querySelector('.navbar');
const navBarUrl = "../static/common/navbar.html";
fetch(navBarUrl)
    .then(response => response.text())
    .then(data => {
        nav.innerHTML = data;
    });

// Dynamically load the footer
const footer_ = document.querySelector('.footer_');
const footerBarUrl = "../static/common/footer.html";
fetch(footerBarUrl)
    .then(response => response.text())
    .then(data => {
        footer_.innerHTML = data;
    });

// Dynamically load the popup
const popup_ = document.querySelector('.popup_');
const popUpUrl = "../static/common/popup.html";

fetch(popUpUrl)
    .then(response => response.text())
    .then(data => {
        popup_.innerHTML = data;
        const modal = document.getElementById('startupModal');
        if (modal) {
            modal.style.display = 'block';

            // Auto-close after 3 seconds
            setTimeout(() => {
                closeModal();
            }, 1000);
        }
    });

// Show the startup modal on page load
function closeModal() {
    document.getElementById('startupModal').style.display = 'none';
}
