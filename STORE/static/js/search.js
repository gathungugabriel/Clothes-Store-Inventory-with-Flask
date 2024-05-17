document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded event fired');

    function attachToggleEventListeners() {
        const toggleButtons = document.querySelectorAll('.toggle-button');
        console.log('Found', toggleButtons.length, 'toggle buttons');

        toggleButtons.forEach(button => {
            console.log('Attaching event listener to button:', button);
            button.addEventListener('click', function() {
                const item = this.getAttribute('data-item');
                const typeMaterial = this.getAttribute('data-type-material');
                const size = this.getAttribute('data-size');
                const price = this.getAttribute('data-price');
                const itemList = document.getElementById(`items_${item.replace(/\s+/g, '_')}`);

                console.log('Clicked toggle button for item:', item);

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
                    console.log('Fetched data:', data);
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

                    itemList.innerHTML = `
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
                        itemList.textContent = 'An error occurred while fetching items. Please try again later.';
                        itemList.classList.toggle('d-none');
                    }
                });
            });
        });

        console.log('Event listeners attached to toggle buttons');
    }

    function displayFilteredResults(filteredData) {
        console.log('displayFilteredResults called with data:', filteredData);
        const productTableBody = document.getElementById('productTableBody');
        let tableHTML = '';

        productTableBody.innerHTML = '';

        filteredData.forEach(product => {
            tableHTML += `
                <tr>
                    <td>${product.item}</td>
                    <td>${product.type_material}</td>
                    <td>${product.size}</td>
                    <td>${product.price}</td>
                    <td>${product.quantity}</td>
                    <td>
                        <button class="btn btn-info toggle-button" 
                                data-item="${product.item}"
                                data-type-material="${product.type_material}"
                                data-size="${product.size}"
                                data-price="${product.price}">List</button>
                        <div id="items_${product.item.replace(/\s+/g, '_')}" style="display: none;">
                            <!-- List of items goes here -->
                        </div>
                    </td>
                </tr>`;
        });

        productTableBody.innerHTML = tableHTML;
        document.getElementById('productTableContainer').style.display = 'block';

        attachToggleEventListeners();
    }

    const searchButton = document.getElementById('searchButton');
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            console.log('Search button clicked');
            const searchInput = document.getElementById('searchInput').value.trim().toLowerCase();
            console.log('Search term:', searchInput);

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
                console.log('Filtered data received:', data);
                displayFilteredResults(data.products);
                if (data.products.length === 0) {
                    document.getElementById('noResultsMessage').style.display = 'block';
                } else {
                    document.getElementById('noResultsMessage').style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error filtering products:', error);
                const productTableBody = document.getElementById('productTableBody');
                productTableBody.textContent = 'An error occurred while filtering products. Please try again later.';
            });
        });
    } else {
        console.error('Search button not found');
    }

    attachToggleEventListeners();
});
