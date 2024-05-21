// search.js

document.addEventListener('DOMContentLoaded', function() {
    // Function to update the product table with filtered results
    function displayFilteredResults(filteredData) {
        const productTableBody = document.getElementById('productTableBody');
        let tableHTML = '';

        // Clear the existing table body content
        productTableBody.innerHTML = '';

        // Generate HTML for each filtered product and append it to the table
        filteredData.forEach(product => {
            tableHTML += `
                <tr>
                    <td>${product.item}</td>
                    <td>${product.type_material}</td>
                    <td>${product.size}</td>
                    <td>${product.price}</td>
                    <td>
                        <button class="btn btn-info toggle-button" 
                                data-item="${product.item}"
                                data-type-material="${product.type_material}"
                                data-size="${product.size}"
                                data-price="${product.price}">List</button>
                    </td>
                </tr>
                <tr id="items_${product.item.replace(/\s+/g, '_')}" class="nested-table-container d-none">
                    <td colspan="5">
                        <!-- List of items goes here -->
                    </td>
                </tr>`;
        });

        // Update the product table with the filtered results
        productTableBody.innerHTML = tableHTML;
        document.getElementById('productTableContainer').style.display = 'block';

        // Reattach event listeners to the toggle buttons
        attachToggleEventListeners();
    }

    // Add event listener for the search button
    document.getElementById('searchButton').addEventListener('click', function() {
        // Get the search term from the input field
        const searchInput = document.getElementById('searchInput').value.trim().toLowerCase();

        // Send AJAX request to the server with the search term
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
            // Update the product table with the filtered results
            displayFilteredResults(data.products);

            // Display a message if no results are found
            if (data.products.length === 0) {
                document.getElementById('noResultsMessage').style.display = 'block';
            } else {
                document.getElementById('noResultsMessage').style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error filtering products:', error);
            // Handle error
        });
    });

    // Function to attach event listeners to the toggle buttons
    function attachToggleEventListeners() {
        const toggleButtons = document.querySelectorAll('.toggle-button');

        toggleButtons.forEach(button => {
            button.addEventListener('click', function() {
                const item = this.getAttribute('data-item');
                const typeMaterial = this.getAttribute('data-type-material');
                const size = this.getAttribute('data-size');
                const price = this.getAttribute('data-price');
                const itemList = document.getElementById(`items_${item.replace(/\s+/g, '_')}`);

                // Send AJAX request to expand items when a toggle button is clicked
                fetch('/expand_items', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        item: item,
                        type_material: typeMaterial,
                        size: size,
                        price: price
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    // Update the nested table with the expanded items
                    if (!itemList) {
                        console.error(`Item list container not found for item: ${item}`);
                        return;
                    }
                    let tableHTML = '';
                    data.forEach(product => {
                        tableHTML += `
                            <tr>
                                <td>${product.code}</td>
                                <td>${product.item}</td>
                                <td>${product.color}</td>
                                <td>${product.description}</td>
                                <td>${product.price}</td>
                            </tr>`;
                    });

                    itemList.querySelector('td').innerHTML = `
                        <table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th scope="col">Code</th>
                                    <th scope="col">Item</th>
                                    <th scope="col">Color</th>
                                    <th scope="col">Description</th>
                                    <th scope="col">Price</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${tableHTML}
                            </tbody>
                        </table>`;
                    itemList.classList.toggle('d-none');
                })
                .catch(error => {
                    console.error('Error fetching items:', error);
                    if (itemList) {
                        itemList.querySelector('td').textContent = 'An error occurred while fetching items. Please try again later.';
                        itemList.classList.toggle('d-none');
                    }
                });
            });
        });
    }

    // Attach event listeners to the toggle buttons
    attachToggleEventListeners();
});
