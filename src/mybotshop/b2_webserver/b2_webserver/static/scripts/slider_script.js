// Function to update slider values and send data to the backend
function sendSliderData() {
    const linearVelocity = document.getElementById('slider1').value;
    const angularVelocity = document.getElementById('slider2').value;

    // Update the displayed values with units
    document.getElementById('slider1-value').textContent = `${linearVelocity/100} m/s`;
    document.getElementById('slider2-value').textContent = `${angularVelocity/100} rad/s`;

    // Send the data to the Python backend
    fetch('/slider_control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            linear_velocity: linearVelocity,
            angular_velocity: angularVelocity,
        }),
    })
        .then(response => response.json())
        .then(data => {
            console.log('Slider Data Sent Successfully:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}

// Add event listeners to the sliders
document.getElementById('slider1').addEventListener('input', sendSliderData);
document.getElementById('slider2').addEventListener('input', sendSliderData);