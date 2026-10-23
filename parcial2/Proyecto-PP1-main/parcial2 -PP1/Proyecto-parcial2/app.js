
const formulario = document.getElementById("formularioModelo");
const mensaje = document.getElementById("mensajeFormulario");

const archivos = [
  "vistaFrontal",
  "vistaTrasera",
  "vistaSuperior",
  "vistaInferior"
];

const TAMANO_MAXIMO = 10 * 1024 * 1024; // 10 MB

// Validación del formulario: solo se ejecuta en la página que lo contiene
if (formulario && mensaje) {
  formulario.addEventListener("submit", function (evento) {
    mensaje.textContent = "";
    mensaje.classList.remove("d-none", "alert-success", "alert-danger");

    for (const id of archivos) {
      const campo = document.getElementById(id);
      const archivo = campo.files[0];

      if (!archivo) {
        evento.preventDefault();
        mostrarError("Tenés que seleccionar las cuatro imágenes.");
        campo.focus();
        return;
      }

      if (archivo.size > TAMANO_MAXIMO) {
        evento.preventDefault();
        mostrarError("Cada imagen debe pesar como máximo 10 MB.");
        campo.focus();
        return;
      }

      if (!["image/jpeg", "image/png"].includes(archivo.type)) {
        evento.preventDefault();
        mostrarError("Las imágenes deben estar en formato JPG o PNG.");
        campo.focus();
        return;
      }
    }

    mensaje.textContent = "Enviando imágenes al servidor...";
    mensaje.classList.add("alert-success");
  });
}

function mostrarError(texto) {
  mensaje.textContent = texto;
  mensaje.classList.add("alert-danger");
}

// Buscador de categorías: solo se ejecuta si existe en esta página
const buscador = document.getElementById("buscadorCategorias");
const tarjetas = document.querySelectorAll("#listaCategorias .category-card");
const mensajeSinResultados = document.getElementById("mensajeSinResultados");

if (buscador && mensajeSinResultados) {
  buscador.addEventListener("input", function () {
    const textoBuscado = buscador.value.trim().toLowerCase();
    let categoriasVisibles = 0;

    tarjetas.forEach(function (tarjeta) {
      const nombreCategoria = tarjeta.querySelector("h5").textContent.toLowerCase();
      const coincide = nombreCategoria.includes(textoBuscado);

      tarjeta.parentElement.classList.toggle("d-none", !coincide);

      if (coincide) {
        categoriasVisibles++;
      }
    });

    mensajeSinResultados.classList.toggle(
      "d-none",
      categoriasVisibles > 0
    );
  });
}
