let map, marker, geocoder;

function initMap() {
  const centro = { lat: 19.4326, lng: -99.1332 };
  map = new google.maps.Map(document.getElementById("map"), {
    zoom: 12,
    center: centro,
  });

  marker = new google.maps.Marker({
    position: centro,
    map: map,
  });

  geocoder = new google.maps.Geocoder();

  // Lógica de autocompletado de colonia
  const coloniaInput = document.getElementById("colonia");
  $(coloniaInput).on("input", function () {
    const valor = this.value;

    if (valor.length < 3) return;

    $.ajax({
      url: "/api/direcciones/",
      data: { term: valor },
      success: function (data) {
        const lista = data.map(
          (item) => `<option value="${item.colonia}" 
                          data-cp="${item.cp}" 
                          data-municipio="${item.municipio}" 
                          data-estado="${item.estado}">
                     ${item.label}
                   </option>`
        );

        const datalist = $("#sugerencias");
        datalist.html(lista.join(""));
      },
    });
  });

  coloniaInput.addEventListener("change", function () {
    const selected = $("#sugerencias option").filter(function () {
      return this.value === coloniaInput.value;
    });

    if (selected.length) {
      $("#cp").val(selected.data("cp"));
      $("#municipio").val(selected.data("municipio"));
      $("#estado").val(selected.data("estado"));
      actualizarMapa();
    }
  });

  // ------------------------------
  // Cargar selects dinámicos
  // ------------------------------

  function cargarOpciones(url, selectId, clave, valor) {
    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        const select = document.getElementById(selectId);
        data.forEach((item) => {
          const option = document.createElement("option");
          option.value = item[clave];
          option.textContent = item[valor];
          select.appendChild(option);
        });
      })
      .catch((error) => console.error(`Error cargando ${selectId}:`, error));
  }

  cargarOpciones("/estados/", "estado", "id_estado", "nombre");
  cargarOpciones("/municipios/", "municipio", "id_municipio", "nombre");
  cargarOpciones("/colonias/", "colonia", "id_colonia", "nombre");
  cargarOpciones("/codigos-postales/", "cp", "id_codigo_postal", "codigo");
}

function actualizarMapa() {
  const colonia = $("#colonia").val();
  const cp = $("#cp").val();
  const municipio = $("#municipio").val();
  const estado = $("#estado").val();
  const direccion = `${colonia}, ${cp}, ${municipio}, ${estado}, México`;

  geocoder.geocode({ address: direccion }, function (results, status) {
    if (status === "OK") {
      const location = results[0].geometry.location;
      map.setCenter(location);
      map.setZoom(16);
      marker.setPosition(location);
    }
  });
}
