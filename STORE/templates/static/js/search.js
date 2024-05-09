// search.js

document.addEventListener('DOMContentLoaded', function() {
    // Add event listener to the search button
    document.getElementById('searchButton').addEventListener('click', function() {
        // Get the search query from the input field
        var query = document.getElementById('searchInput').value;
        
        // Send an AJAX request to the server to search for products
        fetch('/search?q=' + encodeURIComponent(query))
            .then(response => response.json())
            .then(data => {
                // Clear previous search results
                document.getElementById('searchResults').innerHTML = '';

                // Check if there are search results
                if (data.length > 0) {
                    // Iterate through each search result and create HTML elements to display them
                    data.forEach(product => {
                        var productHTML = `
                            <tr>
                                <th scope="row">${product.id}</th>
                                <td>${product.code}</td>
                                <td>${product.item}</td>
                                <td>${product.type_material}</td>
                                <td>${product.size}</td>
                                <td>${product.color}</td>
                                <td>${product.description}</td>
                                <td>${product.price}</td>
                                <td>${product.quantity}</td>
                            </tr>
                        `;
                        // Append the HTML for each product to the search results table
                        document.getElementById('searchResults').innerHTML += productHTML;
                    });
                } else {
                    // If no results found, display a message
                    document.getElementById('searchResults').innerHTML = '<tr><td colspan="9">No results found.</td></tr>';
                }
            })
            .catch(error => {
                console.error('Error fetching search results:', error);
            });
    });
});
