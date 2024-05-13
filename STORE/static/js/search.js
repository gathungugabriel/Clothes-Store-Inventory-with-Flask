document.addEventListener('DOMContentLoaded', function() {
    // Function to display filtered results
    function displayFilteredResults(filteredData) {
        const productTableBody = document.getElementById('productTableBody');
        let tableHTML = '';

        // Clear previous results
        productTableBody.innerHTML = '';

        // Populate table with filtered data
        filteredData.forEach(product => {
            tableHTML += `
                <tr>
                    <td>${product.id}</td>
                    <td>${product.code}</td>
                    <td>${product.item}</td>
                    <td>${product.type_material}</td>
                    <td>${product.size}</td>
                    <td>${product.color}</td>
                    <td>${product.description}</td>
                    <td>${product.price}</td>
                    <td>${product.quantity}</td>
                </tr>`;
        });

        // Update the table body with the new HTML content
        productTableBody.innerHTML = tableHTML;

        // Show the product table
        document.getElementById('productTableContainer').style.display = 'block';
    }

    // Add event listener to the search button
    const searchButton = document.getElementById('searchButton');
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            const searchInput = document.getElementById('searchInput').value.trim().toLowerCase();

            // Send an AJAX request to filter products
            fetch('/filter_products', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ search_term: searchInput })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Display filtered results
                displayFilteredResults(data.products);
            })
            .catch(error => {
                console.error('Error filtering products:', error);
            });
        });
    } else {
        console.error('Search button not found');
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Function to filter products based on search term
    function filterProducts() {
        const searchTerm = searchInput.value.trim().toLowerCase();
        console.log('Search term:', searchTerm); // Debugging

        productRows.forEach(function(row) {
            const rowData = row.textContent.toLowerCase();
            if (rowData.includes(searchTerm)) {
                row.style.display = ''; // Show the row if it matches the search term
            } else {
                row.style.display = 'none'; // Hide the row if it doesn't match
            }
        });

        // Show/hide no results message based on whether any rows are visible
        const noResultsMessage = document.getElementById('noResultsMessage');
        if (productRows.length === 0 || [...productRows].every(row => row.style.display === 'none')) {
            noResultsMessage.style.display = 'block'; // Show message if no rows are visible
        } else {
            noResultsMessage.style.display = 'none'; // Hide message if at least one row is visible
        }
    }

    // Add event listener for input change in search input field
    const searchInput = document.getElementById('searchInput');
    const productRows = document.querySelectorAll('#productTableBody tr');
    searchInput.addEventListener('input', filterProducts);
});

