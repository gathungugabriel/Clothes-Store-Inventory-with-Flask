// search.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed');

    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const productTableBody = document.getElementById('productTableBody');
    const noResultsMessage = document.getElementById('noResultsMessage');
    const addDataButton = document.getElementById('addDataButton');
    const codeInput = document.getElementById('code');
    const buyingPriceInput = document.getElementById('buying_price');
    const sellingPriceInput = document.getElementById('selling_price');

    // Function to hide flash messages after 2 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.display = 'none';
        }, 2000);
    });

    if (searchButton && searchInput) {
        searchButton.addEventListener('click', () => {
            console.log('Search button clicked');
            const searchTerm = searchInput.value.trim().toLowerCase();
            console.log('Search term:', searchTerm);
            if (searchTerm) {
                fetch('/filter_products', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ search_term: searchTerm }),
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Filtered products data:', data);
                    const { products } = data;
                    productTableBody.innerHTML = '';
                    if (products.length > 0) {
                        let grandTotalQuantity = 0;
                        let grandTotalBuyingPrice = 0;
                        let grandTotalSellingPrice = 0;
                        let grandTotalProfit = 0;

                        products.forEach(group => {
                            const category = group.category;
                            const item = group.item;
                            const formattedCode = group.products[0].code.replace(/ /g, '_').replace(/-/g, '_');
                            const totalQuantity = group.products.reduce((sum, product) => sum + product.quantity, 0);
                            const totalBuyingPrice = group.products.reduce((sum, product) => sum + (product.buying_price * product.quantity), 0);
                            const totalSellingPrice = group.products.reduce((sum, product) => sum + (product.selling_price * product.quantity), 0);
                            const totalProfit = group.products.reduce((sum, product) => sum + (product.profit * product.quantity), 0);

                            grandTotalQuantity += totalQuantity;
                            grandTotalBuyingPrice += totalBuyingPrice;
                            grandTotalSellingPrice += totalSellingPrice;
                            grandTotalProfit += totalProfit;

                            const row = `
                                <tr>
                                    <td>${item}</td>
                                    <td>${category}</td>
                                    <td>${totalQuantity}</td>
                                    <td>${totalBuyingPrice.toFixed(2)}</td>
                                    <td>${totalSellingPrice.toFixed(2)}</td>
                                    <td>${totalProfit.toFixed(2)}</td>
                                    <td><button class="btn btn-info toggle-button" data-code="${formattedCode}">Expand</button></td>
                                </tr>
                                <tr id="items_${formattedCode}" class="nested-table-container d-none">
                                    <td colspan="7"></td>
                                </tr>
                            `;
                            productTableBody.insertAdjacentHTML('beforeend', row);
                        });

                        const totalsRow = `
                            <tr>
                                <td colspan="2"><strong>Totals</strong></td>
                                <td><strong>${grandTotalQuantity}</strong></td>
                                <td><strong>${grandTotalBuyingPrice.toFixed(2)}</strong></td>
                                <td><strong>${grandTotalSellingPrice.toFixed(2)}</strong></td>
                                <td><strong>${grandTotalProfit.toFixed(2)}</strong></td>
                                <td></td>
                            </tr>
                        `;
                        productTableBody.insertAdjacentHTML('beforeend', totalsRow);

                        noResultsMessage.classList.add('d-none');
                    } else {
                        noResultsMessage.classList.remove('d-none');
                    }
                    attachToggleEventListeners();
                })
                .catch(error => {
                    console.error('Error fetching filtered products:', error);
                });
            }
        });
    } else {
        console.error('Search input or button not found');
    }

    if (addDataButton) {
        addDataButton.addEventListener('click', function() {
            console.log('Add Data button clicked');
            fetch('/add_data_to_db')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Add data response:', data);
                    alert(data.message);
                })
                .catch(error => {
                    console.error('Error adding data to database:', error);
                    alert('Error adding data to database.');
                });
        });
    } else {
        console.error('Add Data button not found');
    }

    function attachToggleEventListeners() {
        console.log('Attaching toggle event listeners');
        const toggleButtons = document.querySelectorAll('.toggle-button');
        toggleButtons.forEach(button => {
            console.log('Attaching event listener to button:', button);
            button.addEventListener('click', (event) => {
                console.log('Toggle button clicked');
                const code = event.target.getAttribute('data-code');
                console.log('Code:', code);
                const nestedTableContainer = document.getElementById(`items_${code}`);
                console.log('Nested table container:', nestedTableContainer);
                if (nestedTableContainer) {
                    nestedTableContainer.classList.toggle('d-none');
                    if (!nestedTableContainer.classList.contains('d-none')) {
                        fetch('/expand_items', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ item: code }),
                        })
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Network response was not ok');
                            }
                            return response.json();
                        })
                        .then(data => {
                            console.log('Expanded items data:', data);
                            const { products } = data;
                            const totalNestedBuyingPrice = products.reduce((sum, product) => sum + product.buying_price, 0);
                            const totalNestedSellingPrice = products.reduce((sum, product) => sum + product.selling_price, 0);
                            const totalNestedProfit = products.reduce((sum, product) => sum + product.profit, 0);
                            const nestedTableContent = products.map(product => `
                                <tr>
                                    <td>${product.code}</td>
                                    <td>${product.size}</td>
                                    <td>${product.type_material}</td>
                                    <td>${product.color}</td>
                                    <td>${product.description}</td>
                                    <td>${product.buying_price}</td>
                                    <td>${product.selling_price}</td>
                                    <td>${product.profit}</td>
                                    <td>
                                        <button class="btn btn-warning update-button" data-code="${product.code}">Update</button>
                                        <button class="btn btn-danger delete-button" data-code="${product.code}">Delete</button>
                                    </td>
                                </tr>
                            `).join('');
                            nestedTableContainer.querySelector('td').innerHTML = `
                                <table class="table table-bordered">
                                    <thead>
                                        <tr>
                                            <th>Code</th>
                                            <th>Size</th>
                                            <th>Type Material</th>
                                            <th>Color</th>
                                            <th>Description</th>
                                            <th>Buying Price</th>
                                            <th>Selling Price</th>
                                            <th>Profit</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${nestedTableContent}
                                    </tbody>
                                    <tfoot>
                                        <tr>
                                            <td colspan="5"><strong>Totals</strong></td>
                                            <td><strong>${totalNestedBuyingPrice.toFixed(2)}</strong></td>
                                            <td><strong>${totalNestedSellingPrice.toFixed(2)}</strong></td>
                                            <td><strong>${totalNestedProfit.toFixed(2)}</strong></td>
                                            <td></td>
                                        </tr>
                                    </tfoot>
                                </table>
                            `;
                            attachUpdateDeleteEventListeners();
                        })
                        .catch(error => {
                            console.error('Error expanding items:', error);
                        });
                    }
                } else {
                    console.error(`Nested table container with ID items_${code} not found`);
                }
            });
        });
    }

    function attachUpdateDeleteEventListeners() {
        console.log('Attaching update and delete event listeners');
        const updateButtons = document.querySelectorAll('.update-button');
        const deleteButtons = document.querySelectorAll('.delete-button');

        updateButtons.forEach(button => {
            button.addEventListener('click', (event) => {
                console.log('Update button clicked');
                const code = event.target.getAttribute('data-code');
                // Add your update logic here
            });
        });

        deleteButtons.forEach(button => {
            button.addEventListener('click', (event) => {
                console.log('Delete button clicked');
                const code = event.target.getAttribute('data-code');
                // Add your delete logic here
            });
        });
    }

    attachToggleEventListeners();
    
    const prefixes = {
        'SC': { item: 'shirt', category: 'casual' },
        'SO': { item: 'shirt', category: 'official' },
        'TC': { item: 'trouser', category: 'casual' },
        'TO': { item: 'trouser', category: 'official' },
        'TSC': { item: 'tshirt', category: 'casual' },
        'TSO': { item: 'tshirt', category: 'official' },
        'SWC': { item: 'sweater', category: 'casual' },
        'SWO': { item: 'sweater', category: 'official' },
        'CC': { item: 'coat', category: 'casual' },
        'CO': { item: 'coat', category: 'official' },
        'SUC': { item: 'suit', category: 'casual' },
        'SUO': { item: 'suit', category: 'official' },
        'TIE': { item: 'tie', category: '' },
        'BLT': { item: 'belt', category: '' },
        'SHRT': { item: 'short', category: '' },
        'SHC': { item: 'shoes', category: 'casual' },
        'SHO': { item: 'shoes', category: 'official' },
        'BX': { item: 'boxers', category: '' },
        'VST': { item: 'vest', category: '' }
    };

    function autoFillItemAndCategory() {
        const code = codeInput.value;  // Use codeInput here
        const prefix = code.match(/[A-Za-z]+/)[0];
        if (prefixes[prefix]) {
            document.getElementById('item').value = prefixes[prefix].item;
            document.getElementById('category').value = prefixes[prefix].category;
        } else {
            document.getElementById('item').value = '';
            document.getElementById('category').value = '';
        }
    }

    function calculateProfit() {
        const buyingPrice = parseFloat(buyingPriceInput.value) || 0;
        const sellingPrice = parseFloat(sellingPriceInput.value) || 0;
        document.getElementById('profit').value = (sellingPrice - buyingPrice).toFixed(2);
    }

    if (codeInput && buyingPriceInput && sellingPriceInput) {
        codeInput.addEventListener('input', autoFillItemAndCategory);
        buyingPriceInput.addEventListener('input', calculateProfit);
        sellingPriceInput.addEventListener('input', calculateProfit);
    } else {
        console.error('Code input, buying price input, or selling price input not found');
    }
});
