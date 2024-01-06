var cartItems = JSON.parse('{{ cart_items|tojson|safe }}');
updateCartDisplay();

function updateCartDisplay() {
  var cartItemsDiv = document.getElementById('cart-items');
  cartItemsDiv.innerHTML = '';

  if (cartItems.length === 0) {
    cartItemsDiv.innerHTML = '<p>Your cart is empty.</p>';
    return;
  }

  var itemsTable = document.createElement('table');
  var headerRow = itemsTable.insertRow();
  headerRow.innerHTML = '<th>Product Name</th><th>Price</th><th>Quantity</th>';

  for (var i = 0; i < cartItems.length; i++) {
    var item = cartItems[i];
    var row = itemsTable.insertRow();
    row.innerHTML = '<td>' + item.product_name + '</td><td>' + item.price + '</td><td>' + item.quantity + '</td>';
  }

  cartItemsDiv.appendChild(itemsTable);
}