  document.addEventListener("DOMContentLoaded", function () {
    const itemsPerPage = 6;
    let currentPage = 1;
    const alcaldias = document.querySelectorAll('.alcaldia-page');
    const totalItems = alcaldias.length;
    const totalPages = Math.ceil(totalItems / itemsPerPage);

    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');

    function showPage(page) {
      const startIndex = (page - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;

      alcaldias.forEach((item, index) => {
        item.style.display = (index >= startIndex && index < endIndex) ? 'block' : 'none';
      });

      // Mostrar u ocultar botones
      prevButton.style.display = (page === 1) ? 'none' : 'inline-block';

      // Oculta "Siguiente" si estamos en la última página
      const remainingItems = totalItems - endIndex;
      nextButton.style.display = (remainingItems <= 0) ? 'none' : 'inline-block';
    }

    // Eventos de paginación
    prevButton.addEventListener('click', function (e) {
      e.preventDefault();
      if (currentPage > 1) {
        currentPage--;
        showPage(currentPage);
      }
    });

    nextButton.addEventListener('click', function (e) {
      e.preventDefault();
      const startIndex = currentPage * itemsPerPage;
      if (startIndex < totalItems) {
        currentPage++;
        showPage(currentPage);
      }
    });

    // Mostrar la primera página al cargar
    showPage(currentPage);
  });
