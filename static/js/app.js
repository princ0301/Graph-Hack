// static/js/app.js
document.addEventListener('DOMContentLoaded', function() {
    // Update theme and destination text
    const themeSelect = document.getElementById('travel_theme');
    const destInput = document.getElementById('destination');
    const themeText = document.getElementById('theme-text');
    const destText = document.getElementById('dest-text');

    themeSelect.addEventListener('change', function() {
        themeText.textContent = this.value;
    });
    
    destInput.addEventListener('input', function() {
        destText.textContent = this.value;
    });

    // Update days value
    const daysSlider = document.getElementById('num_days');
    const daysValue = document.getElementById('days-value');
    
    daysSlider.addEventListener('input', function() {
        daysValue.textContent = this.value;
    });

    // Set default dates
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const nextWeek = new Date(today);
    nextWeek.setDate(nextWeek.getDate() + 7);
    
    document.getElementById('departure_date').value = formatDate(tomorrow);
    document.getElementById('return_date').value = formatDate(nextWeek);

    // Form submission
    const form = document.getElementById('travelForm');
    const loading = document.querySelector('.loading');
    const formContainer = document.querySelector('.container-fluid');
    const resultsContainer = document.getElementById('resultsContainer');
    
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        loading.style.display = 'block';
        
        const formData = new FormData(form);
        
        // Add radio button values
        const budget = document.querySelector('input[name="budget"]:checked').value;
        formData.set('budget', budget);
        
        const flightClass = document.querySelector('input[name="flight_class"]:checked').value;
        formData.set('flight_class', flightClass);
        
        // Add checkbox values
        formData.set('visa_required', document.getElementById('visa_required').checked ? 'on' : '');
        formData.set('travel_insurance', document.getElementById('travel_insurance').checked ? 'on' : '');
        formData.set('currency_converter', document.getElementById('currency_converter').checked ? 'on' : '');
        
        fetch('/generate_plan', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loading.style.display = 'none';
            
            if (data.success) {
                // Show results
                displayResults(data.travel_plan);
                formContainer.style.display = 'none';
                resultsContainer.style.display = 'block';
                
                // Scroll to top
                window.scrollTo(0, 0);
            } else {
                alert('Error generating travel plan: ' + data.error);
            }
        })
        .catch(error => {
            loading.style.display = 'none';
            alert('Error: ' + error);
        });
    });
    
    // Plan another trip button
    document.getElementById('planAnotherTrip').addEventListener('click', function() {
        formContainer.style.display = 'block';
        resultsContainer.style.display = 'none';
    });

    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function displayResults(travelPlan) {
        // Update summary
        document.getElementById('result-theme').textContent = travelPlan.travel_theme;
        document.getElementById('result-dest').textContent = travelPlan.destination;
        document.getElementById('result-days').textContent = travelPlan.num_days;
        
        // Display flights
        const flightsContainer = document.getElementById('flightsContainer');
        flightsContainer.innerHTML = '';
        
        if (travelPlan.flights && travelPlan.flights.length > 0) {
            travelPlan.flights.forEach(flight => {
                const flightCard = document.createElement('div');
                flightCard.className = 'col-md-4';
                flightCard.innerHTML = `
                    <div class="flight-card">
                        ${flight.airline_logo ? `<img src="${flight.airline_logo}" width="100" alt="Flight Logo" />` : ''}
                        <h3 class="mt-2">${flight.airline}</h3>
                        <p><strong>Departure:</strong> ${flight.formatted_departure_time}</p>
                        <p><strong>Arrival:</strong> ${flight.formatted_arrival_time}</p>
                        <p><strong>Total Duration:</strong> ${flight.total_duration || 'N/A'}</p>
                        <p><strong>Price:</strong> ${flight.price}</p>
                        <a href="${flight.booking_link}" target="_blank" class="book-now-btn">Book Now</a>
                    </div>
                `;
                flightsContainer.appendChild(flightCard);
            });
        } else {
            flightsContainer.innerHTML = '<div class="col-12"><p>No flight options available.</p></div>';
        }
        
        // Display hotels
        const hotelsContainer = document.getElementById('hotelsContainer');
        hotelsContainer.innerHTML = '';
        
        if (travelPlan.accommodations && travelPlan.accommodations.hotels) {
            travelPlan.accommodations.hotels.forEach(hotel => {
                const hotelCard = document.createElement('div');
                hotelCard.className = 'hotel-card';
                hotelCard.innerHTML = `
                    <h4>${hotel.name}</h4>
                    <p><strong>Rating:</strong> ${hotel.rating}</p>
                    <p><strong>Price Range:</strong> ${hotel.price_range}</p>
                    <p>${hotel.description}</p>
                `;
                hotelsContainer.appendChild(hotelCard);
            });
        }
        
        // Display restaurants
        const restaurantsContainer = document.getElementById('restaurantsContainer');
        restaurantsContainer.innerHTML = '';
        
        if (travelPlan.accommodations && travelPlan.accommodations.restaurants) {
            travelPlan.accommodations.restaurants.forEach(restaurant => {
                const restaurantCard = document.createElement('div');
                restaurantCard.className = 'restaurant-card';
                restaurantCard.innerHTML = `
                    <h4>${restaurant.name}</h4>
                    <p><strong>Cuisine:</strong> ${restaurant.cuisine}</p>
                    <p><strong>Price Range:</strong> ${restaurant.price_range}</p>
                    <p>${restaurant.description}</p>
                `;
                restaurantsContainer.appendChild(restaurantCard);
            });
        }
        
        // Display itinerary
        const itineraryContainer = document.getElementById('itineraryContainer');
        itineraryContainer.innerHTML = '';
        
        if (travelPlan.itinerary && travelPlan.itinerary.length > 0) {
            travelPlan.itinerary.forEach(day => {
                const dayCard = document.createElement('div');
                dayCard.className = 'day-card';
                
                let activitiesHTML = '';
                if (day.activities && day.activities.length > 0) {
                    activitiesHTML = '<ul class="activity-list">';
                    day.activities.forEach(activity => {
                        activitiesHTML += `<li>${activity}</li>`;
                    });
                    activitiesHTML += '</ul>';
                }
                
                dayCard.innerHTML = `
                    <div class="day-title">${day.title}</div>
                    ${activitiesHTML}
                `;
                itineraryContainer.appendChild(dayCard);
            });
        } else {
            itineraryContainer.innerHTML = '<p>No itinerary available.</p>';
        }
    }
});