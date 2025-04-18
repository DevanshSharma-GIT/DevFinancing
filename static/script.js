document.addEventListener('DOMContentLoaded', function () {
    console.log('Script loaded and DOM content loaded');

    // Retrieve transactions data with error handling
    let transactions = [];
    const transactionsDataElement = document.getElementById('transactions-data');
    if (transactionsDataElement && transactionsDataElement.dataset.transactions) {
        try {
            transactions = JSON.parse(transactionsDataElement.dataset.transactions);
            console.log('Parsed transactions:', transactions);
        } catch (e) {
            console.error('Failed to parse transactions JSON:', e);
            transactions = [];
        }
    } else {
        console.warn('No transactions data element or dataset found');
    }

    // Dynamically update category totals table
    const expenseByCategory = {};
    transactions.forEach(transaction => {
        if (transaction?.type === 'expense') {
            const cat = transaction?.category || 'other';
            expenseByCategory[cat] = (expenseByCategory[cat] || 0) + parseFloat(transaction?.amount || 0);
        }
    });
    console.log('Category totals:', expenseByCategory);

    if (Object.keys(expenseByCategory).length > 0) {
        const categoryTableBody = document.getElementById('categoryTotals');
        if (categoryTableBody) {
            categoryTableBody.innerHTML = '';
            for (const [category, total] of Object.entries(expenseByCategory)) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${category.charAt(0).toUpperCase() + category.slice(1)}</td>
                    <td class="expense">${total.toFixed(2)}</td>
                `;
                categoryTableBody.appendChild(row);
            }
            console.log('Category totals table updated:', expenseByCategory);
        } else {
            console.error('Category totals table body not found');
        }
    } else {
        console.log('No category totals to display');
    }
});